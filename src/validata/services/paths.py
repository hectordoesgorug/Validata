"""Resolve writable portable or development storage locations."""

from __future__ import annotations

import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


class StorageError(OSError):
    """Raised when neither the primary nor fallback storage can be used."""


@dataclass(frozen=True, slots=True)
class StoragePaths:
    root: Path
    source: str

    @property
    def settings_file(self) -> Path:
        return self.root / "settings.json"

    @property
    def cache_file(self) -> Path:
        return self.root / "cache.json"

    @property
    def log_file(self) -> Path:
        return self.root / "validata.log"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _probe_writable(directory: Path) -> bool:
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".validata-write-test-", dir=directory, delete=True
        ):
            pass
        return True
    except OSError:
        return False


def _prepare(directory: Path, probe: Callable[[Path], bool]) -> bool:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        return False
    return probe(directory)


def resolve_storage_paths(
    *,
    project_root: Path | str | None = None,
    executable_path: Path | str | None = None,
    local_app_data: Path | str | None = None,
    frozen: bool | None = None,
    writable_probe: Callable[[Path], bool] = _probe_writable,
) -> StoragePaths:
    """Choose portable executable storage, development storage, or LocalAppData."""

    if frozen is None:
        frozen = bool(getattr(sys, "frozen", False))

    if frozen:
        executable = Path(executable_path or sys.executable).resolve()
        primary = executable.parent
        primary_source = "portable"
    else:
        primary = Path(project_root or _project_root()).resolve() / ".validata-data"
        primary_source = "development"

    if _prepare(primary, writable_probe):
        return StoragePaths(primary, primary_source)

    fallback_value = local_app_data
    if fallback_value is None:
        fallback_value = os.environ.get("LOCALAPPDATA")
    if fallback_value:
        fallback = Path(fallback_value).expanduser().resolve() / "Validata"
        if _prepare(fallback, writable_probe):
            return StoragePaths(fallback, "local-app-data")

    raise StorageError(
        "Validata could not write to its primary storage location or "
        "%LOCALAPPDATA%\\Validata. Choose a writable location and try again."
    )
