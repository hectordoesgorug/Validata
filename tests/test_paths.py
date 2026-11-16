from pathlib import Path

import pytest

from validata.services.paths import StorageError, resolve_storage_paths


def test_prefers_writable_executable_directory(tmp_path: Path) -> None:
    executable = tmp_path / "portable" / "Validata.exe"
    paths = resolve_storage_paths(
        frozen=True,
        executable_path=executable,
        local_app_data=tmp_path / "local",
    )
    assert paths.root == executable.parent
    assert paths.source == "portable"
    assert paths.settings_file.name == "settings.json"


def test_falls_back_when_portable_directory_is_unwritable(tmp_path: Path) -> None:
    portable = tmp_path / "bundle"
    fallback = tmp_path / "local"

    def probe(path: Path) -> bool:
        return path != portable

    paths = resolve_storage_paths(
        frozen=True,
        executable_path=portable / "Validata.exe",
        local_app_data=fallback,
        writable_probe=probe,
    )
    assert paths.root == fallback / "Validata"
    assert paths.source == "local-app-data"


def test_development_uses_ignored_project_local_storage(tmp_path: Path) -> None:
    paths = resolve_storage_paths(
        frozen=False,
        project_root=tmp_path,
        local_app_data=tmp_path / "local",
    )
    assert paths.root == tmp_path / ".validata-data"
    assert paths.source == "development"


def test_uses_local_app_data_if_development_storage_is_unwritable(tmp_path: Path) -> None:
    primary = tmp_path / ".validata-data"
    fallback = tmp_path / "local"
    paths = resolve_storage_paths(
        frozen=False,
        project_root=tmp_path,
        local_app_data=fallback,
        writable_probe=lambda path: path != primary,
    )
    assert paths.root == fallback / "Validata"


def test_fails_when_no_storage_location_is_usable(tmp_path: Path) -> None:
    with pytest.raises(StorageError, match="could not write"):
        resolve_storage_paths(
            frozen=False,
            project_root=tmp_path,
            local_app_data="",
            writable_probe=lambda _path: False,
        )
