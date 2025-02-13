"""Fixtures for prompt tests."""

import pytest
from models import Prompt

@pytest.fixture(autouse=True)
def cleanup_prompts(db_session):
    """Clean up all prompts before and after each test."""
    db_session.query(Prompt).delete()
    db_session.commit()
    yield
    db_session.query(Prompt).delete()
    db_session.commit()
