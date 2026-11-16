"""Initialize bounded, duplicate-safe application logging."""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .paths import StoragePaths


@dataclass(frozen=True, slots=True)
class LoggingSetup:
    logger: logging.Logger
    log_path: Path | None
    error: str | None = None


def initialize_logging(
    paths: StoragePaths,
    *,
    max_bytes: int = 1_000_000,
    backup_count: int = 3,
) -> LoggingSetup:
    logger = logging.getLogger("validata")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    wanted_path = str(paths.log_file.resolve())

    matching_handler = None
    for handler in tuple(logger.handlers):
        if getattr(handler, "_validata_owned", False):
            if getattr(handler, "_validata_path", None) == wanted_path and matching_handler is None:
                matching_handler = handler
                continue
            logger.removeHandler(handler)
            handler.close()
    if matching_handler is not None:
        return LoggingSetup(logger, paths.log_file)

    try:
        paths.root.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            paths.log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
    except OSError as exc:
        if not any(isinstance(item, logging.NullHandler) and getattr(item, "_validata_owned", False) for item in logger.handlers):
            fallback = logging.NullHandler()
            fallback._validata_owned = True  # type: ignore[attr-defined]
            logger.addHandler(fallback)
        message = f"File logging is unavailable at {paths.log_file}: {exc}"
        warnings.warn(message, RuntimeWarning, stacklevel=2)
        return LoggingSetup(logger, None, message)

    handler._validata_owned = True  # type: ignore[attr-defined]
    handler._validata_path = wanted_path  # type: ignore[attr-defined]
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    return LoggingSetup(logger, paths.log_file)
