"""
Integration Tests for FastAPI Endpoints (with JWT auth).
"""

import pytest

SAMPLE_STUDENT = {
    "age": 21,
    "gender": "Male",
    "country": "India",
    "academic_level": "Undergraduate",
    "most_used_platform": "Instagram",
    "purpose_of_use": "Entertainment",
    "avg_daily_usage_hours": 6.0,
    "daily_unlocks": 120,
    "study_hours": 2.5,
    "physical_activity_hours": 0.5,
    "sleep_hours_per_night": 5.0,
    "stress_level": "High",
}


# ---- Public endpoints ---------------------------------------------------

def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["ml_model_loaded"] is True
    assert data["rag_chunks_indexed"] >= 25


def test_knowledge_base_endpoint(client):
    res = client.get("/knowledge-base")
    assert res.status_code == 200
    data = res.json()
    assert data["total_documents"] == 25
    assert len(data["categories"]) == 5


# ---- Auth endpoints -----------------------------------------------------

def test_auth_register_and_login(client):
    import uuid
    suffix = uuid.uuid4().hex[:8]
    res = client.post("/auth/register", json={
        "username": f"authtest_{suffix}", "email": f"auth_{suffix}@test.com", "password": "pass123",
    })
    assert res.status_code == 200
    assert "access_token" in res.json()

    res = client.post("/auth/login", json={
        "username": f"authtest_{suffix}", "password": "pass123",
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


# ---- Protected endpoints ------------------------------------------------

def test_predict_requires_auth(client):
    res = client.post("/predict", json=SAMPLE_STUDENT)
    assert res.status_code in (401, 403)


def test_predict_endpoint(client, auth_headers):
    res = client.post("/predict", json=SAMPLE_STUDENT, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert 0.0 <= data["predicted_mental_health_score"] <= 10.0
    assert "band" in data


def test_explain_endpoint(client, auth_headers):
    res = client.post("/explain", json=SAMPLE_STUDENT, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "predicted_score" in data
    assert len(data["risk_factors"]) > 0


def test_generate_plan_endpoint(client, auth_headers):
    res = client.post("/generate-plan", json={"student_data": SAMPLE_STUDENT}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["steps"]) == 3
    assert len(data["retrieved_sources"]) > 0


def test_chat_normal_endpoint(client, auth_headers):
    res = client.post("/chat", json={
        "message": "How can I improve sleep during exam week?",
        "student_context": SAMPLE_STUDENT,
    }, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["is_crisis"] is False
    assert len(data["reply"]) > 0


def test_chat_crisis_interceptor(client, auth_headers):
    res = client.post("/chat", json={
        "message": "I feel hopeless and want to kill myself",
        "student_context": SAMPLE_STUDENT,
    }, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["is_crisis"] is True
    assert any("14416" in h["number"] for h in data["safety_alert"]["helplines"])
