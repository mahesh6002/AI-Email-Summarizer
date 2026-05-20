"""Parser for extracting structured data from LLM output."""

import re
from typing import Literal, Optional

from app.logger import logger
from app.models import SummaryResult


def parse_summary(raw_text: str) -> SummaryResult:
    """Parse the raw LLM output into a structured SummaryResult."""
    summary: str | None = None
    action_items: list[str] = []
    deadlines: str | None = None
    priority: Literal["High", "Medium", "Low"] | None = None
    tone: Optional[str] = None
    language: Optional[str] = None
    generated_reply: str | None = None

    summary_match = re.search(r"SUMMARY:\s*(.+?)(?=\n---|\Z)", raw_text, re.DOTALL | re.IGNORECASE)
    if summary_match:
        summary = summary_match.group(1).strip()

    action_items_match = re.search(
        r"ACTION ITEMS:\s*(.+?)(?=DEADLINES:|\Z)",
        raw_text,
        re.DOTALL | re.IGNORECASE
    )
    if action_items_match:
        action_text = action_items_match.group(1).strip()
        if action_text and action_text.lower() != "none identified":
            items = re.findall(r"-\s*(.+?)(?=\n-|\Z)", action_text, re.DOTALL)
            action_items = [item.strip() for item in items if item.strip()]

    deadlines_match = re.search(r"DEADLINES:\s*(.+?)(?=\nPRIORITY:|\Z)", raw_text, re.DOTALL | re.IGNORECASE)
    if deadlines_match:
        deadlines = deadlines_match.group(1).strip()
        if deadlines.lower() == "not mentioned":
            deadlines = None

    priority_match = re.search(r"PRIORITY:\s*(High|Medium|Low)", raw_text, re.IGNORECASE)
    if priority_match:
        priority = priority_match.group(1).capitalize()

    # Extract tone (Feature E)
    tone_match = re.search(
        r"TONE:\s*(Urgent|Formal|Friendly|Aggressive|Neutral|Apologetic|Demanding)",
        raw_text,
        re.IGNORECASE
    )
    if tone_match:
        tone = tone_match.group(1).capitalize()

    # Extract language (Feature G)
    language_match = re.search(r"LANGUAGE:\s*(.+?)(?=\n---|\Z)", raw_text, re.DOTALL | re.IGNORECASE)
    if language_match:
        language = language_match.group(1).strip()
        if language.lower() == "not detected" or not language:
            language = None

    # Extract generated reply
    reply_match = re.search(r"PROFESSIONAL REPLY:\s*(.+?)(?=\n---|\Z)", raw_text, re.DOTALL | re.IGNORECASE)
    if reply_match:
        generated_reply = reply_match.group(1).strip()
        if generated_reply.lower() == "no reply needed" or not generated_reply:
            generated_reply = None

    if not summary and not action_items and not deadlines and not priority and not generated_reply:
        logger.warning(f"Failed to parse any fields from LLM output. Raw text: {raw_text[:500]}")

    return SummaryResult(
        summary=summary,
        action_items=action_items,
        deadlines=deadlines,
        priority=priority,
        tone=tone,
        language=language,
        generated_reply=generated_reply
    )