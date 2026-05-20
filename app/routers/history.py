"""History API endpoints for summary management."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.crud import (
    delete_summary,
    get_summary_by_request_id,
    get_summaries,
    search_summaries,
)

router = APIRouter(prefix="/history", tags=["history"])


class SummaryItem(BaseModel):
    """Summary item response model."""

    request_id: str
    email_preview: str
    summary: str
    priority: str
    created_at: str
    processing_time_ms: Optional[int] = None


class HistoryResponse(BaseModel):
    """Paginated history response."""

    items: list[SummaryItem]
    total: int
    page: int
    per_page: int


@router.get("", response_model=HistoryResponse)
def list_history(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    sort: str = Query("newest", description="Sort by newest or oldest"),
    db: Session = Depends(get_db),
) -> HistoryResponse:
    """List all summaries with pagination."""
    summaries, total = get_summaries(
        db=db,
        page=page,
        per_page=per_page,
        priority=priority,
        sort=sort,
    )

    items = [
        SummaryItem(
            request_id=s.request_id,
            email_preview=s.email_text[:100],
            summary=s.summary,
            priority=s.priority,
            created_at=s.created_at.isoformat(),
            processing_time_ms=s.processing_time_ms,
        )
        for s in summaries
    ]

    return HistoryResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{request_id}", response_model=SummaryItem)
def get_history_item(
    request_id: str,
    db: Session = Depends(get_db),
) -> SummaryItem:
    """Get a single summary by request_id."""
    summary = get_summary_by_request_id(db, request_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    return SummaryItem(
        request_id=summary.request_id,
        email_preview=summary.email_text[:100],
        summary=summary.summary,
        priority=summary.priority,
        created_at=summary.created_at.isoformat(),
        processing_time_ms=summary.processing_time_ms,
    )


@router.delete("/{request_id}")
def delete_history_item(
    request_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Delete a summary by request_id."""
    deleted = delete_summary(db, request_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Summary not found")

    return {"message": "Summary deleted successfully"}


@router.get("/search", response_model=HistoryResponse)
def search_history(
    q: str = Query(..., description="Search keyword"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> HistoryResponse:
    """Search summaries by keyword."""
    summaries, total = search_summaries(
        db=db,
        query_text=q,
        page=page,
        per_page=per_page,
    )

    items = [
        SummaryItem(
            request_id=s.request_id,
            email_preview=s.email_text[:100],
            summary=s.summary,
            priority=s.priority,
            created_at=s.created_at.isoformat(),
            processing_time_ms=s.processing_time_ms,
        )
        for s in summaries
    ]

    return HistoryResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
    )