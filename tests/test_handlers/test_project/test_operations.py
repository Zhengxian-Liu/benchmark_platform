"""Tests for project operations."""

import pytest
from datetime import datetime
from handlers.project import (
    get_supported_projects,
    get_project_languages,
    get_project_sessions,
    get_project_statistics,
    get_language_statistics,
    PROJECT_CONFIG,
    ProjectError
)
from models import Translation, EvaluationResult, SessionText

def test_get_supported_projects():
    """Test getting list of supported projects."""
    projects = get_supported_projects()
    assert isinstance(projects, list)
    assert len(projects) == len(PROJECT_CONFIG)
    assert all(project in PROJECT_CONFIG for project in projects)

def test_get_project_languages(sample_project):
    """Test getting supported languages for a project."""
    languages = get_project_languages(sample_project)
    assert isinstance(languages, list)
    assert languages == PROJECT_CONFIG[sample_project]
    
    # Test invalid project
    with pytest.raises(ProjectError):
        get_project_languages("invalid_project")

def test_get_project_sessions(
    db_session,
    sample_project,
    sample_language,
    project_sessions
):
    """Test getting project sessions with filters."""
    # Get all sessions
    sessions = get_project_sessions(db_session, sample_project)
    assert len(sessions) == len(project_sessions)
    
    # Filter by status
    completed = get_project_sessions(db_session, sample_project, status="completed")
    assert len(completed) == 2
    assert all(s.status == "completed" for s in completed)
    
    # Filter by language
    languages = PROJECT_CONFIG[sample_project][:2]  # Same as in fixture
    lang_sessions = get_project_sessions(
        db_session,
        sample_project,
        language_code=languages[0]
    )
    assert all(any(l.language_code == languages[0] for l in s.languages)
               for s in lang_sessions)
    
    # Test invalid project
    with pytest.raises(ProjectError):
        get_project_sessions(db_session, "invalid_project")

def test_get_project_statistics(
    db_session,
    sample_project,
    project_sessions
):
    """Test getting project statistics."""
    # Create session texts for each session
    for session in project_sessions:
        session_text = SessionText(
            session_id=session.id,
            text_id=f"text_{session.status}",
            source_text=f"Source text for {session.status}",
            extra_data={"key": "value"}
        )
        db_session.add(session_text)
    db_session.commit()
    
    # Add translations and evaluations for completed sessions
    completed_sessions = [s for s in project_sessions if s.status == "completed"]
    for session in completed_sessions:
        # Get session text (should exist now)
        session_text = db_session.query(SessionText)\
            .filter(SessionText.session_id == session.id)\
            .first()
        assert session_text is not None, f"Session text not found for session {session.id}"
            
        translation = Translation(
            session_text_id=session_text.id,
            session_language_id=session.languages[0].id,
            translated_text=f"Test translation for {session.status}",
            metrics={"bleu": 0.8},
            timestamp=datetime.now()
        )
        db_session.add(translation)
        db_session.flush()  # Get translation.id
        
        evaluation = EvaluationResult(
            translation_id=translation.id,
            score=85,
            comments="Test evaluation",
            timestamp=datetime.now()
        )
        db_session.add(evaluation)
    db_session.commit()
    
    # Test statistics
    stats = get_project_statistics(db_session, sample_project)
    
    assert isinstance(stats, dict)
    assert stats["total_sessions"] == len(project_sessions)
    assert stats["active_sessions"] == 1  # in_progress
    assert stats["completed_sessions"] == 2  # completed x2
    assert stats["supported_languages"] == PROJECT_CONFIG[sample_project]
    assert stats["total_evaluations"] == len(completed_sessions)
    assert isinstance(stats["average_score"], float)
    assert stats["prompts_per_language"]  # Should have some prompt counts
    
    # Test with language filter
    languages = PROJECT_CONFIG[sample_project][:2]  # Same as in fixture
    lang_stats = get_project_statistics(
        db_session,
        sample_project,
        language_code=languages[0]
    )
    assert isinstance(lang_stats, dict)
    assert lang_stats["total_sessions"] > 0
    
    # Test invalid project
    with pytest.raises(ProjectError):
        get_project_statistics(db_session, "invalid_project")
    
    # Test invalid language
    with pytest.raises(ProjectError):
        get_project_statistics(
            db_session,
            sample_project,
            language_code="INVALID"
        )

def test_get_language_statistics(
    db_session,
    sample_language,
    project_sessions
):
    """Test getting language statistics."""
    stats = get_language_statistics(db_session, sample_language)
    
    assert isinstance(stats, dict)
    assert "supporting_projects" in stats
    assert isinstance(stats["supporting_projects"], list)
    assert all(project in PROJECT_CONFIG for project in stats["supporting_projects"])
    
    assert stats["total_sessions"] >= 0
    assert stats["completed_sessions"] >= 0
    assert stats["ongoing_sessions"] >= 0
    assert (stats["completed_sessions"] + stats["ongoing_sessions"] == 
            stats["total_sessions"])

def test_project_language_combinations():
    """Test various project and language combinations."""
    for project in PROJECT_CONFIG:
        languages = get_project_languages(project)
        # Every project should have at least one language
        assert len(languages) > 0
        
        # Each language should be unique
        assert len(languages) == len(set(languages))

def test_project_errors(db_session):
    """Test error handling for invalid inputs."""
    with pytest.raises(ProjectError):
        get_project_statistics(db_session, "invalid_project")
        
    with pytest.raises(ProjectError):
        get_project_sessions(db_session, "invalid_project")
        
    with pytest.raises(ProjectError):
        get_project_languages("invalid_project")
