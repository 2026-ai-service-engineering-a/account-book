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
