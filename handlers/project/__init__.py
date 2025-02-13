"""Project management module."""

from .config import PROJECT_CONFIG, PROJECT_METADATA, VALID_SESSION_STATUSES
from .operations import (
    get_supported_projects,
    get_project_languages,
    get_project_sessions,
    get_project_statistics,
    get_language_statistics
)
from .validation import (
    validate_project_name,
    validate_language_code,
    validate_session_status,
    get_language_projects,
    get_common_languages
)

__all__ = [
    'PROJECT_CONFIG',
    'PROJECT_METADATA',
    'VALID_SESSION_STATUSES',
    'get_supported_projects',
    'get_project_languages',
    'get_project_sessions',
    'get_project_statistics',
    'get_language_statistics',
    'validate_project_name',
    'validate_language_code',
    'validate_session_status',
    'get_language_projects',
    'get_common_languages'
]
