"""Style guide operations."""

from datetime import datetime
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import Session
from models import StyleGuide
import pandas as pd

class StyleGuideError(Exception):
    """Base exception for style guide operations."""
    pass

def process_style_guide(
    db: Session,
    file_path: str,
    project_name: str,
    language_code: str,
    created_by: str = "system"
) -> StyleGuide:
    """Process uploaded style guide file and save to database."""
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Get current version
        current = (
            db.query(StyleGuide)
            .filter(
                StyleGuide.project_name == project_name,
                StyleGuide.language_code == language_code
            )
            .order_by(StyleGuide.version.desc())
            .first()
        )
        
        new_version = (current.version + 1) if current else 1
        
        # Create new style guide
        # Get original file name from file path
        source_file_name = file_path.split('/')[-1]  # Extract filename from path
        
        guide = StyleGuide(
            project_name=project_name,
            language_code=language_code,
            content=df.to_json(),  # Store as proper JSON
            version=new_version,
            source_file_name=source_file_name,
            guide_metadata={
                "columns": df.columns.tolist(),
                "rows": len(df)
            },
            created_at=datetime.now(),
            created_by=created_by,
            updated_at=datetime.now()
        )
        
        db.add(guide)
        db.commit()
        db.refresh(guide)
        return guide
        
    except Exception as e:
        raise StyleGuideError(f"Failed to process style guide: {str(e)}")

def apply_style_guide(
    text: str,
    style_guide: StyleGuide
) -> Tuple[str, Dict]:
    """Apply style guide rules to text.
    This is a placeholder implementation.
    """
    try:
        return text, {
            "applied_rules": [],
            "modifications": []
        }
    except Exception as e:
        raise StyleGuideError(f"Failed to apply style guide: {str(e)}")
