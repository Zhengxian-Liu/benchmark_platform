"""Global test fixtures."""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal, reset_db
from models import (
    Session as DbSession,
    SessionText,
    SessionLanguage,
    Translation,
    EvaluationResult,
    StyleGuide
)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Reset database before test session."""
    reset_db()

@pytest.fixture
def db_session() -> Session:
    """Get a database session for testing."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def sample_style_guide(db_session):
    """Create a sample style guide."""
    guide = StyleGuide(
        project_name="原神",
        language_code="EN",
        content="Test style guide content",
        version=1,
        guide_metadata={"rules": ["rule1", "rule2"]},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db_session.add(guide)
    db_session.commit()
    return guide
