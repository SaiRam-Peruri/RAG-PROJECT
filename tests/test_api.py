"""Tests for API endpoints."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from rag_project.api.app import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "api_key_set" in data

    def test_health_no_auth_required(self):
        """Health endpoint should work without API key."""
        response = client.get("/health")
        assert response.status_code == 200


class TestAuthMiddleware:
    def test_open_access_when_no_key_set(self):
        """When RAG_API_KEY is empty, all endpoints should be accessible."""
        response = client.get("/opportunities")
        # Should not be 401/403 when api_key is empty
        assert response.status_code in (200, 500)  # 500 if chroma not ready


class TestRequestValidation:
    def test_query_empty_question_rejected(self):
        response = client.post("/query", json={"question": "", "mode": "auth"})
        assert response.status_code == 422  # Validation error

    def test_query_invalid_mode_rejected(self):
        response = client.post("/query", json={"question": "test", "mode": "invalid"})
        assert response.status_code == 422

    def test_generate_missing_fields(self):
        response = client.post("/generate", json={})
        assert response.status_code == 422


class TestRateLimitModel:
    def test_rate_limiter_import(self):
        from rag_project.api.rate_limit import RateLimiter
        rl = RateLimiter(rpm=5)
        assert rl.rpm == 5
