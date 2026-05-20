"""Database module for AI Email Summarizer."""

from app.database.connection import engine, get_db
from app.database.models import Base, Summary, User
from app.database.crud import (
    create_summary,
    get_summary_by_request_id,
    get_summaries,
    search_summaries,
    delete_summary,
    create_user,
    get_user_by_email,
    get_user_by_id,
)

__all__ = [
    "engine",
    "get_db",
    "Base",
    "Summary",
    "User",
    "create_summary",
    "get_summary_by_request_id",
    "get_summaries",
    "search_summaries",
    "delete_summary",
    "create_user",
    "get_user_by_email",
    "get_user_by_id",
]