from __future__ import annotations

import pytest
from pydantic import ValidationError

from agent.infrastructure.settings import Settings

KEYS = (
    "AGENT_MODEL",
    "EMBEDDING_MODEL",
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
)


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
    monkeypatch.setenv("EMBEDDING_MODEL", "")  # 벡터 검색을 끄면 Gemini 키가 없어도 뜬다
    assert Settings(_env_file=None).api_key() == "a-key"


def test_embedding_model_needs_its_own_key(monkeypatch):
    # 대화는 Anthropic이어도 임베딩이 Gemini면 Gemini 키가 있어야 한다
    monkeypatch.setenv("AGENT_MODEL", "anthropic/claude-haiku-4-5")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "a-key")
    with pytest.raises(ValidationError, match="GEMINI_API_KEY"):
        Settings(_env_file=None)


def test_rag_defaults(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g-key")
    settings = Settings(_env_file=None)
    assert settings.embedding_dimensions == 768 and settings.api_key(settings.embedding_model)
    assert settings.classify_abstain_below < settings.classify_min_confidence


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


def test_document_retrieval_defaults_were_measured(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "g-key")
    settings = Settings(_env_file=None)
    assert (settings.doc_chunk_strategy, settings.doc_search_mode, settings.doc_top_k) == (
        "paragraph_item",
        "hybrid",
        8,
    )
    with pytest.raises(ValidationError):
        Settings(_env_file=None, doc_search_mode="bm25")  # 일부러 틀린 값
