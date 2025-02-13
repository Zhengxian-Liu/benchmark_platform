"""FastAPI application and routes."""

from fastapi import FastAPI, Request, Depends, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any

import models
from models import Translation
import tempfile
from datetime import datetime
from database import SessionLocal, engine
from handlers.session.operations import (
    create_session,
    process_excel_file,
    get_session_texts,
    get_session_progress,
    update_session_status,
    create_session_texts,
    update_session_data,
    get_session
)
from handlers.project.operations import get_project_sessions
from handlers.prompt.operations import get_prompts, create_prompt, update_prompt, get_prompt_versions
from handlers.translation.operations import translate_text
from handlers.style_guide.operations import process_style_guide
import utils

app = FastAPI(title="Translation Benchmark Platform API")

# Dependency
def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/projects", response_model=List[str])
async def list_projects(db: Session = Depends(get_db)):
    """Get list of all project names."""
    return utils.get_project_names()

@app.get("/projects/{project_name}/languages", response_model=List[str])
def get_project_languages(project_name: str, db: Session = Depends(get_db)):
    """Get supported languages for a project."""
    return utils.get_language_codes(project_name)

@app.post("/projects/{project_name}/sessions")
async def create_new_session(
    project_name: str,
    file: UploadFile = File(...),
    languages: List[str] = [],
    db: Session = Depends(get_db)
):
    """Create a new session for a project."""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Process the Excel file
        success, message, detected_languages, column_mappings = process_excel_file(
            db,
            temp_file_path
        )

        if not success:
            raise HTTPException(status_code=400, detail=message)

        # Create session
        session = create_session(
            db,
            project_name,
            file.filename,
            temp_file_path,
            languages or detected_languages,
            column_mappings
        )

        # Create session texts
        success, message = create_session_texts(
            db,
            session.id,
            temp_file_path,
            languages or detected_languages
        )

        if not success:
            raise HTTPException(status_code=400, detail=message)

        return {
            "session_id": session.id,
            "status": "created",
            "languages": languages or detected_languages
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_name}/sessions", response_model=List[Dict[str, Any]])
def list_project_sessions(project_name: str, db: Session = Depends(get_db)):
    """Get all sessions for a project."""
    sessions = get_project_sessions(db, project_name)
    return [
        {
            "id": s.id,
            "created_at": s.created_at,
            "status": s.status,
            "progress": get_session_progress(db, s.id)
        }
        for s in sessions
    ]

@app.get("/sessions/{session_id}/texts", response_model=List[Dict[str, Any]])
def get_session_text_list(session_id: int, db: Session = Depends(get_db)):
    """Get all texts for a session."""
    texts = get_session_texts(db, session_id)
    return [
        {
            "id": t.id,
            "text_id": t.text_id,
            "source_text": t.source_text,
            "extra_data": t.extra_data,
            "ground_truth": t.ground_truth
        }
        for t in texts
    ]

@app.post("/sessions/{session_id}/translate")
def translate_session_texts(
    session_id: int,
    language_code: str,
    db: Session = Depends(get_db)
):
    """Translate all texts in a session to a specific language."""
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        texts = get_session_texts(db, session_id)
        prompts = get_prompts(db, session.project_name, language_code)
        
        if not prompts:
            raise HTTPException(status_code=400, detail=f"No prompt found for {language_code}")

        results = []
        for text in texts:
            prompt_text = prompts[0].prompt_text
            if "{text}" in prompt_text:
                prompt_text = prompt_text.replace("{text}", text.source_text)
            else:
                prompt_text = f"{prompt_text}\n\nText to translate: {text.source_text}"

            response = translate_text(prompt_text, "EN", language_code)
            
            translation = Translation(
                session_text_id=text.id,
                prompt_id=prompts[0].id,
                translated_text=response["translated_text"],
                metrics={}
            )
            db.add(translation)
            
            results.append({
                "text_id": text.text_id,
                "translation": response["translated_text"]
            })

        # Update session data
        if 'translations' not in session.data:
            session.data['translations'] = {}
        if language_code not in session.data['translations']:
            session.data['translations'][language_code] = {}

        for result in results:
            session.data['translations'][language_code][result['text_id']] = {
                'text': result['translation'],
                'timestamp': datetime.utcnow().isoformat(),
                'prompt_version': prompts[0].version
            }

        db.commit()
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects/{project_name}/style-guides/{language_code}")
async def upload_style_guide(
    project_name: str,
    language_code: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a new style guide for a project and language."""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Process style guide
        guide = process_style_guide(
            db,
            temp_file_path,
            project_name,
            language_code,
            created_by="admin"  # TODO: Add proper user management
        )

        return {
            "status": "success",
            "version": guide.version,
            "file_name": file.filename
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects/{project_name}/prompts/{language_code}")
def create_project_prompt(
    project_name: str,
    language_code: str,
    prompt_text: str,
    db: Session = Depends(get_db)
):
    """Create a new prompt for a project and language."""
    try:
        prompt = create_prompt(db, project_name, language_code, prompt_text)
        return {
            "status": "success",
            "version": prompt.version,
            "prompt_text": prompt.prompt_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/prompts/{prompt_id}")
def update_existing_prompt(
    prompt_id: int,
    prompt_text: str,
    changes: str = "Updated prompt",
    db: Session = Depends(get_db)
):
    """Update an existing prompt."""
    try:
        prompt = update_prompt(db, prompt_id, prompt_text, changes)
        return {
            "status": "success",
            "version": prompt.version,
            "prompt_text": prompt.prompt_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_name}/prompts/{language_code}")
def get_project_prompts(
    project_name: str,
    language_code: str,
    db: Session = Depends(get_db)
):
    """Get all prompts for a project and language."""
    prompts = get_prompts(db, project_name, language_code)
    return [{
        "id": p.id,
        "version": p.version,
        "prompt_text": p.prompt_text,
        "created_at": p.created_at
    } for p in prompts]
