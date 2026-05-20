"""Unit tests for the summarizer client."""

import pytest
from unittest.mock import patch, MagicMock

from app.summarizer.client import SummaryClient, SummarizationError


class TestSummarizer:
    """Tests for the summarizer client."""

    @patch("app.summarizer.client.genai")
    def test_summarize_email_success(self, mock_genai):
        """Test successful email summarization."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "SUMMARY: Test summary\nACTION ITEMS:\n- Test action\nDEADLINES: Not mentioned\nPRIORITY: Low"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.configure.return_value = None

        client = SummaryClient()
        result = client.summarize_email("Test email text")

        assert "SUMMARY" in result or "Test summary" in result