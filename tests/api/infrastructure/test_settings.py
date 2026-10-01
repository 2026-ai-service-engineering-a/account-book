from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.infrastructure.settings import Settings

NAMES = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_HOST", "POSTGRES_PORT")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in NAMES:
        monkeypatch.delenv(name, raising=False)


def test_dies_without_a_password():
    # 시크릿에는 기본값이 없다(development-rules 6.3)
    with pytest.raises(ValidationError, match="postgres_password"):
        Settings(_env_file=None)


def test_builds_a_psycopg_url_without_leaking_the_password(monkeypatch):
    monkeypatch.setenv("POSTGRES_PASSWORD", "p@ss/word")
    settings = Settings(_env_file=None)
    url = settings.database_url()
    assert url.drivername == "postgresql+psycopg" and url.host == "db" and url.port == 5432
    assert url.password == "p@ss/word" and "p@ss" not in str(url)  # 문자열로 찍으면 가려진다
    assert settings.database_url("other").database == "other"


def test_ignores_other_services_variables(tmp_path):
    env = tmp_path / ".env"
    env.write_text("POSTGRES_PASSWORD=x\nGEMINI_API_KEY=secret\n")
    settings = Settings(_env_file=env)
    assert not hasattr(settings, "gemini_api_key")
