from test_conversions import samples, execute, ENGINES, ROOT
from pathlib import Path
import pytest, os, time, subprocess, json, sys
import convert as worker


@pytest.mark.parametrize("target", ["mobi", "azw3", "pdf", "txt"])
def test_ebooks(samples, tmp_path, target):
    result = execute(samples / "livro.epub", target, tmp_path)[0]
    assert result.stat().st_size > 20
    if target == "pdf":
        from pypdf import PdfReader

        assert len(PdfReader(result).pages) > 0
    elif target == "txt":
        assert "Conversor" in result.read_text(encoding="utf-8-sig")
    else:
        restored = execute(result, "epub", tmp_path)[0]
        import zipfile

        with zipfile.ZipFile(restored) as z:
            assert z.read("mimetype") == b"application/epub+zip"


def test_oda_roundtrip(samples, tmp_path):
    import ezdxf

    dwg = execute(samples / "desenho.dxf", "dwg", tmp_path)[0]
    dxf = execute(dwg, "dxf", tmp_path)[0]
    assert len(ezdxf.readfile(dxf).modelspace()) >= 2


@pytest.mark.parametrize("fmt", ["woff", "woff2"])
def test_font_restoration(samples, tmp_path, fmt):
    from fontTools.ttLib import TTFont

    compressed = execute(samples / "fonte.ttf", fmt, tmp_path)[0]
    restored = execute(compressed, "sfnt", tmp_path)[0]
    with TTFont(restored) as result, TTFont(samples / "fonte.ttf") as original:
        assert result["maxp"].numGlyphs == original["maxp"].numGlyphs


def test_heic_read(samples, tmp_path):
    from PIL import Image

    source = tmp_path / "foto.heic"
    worker.run([ENGINES["magick"], samples / "imagem.png", source])
    output = execute(source, "jpg", tmp_path)[0]
    with Image.open(output) as im:
        assert im.size == (320, 240)


def test_cancellation(samples, tmp_path):
    marker = tmp_path / "cancel"
    marker.write_text("")
    out = tmp_path / "saida"
    result = subprocess.run(
        [sys.executable, str(ROOT / "worker" / "convert.py")],
        input=json.dumps(
            dict(
                inputs=[str(samples / "imagem.png")],
                target="webp",
                outputDirectory=str(out),
                engines=ENGINES,
                cancellationFile=str(marker),
            )
        ),
        text=True,
        capture_output=True,
        encoding="utf-8",
    )
    assert result.returncode == 1 and "cancelada" in result.stdout
    assert not out.exists()


def test_cancel_running_engine(tmp_path):
    marker = tmp_path / "cancel"
    script = tmp_path / "sleep.py"
    script.write_text("import time;time.sleep(30)")
    # Run a worker operation with an actual subprocess and a cancellation marker.
    harness = tmp_path / "harness.py"
    harness.write_text(
        "import sys\nfrom pathlib import Path\nsys.path.insert(0,sys.argv[1])\nimport convert\nconvert.cancel_file=sys.argv[2]\nconvert.run([sys.executable,sys.argv[3]])\n",
        encoding="utf-8",
    )
    process = subprocess.Popen(
        [sys.executable, str(harness), str(ROOT / "worker"), str(marker), str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(0.5)
    started = time.monotonic()
    marker.write_text("")
    out, err = process.communicate(timeout=5)
    assert process.returncode != 0 and time.monotonic() - started < 5
