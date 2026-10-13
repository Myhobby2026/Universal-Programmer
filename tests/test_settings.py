from core.settings import SettingsStore


def test_settings_recover_and_persist(tmp_path):
    path = tmp_path / "settings.json"
    settings = SettingsStore(path)
    settings.set("theme", "light")
    settings.save()
    assert SettingsStore(path).get("theme") == "light"
