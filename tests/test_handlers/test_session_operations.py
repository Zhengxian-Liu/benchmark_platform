"""Tests for session operations in handlers."""

import pytest
import pandas as pd
import tempfile
import os

from handlers.session.crud import (
    get_session_texts,
    update_session_status,
    update_session_data,
    get_session_progress
)
from handlers.session.file_processing import (
    process_excel_file,
    create_session_texts
)
from models import Translation, SessionLanguage

def test_process_excel_file(db_session):
    """Test Excel file processing with various column formats."""
    # Create DataFrame with test data
    data = {
        'Text ID': ['1', '2'],
        'Source Text': ['Hello', 'World'],
        'Extra Info': ['context1', 'context2'],
        'EN': ['Hello', 'World'],
        'ES': ['Hola', 'Mundo']
    }
    df = pd.DataFrame(data)
    print(f"Created DataFrame columns: {df.columns.tolist()}")
    
    fd, file_path = tempfile.mkstemp(suffix='.xlsx')
    os.close(fd)
    
    try:
        df.to_excel(file_path, index=False)
        success, message, language_codes, mappings = process_excel_file(db_session, file_path)
        print(f"File processing results: success={success}, message={message}, mappings={mappings}")
        
        assert success, f"Failed to process Excel file: {message}"
        assert set(mappings.keys()) >= {'textid', 'source', 'extra'}
        assert 'source' in mappings, "Should detect a source column"
        assert 'textid' in mappings, "Should detect a text ID column"
        assert 'extra' in mappings, "Should detect an extra column"
        assert set(language_codes) >= {'EN', 'ES'}
    finally:
        os.remove(file_path)

def test_process_excel_file_missing_columns(db_session):
    """Test Excel processing with missing required columns."""
    df = pd.DataFrame({
        'Some Column': ['data1'],
        'Another Column': ['data2']
    })
    fd, file_path = tempfile.mkstemp(suffix='.xlsx')
    os.close(fd)
    
    try:
        df.to_excel(file_path, index=False)
        success, message, _, _ = process_excel_file(db_session, file_path)
        assert not success
        assert "Could not detect Source column" in message
    finally:
        os.remove(file_path)

def test_create_session_texts(db_session, sample_session):
    """Test creation of session texts from Excel file."""
    # Setup session data with required column mappings
    if not sample_session.data:
        sample_session.data = {}
    
    sample_session.data["column_mappings"] = {
        "source": "Source Text",
        "textid": "Text ID",
        "extra": "Extra Info"
    }
    db_session.commit()
    
    # Create test data with explicit list values
    data = {
        'Text ID': ['1', '2'],
        'Source Text': ['Hello', 'World'],
        'Extra Info': ['context1', 'context2'],
        'EN': ['Hello', 'World'],
        'ES': ['Hola', 'Mundo']
    }
    df = pd.DataFrame(data)
    fd, file_path = tempfile.mkstemp(suffix='.xlsx')
    os.close(fd)
    
    try:
        df.to_excel(file_path, index=False)
        success, message = create_session_texts(
            db_session,
            sample_session.id,
            file_path,
            ['EN', 'ES']
        )
        assert success, f"Failed to create session texts: {message}"
        
        # Verify texts were created
        texts = get_session_texts(db_session, sample_session.id)
        assert len(texts) == 2
        assert texts[0].text_id == '1'
        assert texts[0].source_text == 'Hello'
        assert texts[0].extra_data == 'context1'
        assert texts[0].ground_truth == {'EN': 'Hello', 'ES': 'Hola'}
    finally:
        os.remove(file_path)

def test_session_text_pagination(db_session, sample_session):
    """Test pagination of session texts."""
    # Setup session data with required column mappings
    if not sample_session.data:
        sample_session.data = {}
    
    sample_session.data["column_mappings"] = {
        "source": "Source Text",
        "textid": "Text ID",
        "extra": "Extra Info"
    }
    db_session.commit()
    
    # Create test data with list comprehensions
    data = {
        'Text ID': [f'id{i}' for i in range(5)],
        'Source Text': [f'text{i}' for i in range(5)],
        'EN': [f'text{i}' for i in range(5)]
    }
    df = pd.DataFrame(data)
    fd, file_path = tempfile.mkstemp(suffix='.xlsx')
    os.close(fd)
    
    try:
        df.to_excel(file_path, index=False)
        success, message = create_session_texts(
            db_session,
            sample_session.id,
            file_path,
            ['EN']
        )
        assert success, f"Failed to create session texts: {message}"
        
        # Test pagination
        texts = get_session_texts(db_session, sample_session.id, offset=2, limit=2)
        print(f"Retrieved {len(texts)} texts: {[text.text_id for text in texts]}")
        assert len(texts) == 2, f"Expected 2 texts, got {len(texts)}"
        assert texts[0].text_id == 'id2'
        assert texts[1].text_id == 'id3'
    finally:
        os.remove(file_path)

def test_update_session_status(db_session, sample_session):
    """Test updating session status."""
    assert update_session_status(db_session, sample_session.id, "completed")
    session = db_session.get(sample_session.__class__, sample_session.id)
    assert session.status == "completed"

def test_update_session_data(db_session, sample_session):
    """Test updating session data dictionary."""
    # Initialize data if needed
    if not sample_session.data:
        sample_session.data = {}
        db_session.commit()
    
    print(f"Initial session data: {sample_session.data}")
    
    # Prepare update data
    update_data = {
        "new_field": "new_value",
        "selected_languages": ["FR", "DE"]
    }
    
    success = update_session_data(db_session, sample_session.id, update_data)
    assert success, "Failed to update session data"
    
    db_session.refresh(sample_session)
    print(f"Session data after update: {sample_session.data}")
    
    assert "new_field" in sample_session.data, f"Expected new_field in {sample_session.data}"
    assert sample_session.data["new_field"] == "new_value"
    assert set(sample_session.data.get("selected_languages", [])) >= {"FR", "DE"}

def test_get_session_progress(db_session, sample_session, sample_texts):
    """Test getting session progress with translations and evaluations."""
    # Create a session language entry
    session_lang = SessionLanguage(
        session_id=sample_session.id,
        language_code="EN",
        prompts={"prompt_id": 1, "version": 1}
    )
    db_session.add(session_lang)
    db_session.commit()
    
    # Create a translation for the first text
    translation = Translation(
        session_text_id=sample_texts[0].id,
        session_language_id=session_lang.id,
        translated_text="Test translation",
        metrics={"score": 0.9}
    )
    db_session.add(translation)
    db_session.commit()
    
    progress = get_session_progress(db_session, sample_session.id)
    assert progress["total"] == len(sample_texts)
    assert progress["translated"] >= 1
    assert progress["evaluated"] == 0  # No evaluations yet

def test_invalid_session_operations(db_session):
    """Test operations with invalid session ID."""
    invalid_id = 999
    
    assert not update_session_status(db_session, invalid_id, "completed")
    assert not update_session_data(db_session, invalid_id, {"test": "data"})
    assert get_session_progress(db_session, invalid_id) == {}
