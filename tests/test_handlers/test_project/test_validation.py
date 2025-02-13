"""Tests for project validation functions."""

import pytest
from handlers.project.validation import (
    validate_project_name,
    validate_language_code,
    validate_project_languages,
    validate_session_status,
    get_language_projects,
    get_common_languages,
    VALID_SESSION_STATUSES
)
from handlers.project.operations import PROJECT_CONFIG

def test_validate_project_name():
    """Test project name validation."""
    # Test valid project
    success, msg = validate_project_name(list(PROJECT_CONFIG.keys())[0])
    assert success
    assert msg == ""
    
    # Test empty project name
    success, msg = validate_project_name("")
    assert not success
    assert "empty" in msg.lower()
    
    # Test invalid project
    success, msg = validate_project_name("invalid_project")
    assert not success
    assert "not found" in msg.lower()
    assert "available projects" in msg.lower()

def test_validate_language_code():
    """Test language code validation."""
    sample_project = list(PROJECT_CONFIG.keys())[0]
    sample_language = PROJECT_CONFIG[sample_project][0]
    
    # Test valid language without project
    success, msg = validate_language_code(sample_language)
    assert success
    assert msg == ""
    
    # Test valid language with project
    success, msg = validate_language_code(sample_language, sample_project)
    assert success
    assert msg == ""
    
    # Test empty language
    success, msg = validate_language_code("")
    assert not success
    assert "empty" in msg.lower()
    
    # Test invalid language
    success, msg = validate_language_code("XX")
    assert not success
    assert "not supported" in msg.lower()
    
    # Test valid language with wrong project
    invalid_lang = next(
        lang for project, langs in PROJECT_CONFIG.items()
        if project != sample_project
        for lang in langs
        if lang not in PROJECT_CONFIG[sample_project]
    )
    success, msg = validate_language_code(invalid_lang, sample_project)
    assert not success
    assert "not supported" in msg.lower()
    assert sample_project in msg

def test_validate_project_languages():
    """Test validation of multiple languages for a project."""
    sample_project = list(PROJECT_CONFIG.keys())[0]
    valid_langs = PROJECT_CONFIG[sample_project][:2]  # Take first two languages
    
    # Test valid languages
    success, msg, langs = validate_project_languages(sample_project, valid_langs)
    assert success
    assert msg == ""
    assert set(langs) == set(valid_langs)
    
    # Test mix of valid and invalid languages
    mixed_langs = valid_langs + ["XX", "YY"]
    success, msg, langs = validate_project_languages(sample_project, mixed_langs)
    assert not success
    assert "invalid languages" in msg.lower()
    assert set(langs) == set(valid_langs)  # Should return valid ones
    
    # Test invalid project
    success, msg, langs = validate_project_languages("invalid_project", valid_langs)
    assert not success
    assert "not found" in msg.lower()
    assert not langs  # Should be empty list

def test_validate_session_status():
    """Test session status validation."""
    # Test valid statuses
    for status in VALID_SESSION_STATUSES:
        success, msg = validate_session_status(status)
        assert success
        assert msg == ""
    
    # Test empty status
    success, msg = validate_session_status("")
    assert not success
    assert "empty" in msg.lower()
    
    # Test invalid status
    success, msg = validate_session_status("invalid_status")
    assert not success
    assert "invalid status" in msg.lower()
    assert all(status in msg for status in VALID_SESSION_STATUSES)

def test_get_language_projects():
    """Test getting projects that support a language."""
    # Test with common language
    common_lang = next(
        lang for langs in PROJECT_CONFIG.values()
        for lang in langs
        if sum(1 for p_langs in PROJECT_CONFIG.values() if lang in p_langs) > 1
    )
    projects = get_language_projects(common_lang)
    assert len(projects) > 1
    assert all(common_lang in PROJECT_CONFIG[p] for p in projects)
    
    # Test with unique language
    unique_lang = next(
        lang for langs in PROJECT_CONFIG.values()
        for lang in langs
        if sum(1 for p_langs in PROJECT_CONFIG.values() if lang in p_langs) == 1
    )
    projects = get_language_projects(unique_lang)
    assert len(projects) == 1
    
    # Test with invalid language
    projects = get_language_projects("XX")
    assert not projects  # Should be empty list

def test_get_common_languages():
    """Test finding common languages between projects."""
    # Test with single project
    project = list(PROJECT_CONFIG.keys())[0]
    langs = get_common_languages([project])
    assert set(langs) == set(PROJECT_CONFIG[project])
    
    # Test with multiple projects
    projects = list(PROJECT_CONFIG.keys())[:2]  # Take first two projects
    langs = get_common_languages(projects)
    assert all(lang in PROJECT_CONFIG[p] for p in projects for lang in langs)
    
    # Test with invalid project
    langs = get_common_languages(["invalid_project"])
    assert not langs  # Should be empty list
    
    # Test with mix of valid and invalid projects
    langs = get_common_languages([project, "invalid_project"])
    assert not langs  # Should be empty list
    
    # Test with empty list
    assert not get_common_languages([])  # Should be empty list
