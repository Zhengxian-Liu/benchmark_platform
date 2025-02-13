"""Tests for datetime handling in session management."""

import pytest
from datetime import datetime, UTC

from handlers.session.crud import create_session

def test_session_timezone_handling(db_session, sample_project):
    """Test that session creation uses UTC timezone for timestamps."""
    # Create a session with minimum required data
    session = create_session(
        db=db_session,
        project_name=sample_project,
        source_file_name="test.xlsx",
        source_file_path="/test/path.xlsx",
        selected_languages=["EN"],
        column_mappings={
            "source": "Source",
            "textid": "ID"
        }
    )

    # Parse the created_at timestamp from session data
    created_at = datetime.fromisoformat(session.data["created_at"])
    
    # Verify timezone awareness
    assert created_at.tzinfo is not None, "Created timestamp should be timezone-aware"
    assert created_at.tzinfo.tzname(None) == 'UTC', "Timestamp should be in UTC"
    
    # Verify the timestamp is recent (within last minute)
    now = datetime.now(UTC)
    time_diff = now - created_at
    assert time_diff.total_seconds() < 60, "Created timestamp should be recent"
