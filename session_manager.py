from sqlalchemy.orm import Session
import pandas as pd
from models import Session as DbSession, SessionText
from datetime import datetime
from typing import Dict, List, Optional

def create_session(db: Session, project_name: str, source_file_name: str) -> DbSession:
    """Create a new session for a project."""
    db_session = DbSession(
        project_name=project_name,
        source_file_name=source_file_name,
        status="in_progress"
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def process_excel_file(
    db: Session,
    file_path: str,
    session_id: int,
    language_codes: List[str]
) -> tuple[bool, str]:
    """
    Process an uploaded Excel file and store its contents in the database.
    
    Args:
        db: Database session
        file_path: Path to the uploaded Excel file
        session_id: ID of the session to associate the texts with
        language_codes: List of language codes to look for in ground truth columns
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Validate required columns
        required_columns = {'textid', 'source', 'extra'}
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"
        
        # Process each row
        for _, row in df.iterrows():
            # Build ground truth dictionary for each language
            ground_truth = {}
            for lang in language_codes:
                if lang in df.columns:
                    ground_truth[lang] = row[lang] if pd.notna(row[lang]) else None
            
            # Create SessionText entry
            text = SessionText(
                session_id=session_id,
                text_id=str(row['textid']),
                source_text=row['source'],
                extra_data=row['extra'] if pd.notna(row['extra']) else None,
                ground_truth=ground_truth
            )
            db.add(text)
        
        db.commit()
        return True, "Excel file processed successfully"
        
    except Exception as e:
        db.rollback()
        return False, f"Error processing Excel file: {str(e)}"

def get_session(db: Session, session_id: int) -> Optional[DbSession]:
    """Get a session by ID."""
    return db.query(DbSession).filter(DbSession.id == session_id).first()

def get_project_sessions(db: Session, project_name: str) -> List[DbSession]:
    """Get all sessions for a project."""
    return db.query(DbSession).filter(DbSession.project_name == project_name).all()

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