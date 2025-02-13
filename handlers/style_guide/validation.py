"""Style guide validation functions."""

from typing import List, Optional, Tuple
import pandas as pd

def validate_style_guide_columns(df: pd.DataFrame) -> Tuple[bool, Optional[str], List[str]]:
    """
    Validate and detect columns in style guide Excel file.

    Args:
        df: Pandas DataFrame containing the style guide data

    Returns:
        Tuple containing:
        - bool: Whether validation passed
        - Optional[str]: Error message if validation failed, None otherwise
        - List[str]: List of available columns
    """
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
