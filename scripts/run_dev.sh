#!/bin/bash
set -e
echo "Starting AI Email Summarizer..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload