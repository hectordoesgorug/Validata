import tkinter as tk
from pathlib import Path
from threading import Thread

import pytest

from validata import __version__
from validata.app import create_application
from validata.core.events import UiEvent
from validata.services.paths import StoragePaths


def test_application_package_imports() -> None:
    assert __version__ == "0.1.0"
    from validata.__main__ import main

    assert callable(main)


def test_gui_startup_and_appearance_persistence_when_display_is_available(tmp_path: Path) -> None:
    try:
        probe = tk.Tk()
        probe.withdraw()
        probe.destroy()
    except tk.TclError as exc:
        pytest.skip(f"no graphical session is available: {exc}")

    application = create_application(storage_paths=StoragePaths(tmp_path / "data", "development"))
    try:
        application.root.withdraw()
        application.root.update()
        assert application.root.title() == "Validata"
        assert application.tabs.get() == "Validator"
        application.tabs.set("Counter")
        assert application.tabs.get() == "Counter"
        row_id = application.validator_view.results.insert_row(
            ("Sample.txt", str(tmp_path), "Text", "Balanced", "Skipped", "UI component check"),
            status="skipped",
        )
        assert application.validator_view.results.tree.exists(row_id)
        assert application.validator_view.results.tree.item(row_id, "tags") == ("skipped",)
        application.validator_view.results.update_row(
            row_id,
            values=("Sample.txt", str(tmp_path), "Text", "Balanced", "Skipped", "Updated"),
        )
        assert application.validator_view.results.tree.item(row_id, "values")[-1] == "Updated"
        application.validator_view.results.remove_row(row_id)
        thread_errors = []

        def insert_from_worker() -> None:
            try:
                application.validator_view.results.insert_row(("x", "x", "x", "x", "x", "x"))
            except RuntimeError as exc:
                thread_errors.append(str(exc))

        worker = Thread(target=insert_from_worker)
        worker.start()
        worker.join(timeout=2)
        assert not worker.is_alive()
        assert thread_errors == ["results table may only be accessed on its creating thread"]

        application.open_settings()
        application.root.update()
        assert str(application.paths.root) in application._storage_label.cget("text")
        application._change_appearance("Dark")
        assert application.settings_store.load().appearance_mode == "Dark"
        assert application._appearance_menu.get() == "Dark"
        application.dispatcher.publish(UiEvent("smoke"))
        close_command = application.root.protocol("WM_DELETE_WINDOW")
        application.root.after(120, lambda: application.root.tk.call(close_command))
        application.run()
        assert application._closing
    finally:
        if not application._closing:
            application.close()
