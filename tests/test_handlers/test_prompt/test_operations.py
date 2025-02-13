"""Tests for prompt management operations."""

import pytest
from datetime import datetime, timedelta
from handlers.prompt import (
    get_prompts,
    create_prompt,
    update_prompt,
    get_prompt_versions,
    get_prompt_by_version_string
)

def test_create_prompt(db_session, sample_project):
    """Test creating a new prompt."""
    prompt = create_prompt(
        db=db_session,
        project_name=sample_project,
        language_code="EN",
        prompt_text="Test prompt text",
        change_log="Initial version"
    )
    
    assert prompt.project_name == sample_project
    assert prompt.language_code == "EN"
    assert prompt.prompt_text == "Test prompt text"
    assert prompt.version == 1
    assert prompt.change_log == "Initial version"
    assert isinstance(prompt.timestamp, datetime)

def test_update_prompt(db_session, sample_project):
    """Test updating an existing prompt."""
    # Create initial prompt
    prompt = create_prompt(
        db=db_session,
        project_name=sample_project,
        language_code="EN",
        prompt_text="Original text",
        change_log="Initial version"
    )
    
    # Update prompt
    updated = update_prompt(
        db=db_session,
        prompt_id=prompt.id,
        new_prompt_text="Updated text",
        change_log="Updated version"
    )
    
    assert updated.project_name == sample_project
    assert updated.language_code == "EN"
    assert updated.prompt_text == "Updated text"
    assert updated.version == 2
    assert updated.change_log == "Updated version"
    
    # Original prompt should remain unchanged
    original = get_prompts(db_session, sample_project, "EN")[-1]
    assert original.prompt_text == "Original text"
    assert original.version == 1

def test_get_prompt_versions(db_session, sample_project):
    """Test getting prompt version strings."""
    # Create multiple versions
    create_prompt(
        db=db_session,
        project_name=sample_project,
        language_code="EN",
        prompt_text="Version 1",
        change_log="Initial"
    )
    
    # Simulate some time passing
    prompt = update_prompt(
        db=db_session,
        prompt_id=1,
        new_prompt_text="Version 2",
        change_log="Update"
    )
    
    versions = get_prompt_versions(db_session, sample_project, "EN")
    assert len(versions) == 2
    assert all("Version" in v for v in versions)
    assert all(sample_project in get_prompt_by_version_string(
        db_session, sample_project, "EN", v).project_name
        for v in versions
    )

def test_get_prompt_by_version_string(db_session, sample_project):
    """Test retrieving prompt by version string."""
    prompt = create_prompt(
        db=db_session,
        project_name=sample_project,
        language_code="EN",
        prompt_text="Test text",
        change_log="Test"
    )
    
    version_str = f"Version {prompt.version} ({prompt.timestamp.strftime('%Y-%m-%d %H:%M')})"
    retrieved = get_prompt_by_version_string(
        db_session,
        sample_project,
        "EN",
        version_str
    )
    
    assert retrieved is not None
    assert retrieved.id == prompt.id
    assert retrieved.prompt_text == "Test text"

def test_get_prompt_by_invalid_version_string(db_session, sample_project):
    """Test handling invalid version strings."""
    # Test with malformed string
    result = get_prompt_by_version_string(
        db_session,
        sample_project,
        "EN",
        "Invalid version string"
    )
    assert result is None
    
    # Test with non-existent version
    result = get_prompt_by_version_string(
        db_session,
        sample_project,
        "EN",
        "Version 999 (2025-01-01 00:00)"
    )
    assert result is None

def test_update_nonexistent_prompt(db_session):
    """Test attempting to update non-existent prompt."""
    with pytest.raises(ValueError) as exc:
        update_prompt(
            db_session,
            prompt_id=999,
            new_prompt_text="Test",
            change_log="Test"
        )
    assert "No prompt found" in str(exc.value)

def test_get_prompts_empty(db_session, sample_project):
    """Test getting prompts when none exist."""
    prompts = get_prompts(db_session, sample_project, "FR")
    assert len(prompts) == 0
    
    versions = get_prompt_versions(db_session, sample_project, "FR")
    assert len(versions) == 0
