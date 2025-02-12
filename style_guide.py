import pandas as pd
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

import models
from utils import sanitize_string

class StyleGuideError(Exception):
    """Custom exception for style guide processing errors"""
    pass

def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of file content"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_style_guide_columns(df: pd.DataFrame) -> Tuple[bool, Optional[str], List[str]]:
    """Validate and detect columns in style guide Excel"""
    # Detect name column
    name_column = next((col for col in df.columns
                       if any(term in col.lower() for term in ['name', 'chinese', '名前', '이름'])), None)
    if not name_column:
        return False, "Could not find a name column", []
    
    # Get all available columns
    available_columns = [col for col in df.columns if pd.notna(col)]
    
    # Validate name column is not empty
    if df[name_column].isna().all():
        return False, f"Name column '{name_column}' is empty", available_columns
        
    return True, None, available_columns

def process_style_guide(
    db: Session,
    file_path: str,
    project_name: str,
    language_code: str,
    created_by: str
) -> models.StyleGuide:
    """Process style guide Excel file and store in database"""
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Validate and get columns
        is_valid, error_msg, available_columns = validate_style_guide_columns(df)
        if not is_valid:
            raise StyleGuideError(error_msg)
            
        # Get name column
        name_column = next(col for col in df.columns
                         if any(term in col.lower() for term in ['name', 'chinese', '名前', '이름']))
            
        # Clean data - replace NaN with None
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notna(df), None)
            
        # Compute file hash
        file_hash = compute_file_hash(file_path)
        
        # Check if identical file already exists
        existing_guide = db.query(models.StyleGuide).filter(
            and_(
                models.StyleGuide.project_name == project_name,
                models.StyleGuide.language_code == language_code,
                models.StyleGuide.file_hash == file_hash,
                models.StyleGuide.status == "active"
            )
        ).first()
        
        if existing_guide:
            return existing_guide
            
        # Get latest version number
        latest_version = db.query(models.StyleGuide).filter(
            and_(
                models.StyleGuide.project_name == project_name,
                models.StyleGuide.language_code == language_code
            )
        ).order_by(models.StyleGuide.version.desc()).first()
        
        new_version = (latest_version.version + 1) if latest_version else 1
        
        # Process entries into JSON format
        entries = {}
        for _, row in df.iterrows():
            # Skip rows where name is None
            if pd.isna(row[name_column]):
                continue
                
            # Clean and store name
            clean_name = sanitize_string(str(row[name_column]))
            entries[clean_name] = {}
            
            # Add all columns except name
            for col in available_columns:
                if col != name_column:
                    # Convert to string if not None, otherwise store as null
                    value = row[col]
                    if pd.notna(value):
                        entries[clean_name][col] = str(value)
                    else:
                        entries[clean_name][col] = None
        
        # Create new style guide entry
        new_guide = models.StyleGuide(
            project_name=project_name,
            language_code=language_code,
            version=new_version,
            entries=entries,
            file_name=Path(file_path).name,
            file_hash=file_hash,
            status="active",
            created_by=created_by
        )
        
        # Archive old versions
        old_guides = db.query(models.StyleGuide).filter(
            and_(
                models.StyleGuide.project_name == project_name,
                models.StyleGuide.language_code == language_code,
                models.StyleGuide.status == "active"
            )
        ).all()
        for guide in old_guides:
            guide.status = "archived"
        
        db.add(new_guide)
        db.commit()
        db.refresh(new_guide)
        
        return new_guide
        
    except Exception as e:
        db.rollback()
        raise StyleGuideError(f"Error processing style guide: {str(e)}")

def apply_style_guide(
    prompt_text: str,
    extra_data: Dict,
    style_guide_entries: Dict
) -> str:
    """Apply style guide entries to prompt text using extra data"""
    if not extra_data or not style_guide_entries:
        return prompt_text
        
    result = prompt_text
    
    # Extract Chinese names from extra data
    chinese_names = []
    if isinstance(extra_data, dict):
        chinese_names = [name for name in extra_data.get('extra', '').split()
                        if name in style_guide_entries]
    elif isinstance(extra_data, str):
        chinese_names = [name for name in extra_data.split()
                        if name in style_guide_entries]
    
    # Replace tags with style guide values
    for name in chinese_names:
        if name in style_guide_entries:
            entry = style_guide_entries[name]
            # Replace name tag
            result = result.replace('{name}', name)
            # Replace other attribute tags
            for attr, value in entry.items():
                result = result.replace(f'{{{attr}}}', str(value))
                
    return result