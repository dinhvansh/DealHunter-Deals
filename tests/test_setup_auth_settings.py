from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from dealhunter.api.setup_auth import router
from dealhunter.core.config import get_settings
from dealhunter.db import Base
from dealhunter.db.session import get_db
from dealhunter.services.security import hash_password, verify_password


def _client(monkeypatch) -> TestClient:
    monkeypatch.setenv("DEALHUNTER_SECRET_KEY", "unit-test-master-secret")
    monkeypatch.setenv("DEALHUNTER_DATABASE_URL", "sqlite://")
    get_settings.cache_clear()
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = Session(engine)

    def override_db():
        yield session

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def test_passwords_are_scrypt_hashed():
    encoded = hash_password("long-enough-password")
    assert encoded.startswith("scrypt$")
    assert "long-enough-password" not in encoded
    assert verify_password("long-enough-password", encoded)
    assert not verify_password("wrong-password", encoded)


def test_first_run_creates_admin_session_and_masks_ai_secret(monkeypatch):
    client = _client(monkeypatch)
    response = client.post(
        "/api/v1/setup/complete",
        json={
            "admin_email": "Admin@Example.com",
            "admin_password": "strong-password-123",
            "display_name": "Admin",
            "app_url": "https://deal.example.com",
            "timezone": "Asia/Ho_Chi_Minh",
            "language": "vi",
            "ai_provider": "openai_compatible",
            "ai_base_url": "https://api.example.com/v1",
            "ai_api_key": "secret-api-token-123456",
            "ai_model": "model-x",
        },
    )
    assert response.status_code == 200
    assert "dealhunter_session" in response.cookies

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "admin@example.com"

    settings = client.get("/api/v1/settings")
    assert settings.status_code == 200
    payload = settings.json()
    assert payload["ai"]["configured"] is True
    assert payload["ai"]["secret_masked"] != "secret-api-token-123456"
    assert "secret-api-token-123456" not in settings.text


def test_setup_can_only_run_once_and_login_rejects_bad_password(monkeypatch):
    client = _client(monkeypatch)
    payload = {
        "admin_email": "admin@example.com",
        "admin_password": "strong-password-123",
        "display_name": "Admin",
    }
    assert client.post("/api/v1/setup/complete", json=payload).status_code == 200
    assert client.post("/api/v1/setup/complete", json=payload).status_code == 409

    client.post("/api/v1/auth/logout")
    bad = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "wrong-password"},
    )
    assert bad.status_code == 401
    good = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "strong-password-123"},
    )
    assert good.status_code == 200
    assert "dealhunter_session" in good.cookies
