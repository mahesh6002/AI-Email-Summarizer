"""Pydantic request/response models."""

from typing import Optional

from pydantic import BaseModel, Field
from typing import Literal


class SummarizeRequest(BaseModel):
    """Request model for email summarization."""
    email_text: str = Field(..., min_length=10, max_length=20000)
    source: str = "manual"
    generate_reply: bool = Field(default=False, description="Whether to generate a professional reply")


class SummaryResult(BaseModel):
    """Structured summary result from LLM parsing."""
    summary: str | None
    action_items: list[str]
    deadlines: str | None
    priority: Literal["High", "Medium", "Low"] | None
    tone: Optional[str] = Field(default=None, description="Detected email tone (Urgent, Formal, Friendly, etc.)")
    language: Optional[str] = Field(default=None, description="Detected email language")
    generated_reply: str | None = Field(default=None, description="AI-generated professional reply to the email")


class SummarizeResponse(SummaryResult):
    """Response model for the /summarize endpoint."""
    request_id: str = Field(..., description="Unique request ID for this summarization")
    processing_time_ms: int