from __future__ import annotations

from typing import Self

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """agent가 환경변수를 읽는 유일한 자리(development-rules 6.3).

    키는 셋 중 하나만 채우면 된다. 대신 `AGENT_MODEL`의 제공자 키가 비어 있으면 뜨는 순간
    죽는다 — 시크릿에는 기본값을 주지 않는다.
    """

    # litellm 표기(<제공자>/<모델>). 기본값은 가장 싼 축이다(docs/ai/README.md 4장).
    agent_model: str = "gemini/gemini-flash-lite-latest"
    gemini_api_key: SecretStr = SecretStr("")
    openai_api_key: SecretStr = SecretStr("")
    anthropic_api_key: SecretStr = SecretStr("")
    # LLM 호출 한 번의 상한. 스키마를 못 맞추면 한 번 더 부르니, 요청 하나는 이것의 두 배까지 간다.
    agent_timeout_seconds: float = 10.0
    # 대화 루프의 상한(docs/ai/agent-loop.md 8장). 넘으면 끊고 그때까지의 답을 낸다.
    agent_max_steps: int = 8  # LLM 호출 수
    agent_max_cost_usd: float = 0.50  # 요청 하나가 쓸 수 있는 돈

    # api의 주소. 지금은 compose가 ui 안의 api 대역(http://ui:8080)으로 덮어쓴다.
    api_base_url: str = "http://api:8000"

    # 카테고리 고르기(RAG) — docs/ai/category-suggestion-rag.md.
    # EMBEDDING_MODEL이 비면 벡터 검색을 끈다. 규칙·이력만으로 돌고, 나머지는 사람이 고른다.
    embedding_model: str = "gemini/gemini-embedding-001"
    # pgvector의 HNSW 인덱스가 받는 2000차원 아래로 받아 둔다. 저장소를 옮겨도 다시 색인하지 않게.
    embedding_dimensions: int = 768
    classify_min_confidence: float = 0.7  # 이 이상이면 LLM 없이 검색 결과를 쓴다
    classify_abstain_below: float = 0.25  # 이 아래면 LLM도 부르지 않고 사람에게 넘긴다

    # .env에는 다른 서비스의 변수도 있다. agent가 쓰지 않는 것은 모른 척한다.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def _key_for_model(self) -> Self:
        self.api_key()
        if self.embedding_model:
            self.api_key(self.embedding_model)
        return self

    def api_key(self, model: str | None = None) -> str:
        """`model`(기본은 AGENT_MODEL)의 제공자 키. 비어 있으면 ValueError."""
        name = model or self.agent_model
        provider = name.partition("/")[0]
        keys = {
            "gemini": self.gemini_api_key,
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
        }
        if provider not in keys:
            raise ValueError(f"{name}의 제공자를 모른다: {provider}")
        key = keys[provider].get_secret_value()
        if not key:
            raise ValueError(f"{name}을 쓰는데 {provider.upper()}_API_KEY가 비어 있다")
        return key
