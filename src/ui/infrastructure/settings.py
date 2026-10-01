from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ui가 환경변수를 읽는 유일한 자리(development-rules 6.3)."""

    user_timezone: str = "Asia/Seoul"
    # 비어 있으면 AI 자리에 각본 대역이 선다. 키 없이 화면을 만져 볼 수 있게 하려는 것이다.
    agent_base_url: str = ""
    # agent의 LLM 호출 한 번 상한(agent와 같은 변수). agent는 스키마가 틀리면 한 번 더 부르니
    # ui는 그보다 오래 기다린다.
    agent_timeout_seconds: float = 10.0

    # .env에는 다른 서비스의 변수도 있다. ui가 쓰지 않는 것은 모른 척한다.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
