"""Prompt operations."""

from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from models import Prompt

def get_prompts(db: Session, project_name: str, language_code: str) -> List[Prompt]:
    """Get prompts for a project and language."""
    return (
        db.query(Prompt)
        .filter(
            Prompt.project_name == project_name,
            Prompt.language_code == language_code
        )
        .order_by(Prompt.version.desc())
        .all()
    )

def create_prompt(
    db: Session,
    project_name: str,
    language_code: str,
    prompt_text: str,
    created_by: str = "system"
) -> Prompt:
    """Create a new prompt version."""
    # Get current version
    current = (
        db.query(Prompt)
        .filter(
            Prompt.project_name == project_name,
            Prompt.language_code == language_code
        )
        .order_by(Prompt.version.desc())
        .first()
    )
    
    new_version = (current.version + 1) if current else 1
    
    prompt = Prompt(
        project_name=project_name,
        language_code=language_code,
        prompt_text=prompt_text,
        version=new_version,
        created_by=created_by,
        created_at=datetime.now()
    )
    
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt

def update_prompt(
    db: Session,
    prompt_id: int,
    prompt_text: str,
    updated_by: str = "system"
) -> Optional[Prompt]:
    """Update an existing prompt."""
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        return None
    
    prompt.prompt_text = prompt_text
    prompt.updated_by = updated_by
    prompt.updated_at = datetime.now()
    
    db.commit()
    db.refresh(prompt)
    return prompt

def get_prompt_versions(
    db: Session,
    project_name: str,
    language_code: str
) -> List[Prompt]:
    """Get version history for a project-language pair."""
    return (
        db.query(Prompt)
        .filter(
            Prompt.project_name == project_name,
            Prompt.language_code == language_code
        )
        .order_by(Prompt.version.desc())
        .all()
    )

def get_prompt_by_version_string(
    db: Session,
    project_name: str,
    language_code: str,
    version_str: str
) -> Optional[Prompt]:
    """Get a specific prompt version."""
    try:
        version = int(version_str.split(" ")[1])  # Extract number from "Version X"
        return (
            db.query(Prompt)
            .filter(
                Prompt.project_name == project_name,
                Prompt.language_code == language_code,
                Prompt.version == version
            )
            .first()
        )
    except (ValueError, IndexError):
        return None
