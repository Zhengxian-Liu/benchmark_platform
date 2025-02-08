from sqlalchemy.orm import Session
from sqlalchemy import desc
import models
from datetime import datetime

def get_prompts(db: Session, project_name: str, language_code: str):
    """Get all prompts for a specific project and language."""
    return db.query(models.Prompt).filter(
        models.Prompt.project_name == project_name,
        models.Prompt.language_code == language_code
    ).order_by(desc(models.Prompt.version)).all()

def create_prompt(db: Session, project_name: str, language_code: str, prompt_text: str, change_log: str):
    """Create a new prompt with version 1."""
    prompt = models.Prompt(
        project_name=project_name,
        language_code=language_code,
        prompt_text=prompt_text,
        version=1,
        timestamp=datetime.now(),
        change_log=change_log
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt

def update_prompt(db: Session, prompt_id: int, new_prompt_text: str, change_log: str):
    """Create a new version of an existing prompt."""
    # Get the current prompt
    current_prompt = db.query(models.Prompt).filter(models.Prompt.id == prompt_id).first()
    
    # Create a new version
    new_version = current_prompt.version + 1
    prompt = models.Prompt(
        project_name=current_prompt.project_name,
        language_code=current_prompt.language_code,
        prompt_text=new_prompt_text,
        version=new_version,
        timestamp=datetime.now(),
        change_log=change_log
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt

def get_prompt_versions(db: Session, project_name: str, language_code: str):
    """Get all versions of a prompt for a project and language, formatted for dropdown."""
    prompts = db.query(models.Prompt).filter(
        models.Prompt.project_name == project_name,
        models.Prompt.language_code == language_code
    ).order_by(desc(models.Prompt.version)).all()

    return [f"Version {p.version} ({p.timestamp.strftime('%Y-%m-%d %H:%M')})" for p in prompts]

def get_prompt_by_version_string(db: Session, project_name: str, language_code: str, version_string: str):
    """
    Retrieves a specific prompt given the project name, language code and a version string
    like "Version 1 (2024-02-08 15:30)".
    """

    # Extract the version number from the version string.  Assumes the format is consistent.
    try:
        version_number = int(version_string.split(" ")[1])
    except (ValueError, IndexError):
        return None

    return db.query(models.Prompt).filter(
        models.Prompt.project_name == project_name,
        models.Prompt.language_code == language_code,
        models.Prompt.version == version_number
    ).first()