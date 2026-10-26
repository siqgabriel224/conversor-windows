"""Resize a single image or full video, preserving the source and its duration."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import convert as conversion

IMAGES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
    ".heic",
    ".heif",
    ".avif",
    ".gif",
}
VIDEOS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
    ".avi",
    ".m4v",
    ".mpg",
    ".mpeg",
    ".mts",
    ".m2ts",
    ".ts",
}
ANCHORS = {
    "northwest": (0, 0),
    "north": (0.5, 0),
    "northeast": (1, 0),
    "west": (0, 0.5),
    "center": (0.5, 0.5),
    "east": (1, 0.5),
    "southwest": (0, 1),
    "south": (0.5, 1),
    "southeast": (1, 1),
}


def validate(request):
    source = Path(request["inputs"][0]).resolve(strict=True)
    video = source.suffix.lower() in VIDEOS
    if not source.is_file() or (not video and source.suffix.lower() not in IMAGES):
        raise ValueError("Escolha uma imagem ou um vídeo compatível.")
    size = request["resize"]
    width, height = int(size["width"]), int(size["height"])
    if (
        not 16 <= width <= 7680
        or not 16 <= height <= 7680
        or width * height > 33_177_600
    ):
        raise ValueError(
            "Use medidas de 16 a 7680 pixels, com no máximo 33 milhões de pixels."
        )
    if video and (width % 2 or height % 2):
        raise ValueError("Para vídeos, largura e altura precisam ser números pares.")
    if size["mode"] not in {"cover", "contain"} or size["anchor"] not in ANCHORS:
        raise ValueError("Enquadramento inválido.")
    target = size["videoFormat" if video else "imageFormat"]
    if target not in ({"mp4", "mkv", "webm"} if video else {"png", "jpg", "webp"}):
        raise ValueError("Formato de saída incompatível com o arquivo.")
    return source, video, width, height, size, target


def video_filter(width, height, mode, anchor):
    # Normalize non-square pixels before calculating the visible framing.
    normalize = "scale=trunc(iw*sar/2)*2:ih,setsar=1,"
    if mode == "cover":
        x, y = ANCHORS[anchor]
        return (
            normalize
            + f"scale={width}:{height}:force_original_aspect_ratio=increase:force_divisible_by=2,"
            f"crop={width}:{height}:(iw-ow)*{x}:(ih-oh)*{y},setsar=1"
        )
    return (
        normalize
        + f"scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
    )


def resize(request):
    conversion.cancel_file = request.get("cancellationFile")
    conversion.check_cancel()
    source, video, width, height, size, target = validate(request)
    preview = bool(request.get("preview"))
    folder = Path(request.get("outputDirectory") or source.parent).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    engine = request["engines"]
    conversion.emit(progress=5, message="Preparando enquadramento…")
    with tempfile.TemporaryDirectory(prefix="conversor-resize-") as temp:
        result = Path(temp) / ("preview.png" if preview else f"saida.{target}")
        if video:
            vf = video_filter(width, height, size["mode"], size["anchor"])
            progress_path = Path(temp) / "progress.txt"
            duration = 0
            if not preview:
                probe = Path(engine["ffmpeg"]).with_name("ffprobe.exe")
                metadata = json.loads(
                    conversion.run(
                        [probe, "-v", "error", "-show_format", "-of", "json", source]
                    )
                )
                duration = float(metadata.get("format", {}).get("duration", 0))

            last_progress = 0

            def update_progress():
                nonlocal last_progress
                if duration <= 0 or not progress_path.exists():
                    return
                try:
                    text = progress_path.read_text(encoding="utf-8")
                    timestamps = [
                        int(line.partition("=")[2])
                        for line in text.splitlines()
                        if line.startswith("out_time_us=")
                        and line.partition("=")[2].isdigit()
                    ]
                    percent = (
                        min(95, int(5 + 90 * timestamps[-1] / (duration * 1_000_000)))
                        if timestamps
                        else 5
                    )
                    if percent > last_progress:
                        last_progress = percent
                        conversion.emit(
                            progress=percent,
                            message=f"Redimensionando vídeo · {percent}%",
                        )
                except (OSError, ValueError):
                    pass

            args = [
                engine["ffmpeg"],
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                source,
                "-map",
                "0:v:0",
                "-vf",
                vf,
                "-progress",
                progress_path,
                "-nostats",
            ]
            if preview:
                args += ["-frames:v", "1", "-update", "1"]
            else:
                args += ["-map", "0:a?", "-map_metadata", "-1"]
                if target == "webm":
                    args += [
                        "-c:v",
                        "libvpx-vp9",
                        "-crf",
                        "30",
                        "-b:v",
                        "0",
                        "-deadline",
                        "good",
                        "-cpu-used",
                        "4",
                        "-c:a",
                        "libopus",
                    ]
                else:
                    args += [
                        "-c:v",
                        "libx264",
                        "-preset",
                        "medium",
                        "-crf",
                        "20",
                        "-c:a",
                        "aac",
                        "-b:a",
                        "192k",
                    ]
                args += ["-pix_fmt", "yuv420p"]
                if target == "mp4":
                    args += ["-movflags", "+faststart"]
            args += [result]
            conversion.run(args, timeout=24 * 3600, on_tick=update_progress)
        else:
            geometry = f"{width}x{height}"
            args = [
                engine["magick"],
                str(source) + "[0]",
                "-auto-orient",
                "-resize",
                geometry + ("^" if size["mode"] == "cover" else ""),
                "-background",
                "none" if size["mode"] == "cover" else "black",
                "-gravity",
                size["anchor"] if size["mode"] == "cover" else "center",
                "-extent",
                geometry,
            ]
            if not preview and target == "jpg":
                args += ["-alpha", "remove", "-alpha", "off"]
            args += [
                "-quality",
                str(max(1, min(100, int(request.get("quality", 90))))),
                result,
            ]
            conversion.run(args)
        conversion.check_cancel()
        if not result.is_file() or result.stat().st_size == 0:
            raise ValueError("O componente não gerou um resultado válido.")
        name = f"{source.stem} - {width}x{height}.{('png' if preview else target)}"
        output = conversion.publish_file(result, folder, name)
        conversion.emit(
            progress=100,
            message="Prévia pronta" if preview else "Redimensionamento concluído",
            outputs=[output],
        )
        return output


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        resize(json.loads(sys.stdin.readline()))
    except Exception as error:
        conversion.emit(error=str(error))
        sys.exit(1)
