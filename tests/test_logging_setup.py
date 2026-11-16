import logging
from pathlib import Path

from logging.handlers import RotatingFileHandler

import pytest

from validata.services.logging_setup import initialize_logging
from validata.services.paths import StoragePaths


def test_logging_uses_resolved_location_and_does_not_duplicate_handlers(tmp_path: Path) -> None:
    paths = StoragePaths(tmp_path / "app-data", "development")
    first = initialize_logging(paths)
    second = initialize_logging(paths)
    owned = [handler for handler in first.logger.handlers if getattr(handler, "_validata_owned", False)]

    assert first.log_path == paths.log_file
    assert second.logger is first.logger
    assert len(owned) == 1
    assert isinstance(owned[0], RotatingFileHandler)

    first.logger.info("startup check")
    owned[0].flush()
    assert "startup check" in paths.log_file.read_text(encoding="utf-8")


def test_log_rotation_bounds_file_count(tmp_path: Path) -> None:
    paths = StoragePaths(tmp_path / "app-data", "development")
    setup = initialize_logging(paths, max_bytes=150, backup_count=2)
    for index in range(30):
        setup.logger.info("record %03d %s", index, "x" * 50)
    for handler in setup.logger.handlers:
        if getattr(handler, "_validata_owned", False):
            handler.flush()

    files = list(paths.root.glob("validata.log*"))
    assert paths.log_file.exists()
    assert len(files) > 1
    assert len(files) <= 3


def test_logging_failure_is_reported_without_raising(tmp_path: Path, monkeypatch) -> None:
    paths = StoragePaths(tmp_path / "app-data", "development")

    def fail_handler(*_args, **_kwargs):
        raise OSError("simulated log failure")

    monkeypatch.setattr("validata.services.logging_setup.RotatingFileHandler", fail_handler)
    with pytest.warns(RuntimeWarning, match="File logging is unavailable"):
        setup = initialize_logging(paths)
    assert setup.log_path is None
    assert setup.error is not None
    assert isinstance(setup.logger, logging.Logger)
