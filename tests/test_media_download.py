"""Offline contract tests. Platform availability is checked by the live smoke script."""

import importlib.util
import json
from pathlib import Path
import shutil

import pytest
from yt_dlp import YoutubeDL

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "media_download", ROOT / "worker" / "media_download.py"
)
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)
ENGINES = {
    key: str(ROOT / item["path"])
    for key, item in json.loads(
        (ROOT / "engines.json").read_text(encoding="utf-8-sig")
    ).items()
}


@pytest.fixture(scope="session")
def offline_media(tmp_path_factory):
    source = tmp_path_factory.mktemp("payload") / "source.mp4"
    source.write_bytes(b"synthetic payload for publication tests")
    return source


@pytest.fixture(autouse=True)
def reset_cancellation(tmp_path, monkeypatch, offline_media):
    monkeypatch.setattr(media.tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(OfflineDownloader, "source", offline_media)
    media.conversion.cancel_file = None
    yield
    media.conversion.cancel_file = None


@pytest.mark.parametrize(
    "url,platform",
    [
        ("https://www.youtube.com/watch?v=abc", "YouTube"),
        ("youtu.be/abc", "YouTube"),
        ("https://m.youtube.com/shorts/abc", "YouTube"),
        ("https://youtube.com/playlist?list=abc", "YouTube"),
        ("https://www.instagram.com/reel/abc/", "Instagram"),
        ("https://instagram.com/p/abc/", "Instagram"),
        ("https://www.tiktok.com/@example/video/123", "TikTok"),
        ("https://vt.tiktok.com/abc/", "TikTok"),
        ("https://vm.tiktok.com/abc/", "TikTok"),
    ],
)
def test_supported_urls(url, platform):
    normalized, name = media.normalize_url(url)
    assert name == platform and normalized.startswith("https://")


@pytest.mark.parametrize(
    "url",
    [
        "https://vimeo.com/123",
        "https://youtube.com.evil.test/watch?v=abc",
        "https://evilyoutube.com/watch?v=abc",
        "https://user:secret@youtube.com/watch?v=abc",
        "file:///C:/video.mp4",
        "ftp://youtube.com/watch?v=abc",
        "https://youtube.com:8080/watch?v=abc",
        "https://youtube.com/",
        "https://instagram.com/",
        "https://127.0.0.1/video",
        "",
    ],
)
def test_unsupported_urls_do_not_reach_platform(url):
    with pytest.raises(ValueError):
        media.normalize_url(url)


@pytest.mark.parametrize("container", ["mp4", "mkv"])
@pytest.mark.parametrize("height", [0, 720, 1080, 2160])
def test_video_resolution_limit(container, height):
    options = media.format_options("video", container, height)
    assert options["merge_output_format"] == container
    assert (
        (f"height<={height}" in options["format"])
        if height
        else "height<=" not in options["format"]
    )
    assert options["postprocessors"][0]["key"] == "FFmpegVideoRemuxer"


@pytest.mark.parametrize("container", ["mp3", "m4a", "wav", "flac"])
@pytest.mark.parametrize("bitrate", [128, 320])
def test_audio_selection(container, bitrate):
    options = media.format_options("audio", container, 0, bitrate)
    processor = options["postprocessors"][0]
    assert processor["preferredcodec"] == container
    assert processor["preferredquality"] == str(bitrate)
    assert options["format"] == "bestaudio/best"


@pytest.mark.parametrize(
    "arguments",
    [
        ("video", "avi", 0),
        ("audio", "ogg", 0),
        ("unknown", "mp4", 0),
        ("video", "mp4", -1),
        ("video", "mp4", 20000),
        ("audio", "mp3", 0, 1000),
    ],
)
def test_invalid_quality_or_container(arguments):
    with pytest.raises(ValueError):
        media.format_options(*arguments)


class OfflineDownloader(YoutubeDL):
    source = None
    metadata = {
        "id": "abc",
        "title": "Ação de teste",
        "duration": 5,
        "formats": [
            {"height": 720, "vcodec": "h264"},
            {"height": 1080, "vcodec": "h264"},
            {"height": 1080, "vcodec": "h264"},
            {"vcodec": "none"},
        ],
    }
    item_count = 1
    fail_last = False
    cancel_after_first = None

    def __init__(self, options):
        super().__init__(options, auto_init=False)

    def extract_info(self, _url, download=False, **kwargs):
        if self.metadata.get("_type") == "playlist" and _url.endswith("/entry"):
            return {
                "id": "entry",
                "title": "Item",
                "formats": [{"height": 720, "vcodec": "h264"}],
            }
        return self.metadata

    def download(self, urls):
        assert len(urls) == 1
        for index in range(self.item_count):
            if self.fail_last and index == self.item_count - 1:
                self.params["logger"].error("Item indisponível")
                continue
            file = Path(self.params["outtmpl"]["default"]).parent / f"Vídeo {index}.mp4"
            shutil.copyfile(self.source, file)
            info = {
                "id": str(index),
                "title": f"Vídeo {index}",
                "filepath": str(file),
                "playlist_index": index + 1,
                "playlist_count": self.item_count,
            }
            for hook in self.params["progress_hooks"]:
                hook(
                    dict(
                        status="finished",
                        downloaded_bytes=file.stat().st_size,
                        total_bytes=file.stat().st_size,
                        info_dict=info,
                    )
                )
            for processor in self._pps["after_move"]:
                processor.run(info)
            if self.cancel_after_first:
                Path(self.cancel_after_first).write_text("")


def request(tmp_path, **options):
    return dict(
        url="https://youtube.com/watch?v=abc",
        mode="video",
        format="mp4",
        outputDirectory=str(tmp_path),
        engines=ENGINES,
        **options,
    )


def test_inspection_returns_unique_available_resolutions(tmp_path):
    metadata = media.inspect_link(request(tmp_path), OfflineDownloader)
    assert metadata["heights"] == [1080, 720]
    assert metadata["duration"] == 5 and metadata["playlistCount"] == 1


def test_playlist_requires_explicit_selection(tmp_path):
    class Playlist(OfflineDownloader):
        metadata = {
            "_type": "playlist",
            "title": "Minha playlist",
            "entries": [
                {"url": "https://youtube.com/entry"},
                {"url": "https://youtube.com/second"},
            ],
        }

    with pytest.raises(ValueError, match="Marque"):
        media.inspect_link(request(tmp_path), Playlist)
    metadata = media.inspect_link(request(tmp_path, includePlaylist=True), Playlist)
    assert metadata["playlistCount"] == 2 and metadata["heights"] == [720]


def test_publish_never_overwrites_existing_file(tmp_path):
    existing = tmp_path / "Vídeo 0.mp4"
    existing.write_bytes(b"original")
    outputs = media.download_media(request(tmp_path), OfflineDownloader)
    assert existing.read_bytes() == b"original"
    assert Path(outputs[0]).name == "Vídeo 0 (1).mp4"
    assert Path(outputs[0]).read_bytes() == OfflineDownloader.source.read_bytes()


def test_playlist_failure_preserves_successful_items(tmp_path, capsys):
    class PartialPlaylist(OfflineDownloader):
        item_count = 3
        fail_last = True

    outputs = media.download_media(
        request(tmp_path, includePlaylist=True), PartialPlaylist
    )
    assert len(outputs) == 2 and all(Path(path).is_file() for path in outputs)
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert "falha" in events[-1]["warning"]


def test_failed_download_does_not_publish_an_empty_file(tmp_path):
    class Failed(OfflineDownloader):
        fail_last = True

    with pytest.raises(ValueError):
        media.download_media(request(tmp_path), Failed)
    assert not list(tmp_path.iterdir())


def test_cancel_playlist_keeps_completed_item(tmp_path):
    marker = tmp_path / "cancelar"
    media.conversion.cancel_file = str(marker)

    class Cancelled(OfflineDownloader):
        item_count = 2
        cancel_after_first = str(marker)

    with pytest.raises(ValueError, match="cancelada"):
        media.download_media(request(tmp_path, includePlaylist=True), Cancelled)
    assert (tmp_path / "Vídeo 0.mp4").is_file()
    assert not (tmp_path / "Vídeo 1.mp4").exists()


def test_error_messages_do_not_expose_signed_urls():
    message = media.clean_error(
        "ERROR: request failed https://cdn.example/video?token=secret"
    )
    assert "secret" not in message and "[link]" in message


@pytest.mark.parametrize("state", ["is_live", "is_upcoming"])
def test_live_or_upcoming_video_is_not_started(tmp_path, state):
    class Live(OfflineDownloader):
        metadata = dict(OfflineDownloader.metadata, live_status=state)

    with pytest.raises(ValueError, match="ao vivo"):
        media.inspect_link(request(tmp_path), Live)


def test_playlist_consultation_skips_unavailable_first_item(tmp_path):
    class UnavailableFirst(OfflineDownloader):
        metadata = {
            "_type": "playlist",
            "title": "Playlist",
            "entries": [
                {"url": "https://youtube.com/missing"},
                {"url": "https://youtube.com/entry"},
            ],
        }

        def extract_info(self, url, **kwargs):
            if url.endswith("/missing"):
                return None
            return super().extract_info(url, **kwargs)

    metadata = media.inspect_link(
        request(tmp_path, includePlaylist=True), UnavailableFirst
    )
    assert metadata["playlistCount"] == 2 and metadata["heights"] == [720]


def test_playlist_skips_live_items_even_after_first_video(tmp_path, capsys):
    class MixedPlaylist(OfflineDownloader):
        def download(self, urls):
            assert self.params["match_filter"]({"id": "live", "is_live": True})
            assert self.params["match_filter"]({"id": "normal"}) is None
            return super().download(urls)

    outputs = media.download_media(
        request(tmp_path, includePlaylist=True), MixedPlaylist
    )
    assert len(outputs) == 1
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert "falha" in events[-1]["warning"]
