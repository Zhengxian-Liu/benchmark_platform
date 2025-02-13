"""Evaluation validation functions."""

from typing import Dict, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import Translation, SessionText, Prompt

def validate_translation_ids(
    db: Session,
    translation_ids: List[int],
    prompt_version_id: Optional[int] = None
) -> Tuple[bool, str, List[int]]:
    """
    Validate that all translation IDs exist and optionally belong to a prompt version.
    
    Args:
        db: Database session
        translation_ids: List of translation IDs to validate
        prompt_version_id: Optional prompt version ID to filter by
        
    Returns:
        Tuple of (success: bool, error_message: str, found_translation_ids: List[int])
    """
    query = db.query(Translation).filter(Translation.id.in_(translation_ids))
    
    if prompt_version_id:
        query = query.filter(Translation.prompt_version_id == prompt_version_id)
    
    found_ids = [t.id for t in query.all()]
    
    if len(found_ids) != len(translation_ids):
        missing_ids = set(translation_ids) - set(found_ids)
        return False, f"Translations not found: {missing_ids}", found_ids
        
    return True, "", found_ids

def validate_score_range(
    score: Union[int, float],
    min_score: float = 0,
    max_score: float = 100,
    score_type: str = "overall"
) -> Tuple[bool, str]:
    """
    Validate that a score is within the allowed range.
    
    Args:
        score: Score to validate
        min_score: Minimum allowed score
        max_score: Maximum allowed score
        score_type: Type of score being validated (for error messages)
        
    Returns:
        Tuple of (success: bool, error_message: str)
    """
    if not isinstance(score, (int, float)):
        return False, f"{score_type.capitalize()} score must be a number"
        
    if not min_score <= score <= max_score:
        return False, f"{score_type.capitalize()} score must be between {min_score} and {max_score}"
        
    return True, ""

def validate_segment_scores(
    segment_scores: Dict[str, float],
    allowed_segments: Optional[List[str]] = None,
    min_score: float = 0,
    max_score: float = 100
) -> Tuple[bool, str]:
    """
    Validate segment scores dictionary format and values.
    
    Args:
        segment_scores: Dictionary of segment IDs to scores
        allowed_segments: Optional list of allowed segment IDs
        min_score: Minimum allowed score
        max_score: Maximum allowed score
        
    Returns:
        Tuple of (success: bool, error_message: str)
    """
    if not isinstance(segment_scores, dict):
        return False, "Segment scores must be a dictionary"
    
    if allowed_segments and not set(segment_scores.keys()).issubset(allowed_segments):
        invalid_segments = set(segment_scores.keys()) - set(allowed_segments)
        return False, f"Invalid segment IDs: {invalid_segments}"
        
    for segment_id, score in segment_scores.items():
        success, msg = validate_score_range(
            score,
            min_score,
            max_score,
            f"segment {segment_id}"
        )
        if not success:
            return False, msg
            
    return True, ""

def validate_metrics(metrics: Dict[str, float]) -> Tuple[bool, str]:
    """
    Validate automated metrics dictionary format and values.
    
    Args:
        metrics: Dictionary of metric names to values
        
    Returns:
        Tuple of (success: bool, error_message: str)
    """
    if not isinstance(metrics, dict):
        return False, "Metrics must be a dictionary"
        
    valid_metrics = {"bleu", "rouge", "meteor", "ter"}  # Add more as needed
    
    invalid_metrics = set(metrics.keys()) - valid_metrics
    if invalid_metrics:
        return False, f"Invalid metric types: {invalid_metrics}"
        
    for metric, value in metrics.items():
        if not isinstance(value, (int, float)):
            return False, f"Metric '{metric}' value must be a number"
            
        # Some metrics like BLEU are 0-1, others like TER can be larger
        if metric == "bleu" and not 0 <= value <= 1:
            return False, f"BLEU score must be between 0 and 1"
            
    return True, ""

def validate_evaluation_data(
    scores: Dict[str, Union[float, Dict[str, float]]],
    comments: Optional[Dict[str, str]] = None,
    metrics: Optional[Dict[str, float]] = None
) -> Tuple[bool, str]:
    """
    Validate complete evaluation data including scores, comments, and metrics.
    
    Args:
        scores: Dictionary containing overall and segment scores
        comments: Optional dictionary of comments
        metrics: Optional dictionary of automated metrics
        
    Returns:
        Tuple of (success: bool, error_message: str)
    """
    # Validate overall score (required)
    if "overall" not in scores:
        return False, "Overall score is required"
        
    success, msg = validate_score_range(scores["overall"])
    if not success:
        return False, msg
        
    # Validate segment scores if provided
    if "segments" in scores:
        success, msg = validate_segment_scores(scores["segments"])
        if not success:
            return False, msg
            
    # Validate comments structure if provided
    if comments:
        if not isinstance(comments, dict):
            return False, "Comments must be a dictionary"
            
        valid_comment_keys = {"overall", "segments"}
        invalid_keys = set(comments.keys()) - valid_comment_keys
        if invalid_keys:
            return False, f"Invalid comment keys: {invalid_keys}"
            
    # Validate metrics if provided
    if metrics:
        success, msg = validate_metrics(metrics)
        if not success:
            return False, msg
            
    return True, ""
