"""Configuration management - loads and validates environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        load_dotenv()

        # Groq API
        self.GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
        self.GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

        # Gmail (optional)
        self.USE_GMAIL_API: bool = os.getenv("USE_GMAIL_API", "false").lower() == "true"
        self.GOOGLE_CREDENTIALS_PATH: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")

        # Server
        self.API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT: int = int(os.getenv("API_PORT", "8000"))

        # Logging
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

        # Database
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./summaries.db")

        # JWT Auth
        self.JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
        self.JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
        self.JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

        # Rate Limiting
        self.RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))

    def validate(self) -> None:
        """Validate required settings. Raises error if critical settings are missing."""
        if not self.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required. Please set it in the .env file.")


settings = Settings()
settings.validate()