"""Bulk email summarization endpoints."""

import asyncio
import csv
import io
import json
import os
import time
import uuid
from email.parser import Parser
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.logger import logger
from app.summarizer.client import SummaryClient, SummarizationError
from app.summarizer.parser import parse_summary

router = APIRouter(prefix="/bulk", tags=["bulk"])

# In-memory job store (expires after 1 hour)
bulk_jobs: dict[str, dict] = {}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_FILES = 50
MAX_EMAIL_LENGTH = 20000
SEMAPHORE_LIMIT = 5


class BulkJobStatus(BaseModel):
    """Status response for bulk job."""

    job_id: str
    status: str
    total: int
    processed: int
    failed: int
    estimated_seconds_remaining: Optional[int] = None


class BulkJobResponse(BaseModel):
    """Response for bulk job creation."""

    job_id: str
    total: int


def parse_email_file(filename: str, content: bytes) -> tuple[str, str]:
    """Parse an email file and extract text content.

    Returns tuple of (filename, email_text)
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".csv":
        # Parse CSV - look for email_text column
        text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            if "email_text" in row:
                return (filename, row["email_text"][:MAX_EMAIL_LENGTH])
        raise ValueError("CSV must contain 'email_text' column")

    elif ext == ".eml":
        # Parse EML file
        msg = Parser().parsebytes(content)
        body = msg.get_body(prefer_type="plain")
        text = body.get_content() if body else ""
        # Also include subject
        if msg["subject"]:
            text = f"Subject: {msg['subject']}\n\n{text}"
        return (filename, text[:MAX_EMAIL_LENGTH])

    else:
        # Plain text file
        return (filename, content.decode("utf-8")[:MAX_EMAIL_LENGTH])


async def process_file(
    filename: str,
    content: bytes,
    client: SummaryClient,
    job_id: str,
    index: int,
) -> dict:
    """Process a single file and return result."""
    try:
        # Parse the file
        fname, email_text = parse_email_file(filename, content)

        if not email_text or len(email_text.strip()) < 10:
            return {
                "filename": filename,
                "email_preview": "",
                "summary": "",
                "action_items": "",
                "deadlines": "",
                "priority": "",
                "tone": "",
                "language": "",
                "processing_time_ms": 0,
                "error": "Empty or invalid email content",
            }

        # Summarize
        start_time = time.time()
        raw_summary = client.summarize_email(email_text, generate_reply=False)
        result = parse_summary(raw_summary)
        processing_time_ms = int((time.time() - start_time) * 1000)

        return {
            "filename": filename,
            "email_preview": email_text[:100],
            "summary": result.summary or "",
            "action_items": ", ".join(result.action_items) if result.action_items else "",
            "deadlines": result.deadlines or "",
            "priority": result.priority or "",
            "tone": result.tone or "",
            "language": result.language or "",
            "processing_time_ms": processing_time_ms,
            "error": "",
        }

    except Exception as e:
        logger.error(f"Error processing file {filename}: {e}")
        return {
            "filename": filename,
            "email_preview": "",
            "summary": "",
            "action_items": "",
            "deadlines": "",
            "priority": "",
            "tone": "",
            "language": "",
            "processing_time_ms": 0,
            "error": str(e),
        }


async def process_bulk_job(
    job_id: str,
    files_data: list[tuple[str, bytes]],
) -> None:
    """Process all files in a bulk job."""
    client = SummaryClient()
    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)

    results = []
    total = len(files_data)

    async def process_with_semaphore(index: int, filename: str, content: bytes):
        async with semaphore:
            result = await process_file(filename, content, client, job_id, index)
            results.append(result)

            # Update job status
            bulk_jobs[job_id]["processed"] = len(results)
            bulk_jobs[job_id]["failed"] = sum(1 for r in results if r["error"])

    # Create tasks
    tasks = [
        process_with_semaphore(i, filename, content)
        for i, (filename, content) in enumerate(files_data)
    ]

    await asyncio.gather(*tasks, return_exceptions=True)

    # Store results
    bulk_jobs[job_id]["results"] = results
    bulk_jobs[job_id]["status"] = "completed"

    # Cleanup old jobs (older than 1 hour)
    current_time = time.time()
    expired = [
        job_id
        for job_id, job in bulk_jobs.items()
        if current_time - job.get("created_at", 0) > 3600
    ]
    for expired_job in expired:
        del bulk_jobs[expired_job]


@router.post("/summarize", response_model=BulkJobResponse)
async def bulk_summarize(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
) -> BulkJobResponse:
    """Upload multiple email files for bulk summarization."""
    # Validate files
    if not files:
        raise HTTPException(
            status_code=422,
            detail="At least one file is required."
        )

    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=422,
            detail=f"Maximum {MAX_FILES} files allowed per request."
        )

    # Read file contents
    files_data = []
    total_size = 0

    for file in files:
        content = await file.read()
        total_size += len(content)

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=422,
                detail=f"File {file.filename} exceeds maximum size of {MAX_FILE_SIZE // 1024 // 1024}MB."
            )

        files_data.append((file.filename, content))

    if total_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=422,
            detail=f"Total upload size exceeds maximum of {MAX_FILE_SIZE // 1024 // 1024}MB."
        )

    # Create job
    job_id = str(uuid.uuid4())
    bulk_jobs[job_id] = {
        "status": "processing",
        "total": len(files_data),
        "processed": 0,
        "failed": 0,
        "results": [],
        "created_at": time.time(),
    }

    # Process in background
    background_tasks.add_task(process_bulk_job, job_id, files_data)

    logger.info(f"Bulk job created | job_id={job_id} | total_files={len(files_data)}")

    return BulkJobResponse(job_id=job_id, total=len(files_data))


@router.get("/status/{job_id}", response_model=BulkJobStatus)
async def get_bulk_status(job_id: str) -> BulkJobStatus:
    """Get the status of a bulk summarization job."""
    if job_id not in bulk_jobs:
        raise HTTPException(
            status_code=404,
            detail="Job not found. It may have expired."
        )

    job = bulk_jobs[job_id]

    # Calculate estimated time remaining
    if job["status"] == "processing" and job["processed"] > 0:
        elapsed = time.time() - job.get("created_at", time.time())
        per_file_time = elapsed / job["processed"]
        remaining = job["total"] - job["processed"]
        estimated_seconds = int(per_file_time * remaining)
    else:
        estimated_seconds = None

    return BulkJobStatus(
        job_id=job_id,
        status=job["status"],
        total=job["total"],
        processed=job["processed"],
        failed=job.get("failed", 0),
        estimated_seconds_remaining=estimated_seconds,
    )


@router.get("/download/{job_id}")
async def download_bulk_results(job_id: str) -> StreamingResponse:
    """Download bulk summarization results as CSV."""
    if job_id not in bulk_jobs:
        raise HTTPException(
            status_code=404,
            detail="Job not found. It may have expired."
        )

    job = bulk_jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail="Job is still processing. Please wait."
        )

    # Create CSV
    output = io.StringIO()
    fieldnames = [
        "filename",
        "email_preview",
        "summary",
        "action_items",
        "deadlines",
        "priority",
        "tone",
        "language",
        "processing_time_ms",
        "error",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for result in job.get("results", []):
        writer.writerow(result)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=bulk_results_{job_id}.csv"
        },
    )