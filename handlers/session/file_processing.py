"""File processing operations for session management."""

from typing import Dict, List, Tuple

from sqlalchemy.orm import Session
import pandas as pd

from models import SessionText, SessionLanguage
from .crud import get_session

def process_excel_file(
    db: Session,
    file_path: str
) -> Tuple[bool, str, List[str], Dict[str, str]]:
    """
    Process an uploaded Excel file and detect columns and language codes.

    Args:
        db: Database session
        file_path: Path to the uploaded Excel file

    Returns:
        Tuple of (success: bool, message: str, language_codes: List[str], column_mappings: Dict[str, str])
    """
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Detect potential column mappings
        column_mappings = {}
        all_columns = list(df.columns)
        
        # Convert columns to lowercase for comparison
        columns_lower = {col.lower(): col for col in all_columns}
        
        # Detect Source column
        source_candidates = {'source', 'source text', 'text', 'content', 'original', 'src'}
        source_col = next((col_orig for col_lower, col_orig in columns_lower.items() 
                         if any(cand in col_lower for cand in source_candidates)), None)
        if source_col:
            column_mappings['source'] = source_col
            
        # Detect Extra column
        extra_candidates = {'extra', 'additional', 'metadata', 'info', 'context', 'extra info'}
        extra_col = next((col_orig for col_lower, col_orig in columns_lower.items() 
                         if any(cand in col_lower for cand in extra_candidates)), None)
        if extra_col:
            column_mappings['extra'] = extra_col
            
        # Detect Text ID column
        id_candidates = {'textid', 'text id', 'id', 'text_id', 'index', 'key'}
        id_col = next((col_orig for col_lower, col_orig in columns_lower.items() 
                      if any(cand in col_lower for cand in id_candidates)), None)
        if id_col:
            column_mappings['textid'] = id_col

        # Detect language codes from remaining columns
        mapped_cols = set(column_mappings.values())
        language_codes = [col for col in all_columns if col not in mapped_cols]

        # Validate required columns
        if not column_mappings.get('source'):
            return False, "Could not detect Source column. Please ensure a column for source text exists.", [], {}
        if not column_mappings.get('textid'):
            return False, "Could not detect Text ID column. Please ensure a column for text IDs exists.", [], {}

        # Return success with detected mappings
        return True, "Excel file processed successfully", language_codes, column_mappings

    except Exception as e:
        return False, f"Error processing Excel file: {str(e)}", [], {}

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
        # Get session and column mappings
        session = get_session(db, session_id)
        if not session or 'column_mappings' not in session.data:
            return False, "Session not found or missing column mappings"
            
        column_mappings = session.data['column_mappings']
        
        # Validate required mappings
        if not all(key in column_mappings for key in ['textid', 'source']):
            return False, "Missing required column mappings"
            
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Create SessionText entries
        for _, row in df.iterrows():
            # Build ground truth dictionary for selected languages
            ground_truth = {}
            for lang in selected_languages:
                if lang in df.columns:
                    ground_truth[lang] = row[lang] if pd.notna(row[lang]) else None

            # Get values using column mappings
            text_id = str(row[column_mappings['textid']])
            source_text = row[column_mappings['source']]
            # Handle extra data with more robust error checking
            extra_data = None
            if 'extra' in column_mappings and column_mappings['extra'] in row:
                extra_value = row[column_mappings['extra']]
                if pd.notna(extra_value):
                    extra_data = str(extra_value)

            # Create SessionText entry
            text = SessionText(
                session_id=session_id,
                text_id=text_id,
                source_text=source_text,
                extra_data=extra_data,
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
