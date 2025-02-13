"""Tests for session management handlers."""

import pytest
from datetime import datetime, UTC

from models import Session as DbSession, SessionText
from handlers.session.crud import create_session

def test_create_session(db_session, sample_project):
    """Test session creation with basic data."""
    session_data = {
        "selected_languages": ["EN", "ES"],
        "source_file": {
            "name": "test.xlsx",
            "path": "/test/path.xlsx"
        },
        "column_mappings": {
            "source": "Source",
            "textid": "ID"
        }
    }
    
    session = create_session(
        db=db_session,
        project_name=sample_project,
        source_file_name="test.xlsx",
        source_file_path="/test/path.xlsx",
        selected_languages=["EN", "ES"],
        column_mappings=session_data["column_mappings"]
    )
    
    assert session.id is not None
    assert session.project_name == sample_project
    assert session.status == "in_progress"
    assert len(session.data["selected_languages"]) == 2

def test_session_text_creation(db_session, sample_session):
    """Test creation of session texts."""
    text = SessionText(
        session_id=sample_session.id,
        text_id="test_1",
        source_text="Hello world",
        extra_data="Test context",
        ground_truth={
            "EN": "Hello world",
            "ES": "Hola mundo"
        }
    )
    
    db_session.add(text)
    db_session.commit()
    
    fetched_text = (
        db_session.query(SessionText)
        .filter(SessionText.session_id == sample_session.id)
        .first()
    )
    
    assert fetched_text is not None
    assert fetched_text.text_id == "test_1"
    assert fetched_text.source_text == "Hello world"
    assert "EN" in fetched_text.ground_truth
    assert fetched_text.ground_truth["ES"] == "Hola mundo"

def test_session_relationships(db_session, sample_texts):
    """Test relationships between session and texts."""
    session = sample_texts[0].session
    
    assert session is not None
    assert len(session.texts) == 3
    assert all(isinstance(text, SessionText) for text in session.texts)
    
    # Verify text content
    first_text = session.texts[0]
    assert first_text.text_id == "text_0"
    assert first_text.source_text == "Sample source text 0"
    assert first_text.ground_truth["EN"] == "Sample English text 0"

def test_session_data_structure(db_session, sample_session):
    """Test the structure and content of session data."""
    assert "selected_languages" in sample_session.data
    assert "source_file" in sample_session.data
    assert "column_mappings" in sample_session.data
    
    # Verify language selection
    assert isinstance(sample_session.data["selected_languages"], list)
    assert "EN" in sample_session.data["selected_languages"]
    
    # Verify column mappings
    mappings = sample_session.data["column_mappings"]
    assert "source" in mappings
    assert "textid" in mappings
    assert mappings["source"] == "Source Text"
