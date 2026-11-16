import os
from pathlib import Path
from threading import Event

import pytest

from validata.services.discovery import DiscoveredFile, DiscoveryError, discover


def test_streams_nested_unicode_files_and_deduplicates_overlapping_sources(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    first = tmp_path / "one.txt"
    unicode_file = nested / "日本語 🎞.mp4"
    first.write_text("metadata only fixture", encoding="utf-8")
    unicode_file.write_bytes(b"not read by discovery")

    results = list(discover((tmp_path, nested, first), Event()))
    files = [item for item in results if isinstance(item, DiscoveredFile)]
    assert {item.path for item in files} == {first, unicode_file}
    assert len(files) == 2
    assert all(item.size >= 0 for item in files)


def test_empty_folder_and_missing_source(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    results = list(discover((empty, tmp_path / "missing.txt"), Event()))
    errors = [item for item in results if isinstance(item, DiscoveryError)]
    assert len(errors) == 1
    assert errors[0].path == tmp_path / "missing.txt"


def test_enumeration_failure_does_not_stop_other_sources(tmp_path: Path, monkeypatch) -> None:
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    good = tmp_path / "good.txt"
    good.write_text("fixture", encoding="utf-8")
    real_scandir = os.scandir

    def scandir(path):
        if Path(path) == blocked:
            raise PermissionError("synthetic access denial")
        return real_scandir(path)

    monkeypatch.setattr("validata.services.discovery.os.scandir", scandir)
    results = list(discover((blocked, good), Event()))
    assert any(isinstance(item, DiscoveryError) and item.path == blocked for item in results)
    assert any(isinstance(item, DiscoveredFile) and item.path == good for item in results)


def test_file_symlink_is_followed_but_directory_symlink_is_not_recursed(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.write_text("fixture", encoding="utf-8")
    directory = tmp_path / "directory"
    directory.mkdir()
    child = directory / "inside.txt"
    child.write_text("fixture", encoding="utf-8")
    file_link = tmp_path / "file-link.txt"
    broken_link = tmp_path / "broken-link.txt"
    directory_link = tmp_path / "directory-link"
    try:
        file_link.symlink_to(target)
        broken_link.symlink_to(tmp_path / "gone.txt")
        directory_link.symlink_to(directory, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    results = list(discover((tmp_path,), Event()))
    files = [item for item in results if isinstance(item, DiscoveredFile)]
    errors = [item for item in results if isinstance(item, DiscoveryError)]
    paths = {item.path for item in files}
    assert target in paths
    assert child in paths
    assert file_link in paths
    assert directory_link not in paths
    assert any(item.path == broken_link for item in errors)
    assert next(item for item in files if item.path == file_link).is_symlink
    assert not list(discover((directory_link,), Event()))
