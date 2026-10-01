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

    # .env에는 다른 서비스의 변수도 있다. agent가 쓰지 않는 것은 모른 척한다.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def _key_for_model(self) -> Self:
        self.api_key()
        return self

    def api_key(self) -> str:
        provider = self.agent_model.partition("/")[0]
        keys = {
            "gemini": self.gemini_api_key,
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
        }
        if provider not in keys:
            raise ValueError(f"AGENT_MODEL의 제공자를 모른다: {provider}")
        key = keys[provider].get_secret_value()
        if not key:
            raise ValueError(f"AGENT_MODEL이 {provider}인데 {provider.upper()}_API_KEY가 비어 있다")
        return key
