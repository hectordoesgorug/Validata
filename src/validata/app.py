"""Application composition root and Tk lifecycle."""

from __future__ import annotations

import os
import sys
from dataclasses import replace
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

from . import __version__
from .core.events import EventDispatcher, EventPump, UiEvent
from .services.logging_setup import LoggingSetup, initialize_logging
from .services.jobs import JobController
from .services.paths import StorageError, StoragePaths, resolve_storage_paths
from .services.settings import Settings, SettingsStore
from .ui.counter_view import CounterView
from .ui.theme import apply_appearance_mode
from .ui.validator_view import ValidatorView


class ValidataApplication:
    def __init__(
        self,
        paths: StoragePaths,
        settings_store: SettingsStore,
        settings: Settings,
        logging_setup: LoggingSetup,
        *,
        root: Any | None = None,
    ) -> None:
        self.paths = paths
        self.settings_store = settings_store
        self.settings = settings
        self.logging_setup = logging_setup
        self.logger = logging_setup.logger
        apply_appearance_mode(settings.appearance_mode)
        self.root = root or ctk.CTk()
        self._closing = False
        self._close_requested = False
        self._settings_window = None
        self._sources: list[Path] = []
        self._rows: dict[str, tuple[object, ...]] = {}
        self._current_job_id: str | None = None
        self._job_state = "Idle"

        self._configure_window()
        self._build_shell()
        self.dispatcher = EventDispatcher()
        self.job_controller = JobController(self.dispatcher, self.logger)
        self.event_pump = EventPump(self.root, self.dispatcher, self._handle_event)
        self.event_pump.start()
        self.validator_view.add_files_button.configure(command=self.add_files)
        self.validator_view.add_folder_button.configure(command=self.add_folder)
        self.validator_view.remove_button.configure(command=self.remove_sources)
        self.validator_view.clear_button.configure(command=self.clear_sources)
        self.validator_view.start_button.configure(command=self.start_job)
        self.validator_view.cancel_button.configure(command=self.cancel_job)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        warnings = [
            message
            for message in (settings_store.last_issue, logging_setup.error)
            if message
        ]
        if warnings:
            self.root.after_idle(lambda: messagebox.showwarning("Validata startup", "\n\n".join(warnings), parent=self.root))

    def _configure_window(self) -> None:
        self.root.title("Validata")
        self.root.geometry(self.settings.window_geometry)
        self.root.minsize(900, 620)
        icon_path = self._asset_path("icon.ico")
        if icon_path.is_file():
            try:
                self.root.iconbitmap(str(icon_path))
            except Exception:
                self.logger.debug("The application icon could not be set", exc_info=True)

    def _asset_path(self, name: str) -> Path:
        return Path(__file__).resolve().parents[3] / "assets" / name

    def _build_shell(self) -> None:
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.root, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(14, 6))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Validata", font=ctk.CTkFont(size=25, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=8, pady=6
        )
        ctk.CTkButton(header, text="Settings", width=110, command=self.open_settings).grid(
            row=0, column=1, sticky="e", padx=8, pady=6
        )

        self.tabs = ctk.CTkTabview(self.root)
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=20, pady=8)
        validator_tab = self.tabs.add("Validator")
        counter_tab = self.tabs.add("Counter")
        self.validator_view = ValidatorView(validator_tab)
        self.validator_view.pack(fill="both", expand=True)
        self.counter_view = CounterView(counter_tab)
        self.counter_view.pack(fill="both", expand=True)
        self.tabs.set("Validator")

        ctk.CTkLabel(
            self.root,
            text="File-integrity validation and Counter processing are not implemented yet.",
            anchor="w",
            text_color=("gray35", "gray70"),
        ).grid(row=2, column=0, sticky="ew", padx=28, pady=(2, 12))

    def open_settings(self) -> None:
        if self._settings_window is not None and self._settings_window.winfo_exists():
            self._settings_window.focus()
            return

        window = ctk.CTkToplevel(self.root)
        self._settings_window = window
        window.title("Validata Settings")
        window.geometry("560x310")
        window.minsize(480, 280)
        window.transient(self.root)
        window.grid_columnconfigure(0, weight=1)
        window.protocol("WM_DELETE_WINDOW", self._close_settings)

        ctk.CTkLabel(window, text="Settings", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=22, pady=(20, 12)
        )
        ctk.CTkLabel(window, text=f"Version: {__version__}", anchor="w").grid(
            row=1, column=0, sticky="ew", padx=24, pady=6
        )
        self._storage_label = ctk.CTkLabel(
            window,
            text=f"Active storage directory:\n{self.paths.root}",
            anchor="w",
            justify="left",
            wraplength=500,
        )
        self._storage_label.grid(row=2, column=0, sticky="ew", padx=24, pady=6)
        ctk.CTkLabel(window, text="Appearance mode", anchor="w").grid(
            row=3, column=0, sticky="ew", padx=24, pady=(10, 4)
        )
        self._appearance_menu = ctk.CTkOptionMenu(
            window,
            values=["System", "Light", "Dark"],
            command=self._change_appearance,
        )
        self._appearance_menu.set(self.settings.appearance_mode)
        self._appearance_menu.grid(row=4, column=0, sticky="w", padx=24, pady=(0, 18))

    def _change_appearance(self, mode: str) -> None:
        previous = self.settings
        updated = replace(previous, appearance_mode=mode)
        try:
            apply_appearance_mode(mode)
            self.settings_store.save(updated)
        except (ValueError, OSError) as exc:
            self.logger.exception("Could not save appearance preference")
            apply_appearance_mode(previous.appearance_mode)
            self._appearance_menu.set(previous.appearance_mode)
            messagebox.showerror("Settings", f"Could not save appearance setting:\n{exc}", parent=self._settings_window)
            return
        self.settings = updated
        self._appearance_menu.set(mode)

    def _close_settings(self) -> None:
        if self._settings_window is not None:
            self._settings_window.destroy()
            self._settings_window = None

    def _handle_event(self, event: UiEvent) -> None:
        self.logger.debug("Received UI event: %s", event.kind)
        job_id = event.payload.get("job_id")
        if event.kind == "job_finished" and job_id == self._current_job_id:
            counts = event.payload["counts"]
            state = event.payload["state"]
            self.validator_view.set_active(False)
            self._refresh_source_controls()
            self._show_counts(state, counts)
            self._current_job_id = None
            if self._close_requested:
                self._finish_close()
            return
        if job_id != self._current_job_id:
            return
        if event.kind == "job_state":
            state = event.payload["state"]
            self._job_state = state
            self.validator_view.status_label.configure(text=self._progress_text(state, {}))
        elif event.kind == "file_discovered":
            path = Path(event.payload["path"])
            file_id = event.payload["file_id"]
            values = (path.name, str(path.parent), path.suffix.upper() or "Unknown",
                      "—", "Discovered", "Waiting for processing queue")
            self._rows[file_id] = values
            self.validator_view.results.insert_row(values, row_id=file_id)
            self._show_counts(self._job_state, event.payload["counts"])
        elif event.kind == "file_status":
            file_id = event.payload["file_id"]
            prior = self._rows.get(file_id)
            if prior is not None:
                values = (*prior[:4], event.payload["status"], event.payload["detail"])
                self._rows[file_id] = values
                self.validator_view.results.update_row(file_id, values=values)
            self._show_counts(self._job_state, event.payload["counts"])
        elif event.kind == "discovery_error":
            path = Path(event.payload["path"])
            message = event.payload["message"]
            self.logger.warning("Discovery error at %s: %s", path, message)
            error_id = event.payload["error_id"]
            values = (path.name or str(path), str(path.parent), "—", "—", "Discovery Error", message)
            self.validator_view.results.insert_row(values, row_id=error_id, status="warning")
            self._show_counts(self._job_state, event.payload["counts"])
        elif event.kind == "job_error":
            self.validator_view.status_label.configure(text=event.payload["message"])

    def add_files(self) -> None:
        paths = filedialog.askopenfilenames(parent=self.root, title="Add files to Validator")
        self._add_sources(Path(path) for path in paths)

    def add_folder(self) -> None:
        path = filedialog.askdirectory(parent=self.root, title="Add folder to Validator", mustexist=True)
        if path:
            self._add_sources((Path(path),))

    def _add_sources(self, paths) -> None:
        existing = {self._source_key(path) for path in self._sources}
        for path in paths:
            absolute = Path(os.path.abspath(path))
            key = self._source_key(absolute)
            if key not in existing:
                self._sources.append(absolute)
                self.validator_view.source_list.insert("end", str(absolute))
                existing.add(key)
        self._refresh_source_controls()

    @staticmethod
    def _source_key(path: Path) -> str:
        return os.path.normcase(os.path.abspath(path))

    def remove_sources(self) -> None:
        selected = tuple(self.validator_view.source_list.curselection())
        for index in reversed(selected):
            self.validator_view.source_list.delete(index)
            del self._sources[index]
        self._refresh_source_controls()

    def clear_sources(self) -> None:
        self._sources.clear()
        self.validator_view.source_list.delete(0, "end")
        self._refresh_source_controls()

    def _refresh_source_controls(self) -> None:
        self.validator_view.start_button.configure(state="normal" if self._sources else "disabled")

    def start_job(self) -> None:
        if not self._sources or self.job_controller.active:
            return
        self.validator_view.results.clear()
        self._rows.clear()
        try:
            self._current_job_id = self.job_controller.start(tuple(self._sources))
        except RuntimeError as exc:
            self.logger.error("Could not start Validator job: %s", exc)
            return
        self._job_state = "Discovering"
        self.validator_view.set_active(True)
        self._show_counts("Discovering", {})

    def cancel_job(self) -> None:
        self.job_controller.cancel()
        if self.job_controller.active:
            self._job_state = "Cancelling"
            self.validator_view.status_label.configure(text="Cancelling — active infrastructure tasks will finish safely.")

    def _show_counts(self, state: str, counts) -> None:
        self.validator_view.status_label.configure(text=self._progress_text(state, counts))

    @staticmethod
    def _progress_text(state: str, counts) -> str:
        found = counts.get("discovered", 0)
        return (f"{state} — {found:,} files found; {counts.get('running', 0):,} processing; "
                f"{counts.get('completed', 0):,} tasks completed; {counts.get('queued', 0):,} queued; "
                f"{counts.get('cancelled', 0):,} not started; {counts.get('discovery_errors', 0):,} discovery errors; "
                f"{counts.get('processing_errors', 0):,} processing errors. Integrity checks are not implemented.")

    def _finish_close(self) -> None:
        if self._closing:
            return
        self._closing = True
        self.event_pump.stop()
        try:
            self.settings = replace(self.settings, window_geometry=self.root.geometry())
            self.settings_store.save(self.settings)
        except (OSError, ValueError):
            self.logger.exception("Could not persist settings during shutdown")
        finally:
            self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()

    def close(self) -> None:
        if self._closing or self._close_requested:
            return
        if self._current_job_id is not None:
            self._close_requested = True
            if self.job_controller.active:
                self._job_state = "Cancelling"
                self.validator_view.status_label.configure(text="Cancelling job before closing…")
                self.job_controller.cancel()
            else:
                self.validator_view.status_label.configure(text="Finishing job before closing…")
            return
        self._finish_close()


def create_application(*, storage_paths: StoragePaths | None = None) -> ValidataApplication:
    paths = storage_paths or resolve_storage_paths()
    logging_setup = initialize_logging(paths)
    settings_store = SettingsStore(paths.settings_file, logging_setup.logger)
    settings = settings_store.load()
    return ValidataApplication(paths, settings_store, settings, logging_setup)


def main() -> int:
    try:
        application = create_application()
    except StorageError as exc:
        print(f"Validata cannot start: {exc}", file=sys.stderr)
        return 1
    application.run()
    return 0
