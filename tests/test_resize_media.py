"""Real ImageMagick/FFmpeg framing tests, with patterned pixels and audio."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "resize_media", ROOT / "worker" / "resize_media.py"
)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
ENGINES = {
    key: str(ROOT / item["path"])
    for key, item in json.loads(
        (ROOT / "engines.json").read_text(encoding="utf-8-sig")
    ).items()
}
FFMPEG = ENGINES["ffmpeg"]
FFPROBE = str(Path(FFMPEG).with_name("ffprobe.exe"))


def run(args):
    return subprocess.run([str(arg) for arg in args], check=True, capture_output=True)


def probe(path):
    return json.loads(
        run(
            [
                FFPROBE,
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                path,
            ]
        ).stdout
    )


@pytest.fixture(scope="session")
def sources(tmp_path_factory):
    folder = tmp_path_factory.mktemp("resize_sources")
    image = Image.new("RGB", (600, 200))
    draw = ImageDraw.Draw(image)
    for x, color in [(0, "red"), (200, "lime"), (400, "blue")]:
        draw.rectangle((x, 0, x + 199, 199), fill=color)
    source = folder / "imagem áç.png"
    image.save(source)
    video = folder / "vídeo com áudio.mp4"
    run(
        [
            FFMPEG,
            "-v",
            "error",
            "-y",
            "-loop",
            "1",
            "-i",
            source,
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000",
            "-t",
            "1.2",
            "-r",
            "25",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            video,
        ]
    )
    silent = folder / "silencioso.mp4"
    run([FFMPEG, "-v", "error", "-y", "-i", video, "-c:v", "copy", "-an", silent])
    return source, video, silent


@pytest.fixture(autouse=True)
def local_temp(tmp_path, monkeypatch):
    monkeypatch.setattr(worker.tempfile, "tempdir", str(tmp_path))
    worker.conversion.cancel_file = None
    yield
    worker.conversion.cancel_file = None


def request(source, folder, **changes):
    resize = dict(
        width=200,
        height=200,
        mode="cover",
        anchor="center",
        imageFormat="png",
        videoFormat="mp4",
    )
    resize.update(changes)
    return dict(
        inputs=[str(source)],
        resize=resize,
        outputDirectory=str(folder),
        engines=ENGINES,
    )


@pytest.mark.parametrize(
    "anchor,expected",
    [("west", (255, 0, 0)), ("center", (0, 255, 0)), ("east", (0, 0, 255))],
)
def test_crop_anchor_keeps_correct_content(sources, tmp_path, anchor, expected):
    source = sources[0]
    original = hashlib.sha256(source.read_bytes()).hexdigest()
    result = worker.resize(request(source, tmp_path, anchor=anchor))
    with Image.open(result) as image:
        assert image.size == (200, 200)
        assert image.convert("RGB").getpixel((100, 100)) == expected
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original


@pytest.mark.parametrize("target", ["png", "jpg", "webp"])
def test_image_contain_and_custom_pixels(sources, tmp_path, target):
    result = worker.resize(
        request(
            sources[0],
            tmp_path,
            width=321,
            height=201,
            mode="contain",
            imageFormat=target,
        )
    )
    with Image.open(result) as image:
        assert image.size == (321, 201)
        assert max(image.convert("RGB").getpixel((160, 0))) < 8
        assert image.convert("RGB").getpixel((160, 100))[1] > 240


@pytest.mark.parametrize("target", ["mp4", "mkv", "webm"])
@pytest.mark.parametrize("mode", ["cover", "contain"])
def test_video_dimensions_duration_audio_and_full_decode(
    sources, tmp_path, target, mode
):
    source = sources[1]
    original = hashlib.sha256(source.read_bytes()).hexdigest()
    result = worker.resize(
        request(source, tmp_path, width=180, height=320, videoFormat=target, mode=mode)
    )
    metadata = probe(result)
    video = next(s for s in metadata["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"]) == (180, 320)
    assert video["sample_aspect_ratio"] == "1:1"
    assert any(s["codec_type"] == "audio" for s in metadata["streams"])
    assert abs(float(metadata["format"]["duration"]) - 1.2) < 0.15
    run([FFMPEG, "-v", "error", "-xerror", "-i", result, "-f", "null", "-"])
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original


def test_silent_video_and_preview(sources, tmp_path):
    req = request(sources[2], tmp_path)
    result = worker.resize(req)
    assert not any(s["codec_type"] == "audio" for s in probe(result)["streams"])
    req["preview"] = True
    preview = worker.resize(req)
    with Image.open(preview) as image:
        assert image.size == (200, 200)
        assert image.convert("RGB").getpixel((100, 100))[1] > 240


def test_conflict_keeps_existing_and_source(sources, tmp_path):
    req = request(sources[0], tmp_path)
    first = Path(worker.resize(req))
    original = first.read_bytes()
    second = Path(worker.resize(req))
    assert second != first and second.stem.endswith("(1)")
    assert first.read_bytes() == original


@pytest.mark.parametrize(
    "changes",
    [
        dict(width=0),
        dict(height=9000),
        dict(width=7680, height=7680),
        dict(mode="stretch"),
        dict(anchor="invalid"),
        dict(imageFormat="exe"),
    ],
)
def test_invalid_settings_do_not_publish(sources, tmp_path, changes):
    with pytest.raises(ValueError):
        worker.resize(request(sources[0], tmp_path, **changes))
    assert not list(tmp_path.glob("*.png"))


def test_video_odd_dimensions_rejected(sources, tmp_path):
    with pytest.raises(ValueError, match="pares"):
        worker.resize(request(sources[1], tmp_path, width=201))


def test_corrupt_image_fails_without_touching_it(tmp_path):
    source = tmp_path / "corrompida.png"
    source.write_bytes(b"not an image")
    with pytest.raises(ValueError):
        worker.resize(request(source, tmp_path))
    assert source.read_bytes() == b"not an image"
    assert not list(tmp_path.glob("*200x200*"))


def test_cancel_before_start(sources, tmp_path):
    marker = tmp_path / "cancel"
    marker.touch()
    req = request(sources[0], tmp_path)
    req["cancellationFile"] = str(marker)
    with pytest.raises(ValueError, match="cancelada"):
        worker.resize(req)
    assert not list(tmp_path.glob("*.png"))


def test_exif_orientation_is_applied(tmp_path):
    source = tmp_path / "orientada.jpg"
    exif = Image.Exif()
    exif[274] = 6
    image = Image.new("RGB", (200, 100), "red")
    ImageDraw.Draw(image).rectangle((100, 0, 199, 99), fill="blue")
    image.save(source, exif=exif)
    result = worker.resize(request(source, tmp_path, width=100, height=200))
    with Image.open(result) as output:
        assert output.size == (100, 200)
        assert output.convert("RGB").getpixel((50, 30))[0] > 240
        assert output.convert("RGB").getpixel((50, 170))[2] > 240


def test_transparency_survives_png(tmp_path):
    source = tmp_path / "alpha.png"
    Image.new("RGBA", (200, 200), (255, 0, 0, 50)).save(source)
    result = worker.resize(request(source, tmp_path))
    with Image.open(result) as output:
        assert output.convert("RGBA").getpixel((100, 100))[3] == 50


@pytest.mark.parametrize("anchor,channel", [("west", 0), ("center", 1), ("east", 2)])
def test_video_preview_matches_crop_position(sources, tmp_path, anchor, channel):
    req = request(sources[1], tmp_path, anchor=anchor)
    req["preview"] = True
    with Image.open(worker.resize(req)) as image:
        assert image.convert("RGB").getpixel((100, 100))[channel] > 240


def test_anamorphic_video_normalizes_display_pixels(sources, tmp_path):
    source = tmp_path / "anamorphic.mp4"
    run(
        [
            FFMPEG,
            "-v",
            "error",
            "-y",
            "-i",
            sources[1],
            "-vf",
            "setsar=2",
            "-c:v",
            "libx264",
            "-an",
            source,
        ]
    )
    result = worker.resize(
        request(source, tmp_path, width=320, height=180, mode="contain")
    )
    video = next(s for s in probe(result)["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"], video["sample_aspect_ratio"]) == (
        320,
        180,
        "1:1",
    )


def test_rotated_video_uses_visible_orientation(sources, tmp_path):
    source = tmp_path / "rotated.mp4"
    run(
        [
            FFMPEG,
            "-v",
            "error",
            "-y",
            "-display_rotation",
            "90",
            "-i",
            sources[1],
            "-c",
            "copy",
            source,
        ]
    )
    video = next(s for s in probe(source)["streams"] if s["codec_type"] == "video")
    assert any(side.get("rotation") == 90 for side in video.get("side_data_list", []))
    req = request(source, tmp_path, width=200, height=600, mode="contain")
    req["preview"] = True
    with Image.open(worker.resize(req)) as image:
        assert image.size == (200, 600)
        # After autorotation, the colored horizontal stripe fills the portrait.
        assert max(image.convert("RGB").getpixel((100, 10))) > 240
        assert max(image.convert("RGB").getpixel((100, 590))) > 240


def test_cancel_while_video_engine_is_running(sources, tmp_path, monkeypatch):
    marker = tmp_path / "cancel-running"
    req = request(sources[1], tmp_path, width=1920, height=1080)
    req["cancellationFile"] = str(marker)
    original_run = worker.conversion.run

    def cancel_on_progress(args, timeout=3600, on_tick=None):
        if on_tick is None:
            return original_run(args, timeout=timeout)

        def cancel():
            marker.touch()

        return original_run(args, timeout=timeout, on_tick=cancel)

    monkeypatch.setattr(worker.conversion, "run", cancel_on_progress)
    with pytest.raises(ValueError, match="cancelada"):
        worker.resize(req)
    assert not list(tmp_path.glob("*1920x1080*"))
