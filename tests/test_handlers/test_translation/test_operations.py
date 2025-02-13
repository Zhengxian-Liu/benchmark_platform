"""Tests for translation operations."""

import pytest
from datetime import datetime, timedelta

from handlers.translation.operations import (
    create_translation,
    get_translations,
    delete_translation
)

def test_create_translation(
    db_session,
    sample_session_text,
    sample_session_language,
    mock_translate
):
    """Test creating a new translation."""
    translation = create_translation(
        db=db_session,
        session_text_id=sample_session_text.id,
        session_language_id=sample_session_language.id,
        prompt_text="Translate: Hello world",
        source_language="EN",
        target_language="ES"
    )
    
    assert translation.translated_text == "Mocked translation"
    assert translation.metrics["model"] == "test-model-v1"
    assert translation.session_text_id == sample_session_text.id
    assert translation.session_language_id == sample_session_language.id
    
    # Verify mock was called correctly
    mock_translate.assert_called_once_with(
        prompt_text="Translate: Hello world",
        source_language="EN",
        target_language="ES"
    )

def test_create_translation_invalid_ids(db_session, mock_translate):
    """Test creating translation with invalid session text or language IDs."""
    with pytest.raises(ValueError) as exc:
        create_translation(
            db=db_session,
            session_text_id=999,
            session_language_id=999,
            prompt_text="Test",
            source_language="EN",
            target_language="ES"
        )
    assert "No session text found" in str(exc.value)
    
    # Mock wasn't called because validation failed
    mock_translate.assert_not_called()

def test_get_translations(
    db_session,
    sample_session_text,
    sample_session_language
):
    """Test retrieving translations."""
    # Create multiple translations
    translations = []
    for i in range(3):
        translation = create_translation(
            db=db_session,
            session_text_id=sample_session_text.id,
            session_language_id=sample_session_language.id,
            prompt_text=f"Test {i}",
            source_language="EN",
            target_language="ES"
        )
        translations.append(translation)
    
    # Get all translations for the text
    results = get_translations(
        db_session,
        sample_session_text.id
    )
    assert len(results) == 3
    
    # Get translations for specific language
    results = get_translations(
        db_session,
        sample_session_text.id,
        sample_session_language.id
    )
    assert len(results) == 3
    assert all(t.session_language_id == sample_session_language.id for t in results)

def test_delete_translation(
    db_session,
    sample_translation
):
    """Test deleting a translation."""
    assert delete_translation(db_session, sample_translation.id)
    
    # Verify translation was deleted
    assert get_translations(db_session, sample_translation.session_text_id) == []
    
    # Try deleting non-existent translation
    assert not delete_translation(db_session, 999)

def test_translations_ordered_by_date(
    db_session,
    sample_session_text,
    sample_session_language,
    mock_translate
):
    """Test that translations are returned in correct order."""
    # Create translations with different timestamps
    for i in range(3):
        translation = create_translation(
            db=db_session,
            session_text_id=sample_session_text.id,
            session_language_id=sample_session_language.id,
            prompt_text=f"Test {i}",
            source_language="EN",
            target_language="ES"
        )
    
    results = get_translations(db_session, sample_session_text.id)
    
    # Verify descending order
    for i in range(len(results) - 1):
        assert results[i].created_at >= results[i + 1].created_at
