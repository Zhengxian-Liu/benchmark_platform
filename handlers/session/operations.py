"""Session operations."""

from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from models import Session as DbSession, SessionLanguage, SessionText
from handlers.project.validation import validate_project_name, validate_language_code

def get_session(db: Session, session_id: int) -> DbSession:
    """Get session by ID."""
    return db.query(DbSession).filter(DbSession.id == session_id).first()

def get_session_texts(db: Session, session_id: int) -> list:
    """Get all texts for a session."""
    return (
        db.query(SessionText)
        .filter(SessionText.session_id == session_id)
        .order_by(SessionText.id)
        .all()
    )

def create_session(
    db: Session,
    project_name: str,
    source_file_name: str,
    source_file_path: str,
    selected_languages: list,
    column_mappings: dict
) -> DbSession:
    """Create a new session."""
    # Validate project and languages
    success, msg = validate_project_name(project_name)
    if not success:
        raise ValueError(msg)
    
    for lang in selected_languages:
        success, msg = validate_language_code(lang, project_name)
        if not success:
            raise ValueError(msg)
    
    # Create session
    session = DbSession(
        project_name=project_name,
        source_file_name=source_file_name,
        source_file_path=source_file_path,
        status="in_progress",
        created_at=datetime.now(),
        data={
            "selected_languages": selected_languages,
            "column_mappings": column_mappings,
            "source_file": {
                "name": source_file_name,
                "path": source_file_path
            }
        }
    )
    db.add(session)
    db.commit()
    return session

def process_excel_file(db: Session, file_path: str):
    """Process uploaded Excel file."""
    try:
        df = pd.read_excel(file_path)
        columns = df.columns.tolist()
        
        # Try to detect mappings
        detected_mappings = {
            'source': next((col for col in columns if 'source' in col.lower()), None),
            'textid': next((col for col in columns if 'id' in col.lower()), None),
            'extra': next((col for col in columns if 'extra' in col.lower() or 'notes' in col.lower()), None)
        }
        
        # Detect language codes in column names
        language_codes = []
        for col in columns:
            # Check if column might be a language code
            parts = col.split('_')
            if len(parts[-1]) in [2, 3]:  # Language codes are typically 2-3 chars
                language_codes.append(parts[-1].upper())
        
        return True, "File processed successfully", language_codes, detected_mappings
        
    except Exception as e:
        return False, f"Error processing file: {str(e)}", [], {}

def create_session_texts(db: Session, session_id: int, file_path: str, languages: list):
    """Create texts for a session from Excel file."""
    session = get_session(db, session_id)
    if not session:
        return False, "Session not found"
    
    try:
        df = pd.read_excel(file_path)
        mappings = session.data['column_mappings']
        
        for _, row in df.iterrows():
            text = SessionText(
                session_id=session_id,
                text_id=str(row[mappings['textid']]),
                source_text=str(row[mappings['source']]),
                extra_data={mappings['extra']: str(row[mappings['extra']])} if 'extra' in mappings else None
            )
            db.add(text)
            
        # Add languages to session
        for lang_code in languages:
            lang = SessionLanguage(
                session_id=session_id,
                language_code=lang_code,
                prompts={"version": 1}
            )
            db.add(lang)
            
        db.commit()
        return True, "Session texts created successfully"
        
    except Exception as e:
        db.rollback()
        return False, f"Error creating texts: {str(e)}"

def get_session_progress(db: Session, session_id: int):
    """Get session progress statistics."""
    session = get_session(db, session_id)
    if not session:
        return {"total": 0, "translated": 0, "evaluated": 0}
    
    total = db.query(SessionText).filter(SessionText.session_id == session_id).count()
    # TODO: Add logic to count translated and evaluated texts
    
    return {
        "total": total,
        "translated": 0,  # Placeholder
        "evaluated": 0   # Placeholder
    }

def update_session_status(db: Session, session_id: int, status: str):
    """Update session status."""
    session = get_session(db, session_id)
    if session:
        session.status = status
        db.commit()
        return True
    return False

def update_session_data(db: Session, session_id: int, data: dict):
    """Update session data."""
    session = get_session(db, session_id)
    if session:
        session.data.update(data)
        db.commit()
        return True
    return False
