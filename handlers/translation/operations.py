"""Translation operations module."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from models import Translation, SessionText, SessionLanguage
from .utils import translate_text

def create_translation(
    db: Session,
    session_text_id: int,
    session_language_id: int,
    prompt_text: str,
    source_language: str,
    target_language: str
) -> Translation:
    """
    Create a new translation for a session text.
    
    Args:
        db: Database session
        session_text_id: ID of the SessionText
        session_language_id: ID of the SessionLanguage
        prompt_text: Formatted prompt text for translation
        source_language: Source language code
        target_language: Target language code
        
    Returns:
        Created Translation object
        
    Raises:
        ValueError: If session text or language not found
    """
    # Verify session text exists
    text = db.query(SessionText).filter(SessionText.id == session_text_id).first()
    if not text:
        raise ValueError(f"No session text found with ID {session_text_id}")
        
    # Verify session language exists
    lang = db.query(SessionLanguage).filter(SessionLanguage.id == session_language_id).first()
    if not lang:
        raise ValueError(f"No session language found with ID {session_language_id}")
    
    # Perform translation
    result = translate_text(
        prompt_text=prompt_text,
        source_language=source_language,
        target_language=target_language
    )
    
    # Create translation record
    translation = Translation(
        session_text_id=session_text_id,
        session_language_id=session_language_id,
        translated_text=result["translated_text"],
        metrics={"model": result["model"]},
        created_at=datetime.now()
    )
    
    db.add(translation)
    db.commit()
    db.refresh(translation)
    return translation

def get_translations(
    db: Session,
    session_text_id: int,
    session_language_id: Optional[int] = None
) -> List[Translation]:
    """
    Get translations for a session text.
    
    Args:
        db: Database session
        session_text_id: ID of the SessionText
        session_language_id: Optional SessionLanguage ID to filter by
        
    Returns:
        List of Translation objects
    """
    query = db.query(Translation).filter(Translation.session_text_id == session_text_id)
    
    if session_language_id is not None:
        query = query.filter(Translation.session_language_id == session_language_id)
    
    return query.order_by(Translation.created_at.desc()).all()

def delete_translation(db: Session, translation_id: int) -> bool:
    """
    Delete a translation.
    
    Args:
        db: Database session
        translation_id: ID of the translation to delete
        
    Returns:
        True if translation was deleted, False if not found
    """
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    if not translation:
        return False
        
    db.delete(translation)
    db.commit()
    return True
