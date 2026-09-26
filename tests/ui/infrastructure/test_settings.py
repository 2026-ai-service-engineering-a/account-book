from __future__ import annotations

from ui.infrastructure.settings import Settings


def test_default_timezone(monkeypatch):
    monkeypatch.delenv("USER_TIMEZONE", raising=False)
    assert Settings(_env_file=None).user_timezone == "Asia/Seoul"


def test_reads_env_and_ignores_other_services(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("USER_TIMEZONE=UTC\nPOSTGRES_PASSWORD=secret\n")
    monkeypatch.delenv("USER_TIMEZONE", raising=False)
    assert Settings(_env_file=env).user_timezone == "UTC"
