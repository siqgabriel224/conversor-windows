import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "worker_regressions", Path(__file__).resolve().parents[1] / "worker" / "convert.py"
)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def test_empty_tar_link_fields_are_regular_files():
    worker.safe_archive_listing(
        "----------\nPath = arquivo.txt\nMode = -rwxrwxrwx\nSymbolic Link = \nHard Link = \n"
    )


@pytest.mark.parametrize(
    "entry", ["Symbolic Link = alvo.txt", "Hard Link = alvo.txt", "Mode = lrwxrwxrwx"]
)
def test_actual_archive_links_still_rejected(entry):
    with pytest.raises(ValueError, match="links"):
        worker.safe_archive_listing("----------\nPath = arquivo.txt\n" + entry)


def test_publish_retries_transient_windows_lock(tmp_path, monkeypatch):
    stage = tmp_path / "stage"
    stage.mkdir()
    source = stage / "arquivo.txt"
    source.write_bytes(b"conteudo")
    existing = tmp_path / "arquivo.txt"
    existing.write_bytes(b"original existente")
    real_replace = worker.os.replace
    attempts = []

    def locked_once(src, dst):
        attempts.append(dst)
        if len(attempts) < 3:
            raise PermissionError("Bloqueio temporário")
        return real_replace(src, dst)

    monkeypatch.setattr(worker.os, "replace", locked_once)
    monkeypatch.setattr(worker.time, "sleep", lambda _: None)
    result = Path(worker.publish_file(source, tmp_path, "arquivo.txt"))
    assert len(attempts) == 3
    assert result.name == "arquivo (1).txt" and result.read_bytes() == b"conteudo"
    assert existing.read_bytes() == b"original existente"
    assert source.read_bytes() == b"conteudo"


def test_permanent_lock_cleans_own_reservation(tmp_path, monkeypatch):
    stage = tmp_path / "stage"
    stage.mkdir()
    source = stage / "arquivo.txt"
    source.write_bytes(b"conteudo")

    def always_locked(*_):
        raise PermissionError("Sem permissão")

    monkeypatch.setattr(worker.os, "replace", always_locked)
    monkeypatch.setattr(worker.time, "sleep", lambda _: None)
    with pytest.raises(PermissionError):
        worker.publish_file(source, tmp_path, "arquivo.txt")
    assert not (tmp_path / "arquivo.txt").exists()
    assert not list(tmp_path.glob(".conversor-*"))
    assert source.read_bytes() == b"conteudo"


def test_cancel_during_publish_retry(tmp_path, monkeypatch):
    stage = tmp_path / "stage"
    stage.mkdir()
    source = stage / "arquivo.txt"
    source.write_bytes(b"conteudo")
    marker = tmp_path / "cancelar"

    def locked(*_):
        raise PermissionError("Bloqueio temporário")

    monkeypatch.setattr(worker.os, "replace", locked)
    monkeypatch.setattr(worker.time, "sleep", lambda _: marker.write_text(""))
    monkeypatch.setattr(worker, "cancel_file", str(marker))
    with pytest.raises(ValueError, match="cancelada"):
        worker.publish_file(source, tmp_path, "arquivo.txt")
    assert not (tmp_path / "arquivo.txt").exists()
    assert not list(tmp_path.glob(".conversor-*"))
