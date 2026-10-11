from unittest.mock import AsyncMock

import pytest
from app.main import create_app
from app.settings import Settings
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    settings = Settings(_env_file=None, env="test", database_url=None, redis_url=None)
    with TestClient(create_app(settings)) as client:
        client.app.state.database = AsyncMock()
        client.app.state.redis = AsyncMock()
        yield client


def test_ready_when_both_dependencies_respond(client):
    response = client.get("/api/v1/readyz")
    assert response.status_code == 200
    assert response.json()["dependencies"] == {"postgres": "ok", "redis": "ok"}


@pytest.mark.parametrize("dependency", ["database", "redis"])
def test_one_failed_dependency_is_unavailable(client, dependency):
    resource = getattr(client.app.state, dependency)
    probe = resource.ready if dependency == "database" else resource.ping
    probe.side_effect = RuntimeError("synthetic-secret")
    response = client.get("/api/v1/readyz")
    assert response.status_code == 503
    error = response.json()["error"]
    assert error["code"] == "DEPENDENCIES_UNAVAILABLE"
    assert error["details"]["postgres" if dependency == "database" else "redis"] == "unavailable"
    assert error["trace_id"] == response.headers["x-trace-id"]
    assert "synthetic-secret" not in response.text


def test_missing_dependency_does_not_report_ready(client):
    client.app.state.redis = None
    response = client.get("/api/v1/readyz")
    assert response.status_code == 503
    assert response.json()["error"]["details"]["redis"] == "not_configured"
