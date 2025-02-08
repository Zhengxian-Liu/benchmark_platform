from sqlalchemy.orm import Session, joinedload
import models
from typing import Optional, Dict, Any

def get_translation_details(db: Session, text_id: str) -> Optional[Dict[str, Any]]:
    """Get full translation details including prompt and response"""
    translation = db.query(models.Translation)\
        .join(models.SessionText)\
        .filter(models.SessionText.text_id == text_id)\
        .options(joinedload(models.Translation.prompt))\
        .first()

    if not translation:
        return None

    return {
        "prompt": translation.prompt.prompt_text if translation.prompt else "No prompt found",
        "response": translation.translated_text,
        "metrics": translation.metrics,
        "timestamp": translation.timestamp.isoformat()
    }

def evaluate_translation(db: Session, translation_ids: list[int], overall_score: float, comments: str):
    for translation_id in translation_ids:
        evaluation_result = models.EvaluationResult(
            translation_id=translation_id,
            score=overall_score,
            comments=comments
        )
        db.add(evaluation_result)
    db.commit()


def validate_text_id(db: Session, text_id: str) -> bool:
    """Verify if text_id exists in the database"""
    return db.query(models.SessionText)\
        .filter(models.SessionText.text_id == text_id)\
        .first() is not None