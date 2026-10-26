import sys, json, tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "worker"))
import convert

engines = {
    k: str(root / v["path"])
    for k, v in json.loads(
        (root / "engines.json").read_text(encoding="utf-8-sig")
    ).items()
}
out = root / "tests" / "results" / "rede-restrita"
for source, target in [
    ("imagem.png", "webp"),
    ("duas-paginas.pdf", "png"),
    ("documento.docx", "pdf"),
    ("video.mp4", "mp3"),
]:
    result = convert.convert(
        dict(
            inputs=[str(root / "tests" / "fixtures" / source)],
            target=target,
            outputDirectory=str(out),
            engines=engines,
        )
    )
    print(source, "->", target, ":", all(Path(p).exists() for p in result))
