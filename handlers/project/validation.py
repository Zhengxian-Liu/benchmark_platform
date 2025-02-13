"""Project validation functions."""

from typing import Tuple
from .config import PROJECT_CONFIG, VALID_SESSION_STATUSES

def validate_project_name(project_name: str) -> Tuple[bool, str]:
    """Validate if project name is supported."""
    if not project_name:
        return False, "Project name cannot be empty"
    
    if project_name not in PROJECT_CONFIG:
        return False, f"Project '{project_name}' is not supported"
    
    return True, "Project name is valid"

def validate_language_code(language_code: str, project_name: str) -> Tuple[bool, str]:
    """Validate if language code is supported for project."""
    if not language_code:
        return False, "Language code cannot be empty"
    
    if project_name not in PROJECT_CONFIG:
        return False, f"Project '{project_name}' is not supported"
    
    if language_code not in PROJECT_CONFIG[project_name]:
        return False, f"Language '{language_code}' is not supported for project '{project_name}'"
    
    return True, "Language code is valid"

def validate_session_status(status: str) -> Tuple[bool, str]:
    """Validate session status."""
    if not status:
        return False, "Status cannot be empty"
    
    if status not in VALID_SESSION_STATUSES:
        return False, f"Invalid status. Must be one of: {', '.join(VALID_SESSION_STATUSES)}"
    
    return True, "Status is valid"

def get_language_projects(language_code: str) -> list:
    """Get list of projects that support a language."""
    return [
        project for project, languages in PROJECT_CONFIG.items()
        if language_code in languages
    ]

def get_common_languages(projects: list) -> list:
    """Get languages supported by all given projects."""
    if not projects:
        return []
    
    # Get languages from first project
    common_langs = set(PROJECT_CONFIG[projects[0]])
    
    # Intersect with languages from other projects
    for project in projects[1:]:
        if project in PROJECT_CONFIG:
            common_langs &= set(PROJECT_CONFIG[project])
    
    return sorted(list(common_langs))
