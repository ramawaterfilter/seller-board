import importlib.util
from pathlib import Path

import pytest
from app.settings import Settings

ROOT = Path(__file__).resolve().parents[3]


def helper():
    spec = importlib.util.spec_from_file_location(
        "local_auth_helper", ROOT / "scripts/initialize_local_auth.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.req("REQ-001")
def test_helper_rejects_remote_database_before_prompt_or_connection(monkeypatch):
    module = helper()
    settings = Settings(
        _env_file=None,
        env="local",
        database_url="postgresql+psycopg://synthetic@remote.example.test/rci_local",
    )
    monkeypatch.setattr(module, "Settings", lambda: settings)
    monkeypatch.setattr(module.getpass, "getpass", lambda _: pytest.fail("Must not prompt"))
    monkeypatch.setattr(module, "create_engine", lambda *_a, **_k: pytest.fail("Must not connect"))
    with pytest.raises(SystemExit, match="localhost"):
        module.main()


@pytest.mark.req("REQ-001")
def test_helper_rejects_short_password_without_writing_secrets(monkeypatch, tmp_path):
    module = helper()
    path = tmp_path / "secrets.json"
    settings = Settings(
        _env_file=None,
        env="local",
        dev_secrets_file=path,
        database_url="postgresql+psycopg://synthetic@localhost/rci_local",
    )
    monkeypatch.setattr(module, "Settings", lambda: settings)
    monkeypatch.setattr(module.getpass, "getpass", lambda _: "short")
    monkeypatch.setattr(module, "create_engine", lambda *_a, **_k: pytest.fail("Must not connect"))
    with pytest.raises(SystemExit, match="12 to 1024"):
        module.main()
    assert not path.exists()
