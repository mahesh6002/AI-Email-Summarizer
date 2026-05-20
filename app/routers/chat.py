"""Chat and reply generation endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database.connection import get_db
from app.database.crud import get_summary_by_request_id
from app.logger import logger

router = APIRouter(tags=["chat"])


class ChatMessage(BaseModel):
    """Chat message model."""

    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    request_id: str = Field(..., description="UUID of the summary to ask about")
    question: str = Field(..., min_length=1, max_length=500)
    conversation_history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    answer: str
    request_id: str


class DraftReplyRequest(BaseModel):
    """Request model for draft reply endpoint."""

    request_id: str = Field(..., description="UUID of the summary to reply to")
    reply_tone: str = Field(default="professional", description="Tone: professional, casual, brief, detailed")
    instructions: str = Field(default="", description="Additional instructions for the reply")


class DraftReplyResponse(BaseModel):
    """Response model for draft reply endpoint."""

    draft: str
    word_count: int


def build_chat_prompt(
    email_text: str,
    question: str,
    conversation_history: list[dict],
) -> tuple[str, list[dict]]:
    """Build the prompt for the chat endpoint."""
    system_prompt = f"""You are a helpful assistant answering questions about the following email.
Only answer based on the email content. If the answer is not in the email, say so clearly.

Email Content:
```
{email_text}
```

Rules:
- Only answer based on information explicitly stated in the email
- If the information is not in the email, say "This information is not mentioned in the email."
- Be concise and direct"""

    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history (limit to last 10 turns)
    for msg in conversation_history[-10:]:
        messages.append({"role": msg.role, "content": msg.content})

    # Add current question
    messages.append({"role": "user", "content": question})

    return system_prompt, messages


def build_reply_prompt(
    summary: str,
    action_items: list[str],
    reply_tone: str,
    instructions: str,
) -> str:
    """Build the prompt for draft reply generation."""
    return f"""You are a professional email writer.
Given the following email summary and action items, write a reply email.

Summary: {summary}
Action Items: {", ".join(action_items)}
Tone: {reply_tone}
Additional instructions: {instructions}

Rules:
- Write ONLY the email body (no subject line)
- Match the requested tone exactly
- Reference the specific action items from the summary
- Keep it under 150 words unless tone is "detailed"
- Do NOT add information that is not in the summary"""


@router.post("/chat", response_model=ChatResponse)
async def chat_question(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Ask a follow-up question about a summarized email."""
    # Get the original email from the database
    summary = get_summary_by_request_id(db, request.request_id)
    if not summary:
        raise HTTPException(
            status_code=404,
            detail="Summary not found. Please provide a valid request_id."
        )

    logger.info(
        f"Chat request | request_id={request.request_id} | "
        f"question_length={len(request.question)}"
    )

    try:
        # Import here to avoid circular imports
        from app.summarizer.client import summary_client

        # Build the conversation
        _, messages = build_chat_prompt(
            email_text=summary.email_text,
            question=request.question,
            conversation_history=[
                {"role": msg.role, "content": msg.content}
                for msg in request.conversation_history
            ],
        )

        # Call the LLM
        answer = summary_client.chat(
            messages=messages,
            temperature=0.3,
            max_tokens=500,
        )

        return ChatResponse(
            answer=answer,
            request_id=request.request_id,
        )

    except Exception as e:
        logger.error(f"Chat error | request_id={request.request_id} | error={e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate response. Please try again."
        )


@router.post("/reply/draft", response_model=DraftReplyResponse)
async def draft_reply(
    request: DraftReplyRequest,
    db: Session = Depends(get_db),
) -> DraftReplyResponse:
    """Generate a professional reply to an email based on its summary."""
    # Get the summary from the database
    summary = get_summary_by_request_id(db, request.request_id)
    if not summary:
        raise HTTPException(
            status_code=404,
            detail="Summary not found. Please provide a valid request_id."
        )

    # Validate tone
    valid_tones = ["professional", "casual", "brief", "detailed"]
    if request.reply_tone not in valid_tones:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid reply_tone. Must be one of: {', '.join(valid_tones)}"
        )

    logger.info(
        f"Draft reply request | request_id={request.request_id} | "
        f"tone={request.reply_tone}"
    )

    try:
        import json

        from app.summarizer.client import summary_client

        # Parse action items from JSON string
        action_items = json.loads(summary.action_items) if summary.action_items else []

        # Build the prompt
        prompt = build_reply_prompt(
            summary=summary.summary,
            action_items=action_items,
            reply_tone=request.reply_tone,
            instructions=request.instructions,
        )

        # Call the LLM
        draft = summary_client.chat(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Please write the reply email."},
            ],
            temperature=0.3,
            max_tokens=500,
        )

        word_count = len(draft.split())

        return DraftReplyResponse(
            draft=draft,
            word_count=word_count,
        )

    except Exception as e:
        logger.error(f"Draft reply error | request_id={request.request_id} | error={e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate draft reply. Please try again."
        )