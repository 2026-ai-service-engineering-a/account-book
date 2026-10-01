from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """api가 환경변수를 읽는 유일한 자리(development-rules 6.3).

    비밀번호에는 기본값이 없다 — 없으면 뜨는 순간 죽는다. LLM 키는 읽지 않는다.
    """

    postgres_user: str = "account"
    postgres_password: SecretStr
    postgres_db: str = "account_book"
    postgres_host: str = "db"
    postgres_port: int = 5432
    user_timezone: str = "Asia/Seoul"
    # 이 금액 이상의 쓰기는 X-Confirmed-By: user가 있어야 한다(api-contract 4장)
    agent_confirm_threshold: int = 100_000
    # 카테고리 고르기의 검색 — 이웃 몇 건으로 투표하나, 가장 비슷한 이웃 쪽으로 얼마나
    # 기울이나(docs/ai/category-suggestion-rag.md 5장)
    rag_top_k: int = 8
    rag_vote_temperature: float = 0.03

    # .env에는 다른 서비스의 변수도 있다. api가 쓰지 않는 것은 모른 척한다.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def database_url(self, database: str | None = None) -> URL:
        """psycopg 3 드라이버의 접속 주소. `database`를 주면 그 DB로 — 테스트가 따로 만든 DB."""
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=database or self.postgres_db,
        )
