"""Example usage of project module functionality."""

import logging
from datetime import datetime
from database import SessionLocal, reset_db
from models import Session as DbSession, SessionLanguage, SessionText

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Demonstrate project module functionality."""
    # Initialize database
    logger.info("Initializing database...")
    reset_db()

    # Create database session
    db = SessionLocal()
    try:
        # Create a new translation session
        logger.info("Creating new translation session...")
        session = DbSession(
            project_name="原神",  # From PROJECT_CONFIG
            source_file_name="example.xlsx",
            source_file_path="/path/to/example.xlsx",
            status="in_progress",
            created_at=datetime.now(),
            data={
                "selected_languages": ["EN", "DE"],
                "source_file": {
                    "name": "example.xlsx",
                    "path": "/path/to/example.xlsx"
                }
            }
        )
        db.add(session)
        db.flush()  # Get session.id
        logger.info(f"Created new session with ID: {session.id}")
        
        # Add languages to session
        logger.info("Adding languages to session...")
        for lang_code in ["EN", "DE"]:
            lang = SessionLanguage(
                session_id=session.id,
                language_code=lang_code,
                prompts={"prompt_id": 1, "version": 1}
            )
            db.add(lang)
            logger.info(f"Added language {lang_code} to session")
        
        # Add some text to translate
        logger.info("Adding text to translate...")
        text = SessionText(
            session_id=session.id,
            text_id="text_1",
            source_text="Hello world!",
            extra_data={"context": "greeting"}
        )
        db.add(text)
        db.commit()
        logger.info("Added text to session")
        
        # Now demonstrate some project module functionality
        from handlers.project import (
            get_supported_projects,
            get_project_languages,
            get_project_sessions,
            get_project_statistics
        )
        
        logger.info("\n=== Project Module Functions ===")
        
        # Get all supported projects
        logger.info("\nGetting supported projects...")
        projects = get_supported_projects()
        logger.info(f"Supported projects: {projects}")
        
        # Get languages for a project
        project = "原神"
        logger.info(f"\nGetting supported languages for {project}...")
        languages = get_project_languages(project)
        logger.info(f"Supported languages: {languages}")
        
        # Get active sessions
        logger.info(f"\nGetting active sessions for {project}...")
        sessions = get_project_sessions(db, project, status="in_progress")
        logger.info(f"Found {len(sessions)} active sessions")
        
        # Get project statistics
        logger.info(f"\nGetting statistics for {project}...")
        stats = get_project_statistics(db, project)
        logger.info("Project statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
