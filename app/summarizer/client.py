"""Groq API client with retry logic."""

import time
from typing import Any

from groq import Groq

from app.config import settings
from app.logger import logger
from app.summarizer.prompt import SYSTEM_PROMPT, build_user_prompt


class SummarizationError(Exception):
    """Raised when Groq API fails after all retries."""


class InvalidInputError(Exception):
    """Raised when email input fails validation."""


class SummaryClient:
    """Client for interacting with Groq API for email summarization."""

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    def summarize_email(self, email_text: str, generate_reply: bool = False) -> str:
        """Call Groq API to summarize an email thread."""
        user_prompt = build_user_prompt(email_text, generate_reply)

        for attempt in range(3):
            try:
                start_time = time.time()

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=800,
                )

                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    f"Groq API call succeeded | model={self.model} | "
                    f"response_time_ms={elapsed_ms} | attempt={attempt + 1}"
                )

                return response.choices[0].message.content

            except Exception as e:
                error_str = str(e)
                logger.warning(f"API error on attempt {attempt + 1}: {e}")

                if "429" in error_str or "rate" in error_str.lower():
                    if attempt < 2:
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)
                    else:
                        raise SummarizationError(f"Rate limit exceeded after 3 attempts: {e}")
                elif "500" in error_str or "502" in error_str or "503" in error_str:
                    if attempt < 2:
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)
                    else:
                        raise SummarizationError(f"Server error after 3 attempts: {e}")
                else:
                    raise SummarizationError(f"API error: {e}")

        raise SummarizationError("Unexpected error in summarization")

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 500,
    ) -> str:
        """Call Groq API for chat-based interactions (Q&A, reply generation)."""
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                logger.info(
                    f"Groq API chat call succeeded | model={self.model} | "
                    f"attempt={attempt + 1}"
                )

                return response.choices[0].message.content

            except Exception as e:
                error_str = str(e)
                logger.warning(f"Chat API error on attempt {attempt + 1}: {e}")

                if "429" in error_str or "rate" in error_str.lower():
                    if attempt < 2:
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)
                    else:
                        raise SummarizationError(f"Rate limit exceeded after 3 attempts: {e}")
                elif "500" in error_str or "502" in error_str or "503" in error_str:
                    if attempt < 2:
                        wait_time = 2 ** attempt
                        time.sleep(wait_time)
                    else:
                        raise SummarizationError(f"Server error after 3 attempts: {e}")
                else:
                    raise SummarizationError(f"API error: {e}")

        raise SummarizationError("Unexpected error in chat")


summary_client = SummaryClient()