"""Streaming, read-only filesystem discovery for Validator."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Iterator


@dataclass(frozen=True, slots=True)
class DiscoveredFile:
    path: Path
    size: int
    modified_ns: int
    is_symlink: bool


@dataclass(frozen=True, slots=True)
class DiscoveryError:
    path: Path
    message: str


def discover(sources: tuple[Path, ...], cancel: Event) -> Iterator[DiscoveredFile | DiscoveryError]:
    """Yield files/errors incrementally; never recurse through directory links."""
    pending = list(reversed(_unique_sources(sources)))

    while pending and not cancel.is_set():
        path = pending.pop()
        try:
            is_link = path.is_symlink() or path.is_junction()
            if is_link and path.is_dir():
                continue
            if not is_link and path.is_dir():
                with os.scandir(path) as entries:
                    for entry in entries:
                        if cancel.is_set():
                            break
                        try:
                            if entry.is_symlink() or getattr(entry, "is_junction", lambda: False)():
                                item = _file(Path(entry.path), True)
                                if item is not None:
                                    yield item
                            elif entry.is_dir(follow_symlinks=False):
                                pending.append(Path(entry.path))
                            elif entry.is_file(follow_symlinks=False):
                                item = _file(Path(entry.path), False)
                                if item is not None:
                                    yield item
                        except OSError as exc:
                            yield DiscoveryError(Path(entry.path), str(exc))
            else:
                item = _file(path, is_link)
                if item is not None:
                    yield item
        except OSError as exc:
            yield DiscoveryError(path, str(exc))


def _file(path: Path, is_symlink: bool) -> DiscoveredFile | None:
    try:
        info = path.stat() if is_symlink else path.stat(follow_symlinks=True)
    except (OSError, TypeError) as exc:
        raise OSError(f"File is unavailable: {exc}") from exc
    if not path.is_file():
        if is_symlink and path.is_dir():
            return None
        raise OSError("Path is not a regular file")
    return DiscoveredFile(path, info.st_size, info.st_mtime_ns, is_symlink)


def _unique_sources(sources: tuple[Path, ...]) -> tuple[Path, ...]:
    unique: list[Path] = []
    keys: set[str] = set()
    for source in sources:
        absolute = Path(os.path.abspath(source))
        key = os.path.normcase(str(absolute))
        if key not in keys:
            unique.append(absolute)
            keys.add(key)
    directories = [path for path in unique if path.is_dir() and
                   not (path.is_symlink() or path.is_junction())]
    selected = []
    selected_keys = set()
    for path in unique:
        key = os.path.normcase(str(path))
        if path.is_file() and any(_is_under(path, root) for root in directories):
            continue
        if path in directories and any(root != path and _is_under(path, root) for root in directories):
            continue
        if key not in selected_keys:
            selected.append(path)
            selected_keys.add(key)
    return tuple(selected)


def _is_under(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath((os.path.normcase(str(path)), os.path.normcase(str(root)))) == os.path.normcase(str(root))
    except ValueError:
        return False
