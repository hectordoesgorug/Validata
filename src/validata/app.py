"""Application composition root and Tk lifecycle."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from . import __version__
from .core.events import EventDispatcher, EventPump, UiEvent
from .services.logging_setup import LoggingSetup, initialize_logging
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
        self._settings_window = None

        self._configure_window()
        self._build_shell()
        self.dispatcher = EventDispatcher()
        self.event_pump = EventPump(self.root, self.dispatcher, self._handle_event)
        self.event_pump.start()
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
            text="Foundation shell — file processing is not available yet.",
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

    def run(self) -> None:
        self.root.mainloop()

    def close(self) -> None:
        if self._closing:
            return
        self._closing = True
        self.event_pump.stop()
        try:
            geometry = self.root.geometry()
            self.settings = replace(self.settings, window_geometry=geometry)
            self.settings_store.save(self.settings)
        except (OSError, ValueError):
            self.logger.exception("Could not persist settings during shutdown")
        finally:
            self.root.destroy()


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
