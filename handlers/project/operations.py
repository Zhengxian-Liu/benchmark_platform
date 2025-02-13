"""Project operations."""

from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from .config import PROJECT_CONFIG, PROJECT_METADATA
from .validation import validate_project_name, validate_language_code
from models import Session as DbSession

def get_supported_projects() -> List[str]:
    """Get list of all supported projects."""
    return list(PROJECT_CONFIG.keys())

def get_project_languages(project_name: str) -> List[str]:
    """Get supported languages for a project."""
    success, msg = validate_project_name(project_name)
    if not success:
        return []
    return PROJECT_CONFIG[project_name]

def get_project_sessions(
    db: Session,
    project_name: str,
    status: Optional[str] = None
) -> List[DbSession]:
    """Get all sessions for a project."""
    query = db.query(DbSession).filter(DbSession.project_name == project_name)
    
    if status:
        query = query.filter(DbSession.status == status)
    
    return query.order_by(DbSession.created_at.desc()).all()

def get_project_statistics(db: Session, project_name: str) -> Dict:
    """Get statistics for a project."""
    stats = {
        "total_sessions": 0,
        "active_sessions": 0,
        "completed_sessions": 0,
        "prompts_per_language": {},
        "total_evaluations": 0,
        "average_score": 0.0,
        "supported_languages": get_project_languages(project_name)
    }
    
    # Get sessions statistics
    sessions = get_project_sessions(db, project_name)
    stats["total_sessions"] = len(sessions)
    
    # Count sessions by status
    for session in sessions:
        if session.status == "in_progress":
            stats["active_sessions"] += 1
        elif session.status == "completed":
            stats["completed_sessions"] += 1
        
        # Count prompts per language
        if session.data and "selected_languages" in session.data:
            for lang in session.data["selected_languages"]:
                if lang not in stats["prompts_per_language"]:
                    stats["prompts_per_language"][lang] = 0
                stats["prompts_per_language"][lang] += 1
    
    return stats

def get_language_statistics(
    db: Session,
    project_name: str,
    language_code: str
) -> Dict:
    """Get statistics for a project-language pair."""
    stats = {
        "total_translations": 0,
        "evaluated_translations": 0,
        "average_score": 0.0,
        "prompt_versions": 0
    }
    
    # Validate inputs
    if not validate_language_code(language_code, project_name)[0]:
        return stats
    
    # TODO: Add actual statistics calculation
    return stats
