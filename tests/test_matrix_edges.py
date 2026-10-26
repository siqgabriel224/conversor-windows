"""Additional real-file variants beyond the basic extension matrix."""

import hashlib
import json
from pathlib import Path
import subprocess

import pytest
from test_catalog_matrix import (
    matrix_sources,
    convert,
    validate,
    run,
    ENGINES,
    WORKER,
    TEST_ENV,
)


@pytest.mark.parametrize("target", ["zip", "7z"])
def test_unknown_extension_compression(tmp_path, target):
    source = tmp_path / "arquivo-sem-conversor.xyz"
    source.write_bytes(bytes(range(256)))
    output = convert(source, target, tmp_path / "saída")
    validate(output, target, source, "outro")


@pytest.mark.parametrize("target", ["woff", "woff2"])
def test_cff_font_restoration(matrix_sources, tmp_path, target):
    from fontTools.ttLib import TTFont

    original = matrix_sources["otf"]
    compressed = convert(original, target, tmp_path / "compactada")
    restored = convert(compressed, "sfnt", tmp_path / "restaurada")
    assert restored.suffix == ".otf"
    with TTFont(original) as before, TTFont(restored) as after:
        assert before.getBestCmap() == after.getBestCmap()
        assert before.getGlyphOrder() == after.getGlyphOrder()
        assert "CFF " in after


def test_transparency_preserved(tmp_path):
    from PIL import Image

    source = tmp_path / "transparência.png"
    image = Image.new("RGBA", (80, 60), (200, 50, 80, 0))
    image.putpixel((40, 30), (30, 150, 80, 255))
    image.save(source)
    output = convert(source, "webp", tmp_path / "saída")
    with Image.open(output) as result:
        assert result.size == (80, 60)
        assert result.convert("RGBA").getpixel((0, 0))[3] == 0
        assert result.convert("RGBA").getpixel((40, 30))[3] == 255


def test_image_resize(matrix_sources, tmp_path):
    from PIL import Image

    output = convert(matrix_sources["png"], "jpg", tmp_path, width=100)
    with Image.open(output) as image:
        assert image.size == (100, 75)


def test_video_resize(matrix_sources, tmp_path):
    output = convert(matrix_sources["mov"], "mp4", tmp_path, width=160)
    streams = json.loads(
        run(
            [
                Path(ENGINES["ffmpeg"]).with_name("ffprobe.exe"),
                "-v",
                "error",
                "-show_streams",
                "-of",
                "json",
                output,
            ]
        )
    )["streams"]
    assert any(
        s["codec_type"] == "video" and s["width"] == 160 and s["height"] == 120
        for s in streams
    )
    run([ENGINES["ffmpeg"], "-v", "error", "-xerror", "-i", output, "-f", "null", "-"])


def test_silent_video_to_video_and_audio_error(matrix_sources, tmp_path):
    source = tmp_path / "sem-áudio.mov"
    run(
        [
            ENGINES["ffmpeg"],
            "-v",
            "error",
            "-i",
            matrix_sources["mov"],
            "-an",
            "-c:v",
            "copy",
            source,
        ]
    )
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    output = convert(source, "mp4", tmp_path / "vídeo")
    run([ENGINES["ffmpeg"], "-v", "error", "-xerror", "-i", output, "-f", "null", "-"])
    dest = tmp_path / "áudio"
    request = dict(
        inputs=[str(source)], target="mp3", outputDirectory=str(dest), engines=ENGINES
    )
    result = subprocess.run(
        [ENGINES["python"], str(WORKER)],
        input=json.dumps(request).encode(),
        capture_output=True,
        timeout=120,
        env=TEST_ENV,
    )
    assert result.returncode == 1 and "error" in result.stdout.decode("utf-8")
    assert not list(dest.iterdir())
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
