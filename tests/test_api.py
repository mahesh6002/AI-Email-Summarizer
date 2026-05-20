"""Integration tests for the API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestAPI:
    """Tests for FastAPI endpoints."""

    def test_health_check(self):
        """Test GET /health returns ok status."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert "model" in response.json()

    @pytest.mark.parametrize("email_text,expected_status", [
        ("", 422),
        ("short", 422),
        ("a" * 20001, 422),
    ])
    def test_summarize_invalid_input(self, email_text, expected_status):
        """Test POST /summarize with invalid input."""
        response = client.post(
            "/summarize",
            json={"email_text": email_text, "source": "manual"}
        )

        assert response.status_code == expected_status

    def test_summarize_valid_input(self):
        """Test POST /summarize with valid input returns structured JSON."""
        valid_email = "Please review the attached document and provide feedback by Friday. This is urgent."

        response = client.post(
            "/summarize",
            json={"email_text": valid_email, "source": "manual"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "action_items" in data
        assert "deadlines" in data
        assert "priority" in data
        assert "processing_time_ms" in data