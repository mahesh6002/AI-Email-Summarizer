"""Summarize endpoint for email processing."""

import json
import time
import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.config import settings
from app.database.connection import get_db
from app.database.crud import create_summary
from app.email_sources.manual import ManualSource
from app.logger import logger
from app.models import SummarizeRequest, SummarizeResponse
from app.summarizer.client import summary_client, SummarizationError
from app.summarizer.parser import parse_summary

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


def save_summary_to_db(
    db: Session,
    request_id: str,
    email_text: str,
    summary: str,
    action_items: list[str],
    deadlines: Optional[str],
    priority: str,
    processing_time_ms: int,
    tone: Optional[str] = None,
    language: Optional[str] = None,
) -> None:
    """Background task to save summary to database."""
    try:
        create_summary(
            db=db,
            request_id=request_id,
            email_text=email_text,
            summary=summary,
            action_items=json.dumps(action_items),
            deadlines=deadlines,
            priority=priority,
            tone=tone,
            language=language,
            processing_time_ms=processing_time_ms,
        )
        logger.info(f"Summary saved to database | request_id={request_id}")
    except Exception as e:
        logger.error(f"Failed to save summary to database | request_id={request_id} | error={e}")


@router.post("/summarize", response_model=SummarizeResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def summarize_email(
    request: Request,
    summarize_req: SummarizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Summarize an email thread and extract key information."""
    request_id = str(uuid.uuid4())

    if len(summarize_req.email_text) > 20000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email text exceeds maximum allowed length of 20,000 characters."
        )

    logger.info(
        f"Request received | request_id={request_id} | "
        f"source={summarize_req.source} | text_length={len(summarize_req.email_text)} | generate_reply={summarize_req.generate_reply}"
    )

    try:
        start_time = time.time()

        source = ManualSource()
        email_text = source.get_email_text(email_text=summarize_req.email_text)

        raw_summary = summary_client.summarize_email(email_text, summarize_req.generate_reply)
        parsed_result = parse_summary(raw_summary)

        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Request completed | request_id={request_id} | "
            f"processing_time_ms={processing_time_ms}"
        )

        # Save to database in background
        background_tasks.add_task(
            save_summary_to_db,
            db=db,
            request_id=request_id,
            email_text=summarize_req.email_text,
            summary=parsed_result.summary,
            action_items=parsed_result.action_items,
            deadlines=parsed_result.deadlines,
            priority=parsed_result.priority,
            processing_time_ms=processing_time_ms,
            tone=parsed_result.tone,
            language=parsed_result.language,
        )

        return SummarizeResponse(
            request_id=request_id,
            summary=parsed_result.summary,
            action_items=parsed_result.action_items,
            deadlines=parsed_result.deadlines,
            priority=parsed_result.priority,
            tone=parsed_result.tone,
            language=parsed_result.language,
            generated_reply=parsed_result.generated_reply,
            processing_time_ms=processing_time_ms
        )

    except SummarizationError as e:
        logger.error(f"Summarization failed | request_id={request_id} | error={e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Groq API is currently unavailable. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error | request_id={request_id} | error={e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )