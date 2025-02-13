"""Test fixtures for project module."""

from datetime import datetime
import pytest
from sqlalchemy.orm import Session

from database import SessionLocal, reset_db
from models import Session as DbSession, SessionLanguage, Translation, EvaluationResult, SessionText
from handlers.project.config import PROJECT_CONFIG

@pytest.fixture(autouse=True)
def setup_db():
    """Reset database before all tests."""
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
def sample_project():
    """Get a sample project name."""
    return list(PROJECT_CONFIG.keys())[0]  # Get first project, e.g., "原神"

@pytest.fixture
def sample_language(sample_project):
    """Get a sample language code for project."""
    return PROJECT_CONFIG[sample_project][0]  # Get first language

@pytest.fixture
def project_session(db_session, sample_project, sample_language):
    """Create a sample project session."""
    session = DbSession(
        project_name=sample_project,
        source_file_name="test.xlsx",
        source_file_path="/path/to/test.xlsx",
        status="in_progress",
        created_at=datetime.now(),
        data={
            "selected_languages": [sample_language],
            "source_file": {
                "name": "test.xlsx",
                "path": "/path/to/test.xlsx"
            }
        }
    )
    db_session.add(session)
    db_session.commit()
    
    # Add session language
    lang = SessionLanguage(
        session_id=session.id,
        language_code=sample_language,
        prompts={"prompt_id": 1, "version": 1}
    )
    db_session.add(lang)
    db_session.commit()
    
    # Add session text
    text = SessionText(
        session_id=session.id,
        text_id="test_text",
        source_text="Test source text",
        extra_data={"key": "value"}
    )
    db_session.add(text)
    db_session.commit()
    
    return session

@pytest.fixture
def project_sessions(db_session, sample_project):
    """Create multiple sessions with different statuses."""
    sessions = []
    statuses = ["in_progress", "completed", "completed", "archived"]
    languages = PROJECT_CONFIG[sample_project][:2]  # Use first two languages
    
    for status in statuses:
        session = DbSession(
            project_name=sample_project,
            source_file_name=f"test_{status}.xlsx",
            source_file_path=f"/path/to/test_{status}.xlsx",
            status=status,
            created_at=datetime.now(),
            data={
                "selected_languages": languages,
                "source_file": {
                    "name": f"test_{status}.xlsx",
                    "path": f"/path/to/test_{status}.xlsx"
                }
            }
        )
        db_session.add(session)
        db_session.flush()  # Get session.id
        
        # Add languages to session
        for lang_code in languages:
            lang = SessionLanguage(
                session_id=session.id,
                language_code=lang_code,
                prompts={"prompt_id": 1, "version": 1}
            )
            db_session.add(lang)
            
        # Add a test text for each session
        text = SessionText(
            session_id=session.id,
            text_id=f"text_{status}",
            source_text=f"Source text for {status}",
            extra_data={"type": status}
        )
        db_session.add(text)
        
        sessions.append(session)
    
    db_session.commit()
    return sessions

@pytest.fixture
def project_translations(db_session, project_session):
    """Create sample translations for project session."""
    translations = []
    
    # Get session text
    session_text = db_session.query(SessionText)\
        .filter(SessionText.session_id == project_session.id)\
        .first()
    
    # Create translations with evaluations
    for i in range(3):
        translation = Translation(
            session_text_id=session_text.id,
            session_language_id=project_session.languages[0].id,
            translated_text=f"Test translation {i}",
            metrics={"bleu": 0.8},
            timestamp=datetime.now()
        )
        db_session.add(translation)
        db_session.flush()  # Get translation.id
        
        evaluation = EvaluationResult(
            translation_id=translation.id,
            score=85 + i,
            comments={"overall": "Test evaluation"},
            metrics={"bleu": 0.8},
            timestamp=datetime.now()
        )
        db_session.add(evaluation)
        
        translations.append(translation)
    
    db_session.commit()
    return translations
