from __future__ import annotations

from agent.infrastructure.settings import Settings
from agent.interfaces.services import Services
from agent.main import create_app


def test_assembles_from_settings_without_calling_the_model(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g-key")
    monkeypatch.delenv("AGENT_MODEL", raising=False)
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    app = create_app(Settings(_env_file=None))
    assert isinstance(app.state.services, Services)
