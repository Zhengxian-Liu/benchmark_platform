"""Utility functions."""

from handlers.project import PROJECT_CONFIG

def get_project_names() -> list:
    """Get list of all projects."""
    return list(PROJECT_CONFIG.keys())

def get_language_codes(project_name: str) -> list:
    """Get supported languages for a project."""
    return PROJECT_CONFIG.get(project_name, [])
