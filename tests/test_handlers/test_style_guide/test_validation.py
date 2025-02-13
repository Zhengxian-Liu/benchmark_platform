"""Tests for style guide validation functions."""

import pytest
import pandas as pd

from handlers.style_guide import validate_style_guide_columns

def test_validate_valid_columns():
    """Test validation with valid column structure."""
    data = {
        'Chinese Name': ['小明', '小红'],
        'Gender': ['Male', 'Female'],
        'Age': ['20', '22']
    }
    df = pd.DataFrame(data)
    
    success, error_msg, columns = validate_style_guide_columns(df)
    assert success
    assert error_msg is None
    assert set(columns) == {'Chinese Name', 'Gender', 'Age'}

def test_validate_missing_name_column():
    """Test validation when name column is missing."""
    data = {
        'Gender': ['Male', 'Female'],
        'Age': ['20', '22']
    }
    df = pd.DataFrame(data)
    
    success, error_msg, columns = validate_style_guide_columns(df)
    assert not success
    assert "Could not find a name column" in error_msg
    assert len(columns) == 0

def test_validate_empty_name_column():
    """Test validation when name column exists but is empty."""
    data = {
        'Chinese Name': [None, None],
        'Gender': ['Male', 'Female']
    }
    df = pd.DataFrame(data)
    
    success, error_msg, columns = validate_style_guide_columns(df)
    assert not success
    assert "Name column" in error_msg
    assert "empty" in error_msg
    assert set(columns) == {'Chinese Name', 'Gender'}

def test_validate_alternative_name_columns():
    """Test validation with different name column variations."""
    test_cases = [
        {'Name': ['Test']},
        {'Chinese': ['测试']},
        {'名前': ['テスト']},
        {'이름': ['테스트']}
    ]
    
    for data in test_cases:
        df = pd.DataFrame(data)
        success, error_msg, _ = validate_style_guide_columns(df)
        assert success, f"Failed with column name: {list(data.keys())[0]}"
        assert error_msg is None
