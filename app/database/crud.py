"""Database CRUD operations."""

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Summary, User


def create_summary(
    db: Session,
    request_id: str,
    email_text: str,
    summary: str,
    action_items: str,
    priority: str,
    deadlines: Optional[str] = None,
    tone: Optional[str] = None,
    language: Optional[str] = None,
    processing_time_ms: Optional[int] = None,
    user_id: Optional[int] = None,
) -> Summary:
    """Create a new summary record."""
    db_summary = Summary(
        request_id=request_id,
        email_text=email_text[:500],  # Truncate for preview
        summary=summary,
        action_items=action_items,
        deadlines=deadlines,
        priority=priority,
        tone=tone,
        language=language,
        processing_time_ms=processing_time_ms,
        user_id=user_id,
    )
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    return db_summary


def get_summary_by_request_id(db: Session, request_id: str) -> Optional[Summary]:
    """Get a summary by its request_id."""
    return db.query(Summary).filter(Summary.request_id == request_id).first()


def get_summaries(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    priority: Optional[str] = None,
    sort: str = "newest",
    user_id: Optional[int] = None,
) -> tuple[list[Summary], int]:
    """Get paginated list of summaries."""
    query = db.query(Summary)

    # Filter by user if provided (for Feature H)
    if user_id is not None:
        query = query.filter(Summary.user_id == user_id)

    # Filter by priority if provided
    if priority:
        query = query.filter(Summary.priority == priority)

    # Get total count before pagination
    total = query.count()

    # Apply sorting
    if sort == "oldest":
        query = query.order_by(Summary.created_at.asc())
    else:
        query = query.order_by(Summary.created_at.desc())

    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)

    return query.all(), total


def search_summaries(
    db: Session,
    query_text: str,
    page: int = 1,
    per_page: int = 20,
    user_id: Optional[int] = None,
) -> tuple[list[Summary], int]:
    """Search summaries by keyword in email_text or summary."""
    search_pattern = f"%{query_text}%"
    query = db.query(Summary).filter(
        (Summary.email_text.like(search_pattern)) | (Summary.summary.like(search_pattern))
    )

    # Filter by user if provided
    if user_id is not None:
        query = query.filter(Summary.user_id == user_id)

    # Get total count
    total = query.count()

    # Apply pagination and sorting (newest first)
    query = query.order_by(Summary.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    return query.all(), total


def delete_summary(db: Session, request_id: str, user_id: Optional[int] = None) -> bool:
    """Delete a summary by request_id. Returns True if deleted."""
    query = db.query(Summary).filter(Summary.request_id == request_id)

    # If user_id provided, only delete if the summary belongs to that user
    if user_id is not None:
        query = query.filter(Summary.user_id == user_id)

    deleted = query.delete()
    db.commit()
    return deleted > 0


def create_user(db: Session, email: str, hashed_password: str) -> User:
    """Create a new user account."""
    db_user = User(email=email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


# Analytics queries
def get_total_summaries(db: Session, user_id: Optional[int] = None) -> int:
    """Get total count of summaries."""
    query = db.query(func.count(Summary.id))
    if user_id is not None:
        query = query.filter(Summary.user_id == user_id)
    return query.scalar() or 0


def get_summaries_today(db: Session, user_id: Optional[int] = None) -> int:
    """Get count of summaries created today."""
    today = datetime.utcnow().date()
    query = db.query(func.count(Summary.id)).filter(
        func.date(Summary.created_at) == today
    )
    if user_id is not None:
        query = query.filter(Summary.user_id == user_id)
    return query.scalar() or 0


def get_summaries_this_week(db: Session, user_id: Optional[int] = None) -> int:
    """Get count of summaries created this week."""
    from datetime import timedelta

    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday())
    query = db.query(func.count(Summary.id)).filter(
        func.date(Summary.created_at) >= week_start
    )
    if user_id is not None:
        query = query.filter(Summary.user_id == user_id)
    return query.scalar() or 0


def get_avg_processing_time(db: Session, user_id: Optional[int] = None) -> float:
    """Get average processing time in milliseconds."""
    query = db.query(func.avg(Summary.processing_time_ms)).filter(
        Summary.processing_time_ms.isnot(None)
    )
    if user_id is not None:
        query = query.filter(Summary.user_id == user_id)
    return query.scalar() or 0


def get_priority_breakdown(db: Session, user_id: Optional[int] = None) -> dict:
    """Get breakdown of summaries by priority."""
    query = db.query(
        Summary.priority, func.count(Summary.id)
    ).group_by(Summary.priority)
    if user_id is not None:
        query = query.filter(Summary.user_id == user_id)
    results = query.all()
    return {priority: count for priority, count in results}


def get_tone_breakdown(db: Session, user_id: Optional[int] = None) -> dict:
    """Get breakdown of summaries by tone."""
    query = db.query(
        Summary.tone, func.count(Summary.id)
    ).filter(Summary.tone.isnot(None)).group_by(Summary.tone)
    if user_id is not None:
        query = query.filter(Summary.user_id == user_id)
    results = query.all()
    return {tone: count for tone, count in results if tone}


def get_language_breakdown(db: Session, user_id: Optional[int] = None) -> list:
    """Get list of languages with counts."""
    query = db.query(
        Summary.language, func.count(Summary.id)
    ).filter(Summary.language.isnot(None)).group_by(Summary.language)
    if user_id is not None:
        query = query.filter(Summary.user_id == user_id)
    results = query.all()
    return [{"language": lang, "count": count} for lang, count in results if lang]


def get_daily_counts(
    db: Session, days: int = 14, user_id: Optional[int] = None
) -> list:
    """Get daily summary counts for the last N days."""
    from datetime import timedelta

    today = datetime.utcnow().date()
    start_date = today - timedelta(days=days - 1)

    query = db.query(
        func.date(Summary.created_at).label("date"),
        func.count(Summary.id).label("count")
    ).filter(func.date(Summary.created_at) >= start_date)
    if user_id is not None:
        query = query.filter(Summary.user_id == user_id)
    query = query.group_by(func.date(Summary.created_at)).order_by("date")

    results = query.all()
    return [{"date": str(r.date), "count": r.count} for r in results]