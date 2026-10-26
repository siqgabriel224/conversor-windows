"""Opt-in live smoke test. Example URLs come from yt-dlp's own test cases."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ENGINES = {
    key: str(ROOT / item["path"])
    for key, item in json.loads(
        (ROOT / "engines.json").read_text(encoding="utf-8-sig")
    ).items()
}
LINKS = {
    "youtube": "https://www.youtube.com/watch?v=BaW_jenozKc",
    "instagram": "https://www.instagram.com/reel/Chunk8-jurw/",
    "tiktok": "https://www.tiktok.com/@leenabhushan/video/6748451240264420610",
}


def probe(item):
    name, url = item
    request = dict(operation="inspect", url=url, includePlaylist=False, engines=ENGINES)
    try:
        result = subprocess.run(
            [ENGINES["python"], str(ROOT / "worker" / "media_download.py")],
            input=json.dumps(request),
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=125,
        )
        events = [json.loads(line) for line in result.stdout.splitlines()]
        return dict(platform=name, success=result.returncode == 0, events=events)
    except subprocess.TimeoutExpired:
        return dict(
            platform=name, success=False, error="Tempo limite de consulta excedido"
        )


if __name__ == "__main__":
    output = ROOT / "tests" / "results" / "download-platform-probes.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(probe, LINKS.items()))
    output.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(results, ensure_ascii=True))
