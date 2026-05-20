"""Database connection and session management."""

import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./summaries.db")

# Create engine based on database type
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if not Path(db_path).is_absolute():
        # Make it relative to the project root
        project_root = Path(__file__).parent.parent.parent
        db_path = project_root / db_path

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    # For other databases (PostgreSQL, MySQL, etc.)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    from app.database.models import Base

    Base.metadata.create_all(bind=engine)