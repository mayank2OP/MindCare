"""Shared test fixtures for MindCare test suite."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """Register (or login) a test user and return Bearer headers."""
    res = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
    })
    if res.status_code == 200:
        token = res.json()["access_token"]
    else:
        res = client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpass123",
        })
        token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
