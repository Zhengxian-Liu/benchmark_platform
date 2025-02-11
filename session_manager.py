from sqlalchemy.orm import Session
import pandas as pd
from models import Session as DbSession, SessionText, SessionLanguage
from datetime import datetime
from typing import Dict, List, Optional, Tuple

def create_session(
    db: Session, 
    project_name: str, 
    source_file_name: str, 
    source_file_path: str,
    selected_languages: List[str]
) -> DbSession:
    """Create a new session for a project with selected languages."""
    # Initialize session data with basic information
    session_data = {
        "selected_languages": selected_languages,
        "source_file": {
            "name": source_file_name,
            "path": source_file_path
        },
        "prompts": {lang: None for lang in selected_languages},
        "translations": {},
        "evaluations": {},
        "created_at": datetime.utcnow().isoformat()
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

def process_excel_file(
    db: Session,
    file_path: str
) -> tuple[bool, str, List[str]]:
    """
    Process an uploaded Excel file and extract language codes.

    Args:
        db: Database session
        file_path: Path to the uploaded Excel file

    Returns:
        Tuple of (success: bool, message: str, language_codes: List[str])
    """
    try:
        # Read Excel file
        df = pd.read_excel(file_path)

        # Validate required columns
        required_columns = {'textid', 'source', 'extra'}
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}", []

        # Detect language codes from column names
        language_codes = [col for col in df.columns if col not in required_columns]

        return True, "Excel file processed successfully", language_codes

    except Exception as e:
        return False, f"Error processing Excel file: {str(e)}", []

def create_session_texts(
    db: Session,
    session_id: int,
    file_path: str,
    selected_languages: List[str]
) -> Tuple[bool, str]:
    """
    Create SessionText entries for a session after language selection.
    
    Args:
        db: Database session
        session_id: ID of the session
        file_path: Path to the Excel file
        selected_languages: List of selected language codes
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Create SessionText entries
        for _, row in df.iterrows():
            # Build ground truth dictionary for selected languages
            ground_truth = {}
            for lang in selected_languages:
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
        
        # Create SessionLanguage entries
        for lang_code in selected_languages:
            session_lang = SessionLanguage(
                session_id=session_id,
                language_code=lang_code,
                prompts={"prompt_id": None, "version": None}
            )
            db.add(session_lang)
            
        db.commit()
        return True, "Session texts created successfully"
        
    except Exception as e:
        return False, f"Error creating session texts: {str(e)}"
      
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
            
        # Merge update_data with existing data
        session.data.update(update_data)
        db.commit()
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