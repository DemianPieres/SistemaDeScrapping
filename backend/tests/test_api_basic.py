"""Tests básicos: la API arranca y responde sin requerir login."""

import os
import sys

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_leadscraper.db")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402
from app.utils.database import Base, engine  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_me_returns_default_user(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "team@leadscraper.app"
    assert data["full_name"] == "Equipo LeadScraper"


def test_stats_accessible_without_auth(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_businesses"] == 0
    assert data["total_leads"] == 0


def test_invalid_url_rejected(client):
    payload = {"source_url": "https://google.com", "keyword": "test"}
    response = client.post("/api/scraping/jobs", json=payload)
    assert response.status_code == 400
    assert "coordenadas" in response.json()["detail"].lower()
