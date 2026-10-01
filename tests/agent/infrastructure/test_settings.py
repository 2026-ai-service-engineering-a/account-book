from __future__ import annotations

import pytest
from pydantic import ValidationError

from agent.infrastructure.settings import Settings

KEYS = ("AGENT_MODEL", "GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in KEYS:
        monkeypatch.delenv(name, raising=False)


def test_picks_the_key_of_the_models_provider(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g-key")
    settings = Settings(_env_file=None)
    assert settings.agent_model.startswith("gemini/") and settings.api_key() == "g-key"


def test_other_provider(monkeypatch):
    monkeypatch.setenv("AGENT_MODEL", "anthropic/claude-haiku-4-5")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a-key")
    assert Settings(_env_file=None).api_key() == "a-key"


def test_dies_without_the_key_for_the_model(monkeypatch):
    # 시크릿에는 기본값이 없다. 없으면 뜨는 순간 죽는다
    monkeypatch.setenv("OPENAI_API_KEY", "o-key")
    with pytest.raises(ValidationError, match="GEMINI_API_KEY"):
        Settings(_env_file=None)


def test_dies_on_unknown_provider(monkeypatch):
    monkeypatch.setenv("AGENT_MODEL", "mystery/model")
    with pytest.raises(ValidationError, match="mystery"):
        Settings(_env_file=None)


def test_key_does_not_leak_into_repr(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g-key")
    assert "g-key" not in repr(Settings(_env_file=None))


def test_reads_env_file_and_ignores_other_services(tmp_path):
    env = tmp_path / ".env"
    env.write_text("GEMINI_API_KEY=g-key\nAGENT_TIMEOUT_SECONDS=4\nUI_PORT=8080\n")
    settings = Settings(_env_file=env)
    assert settings.agent_timeout_seconds == 4
