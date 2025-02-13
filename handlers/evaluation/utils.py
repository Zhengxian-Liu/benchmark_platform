"""Evaluation utility functions."""

from typing import Dict, List
from datetime import datetime, timedelta
import statistics
from collections import defaultdict

def calculate_weighted_score(
    segment_scores: Dict[str, float],
    weights: Dict[str, float] = None
) -> float:
    """
    Calculate weighted average score from segment scores.
    
    Args:
        segment_scores: Dictionary of segment IDs to scores
        weights: Optional dictionary of segment IDs to weights
        
    Returns:
        Weighted average score
    """
    if not segment_scores:
        return 0.0
        
    if weights is None:
        # Use equal weights if none provided
        total_segments = len(segment_scores)
        weights = {segment_id: 1.0/total_segments for segment_id in segment_scores}
    
    weighted_sum = sum(
        score * weights.get(segment_id, 1.0)
        for segment_id, score in segment_scores.items()
    )
    total_weight = sum(
        weights.get(segment_id, 1.0)
        for segment_id in segment_scores
    )
    
    return weighted_sum / total_weight if total_weight > 0 else 0.0

def analyze_score_distribution(scores: List[float]) -> Dict:
    """
    Analyze distribution of evaluation scores.
    
    Args:
        scores: List of evaluation scores
        
    Returns:
        Dictionary containing statistical measures
    """
    if not scores:
        return {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "std_dev": 0.0,
            "quartiles": [0.0, 0.0, 0.0],
            "buckets": []
        }
    
    # Calculate basic statistics
    mean = statistics.mean(scores)
    median = statistics.median(scores)
    std_dev = statistics.stdev(scores) if len(scores) > 1 else 0.0
    
    # Calculate quartiles
    sorted_scores = sorted(scores)
    quartiles = [
        sorted_scores[int(len(sorted_scores) * q)]
        for q in [0.25, 0.5, 0.75]
    ]
    
    # Create score distribution buckets
    bucket_size = 10  # 0-10, 11-20, etc.
    buckets = defaultdict(int)
    for score in scores:
        bucket = score // bucket_size
        buckets[bucket] += 1
    
    # Format buckets for output
    bucket_list = [
        {
            "range": f"{i*bucket_size}-{(i+1)*bucket_size}",
            "count": count
        }
        for i, count in sorted(buckets.items())
    ]
    
    return {
        "count": len(scores),
        "mean": mean,
        "median": median,
        "std_dev": std_dev,
        "quartiles": quartiles,
        "buckets": bucket_list
    }

def calculate_trend(
    scores: List[float],
    timestamps: List[datetime],
    window_days: int = 7
) -> List[Dict]:
    """
    Calculate evaluation score trends over time.
    
    Args:
        scores: List of evaluation scores
        timestamps: List of evaluation timestamps
        window_days: Size of the rolling window in days
        
    Returns:
        List of dictionaries containing trend data points
    """
    if not scores or len(scores) != len(timestamps):
        return []
    
    # Sort scores by timestamp
    sorted_data = sorted(zip(timestamps, scores), key=lambda x: x[0])
    
    # Calculate moving average
    window = timedelta(days=window_days)
    trend_points = []
    
    for current_time, _ in sorted_data:
        # Get scores within the window
        window_scores = [
            score
            for time, score in sorted_data
            if current_time - window <= time <= current_time
        ]
        
        if window_scores:
            trend_points.append({
                "timestamp": current_time.isoformat(),
                "average_score": statistics.mean(window_scores),
                "sample_size": len(window_scores)
            })
    
    return trend_points
