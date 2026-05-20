"""Unit tests for the output parser."""

import pytest
from app.summarizer.parser import parse_summary
from app.models import SummaryResult


class TestParser:
    """Tests for parse_summary function."""

    def test_parse_valid_output(self):
        """Test parser with well-formed LLM output."""
        raw_output = """---
SUMMARY: The project team is requesting approval for the Q2 budget allocation and discussing the upcoming product launch timeline.
ACTION ITEMS:
- Review the budget proposal
- Schedule a meeting with finance team
- Approve the launch date
DEADLINES: March 15, 2024
PRIORITY: High
---"""

        result = parse_summary(raw_output)

        assert result.summary is not None
        assert "budget" in result.summary.lower() or "project team" in result.summary.lower()
        assert len(result.action_items) >= 2
        assert result.deadlines is not None
        assert result.priority == "High"

    def test_parse_missing_summary(self):
        """Test parser with missing SUMMARY field."""
        raw_output = """---
ACTION ITEMS:
- Complete the report
DEADLINES: Not mentioned
PRIORITY: Medium
---"""

        result = parse_summary(raw_output)

        assert result.summary is None
        assert "Complete the report" in result.action_items
        assert result.priority == "Medium"

    def test_parse_missing_action_items(self):
        """Test parser with missing ACTION ITEMS."""
        raw_output = """---
SUMMARY: This is a test email.
DEADLINES: Not mentioned
PRIORITY: Low
---"""

        result = parse_summary(raw_output)

        assert result.summary is not None
        assert result.action_items == []
        assert result.priority == "Low"

    def test_parse_invalid_priority(self):
        """Test parser with invalid PRIORITY value."""
        raw_output = """---
SUMMARY: Test summary
ACTION ITEMS:
- None identified
DEADLINES: Not mentioned
PRIORITY: Urgent
---"""

        result = parse_summary(raw_output)

        assert result.priority is None

    def test_parse_empty_output(self):
        """Test parser with completely empty output."""
        raw_output = ""

        result = parse_summary(raw_output)

        assert result.summary is None
        assert result.action_items == []
        assert result.deadlines is None
        assert result.priority is None