from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RCI_", extra="ignore", env_file=".env")

    env: Literal["local", "test", "dev", "stage"] = "local"
    secrets_backend: Literal["devfile", "aws_sm", "vault"] = "devfile"
    database_url: SecretStr | None = None
    redis_url: SecretStr | None = None
    dev_secrets_file: Path = Path(".tmp/auth-secrets.json")
    web_origin: str = "http://127.0.0.1:5173"
    local_password_login: bool = False

    @field_validator("database_url")
    @classmethod
    def validate_database(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None:
            try:
                url = make_url(value.get_secret_value())
                valid = url.drivername == "postgresql+psycopg" and bool(url.host and url.database)
            except Exception:
                valid = False
            if not valid:
                raise ValueError("Database must use a PostgreSQL psycopg connection URL.")
        return value

    @field_validator("redis_url")
    @classmethod
    def validate_redis(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None:
            from urllib.parse import urlsplit

            try:
                url = urlsplit(value.get_secret_value())
                valid = url.scheme in {"redis", "rediss"} and bool(url.hostname)
            except ValueError:
                valid = False
            if not valid:
                raise ValueError("Queue must use a Redis connection URL.")
        return value

    @model_validator(mode="after")
    def require_deployed_connections(self):
        if self.local_password_login and self.env != "local":
            raise ValueError("Password-only login is restricted to the local environment.")
        if self.env in {"dev", "stage"} and not (self.database_url and self.redis_url):
            raise ValueError("Dev and stage require database and Redis configuration.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
