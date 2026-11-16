import json
from pathlib import Path

import pytest

from validata.services.settings import Settings, SettingsError, SettingsStore


def test_missing_settings_create_valid_defaults(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    settings = store.load()
    assert settings == Settings()
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "schema_version": 1,
        "appearance_mode": "System",
        "window_geometry": "1120x760",
    }


def test_save_load_round_trip(tmp_path: Path) -> None:
    store = SettingsStore(tmp_path / "settings.json")
    expected = Settings(appearance_mode="Dark", window_geometry="1280x800+10+20")
    store.save(expected)
    assert store.load() == expected


def test_malformed_settings_are_backed_up_and_recovered(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{broken", encoding="utf-8")
    store = SettingsStore(path)

    assert store.load() == Settings()
    assert store.last_issue is not None
    assert store.backup_path is not None
    assert store.backup_path.read_text(encoding="utf-8") == "{broken"
    assert path.read_text(encoding="utf-8") == "{broken"

    store.save(Settings(appearance_mode="Light"))
    assert json.loads(path.read_text(encoding="utf-8"))["appearance_mode"] == "Light"
    assert store.backup_path.exists()


def test_invalid_fields_fall_back_without_losing_valid_values(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"schema_version": 1, "appearance_mode": "Dark", "window_geometry": "bad"}),
        encoding="utf-8",
    )
    store = SettingsStore(path)
    assert store.load() == Settings(appearance_mode="Dark")
    assert store.backup_path is not None and store.backup_path.exists()
    assert store.last_issue is not None


def test_unknown_schema_is_preserved_for_recovery(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"schema_version": 99}', encoding="utf-8")
    store = SettingsStore(path)
    assert store.load() == Settings()
    assert store.backup_path is not None and store.backup_path.exists()
    assert json.loads(path.read_text(encoding="utf-8"))["schema_version"] == 99


def test_refuses_to_replace_recovery_file_when_backup_fails(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "settings.json"
    path.write_text("{broken", encoding="utf-8")
    store = SettingsStore(path)

    def fail_backup(*_args, **_kwargs):
        raise OSError("simulated backup failure")

    monkeypatch.setattr("validata.services.settings.shutil.copy2", fail_backup)
    assert store.load() == Settings()
    with pytest.raises(SettingsError, match="Refusing to replace"):
        store.save(Settings(appearance_mode="Dark"))
    assert path.read_text(encoding="utf-8") == "{broken"


def test_atomic_replace_failure_preserves_original_and_cleans_temp(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "settings.json"
    path.write_text('{"existing":true}', encoding="utf-8")
    store = SettingsStore(path)

    def fail_replace(_source, _destination):
        raise OSError("simulated replace failure")

    monkeypatch.setattr("validata.services.settings.os.replace", fail_replace)
    with pytest.raises(SettingsError, match="Could not write settings"):
        store.save(Settings(appearance_mode="Light"))
    assert path.read_text(encoding="utf-8") == '{"existing":true}'
    assert list(tmp_path.glob(".settings.json.*.tmp")) == []


def test_rejects_invalid_values_on_save(tmp_path: Path) -> None:
    with pytest.raises(SettingsError, match="Unsupported appearance"):
        SettingsStore(tmp_path / "settings.json").save(Settings(appearance_mode="Neon"))
