import pytest
from app.settings import Settings
from pydantic import ValidationError


@pytest.mark.parametrize("url", ["sqlite:///local.db", "postgresql://localhost/rci",
                                 "not-a-url", "postgresql+psycopg:///"])
def test_non_postgresql_database_rejected(url):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url=url)


@pytest.mark.parametrize("url", ["http://localhost", "redis:///", "not-a-url"])
def test_invalid_redis_url_rejected(url):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, redis_url=url)


@pytest.mark.parametrize("env", ["dev", "stage"])
def test_deployed_environment_requires_connections(env):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, env=env, database_url=None, redis_url=None)


def test_connection_password_is_hidden():
    settings = Settings(_env_file=None,
                        database_url="postgresql+psycopg://test:synthetic-secret@localhost/rci",
                        redis_url="redis://:synthetic-secret@localhost/0")
    assert "synthetic-secret" not in repr(settings)
    assert "synthetic-secret" not in settings.model_dump_json()
