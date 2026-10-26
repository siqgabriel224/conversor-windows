"""Local conversion worker. One JSON request on stdin; JSON events on stdout."""

from __future__ import annotations
import json, os, sys, subprocess, tempfile, shutil, re, traceback, time, uuid
from contextlib import closing
from pathlib import Path


def emit(**event):
    print(json.dumps(event, ensure_ascii=False), flush=True)


cancel_file = None


def check_cancel():
    if cancel_file and Path(cancel_file).exists():
        raise ValueError("Conversão cancelada.")


def run(args, timeout=3600, on_tick=None):
    with subprocess.Popen(
        [str(a) for a in args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=0x08000000 if os.name == "nt" else 0,
    ) as process:
        deadline = time.monotonic() + timeout
        try:
            while True:
                check_cancel()
                if time.monotonic() > deadline:
                    raise ValueError("O componente excedeu o tempo limite.")
                try:
                    out, err = process.communicate(timeout=0.25)
                    break
                except subprocess.TimeoutExpired:
                    if on_tick is not None:
                        on_tick()
        except BaseException:
            process.kill()
            process.wait()
            raise
    if process.returncode:
        text = (err or out).decode("utf-8", "replace")[-1600:]
        raise ValueError("O componente de conversão recusou o arquivo. " + text)
    return out.decode("utf-8", "replace")


def pages_for(spec, count):
    if not spec.strip():
        return list(range(count))
    pages = []
    for item in spec.split(","):
        item = item.strip()
        if not re.fullmatch(r"\d+(?:-\d+)?", item):
            raise ValueError("Páginas inválidas. Use, por exemplo, 1-3,5.")
        start, _, end = item.partition("-")
        a = int(start)
        b = int(end or start)
        if a < 1 or b < a or b > count:
            raise ValueError(f"Intervalo fora do documento ({count} páginas).")
        pages.extend(range(a - 1, b))
    return list(dict.fromkeys(pages))


def publish_file(source, folder, name):
    """Reserve the output atomically; only replace a reservation made by this worker."""
    stem = Path(name).stem
    suffix = Path(name).suffix
    for n in range(10000):
        output = folder / (name if n == 0 else f"{stem} ({n}){suffix}")
        try:
            fd = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
        except FileExistsError:
            continue
        temporary = folder / (".conversor-" + uuid.uuid4().hex + ".tmp")
        try:
            check_cancel()
            shutil.copyfile(source, temporary)
            # Windows scanners/sync clients can briefly lock a newly reserved name.
            for attempt in range(6):
                check_cancel()
                try:
                    os.replace(temporary, output)
                    break
                except PermissionError:
                    if attempt == 5:
                        raise
                    time.sleep(0.05 * 2**attempt)
        except BaseException:
            temporary.unlink(missing_ok=True)
            output.unlink(missing_ok=True)
            raise
        return str(output)
    raise ValueError("Não foi possível reservar um nome para o resultado.")


def publish_dir(source, folder, name):
    for n in range(10000):
        output = folder / (name if n == 0 else f"{name} ({n})")
        try:
            output.mkdir()
        except FileExistsError:
            continue
        try:
            for child in source.iterdir():
                shutil.move(str(child), str(output / child.name))
        except BaseException:
            raise ValueError(f"Falha ao salvar. Resultados parciais em {output}")
        return str(output)
    raise ValueError("Não foi possível criar a pasta de saída.")


def safe_archive_listing(text):
    listing = text.split("----------", 1)[-1]
    for line in listing.splitlines():
        if line.startswith("Path = "):
            path = line[7:].replace("\\", "/")
            if path.startswith("/") or ":" in path or ".." in path.split("/"):
                raise ValueError("O arquivo compactado contém caminhos inseguros.")
        link_field = line.partition("=")
        has_link = link_field[0].strip() in ("Symbolic Link", "Hard Link") and bool(
            link_field[2].strip()
        )
        if has_link or re.search(r"(?:Attributes|Mode) = .*\bl[rwx-]{9}", line):
            raise ValueError(
                "A extração de links em arquivos compactados não é suportada."
            )


def convert(request):
    global cancel_file
    cancel_file = request.get("cancellationFile")
    check_cancel()
    inputs = [Path(x).resolve(strict=True) for x in request["inputs"]]
    if not inputs or any(not p.is_file() for p in inputs):
        raise ValueError(
            "Adicione arquivos existentes; pastas não são aceitas nesta operação."
        )
    target = request["target"]
    first = inputs[0]
    ext = first.suffix.lower().lstrip(".")
    quality = max(1, min(100, int(request.get("quality", 85))))
    width = max(0, min(16000, int(request.get("width", 0))))
    engine = request["engines"]
    folder = Path(request.get("outputDirectory") or first.parent)
    folder.mkdir(parents=True, exist_ok=True)
    if not folder.is_dir():
        raise ValueError("A pasta de saída é inválida.")
    emit(progress=10, message="Arquivo recebido; conversão local iniciada")
    with tempfile.TemporaryDirectory(prefix="conversor-job-") as temp:
        stage = Path(temp)
        result = stage / f"{first.stem}.{target}"
        output_files = []
        output_dir = None
        if target in ("zip", "7z"):
            # Flatten inputs explicitly, assigning distinct names if basenames collide.
            bundle = stage / "entrada"
            bundle.mkdir()
            used = set()
            for p in inputs:
                name = p.name
                n = 1
                while name.lower() in used:
                    name = f"{p.stem} ({n}){p.suffix}"
                    n += 1
                used.add(name.lower())
                shutil.copyfile(p, bundle / name)
            result = stage / f"{first.stem}-arquivos.{target}"
            run(
                [
                    engine["sevenzip"],
                    "a",
                    "-t" + target,
                    "-mx=5",
                    result,
                    str(bundle / "*"),
                ]
            )
            output_files = [result]
        elif target == "extract":
            safe_archive_listing(run([engine["sevenzip"], "l", "-slt", first]))
            output_dir = stage / (first.stem + "-extraido")
            output_dir.mkdir()
            run([engine["sevenzip"], "x", first, "-o" + str(output_dir), "-y", "-aou"])
            for child in output_dir.rglob("*"):
                if child.is_symlink() or not child.resolve().is_relative_to(
                    output_dir.resolve()
                ):
                    raise ValueError(
                        "O arquivo compactado contém um link não suportado."
                    )
        elif ext == "pdf" or target == "pdf-merge":
            from pypdf import PdfReader, PdfWriter

            reader = PdfReader(first)
            if reader.is_encrypted:
                raise ValueError(
                    "PDF protegido por senha. Abra uma cópia desbloqueada para converter."
                )
            pages = pages_for(request.get("pages", ""), len(reader.pages))
            if target in ("png", "jpg"):
                import pypdfium2 as pdfium

                output_dir = stage / (first.stem + "-" + target)
                output_dir.mkdir()
                with closing(pdfium.PdfDocument(str(first))) as pdf:
                    for n, index in enumerate(pages):
                        check_cancel()
                        page = pdf[index]
                        bitmap = page.render(scale=2)
                        im = bitmap.to_pil().convert("RGB")
                        if width:
                            im.thumbnail((width, 16000))
                        im.save(
                            output_dir / f"pagina-{index + 1:03d}.{target}",
                            quality=quality,
                        )
                        bitmap.close()
                        page.close()
                        emit(
                            progress=15 + 70 * (n + 1) / len(pages),
                            message=f"Página {n + 1} de {len(pages)}",
                        )
            elif target == "pdf-compress":
                result = stage / (first.stem + "-comprimido.pdf")
                run(
                    [
                        engine["ghostscript"],
                        "-q",
                        "-dSAFER",
                        "-dBATCH",
                        "-dNOPAUSE",
                        "-sDEVICE=pdfwrite",
                        "-dCompatibilityLevel=1.4",
                        "-dPDFSETTINGS=/ebook",
                        "-sOutputFile=" + str(result),
                        first,
                    ]
                )
                output_files = [result]
            elif target in ("pdf-merge", "pdf-extract"):
                writer = PdfWriter()
                if target == "pdf-merge":
                    for source in inputs:
                        writer.append(str(source))
                else:
                    for index in pages:
                        writer.add_page(reader.pages[index])
                result = stage / (
                    first.stem
                    + ("-unidos.pdf" if target == "pdf-merge" else "-paginas.pdf")
                )
                with result.open("wb") as handle:
                    writer.write(handle)
                output_files = [result]
            elif target == "pdf-split":
                output_dir = stage / (first.stem + "-paginas")
                output_dir.mkdir()
                for index in pages:
                    check_cancel()
                    writer = PdfWriter()
                    writer.add_page(reader.pages[index])
                    with (output_dir / f"pagina-{index + 1:03d}.pdf").open(
                        "wb"
                    ) as handle:
                        writer.write(handle)
            else:
                raise ValueError("Conversão PDF não suportada.")
        elif ext in ("jpg", "jpeg", "png", "webp", "bmp", "tif", "tiff", "gif", "heic"):
            args = [engine["magick"], str(first) + "[0]", "-auto-orient"]
            if width:
                args += ["-resize", f"{width}x>"]
            args += ["-quality", str(quality)]
            if target == "pdf":
                png = stage / "imagem.png"
                run(args + [png])
                from PIL import Image

                im = Image.open(png)
                background = Image.new("RGB", im.size, "white")
                if "A" in im.getbands():
                    background.paste(im, mask=im.getchannel("A"))
                else:
                    background.paste(im.convert("RGB"))
                background.save(result, "PDF", resolution=150)
            else:
                run(args + [result])
            output_files = [result]
        elif ext in (
            "doc",
            "docx",
            "odt",
            "rtf",
            "txt",
            "xls",
            "xlsx",
            "ods",
            "csv",
            "tsv",
            "ppt",
            "pptx",
            "odp",
        ):
            # Separate LO user profile prevents attaching to the user's running office session.
            profile = (stage / "lo-profile").as_uri()
            format_id = {
                "tsv": "csv:Text - txt - csv (StarCalc):9,34,76",
                "csv": "csv:Text - txt - csv (StarCalc):44,34,76",
                "txt": "txt:Text (encoded):UTF8",
            }.get(target, target)
            lo_input = first
            if first.suffix.lower().lstrip(".") == target:
                lo_input = stage / ("entrada" + first.suffix)
                shutil.copyfile(first, lo_input)
            # TSV must use tabs, rather than Calc's CSV delimiter auto-detection.
            import_options = (
                ["--infilter=Text - txt - csv (StarCalc):9,34,76,1,"]
                if ext == "tsv"
                else []
            )
            run(
                [
                    engine["libreoffice"],
                    "-env:UserInstallation=" + profile,
                    "--headless",
                    *import_options,
                    "--convert-to",
                    format_id,
                    "--outdir",
                    stage,
                    lo_input,
                ],
                timeout=300,
            )
            actual = stage / (
                lo_input.stem + (".csv" if target == "tsv" else "." + target)
            )
            result = stage / (first.stem + "." + target)
            if actual != result and actual.exists():
                actual.rename(result)
            output_files = [result]
        elif ext in (
            "mp4",
            "mov",
            "mkv",
            "webm",
            "avi",
            "wmv",
            "mp3",
            "wav",
            "flac",
            "aac",
            "m4a",
            "ogg",
            "opus",
        ):
            args = [
                engine["ffmpeg"],
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-n",
                "-i",
                first,
            ]
            if target in ("mp3", "wav", "flac", "aac", "m4a", "ogg"):
                args += ["-vn"]
                codecs = {
                    "mp3": [
                        "-c:a",
                        "libmp3lame",
                        "-b:a",
                        f"{max(64, round(quality / 100 * 320))}k",
                    ],
                    "wav": ["-c:a", "pcm_s16le"],
                    "flac": ["-c:a", "flac"],
                    "aac": ["-c:a", "aac", "-b:a", "192k"],
                    "m4a": ["-c:a", "aac", "-b:a", "192k"],
                    "ogg": ["-c:a", "libvorbis", "-q:a", "5"],
                }
                args += codecs[target]
            else:
                args += (
                    ["-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0", "-c:a", "libopus"]
                    if target == "webm"
                    else [
                        "-c:v",
                        "libx264",
                        "-crf",
                        str(round(35 - quality * 0.17)),
                        "-preset",
                        "medium",
                        "-pix_fmt",
                        "yuv420p",
                        "-c:a",
                        "aac",
                    ]
                )
                if width:
                    args += ["-vf", f"scale=min({width}\\,iw):-2"]
                if target in ("mp4", "mov"):
                    args += ["-movflags", "+faststart"]
            run(args + [result])
            output_files = [result]
        elif ext in ("epub", "mobi", "azw3"):
            run([engine["calibre"], first, result])
            output_files = [result]
        elif ext in ("ttf", "otf", "woff", "woff2"):
            from fontTools.ttLib import TTFont

            with TTFont(first) as font:
                if target == "sfnt":
                    suffix = "otf" if font.sfntVersion == "OTTO" else "ttf"
                    result = stage / (first.stem + "." + suffix)
                    font.flavor = None
                else:
                    font.flavor = target
                font.save(result)
            output_files = [result]
        elif ext in ("dxf", "dwg"):
            if target in ("dwg", "dxf"):
                incoming = stage / "cad-input"
                incoming.mkdir()
                shutil.copyfile(first, incoming / first.name)
                outgoing = stage / "cad-output"
                outgoing.mkdir()
                run(
                    [
                        engine["oda"],
                        incoming,
                        outgoing,
                        "ACAD2018",
                        target.upper(),
                        "0",
                        "0",
                        "*." + ext,
                    ]
                )
                generated = next(
                    (
                        p
                        for p in outgoing.rglob("*")
                        if p.suffix.lower() == "." + target
                    ),
                    None,
                )
                if not generated:
                    raise ValueError("O componente CAD não gerou o resultado.")
                shutil.copyfile(generated, result)
                output_files = [result]
            elif ext == "dxf":
                import ezdxf
                from ezdxf.addons.drawing import (
                    RenderContext,
                    Frontend,
                    layout,
                    svg,
                    pymupdf,
                )

                drawing = ezdxf.readfile(first)
                backend = (
                    svg.SVGBackend() if target == "svg" else pymupdf.PyMuPdfBackend()
                )
                Frontend(RenderContext(drawing), backend).draw_layout(
                    drawing.modelspace(), finalize=True
                )
                page = layout.Page(0, 0)
                if target == "svg":
                    result.write_text(backend.get_string(page), encoding="utf-8")
                elif target == "pdf":
                    result.write_bytes(backend.get_pdf_bytes(page))
                elif target == "png":
                    result.write_bytes(backend.get_pixmap_bytes(page, fmt="png"))
                else:
                    raise ValueError("Formato CAD de saída não suportado.")
                output_files = [result]
            else:
                raise ValueError("Para renderizar DWG, converta primeiro para DXF.")
        else:
            raise ValueError("Tipo de arquivo não suportado por esta conversão.")
        emit(progress=90, message="Validando e salvando o resultado")
        check_cancel()
        if output_dir is not None:
            if not any(output_dir.iterdir()):
                raise ValueError("O componente não produziu arquivos.")
            outputs = [publish_dir(output_dir, folder, output_dir.name)]
        else:
            for output in output_files:
                if not output.is_file() or output.stat().st_size == 0:
                    raise ValueError("O componente não produziu um arquivo válido.")
            outputs = [
                publish_file(output, folder, output.name) for output in output_files
            ]
        emit(progress=100, message="Concluído", outputs=outputs)
        return outputs


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        convert(json.loads(sys.stdin.readline()))
    except BaseException as error:
        emit(error=str(error))
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)
