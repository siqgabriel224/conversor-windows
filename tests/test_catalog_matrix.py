"""Every advertised extension/target pair, using installed engines and worker.

Synthetic inputs exercise formats, not the fidelity of arbitrary user documents.
No user files are changed. Results and sources live under pytest's base temp.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import zlib
from contextlib import closing

import pytest

ROOT = Path(__file__).resolve().parents[1]
INSTALLED = Path(os.environ.get("CONVERSOR_TEST_APP", ROOT)).resolve()
ENGINES = {
    k: str(INSTALLED / v["path"])
    for k, v in json.loads(
        (INSTALLED / "engines.json").read_text(encoding="utf-8-sig")
    ).items()
}
WORKER = INSTALLED / "worker" / "convert.py"
TEST_ENV = dict(
    os.environ,
    CALIBRE_CONFIG_DIRECTORY=str(ROOT / "tests" / "results" / "calibre-matrix-config"),
)
CATALOG = (ROOT / "Catalog.cs").read_text(encoding="utf-8-sig")
INPUTS = {
    k: re.findall(r'"([^"]+)"', v)
    for k, v in re.findall(r'\["(\w+)"\]\s*=\s*\[([^]]+)\]', CATALOG)
}
TARGETS = {}
for category, body in re.findall(r'case "(\w+)":(.*?)(?:break;)', CATALOG, flags=re.S):
    if category == "cad":
        continue
    TARGETS[category] = [
        t
        for call in re.findall(r"Add\(([^)]+)\)", body)
        for t in re.findall(r'"([^"]+)"', call)[1:]
    ]
PAIRS = []
for category, extensions in INPUTS.items():
    for ext in extensions:
        targets = (
            (["pdf", "svg", "png", "dwg"] if ext == "dxf" else ["dxf"])
            if category == "cad"
            else TARGETS[category]
        )
        for target in dict.fromkeys(targets + ["zip", "7z"]):
            if target != ext:
                PAIRS.append((category, ext, target))


def run(args, timeout=180):
    result = subprocess.run(
        [str(x) for x in args], capture_output=True, timeout=timeout, env=TEST_ENV
    )
    assert result.returncode == 0, (result.stdout + result.stderr).decode(
        "utf-8", "replace"
    )[-3000:]
    return result.stdout


def convert(source, target, output, **extra):
    request = dict(
        inputs=[str(source)],
        target=target,
        outputDirectory=str(output),
        quality=85,
        pages="",
        width=0,
        engines=ENGINES,
    )
    request.update(extra)
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    result = subprocess.run(
        [ENGINES["python"], str(WORKER)],
        input=json.dumps(request).encode("utf-8"),
        capture_output=True,
        timeout=360,
        env=TEST_ENV,
    )
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before, "Original changed"
    assert result.returncode == 0, (result.stdout + result.stderr).decode(
        "utf-8", "replace"
    )[-3000:]
    events = [json.loads(line) for line in result.stdout.decode("utf-8").splitlines()]
    outputs = [Path(p) for p in events[-1]["outputs"]]
    assert outputs and all(p.exists() for p in outputs)
    return outputs[0]


def stored_rar(path, name, data):
    def header(raw):
        return struct.pack("<H", zlib.crc32(raw) & 0xFFFF) + raw

    filename = name.encode("ascii")
    main = header(struct.pack("<BHHHI", 0x73, 0, 13, 0, 0))
    file = header(
        struct.pack(
            "<BHHIIBIIBBHI",
            0x74,
            0x8000,
            32 + len(filename),
            len(data),
            len(data),
            2,
            zlib.crc32(data),
            0,
            20,
            0x30,
            len(filename),
            0x20,
        )
        + filename
    )
    end = header(struct.pack("<BHH", 0x7B, 0, 7))
    path.write_bytes(b"Rar!\x1a\x07\x00" + main + file + data + end)


@pytest.fixture(scope="session")
def matrix_sources(tmp_path_factory):
    cache = os.environ.get("CONVERSOR_MATRIX_SOURCES")
    if cache:
        folder = Path(cache)
        expected = json.loads((folder / "sha256.json").read_text())
        paths = {ext: folder / ("amostra." + ext) for ext in expected}
        assert all(
            hashlib.sha256(p.read_bytes()).hexdigest() == expected[ext]
            for ext, p in paths.items()
        )
        return paths
    from PIL import Image, ImageDraw
    from docx import Document
    from openpyxl import Workbook
    from pptx import Presentation
    import ezdxf
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.t2CharStringPen import T2CharStringPen

    folder = tmp_path_factory.mktemp("entradas-ação")
    generated = folder / "generated"
    generated.mkdir()
    paths = {}

    def put(ext, file):
        path = folder / ("amostra." + ext)
        if file != path:
            shutil.copyfile(file, path)
        paths[ext] = path
        return path

    im = Image.new("RGB", (320, 240), "#192331")
    ImageDraw.Draw(im).text((20, 60), "CONVERSOR 12345", fill="#70e0bc")
    for ext in INPUTS["imagem"]:
        path = folder / ("amostra." + ext)
        if ext == "heic":
            run([ENGINES["magick"], paths["png"], path])
        else:
            im.save(path)
        put(ext, path)
    im.save(
        folder / "amostra.pdf",
        save_all=True,
        append_images=[Image.new("RGB", im.size, "white")],
    )
    put("pdf", folder / "amostra.pdf")

    doc = Document()
    doc.add_heading("Conversor 12345", 0)
    doc.add_paragraph("Teste com acentos: ação e conversão.")
    doc.save(folder / "amostra.docx")
    put("docx", folder / "amostra.docx")
    for ext in ("odt", "txt"):
        put(ext, convert(paths["docx"], ext, generated / ("texto-" + ext)))

    def legacy(source, ext, filter_name):
        out = generated / ("legacy-" + ext)
        out.mkdir()
        profile = (out / "profile").as_uri()
        run(
            [
                ENGINES["libreoffice"],
                "-env:UserInstallation=" + profile,
                "--headless",
                "--convert-to",
                ext + ":" + filter_name,
                "--outdir",
                out,
                source,
            ]
        )
        return put(ext, out / (source.stem + "." + ext))

    legacy(paths["docx"], "doc", "MS Word 97")
    legacy(paths["docx"], "rtf", "Rich Text Format")

    wb = Workbook()
    wb.active.append(["Produto", "Valor"])
    wb.active.append(["Teste", 123.45])
    wb.save(folder / "amostra.xlsx")
    put("xlsx", folder / "amostra.xlsx")
    for ext in ("ods", "csv", "tsv"):
        put(ext, convert(paths["xlsx"], ext, generated / ("sheet-" + ext)))
    legacy(paths["xlsx"], "xls", "MS Excel 97")

    ppt = Presentation()
    slide = ppt.slides.add_slide(ppt.slide_layouts[0])
    slide.shapes.title.text = "Conversor 12345"
    slide.placeholders[1].text = "Teste de apresentação"
    ppt.save(folder / "amostra.pptx")
    put("pptx", folder / "amostra.pptx")
    put("odp", convert(paths["pptx"], "odp", generated / "odp"))
    legacy(paths["pptx"], "ppt", "MS PowerPoint 97")

    for ext in INPUTS["video"]:
        path = folder / ("amostra." + ext)
        codecs = (
            ["-c:v", "libvpx-vp9", "-c:a", "libopus"]
            if ext == "webm"
            else (
                ["-c:v", "wmv2", "-c:a", "wmav2"]
                if ext == "wmv"
                else ["-c:v", "libx264", "-c:a", "aac"]
            )
        )
        run(
            [
                ENGINES["ffmpeg"],
                "-v",
                "error",
                "-n",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=320x240:rate=10",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:sample_rate=44100",
                "-t",
                "0.8",
                *codecs,
                path,
            ]
        )
        put(ext, path)
    for ext in INPUTS["audio"]:
        if ext == "opus":
            path = folder / "amostra.opus"
            run(
                [
                    ENGINES["ffmpeg"],
                    "-v",
                    "error",
                    "-n",
                    "-i",
                    paths["mp4"],
                    "-vn",
                    "-c:a",
                    "libopus",
                    path,
                ]
            )
            put(ext, path)
        else:
            put(ext, convert(paths["mp4"], ext, generated / ("audio-" + ext)))

    run(
        [
            ENGINES["pandoc"],
            paths["txt"],
            "--from",
            "markdown",
            "-o",
            folder / "amostra.epub",
        ]
    )
    put("epub", folder / "amostra.epub")
    for ext in ("mobi", "azw3"):
        put(ext, convert(paths["epub"], ext, generated / ("book-" + ext)))

    shutil.copyfile(
        Path(os.environ["WINDIR"]) / "Fonts" / "arial.ttf", folder / "amostra.ttf"
    )
    put("ttf", folder / "amostra.ttf")
    fb = FontBuilder(1000, isTTF=False)
    fb.setupGlyphOrder([".notdef", "A"])
    fb.setupCharacterMap({65: "A"})
    fb.setupHorizontalMetrics({".notdef": (600, 0), "A": (600, 0)})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable(
        {
            "familyName": "Conversor Test",
            "styleName": "Regular",
            "uniqueFontIdentifier": "ConversorTest",
            "fullName": "Conversor Test",
            "psName": "ConversorTest",
        }
    )
    glyphs = {}
    for name in [".notdef", "A"]:
        pen = T2CharStringPen(600, None)
        pen.moveTo((50, 0))
        pen.lineTo((300, 700))
        pen.lineTo((550, 0))
        pen.closePath()
        glyphs[name] = pen.getCharString()
    fb.setupCFF(
        "ConversorTest",
        {
            "FullName": "Conversor Test",
            "FamilyName": "Conversor Test",
            "Weight": "Regular",
        },
        glyphs,
        {},
    )
    fb.setupOS2(
        sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200
    )
    fb.setupPost()
    fb.save(folder / "amostra.otf")
    put("otf", folder / "amostra.otf")
    for ext in ("woff", "woff2"):
        put(ext, convert(paths["ttf"], ext, generated / ext))

    drawing = ezdxf.new()
    drawing.modelspace().add_line((0, 0), (100, 100))
    drawing.modelspace().add_circle((50, 50), 20)
    drawing.saveas(folder / "amostra.dxf")
    put("dxf", folder / "amostra.dxf")
    put("dwg", convert(paths["dxf"], "dwg", generated / "dwg"))
    for ext in ("zip", "7z"):
        put(ext, convert(paths["txt"], ext, generated / ("archive-" + ext)))
    for ext in ("tar", "gz"):
        path = folder / ("amostra." + ext)
        run(
            [
                ENGINES["sevenzip"],
                "a",
                "-t" + ("gzip" if ext == "gz" else ext),
                path,
                paths["txt"],
            ]
        )
        put(ext, path)
    stored_rar(folder / "amostra.rar", paths["txt"].name, paths["txt"].read_bytes())
    put("rar", folder / "amostra.rar")
    assert set(paths) == {ext for exts in INPUTS.values() for ext in exts}
    (folder / "sha256.json").write_text(
        json.dumps(
            {
                ext: hashlib.sha256(p.read_bytes()).hexdigest()
                for ext, p in paths.items()
            },
            indent=2,
        )
    )
    return paths


def validate(output, target, source, category):
    from PIL import Image
    from fontTools.ttLib import TTFont
    import pypdfium2 as pdfium

    if category == "planilha" and target not in ("zip", "7z"):
        if target == "pdf":
            with closing(pdfium.PdfDocument(output)) as doc:
                text = " ".join(
                    doc[i].get_textpage().get_text_bounded() for i in range(len(doc))
                )
                assert "123,45" in text or "123.45" in text, repr(text)
        else:
            if target == "xlsx":
                from openpyxl import load_workbook

                workbook = load_workbook(output, data_only=True)
                assert workbook.active.max_column == 2
                value = list(workbook.active.values)[1][1]
                workbook.close()
            elif target == "ods":
                import zipfile, xml.etree.ElementTree as ET

                with zipfile.ZipFile(output) as archive:
                    tree = ET.fromstring(archive.read("content.xml"))
                ns = {
                    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
                    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
                }
                cell = tree.findall(".//table:table-row", ns)[1].findall(
                    "table:table-cell", ns
                )[1]
                value = cell.get("{" + ns["office"] + "}value") or "".join(
                    cell.itertext()
                )
            else:
                import csv

                with output.open(encoding="utf-8-sig", newline="") as handle:
                    rows = list(
                        csv.reader(handle, delimiter="\t" if target == "tsv" else ",")
                    )
                assert len(rows) == 2 and all(len(row) == 2 for row in rows), rows
                value = rows[1][1]
            assert abs(float(str(value).replace(",", ".")) - 123.45) < 0.00001, value
    if target in ("zip", "7z"):
        dest = output.parent / ("verify-" + target)
        run([ENGINES["sevenzip"], "t", output])
        run([ENGINES["sevenzip"], "x", output, "-o" + str(dest), "-y"])
        assert (dest / source.name).read_bytes() == source.read_bytes()
    elif target == "extract":
        children = [p for p in output.rglob("*") if p.is_file()]
        assert len(children) == 1
        assert "Conversor" in children[0].read_text(encoding="utf-8-sig")
    elif category in ("video", "audio"):
        data = json.loads(
            run(
                [
                    Path(ENGINES["ffmpeg"]).with_name("ffprobe.exe"),
                    "-v",
                    "error",
                    "-show_streams",
                    "-show_format",
                    "-of",
                    "json",
                    output,
                ]
            )
        )
        assert any(s["codec_type"] == "audio" for s in data["streams"])
        assert float(data["format"]["duration"]) >= 0.7
        if target in ("mp4", "mov", "mkv", "webm"):
            assert any(
                s["codec_type"] == "video" and s["width"] == 320 and s["height"] == 240
                for s in data["streams"]
            )
        else:
            assert not any(s["codec_type"] == "video" for s in data["streams"])
        run(
            [
                ENGINES["ffmpeg"],
                "-v",
                "error",
                "-xerror",
                "-i",
                output,
                "-f",
                "null",
                "-",
            ]
        )
    elif target in ("pdf", "pdf-compress", "pdf-extract", "pdf-split"):
        files = list(output.glob("*.pdf")) if output.is_dir() else [output]
        count = 0
        for path in files:
            with closing(pdfium.PdfDocument(path)) as doc:
                count += len(doc)
                assert len(doc) > 0
                for page in doc:
                    image = page.render(scale=0.5).to_pil()
                    assert image.width > 0
                if category in ("texto", "planilha", "slides", "livro"):
                    text = " ".join(
                        doc[i].get_textpage().get_text_bounded()
                        for i in range(len(doc))
                    )
                    assert (
                        "Teste" in text
                        if category == "planilha"
                        else "Conversor" in text
                    ), repr(text)
        if category == "pdf":
            assert count == 2
    elif target in ("png", "jpg", "webp", "bmp", "tiff", "gif"):
        files = list(output.iterdir()) if output.is_dir() else [output]
        if category == "pdf":
            assert len(files) == 2
        for path in files:
            with Image.open(path) as image:
                image.load()
                assert image.width > 0 and image.height > 0
                if category == "imagem":
                    assert image.size == (320, 240)
    elif category == "fonte":
        with TTFont(source) as original, TTFont(output) as font:
            assert font.getGlyphOrder() == original.getGlyphOrder()
            assert font.getBestCmap() == original.getBestCmap()
    elif target == "svg":
        import xml.etree.ElementTree as ET

        assert ET.parse(output).getroot().tag.endswith("svg")
    elif target == "dxf":
        import ezdxf

        assert len(ezdxf.readfile(output).modelspace()) >= 2
    elif target == "dwg":
        restored = convert(output, "dxf", output.parent / "restored")
        import ezdxf

        assert len(ezdxf.readfile(restored).modelspace()) >= 2
    elif target in ("txt", "csv", "tsv"):
        text = output.read_text(encoding="utf-8-sig")
        assert "Teste" in text if category == "planilha" else "Conversor" in text, repr(
            text
        )
        if category == "planilha":
            assert "123" in text and ("\t" in text if target == "tsv" else "," in text)
    elif target in ("mobi", "azw3"):
        restored = convert(output, "txt", output.parent / "restored")
        assert "Conversor" in restored.read_text(encoding="utf-8-sig")
    elif target in ("docx", "odt", "xlsx", "ods", "pptx", "odp", "epub"):
        import zipfile

        with zipfile.ZipFile(output) as archive:
            assert archive.testzip() is None
            contents = b" ".join(
                archive.read(n)
                for n in archive.namelist()
                if n.endswith((".xml", ".html", ".xhtml"))
            )
            assert (
                b"Teste" in contents
                if category == "planilha"
                else b"Conversor" in contents
            )
    else:
        raise AssertionError("No validator for " + target)


@pytest.mark.parametrize(
    ("category", "ext", "target"), PAIRS, ids=[e + "-to-" + t for _, e, t in PAIRS]
)
def test_catalog_pair(matrix_sources, tmp_path, category, ext, target):
    source = matrix_sources[ext]
    output = convert(source, target, tmp_path / "saída")
    validate(output, target, source, category)
