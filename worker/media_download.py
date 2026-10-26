"""JSON bridge between the desktop queue and yt-dlp.

Only the three advertised platforms are accepted. Downloads are staged and
published one item at a time, using the same collision policy as conversions.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tempfile
import time
from urllib.parse import urlsplit, urlunsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import convert as conversion


PLATFORMS = {
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "instagram.com": "Instagram",
    "tiktok.com": "TikTok",
}
AUDIO_FORMATS = {"mp3", "m4a", "wav", "flac"}
VIDEO_FORMATS = {"mp4", "mkv"}


def emit(**event):
    print(json.dumps(event, ensure_ascii=False), flush=True)


def normalize_url(value):
    value = str(value).strip()
    if "://" not in value:
        value = "https://" + value
    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme not in ("http", "https") or parsed.username or parsed.password:
        raise ValueError("Cole um link HTTP ou HTTPS de vídeo, sem credenciais.")
    platform = next(
        (
            name
            for domain, name in PLATFORMS.items()
            if host == domain or host.endswith("." + domain)
        ),
        None,
    )
    if not platform or parsed.port not in (None, 80, 443):
        raise ValueError("Esta aba aceita somente YouTube, Instagram e TikTok.")
    if not parsed.path.strip("/"):
        raise ValueError("Cole o link de um vídeo ou playlist, não a página inicial.")
    return urlunsplit(("https", host, parsed.path, parsed.query, "")), platform


def clean_error(message):
    message = re.sub(r"\x1b\[[0-9;]*m", "", str(message))
    message = re.sub(r"https?://\S+", "[link]", message)
    message = message.removeprefix("ERROR: ").strip()[:500]
    lower = message.lower()
    if any(
        text in lower
        for text in ("sign in", "login required", "log in", "private video", "cookies")
    ):
        return "A plataforma exige login ou o conteúdo é privado. Esta versão usa links públicos, sem importar contas do navegador."
    if any(text in lower for text in ("not a bot", "captcha", "challenge")):
        return "A plataforma pediu uma verificação de acesso. Tente novamente mais tarde ou use outro link público."
    if any(
        text in lower
        for text in ("requested format is not available", "no video formats")
    ):
        return "A qualidade escolhida não está disponível neste item. Consulte o link novamente ou escolha a melhor qualidade disponível."
    if any(text in lower for text in ("drm", "protected")):
        return "Este conteúdo está protegido e não pode ser baixado por esta função."
    return "Não foi possível acessar o conteúdo. " + message


class DownloadLogger:
    def __init__(self):
        self.last_error = None

    def debug(self, _message):
        pass

    def warning(self, message):
        conversion.check_cancel()
        # Warnings are not fatal; the terminal event reports actual item failures.

    def error(self, message):
        conversion.check_cancel()
        self.last_error = clean_error(message)
        emit(warning=self.last_error)


def base_options(engines):
    return {
        "quiet": True,
        "no_warnings": True,
        "logger": DownloadLogger(),
        "cachedir": False,
        "socket_timeout": 20,
        "retries": 3,
        "fragment_retries": 3,
        "allowed_extractors": ["youtube.*", "instagram.*", "tiktok.*"],
        "js_runtimes": {"deno": {"path": engines["deno"]}},
        "remote_components": set(),
        "ffmpeg_location": str(Path(engines["ffmpeg"]).parent),
        "windowsfilenames": True,
        "color": {"stdout": "never", "stderr": "never"},
    }


def inspect_link(request, youtube_dl=None):
    from yt_dlp import YoutubeDL

    factory = youtube_dl or YoutubeDL
    url, platform = normalize_url(request["url"])
    include_playlist = bool(request.get("includePlaylist"))
    options = base_options(request["engines"]) | {
        "skip_download": True,
        "noplaylist": not include_playlist,
        "extract_flat": "in_playlist",
        "ignoreerrors": True,
    }
    conversion.check_cancel()
    with factory(options) as downloader:
        info = downloader.extract_info(url, download=False)
        if not info:
            raise ValueError(
                options["logger"].last_error
                or "O link não retornou um vídeo acessível."
            )
        is_playlist = info.get("_type") in ("playlist", "multi_video")
        entries = list(info.get("entries") or []) if is_playlist else []
        if is_playlist and not include_playlist:
            raise ValueError(
                "Este link aponta para uma playlist ou coleção. Marque a opção de playlist para continuar."
            )
        first = None
        for candidate in entries if is_playlist else [info]:
            conversion.check_cancel()
            if not candidate:
                continue
            if not candidate.get("formats"):
                entry_url = candidate.get("webpage_url") or candidate.get("url")
                candidate = (
                    downloader.extract_info(entry_url, download=False)
                    if entry_url
                    else None
                )
            if not candidate:
                continue
            if is_playlist and is_live_item(candidate):
                continue
            first = candidate
            break
        if not first:
            raise ValueError(
                "Não há itens públicos disponíveis para download nesta seleção."
            )
        if first.get("is_live") or first.get("live_status") in (
            "is_live",
            "is_upcoming",
        ):
            raise ValueError(
                "Transmissões ao vivo e estreias futuras não são suportadas nesta versão. Use um vídeo já publicado."
            )
    heights = sorted(
        {
            int(fmt["height"])
            for fmt in first.get("formats", [])
            if fmt.get("height") and fmt.get("vcodec") != "none"
        },
        reverse=True,
    )
    return {
        "url": url,
        "platform": platform,
        "title": info.get("title") or first.get("title") or platform,
        "uploader": info.get("uploader") or first.get("uploader") or "",
        "duration": first.get("duration") or 0,
        "isPlaylist": is_playlist,
        "playlistCount": len(entries) if is_playlist else 1,
        "heights": heights,
    }


def is_live_item(information):
    return bool(information.get("is_live")) or information.get("live_status") in (
        "is_live",
        "is_upcoming",
    )


def format_options(mode, container, max_height, audio_bitrate=192):
    if mode == "audio":
        if container not in AUDIO_FORMATS:
            raise ValueError("Escolha MP3, M4A, WAV ou FLAC para o áudio.")
        if audio_bitrate not in (96, 128, 192, 256, 320):
            raise ValueError("Escolha uma taxa de áudio entre 96 e 320 kbps.")
        return {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": container,
                    "preferredquality": str(audio_bitrate),
                }
            ],
        }
    if mode != "video" or container not in VIDEO_FORMATS:
        raise ValueError("Escolha MP4 ou MKV para o vídeo.")
    if max_height < 0 or max_height > 16384:
        raise ValueError("Resolução máxima inválida.")
    limit = f"[height<={max_height}]" if max_height else ""
    # Prefer native MP4 streams, while keeping a fallback for the chosen limit.
    selector = f"bv*{limit}+ba/b{limit}"
    if container == "mp4":
        selector = f"bv*{limit}[ext=mp4]+ba[ext=m4a]/b{limit}[ext=mp4]/" + selector
    return {
        "format": selector,
        "merge_output_format": container,
        "postprocessors": [{"key": "FFmpegVideoRemuxer", "preferedformat": container}],
    }


def download_media(request, youtube_dl=None):
    from yt_dlp import YoutubeDL
    from yt_dlp.postprocessor.common import PostProcessor

    factory = youtube_dl or YoutubeDL
    url, _platform = normalize_url(request["url"])
    folder = Path(request["outputDirectory"]).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    mode = request.get("mode", "video")
    container = request.get("format", "mp4")
    selection = format_options(
        mode,
        container,
        int(request.get("maxHeight", 0)),
        int(request.get("audioBitrate", 192)),
    )
    include_playlist = bool(request.get("includePlaylist"))
    published = []
    item_errors = []
    skipped_items = set()
    last_progress = 0.0
    emit(progress=0, message="Conferindo o link e os itens disponíveis…")
    inspect_link(request, factory)

    def filter_item(information, *, incomplete=False):
        conversion.check_cancel()
        if not is_live_item(information):
            return None
        reason = "Transmissão ao vivo ou estreia futura ignorada na playlist."
        item_id = information.get("id") or information.get("title")
        if item_id not in skipped_items:
            skipped_items.add(item_id)
            item_errors.append(reason)
            emit(warning=reason)
        return reason

    def progress(data):
        nonlocal last_progress
        conversion.check_cancel()
        now = time.monotonic()
        if data.get("status") != "finished" and now - last_progress < 0.25:
            return
        last_progress = now
        info = data.get("info_dict") or {}
        count = info.get("playlist_count") or info.get("n_entries") or 1
        index = info.get("playlist_index") or 1
        total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
        fraction = min(1, data.get("downloaded_bytes", 0) / total) if total else 0
        overall = min(95, 95 * ((index - 1 + fraction) / max(index, count)))
        title = str(info.get("title") or "vídeo")[:120]
        message = f"Item {index}/{count} · {title}"
        if data.get("speed"):
            message += f" · {data['speed'] / 1048576:.1f} MB/s"
        emit(progress=overall, message=message)

    class ItemLogger(DownloadLogger):
        def error(self, message):
            super().error(message)
            item_errors.append(clean_error(message))

    class PublishItem(PostProcessor):
        def run(self, information):
            conversion.check_cancel()
            source = Path(information["filepath"]).resolve()
            if not source.is_relative_to(Path(temporary).resolve()):
                raise ValueError(
                    "O componente retornou um arquivo fora da área temporária do download."
                )
            if not source.is_file() or source.stat().st_size == 0:
                raise ValueError("O download não produziu um arquivo válido.")
            # Title length is capped to leave room for collision suffixes on Windows.
            name = source.name
            if len(name) > 170:
                name = source.stem[:150] + source.suffix
            output = conversion.publish_file(source, folder, name)
            published.append(output)
            emit(outputs=published, message=f"{len(published)} item(ns) salvo(s)")
            return [], information

    with tempfile.TemporaryDirectory(prefix="conversor-download-") as temporary:
        options = (
            base_options(request["engines"])
            | selection
            | {
                "logger": ItemLogger(),
                "noplaylist": not include_playlist,
                "ignoreerrors": True,
                "match_filter": filter_item,
                "outtmpl": str(Path(temporary) / "%(title).120B [%(id)s].%(ext)s"),
                "progress_hooks": [progress],
                "postprocessor_hooks": [lambda _: conversion.check_cancel()],
                "overwrites": False,
                "continuedl": False,
                "skip_unavailable_fragments": False,
                "allow_playlist_files": False,
            }
        )
        with factory(options) as downloader:
            downloader.add_post_processor(PublishItem(downloader), when="after_move")
            downloader.download([url])
    conversion.check_cancel()
    if not published:
        raise ValueError(
            item_errors[-1]
            if item_errors
            else "Nenhum item foi baixado. Consulte o link e tente novamente."
        )
    message = (
        "Download concluído"
        if not item_errors
        else f"{len(published)} item(ns) salvo(s); {len(item_errors)} falha(s) na playlist"
    )
    emit(
        progress=100,
        outputs=published,
        message=message,
        warning="" if not item_errors else message,
    )
    return published


def main(request):
    conversion.cancel_file = request.get("cancellationFile")
    conversion.check_cancel()
    if request.get("operation") == "inspect":
        emit(metadata=inspect_link(request))
    else:
        download_media(request)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        main(json.loads(sys.stdin.readline()))
    except BaseException as error:
        message = str(error) if isinstance(error, ValueError) else clean_error(error)
        emit(error=message)
        sys.exit(1)
