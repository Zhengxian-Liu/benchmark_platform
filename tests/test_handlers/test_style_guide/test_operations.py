"""Tests for style guide operations."""

import pytest
import pandas as pd
import tempfile
import os

from handlers.style_guide import process_style_guide, apply_style_guide, StyleGuideError

def test_process_style_guide(db_session, sample_project):
    """Test processing a valid style guide Excel file."""
    # Create sample Excel data
    data = {
        'Chinese Name': ['小明', '小红'],
        'Gender': ['Male', 'Female'],
        'Age': ['20', '22']
    }
    df = pd.DataFrame(data)
    
    # Create temporary file
    fd, file_path = tempfile.mkstemp(suffix='.xlsx')
    os.close(fd)
    
    try:
        df.to_excel(file_path, index=False)
        
        # Process style guide
        guide = process_style_guide(
            db=db_session,
            file_path=file_path,
            project_name=sample_project,
            language_code='ZH',
            created_by='test'
        )
        
        # Verify the guide was created
        assert guide.project_name == sample_project
        assert guide.language_code == 'ZH'
        assert guide.version == 1
        assert guide.status == 'active'
        assert len(guide.entries) == 2
        
        # Verify entries
        assert '小明' in guide.entries
        assert guide.entries['小明']['Gender'] == 'Male'
        assert guide.entries['小明']['Age'] == '20'
        
    finally:
        os.remove(file_path)

def test_process_duplicate_style_guide(db_session, sample_project):
    """Test processing the same style guide file twice."""
    data = {
        'Chinese Name': ['小明'],
        'Gender': ['Male']
    }
    df = pd.DataFrame(data)
    fd, file_path = tempfile.mkstemp(suffix='.xlsx')
    os.close(fd)
    
    try:
        df.to_excel(file_path, index=False)
        
        # Process first time
        guide1 = process_style_guide(
            db=db_session,
            file_path=file_path,
            project_name=sample_project,
            language_code='ZH',
            created_by='test'
        )
        
        # Process same file again
        guide2 = process_style_guide(
            db=db_session,
            file_path=file_path,
            project_name=sample_project,
            language_code='ZH',
            created_by='test'
        )
        
        # Should return the same guide
        assert guide1.id == guide2.id
        assert guide1.version == guide2.version
        
    finally:
        os.remove(file_path)

def test_apply_style_guide():
    """Test applying style guide entries to prompt text."""
    style_guide_entries = {
        '小明': {
            'Gender': 'Male',
            'Age': '20'
        }
    }
    
    # Test with dict extra data
    prompt = "Please translate about {name}, who is {Gender} and {Age} years old."
    extra_data = {'extra': '小明 is a student'}
    result = apply_style_guide(prompt, extra_data, style_guide_entries)
    assert result == "Please translate about 小明, who is Male and 20 years old."
    
    # Test with string extra data
    extra_data = '小明 is a student'
    result = apply_style_guide(prompt, extra_data, style_guide_entries)
    assert result == "Please translate about 小明, who is Male and 20 years old."
    
    # Test with no matching names
    extra_data = 'No matching names here'
    result = apply_style_guide(prompt, extra_data, style_guide_entries)
    assert result == prompt  # Should return original text
