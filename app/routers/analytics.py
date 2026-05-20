"""Analytics endpoints for usage statistics."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.crud import (
    get_avg_processing_time,
    get_daily_counts,
    get_language_breakdown,
    get_priority_breakdown,
    get_summaries_this_week,
    get_summaries_today,
    get_tone_breakdown,
    get_total_summaries,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


class LanguageCount(BaseModel):
    """Language count model."""

    language: str
    count: int


class DailyCount(BaseModel):
    """Daily count model."""

    date: str
    count: int


class AnalyticsResponse(BaseModel):
    """Analytics summary response."""

    total_summaries: int
    summaries_today: int
    summaries_this_week: int
    avg_processing_time_ms: float
    priority_breakdown: dict
    tone_breakdown: dict
    top_languages: list[LanguageCount]
    daily_counts: list[DailyCount]


@router.get("/summary", response_model=AnalyticsResponse)
def get_analytics_summary(
    db: Session = Depends(get_db),
) -> AnalyticsResponse:
    """Get analytics summary with all usage statistics."""
    total = get_total_summaries(db)
    today = get_summaries_today(db)
    this_week = get_summaries_this_week(db)
    avg_time = get_avg_processing_time(db)
    priority = get_priority_breakdown(db)
    tone = get_tone_breakdown(db)
    languages = get_language_breakdown(db)
    daily = get_daily_counts(db, days=14)

    return AnalyticsResponse(
        total_summaries=total,
        summaries_today=today,
        summaries_this_week=this_week,
        avg_processing_time_ms=round(avg_time, 2) if avg_time else 0,
        priority_breakdown=priority,
        tone_breakdown=tone,
        top_languages=[LanguageCount(language=lang["language"], count=lang["count"]) for lang in languages],
        daily_counts=[DailyCount(date=d["date"], count=d["count"]) for d in daily],
    )