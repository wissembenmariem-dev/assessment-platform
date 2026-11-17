import os

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "dummy")
os.environ.setdefault("APP_SECRET_KEY", "test-secret")

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


def test_login_rejects_bad_credentials_then_rate_limits(monkeypatch):
    monkeypatch.setattr(settings, "recruiter_email", "recruiter@example.com")
    monkeypatch.setattr(settings, "recruiter_password", "correct-horse")
    client = TestClient(app)
    codes = [client.post("/api/v1/auth/login", json={"email": "recruiter@example.com", "password": "wrong"}).status_code for _ in range(6)]
    assert codes[:5] == [401] * 5
    assert codes[5] == 429


def test_login_refused_when_password_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "recruiter_email", "recruiter@example.com")
    monkeypatch.setattr(settings, "recruiter_password", "")
    app.state.limiter.reset()
    response = TestClient(app).post("/api/v1/auth/login", json={"email": "recruiter@example.com", "password": ""})
    assert response.status_code == 401
