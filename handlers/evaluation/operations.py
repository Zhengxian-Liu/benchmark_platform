"""Evaluation operations."""

from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from models import EvaluationResult, Translation

def evaluate_translation(
    db: Session,
    translation_id: int,
    score: float,
    comments: Dict = None,
    metrics: Dict = None
) -> Optional[EvaluationResult]:
    """Create or update evaluation for a translation."""
    # Check if translation exists
    translation = db.query(Translation).filter(Translation.id == translation_id).first()
    if not translation:
        return None
    
    # Check for existing evaluation
    evaluation = (
        db.query(EvaluationResult)
        .filter(EvaluationResult.translation_id == translation_id)
        .first()
    )
    
    if evaluation:
        # Update existing evaluation
        evaluation.score = score
        evaluation.comments = comments or evaluation.comments
        evaluation.metrics = metrics or evaluation.metrics
        evaluation.timestamp = datetime.now()
    else:
        # Create new evaluation
        evaluation = EvaluationResult(
            translation_id=translation_id,
            score=score,
            comments=comments or {},
            metrics=metrics or {},
            timestamp=datetime.now()
        )
        db.add(evaluation)
    
    db.commit()
    db.refresh(evaluation)
    return evaluation

def get_translation_evaluations(
    db: Session,
    translation_id: int
) -> List[EvaluationResult]:
    """Get all evaluations for a translation."""
    return (
        db.query(EvaluationResult)
        .filter(EvaluationResult.translation_id == translation_id)
        .order_by(EvaluationResult.timestamp.desc())
        .all()
    )
