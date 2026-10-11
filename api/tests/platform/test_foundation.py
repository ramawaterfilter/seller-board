import pytest
from app.main import create_app
from app.settings import Settings
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError


@pytest.fixture
def client():
    settings = Settings(_env_file=None, env="test", database_url=None, redis_url=None)
    with TestClient(create_app(settings), raise_server_exceptions=False) as instance:
        yield instance


def test_liveness(client):
    response = client.get("/api/v1/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert len(response.headers["x-trace-id"]) == 32


@pytest.mark.parametrize(
    "method,path,status,code",
    [
        ("get", "/api/v1/missing", 404, "NOT_FOUND"),
        ("post", "/api/v1/healthz", 405, "METHOD_NOT_ALLOWED"),
        ("get", "/api/v1/readyz", 503, "DEPENDENCIES_NOT_CONFIGURED"),
    ],
)
def test_error_envelope(client, method, path, status, code):
    response = getattr(client, method)(path)
    assert response.status_code == status
    error = response.json()["error"]
    assert error["code"] == code
    assert isinstance(error["details"], dict)
    assert error["trace_id"] == response.headers["x-trace-id"]


def test_validation_does_not_echo_input(client):
    @client.app.get("/test-validation")
    def validate(count: int):
        return {"count": count}

    response = client.get("/test-validation", params={"count": "synthetic-secret"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "synthetic-secret" not in response.text


def test_unexpected_exception_is_sanitized(client):
    @client.app.get("/test-error")
    def fail():
        raise RuntimeError("synthetic-secret")

    response = client.get("/test-error")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert response.json()["error"]["trace_id"] == response.headers["x-trace-id"]
    assert "synthetic-secret" not in response.text


def test_production_environment_rejected(monkeypatch):
    monkeypatch.setenv("RCI_ENV", "prod")
    with pytest.raises(ValidationError):
        Settings()


def test_openapi(client):
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert "/api/v1/healthz" in response.json()["paths"]
    logout = response.json()["paths"]["/api/v1/auth/logout"]["post"]
    assert any(header["name"] == "X-CSRF-Token" for header in logout["parameters"])
    assert (
        logout["responses"]["401"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ErrorEnvelope"
    )
    assert isinstance(client.app, FastAPI)
