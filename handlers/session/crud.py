"""Session CRUD operations."""

from datetime import datetime, UTC
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from models import Session as DbSession, SessionText, SessionLanguage


def create_session(
    db: Session,
    project_name: str,
    source_file_name: str,
    source_file_path: str,
    selected_languages: List[str],
    column_mappings: Dict[str, str]
) -> DbSession:
    """Create a new session for a project with selected languages and column mappings."""
    # Initialize session data with basic information
    session_data = {
        "selected_languages": selected_languages,
        "source_file": {
            "name": source_file_name,
            "path": source_file_path
        },
        "column_mappings": column_mappings,
        "prompts": {lang: None for lang in selected_languages},
        "translations": {},
        "evaluations": {},
        "created_at": datetime.now(UTC).isoformat()
    }
    
    db_session = DbSession(
        project_name=project_name,
        source_file_name=source_file_name,
        source_file_path=source_file_path,
        status="in_progress",
        data=session_data
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_session(db: Session, session_id: int) -> Optional[DbSession]:
    """Get a session by ID."""
    return db.query(DbSession).filter(DbSession.id == session_id).first()



def get_session_texts(db: Session, session_id: int, offset: int = 0, limit: int = 100) -> List[SessionText]:
    """Get a paginated list of texts for a session."""
    return db.query(SessionText).filter(SessionText.session_id == session_id).offset(offset).limit(limit).all()


def update_session_status(db: Session, session_id: int, status: str) -> bool:
    """Update the status of a session."""
    session = get_session(db, session_id)
    if not session:
        return False
    
    session.status = status
    db.commit()
    return True


def update_session_data(db: Session, session_id: int, update_data: Dict) -> bool:
    """
    Update the session's data field with new information.
    
    Args:
        db: Database session
        session_id: ID of the session
        update_data: Dictionary containing the data to update/add
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        session = get_session(db, session_id)
        if not session:
            return False
            
        # Create a new dictionary to store updated data
        updated_data = session.data.copy()
        # Update with new data
        updated_data.update(update_data)
        # Assign the updated dictionary back to session.data
        session.data = updated_data
        db.commit()
        db.refresh(session)
        return True
        
    except Exception as e:
        print(f"Error updating session data: {str(e)}")
        return False


def get_session_progress(db: Session, session_id: int) -> Dict[str, int]:
    """
    Get the progress of translations and evaluations for a session.
    Returns a dictionary with counts of total texts, translated texts, and evaluated texts.
    """
    session = get_session(db, session_id)
    if not session:
        return {}
    
    total_texts = len(session.texts)
    translated_texts = sum(1 for text in session.texts if text.translations)
    evaluated_texts = sum(
        1 for text in session.texts 
        for trans in text.translations 
        if trans.evaluations
    )
    
    return {
        "total": total_texts,
        "translated": translated_texts,
        "evaluated": evaluated_texts
    }
