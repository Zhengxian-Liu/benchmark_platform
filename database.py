"""Database configuration."""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm import Session
from typing import Generator

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """Initialize the database."""
    from models import (
        Session, SessionLanguage, SessionText,
        Translation, EvaluationResult, StyleGuide
    )
    logging.info("Creating initial database schema...")
    Base.metadata.create_all(bind=engine)
    logging.info("Database schema created successfully")

def reset_db() -> None:
    """Drop and recreate all tables."""
    from models import (  # Import here to avoid circular imports
        Session, SessionLanguage, SessionText,
        Translation, EvaluationResult, StyleGuide
    )
    logging.info("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    logging.info("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    logging.info("Database reset complete")
