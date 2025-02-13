"""Test fixtures for translation handlers."""

import pytest
from unittest.mock import patch
from models import SessionText, SessionLanguage, Translation

@pytest.fixture
def mock_translate():
    """Mock the translate_text function."""
    with patch('handlers.translation.operations.translate_text') as mock:
        mock.return_value = {
            "translated_text": "Mocked translation",
            "model": "test-model-v1"
        }
        yield mock

@pytest.fixture
def sample_session_text(db_session, sample_session):
    """Create a sample session text."""
    text = SessionText(
        session_id=sample_session.id,
        text_id="test_1",
        source_text="Hello world",
        extra_data="Test context"
    )
    db_session.add(text)
    db_session.commit()
    return text

@pytest.fixture
def sample_session_language(db_session, sample_session):
    """Create a sample session language."""
    lang = SessionLanguage(
        session_id=sample_session.id,
        language_code="ES",
        prompts={"prompt_id": 1, "version": 1}
    )
    db_session.add(lang)
    db_session.commit()
    return lang

@pytest.fixture
def sample_translation(db_session, sample_session_text, sample_session_language):
    """Create a sample translation."""
    translation = Translation(
        session_text_id=sample_session_text.id,
        session_language_id=sample_session_language.id,
        translated_text="¡Hola mundo!",
        metrics={"model": "test-model-v1"}
    )
    db_session.add(translation)
    db_session.commit()
    return translation

@pytest.fixture(autouse=True)
def cleanup_translations(db_session):
    """Clean up translations before and after each test."""
    db_session.query(Translation).delete()
    db_session.commit()
    yield
    db_session.query(Translation).delete()
    db_session.commit()
