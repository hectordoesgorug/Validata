"""Small versioned settings store with atomic writes and safe recovery."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
APPEARANCE_MODES = frozenset({"System", "Light", "Dark"})
_GEOMETRY = re.compile(r"^[1-9]\d{2,4}x[1-9]\d{2,4}(?:[+-]\d{1,5}[+-]\d{1,5})?$")


class SettingsError(OSError):
    """Raised when settings cannot be preserved or written safely."""


@dataclass(frozen=True, slots=True)
class Settings:
    appearance_mode: str = "System"
    window_geometry: str = "1120x760"


class SettingsStore:
    def __init__(self, path: Path | str, logger: Any = None) -> None:
        self.path = Path(path)
        self.logger = logger
        self.last_issue: str | None = None
        self.backup_path: Path | None = None
        self._safe_to_replace = True

    def load(self) -> Settings:
        if not self.path.exists():
            settings = Settings()
            self.save(settings)
            return settings

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return self._recover(f"Could not read settings: {exc}")

        if (
            not isinstance(raw, dict)
            or type(raw.get("schema_version")) is not int
            or raw.get("schema_version") != SCHEMA_VERSION
        ):
            return self._recover("Settings use an unsupported or invalid schema version.")

        defaults = Settings()
        appearance = raw.get("appearance_mode", defaults.appearance_mode)
        geometry = raw.get("window_geometry", defaults.window_geometry)
        issues = []
        if not isinstance(appearance, str) or appearance not in APPEARANCE_MODES:
            appearance = defaults.appearance_mode
            issues.append("appearance_mode was invalid")
        if not isinstance(geometry, str) or not _GEOMETRY.fullmatch(geometry):
            geometry = defaults.window_geometry
            issues.append("window_geometry was invalid")
        if issues:
            self.last_issue = "Invalid settings were replaced with defaults: " + ", ".join(issues)
            self._preserve_original()
            self._report_issue()
        return Settings(appearance_mode=appearance, window_geometry=geometry)

    def save(self, settings: Settings) -> None:
        if not self._safe_to_replace and self.path.exists():
            raise SettingsError(
                f"Refusing to replace settings because a recoverable backup could not be made: {self.path}"
            )
        if not isinstance(settings.appearance_mode, str) or settings.appearance_mode not in APPEARANCE_MODES:
            raise SettingsError(f"Unsupported appearance mode: {settings.appearance_mode!r}")
        if not isinstance(settings.window_geometry, str) or not _GEOMETRY.fullmatch(settings.window_geometry):
            raise SettingsError(f"Invalid window geometry: {settings.window_geometry!r}")

        temporary_path: Path | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                dir=self.path.parent,
                delete=False,
            ) as stream:
                temporary_path = Path(stream.name)
                json.dump(
                    {"schema_version": SCHEMA_VERSION, **asdict(settings)},
                    stream,
                    indent=2,
                )
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, self.path)
            temporary_path = None
        except OSError as exc:
            raise SettingsError(f"Could not write settings to {self.path}: {exc}") from exc
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    if self.logger:
                        self.logger.warning("Could not remove temporary settings file %s", temporary_path)

    def _recover(self, issue: str) -> Settings:
        self.last_issue = issue
        self._preserve_original()
        self._report_issue()
        return Settings()

    def _preserve_original(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = self.path.with_name(f"{self.path.name}.corrupt-{timestamp}.bak")
        try:
            shutil.copy2(self.path, backup)
            self.backup_path = backup
        except OSError as exc:
            self._safe_to_replace = False
            self.last_issue = f"{self.last_issue}; original settings could not be backed up: {exc}"

    def _report_issue(self) -> None:
        if self.logger and self.last_issue:
            self.logger.warning("%s (backup: %s)", self.last_issue, self.backup_path or "unavailable")
