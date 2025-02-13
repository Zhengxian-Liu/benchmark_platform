"""Tests for style guide utility functions."""

import pytest
import tempfile
import os

from handlers.style_guide.utils import compute_file_hash

def test_compute_file_hash():
    """Test file hash computation."""
    # Create a temporary file with known content
    fd, file_path = tempfile.mkstemp()
    try:
        with os.fdopen(fd, 'w') as temp_file:
            temp_file.write("test content")
        
        # Compute hash
        hash1 = compute_file_hash(file_path)
        
        # Verify it's a valid SHA-256 hash (64 characters)
        assert len(hash1) == 64
        assert all(c in '0123456789abcdef' for c in hash1)
        
        # Compute hash again and verify it's the same
        hash2 = compute_file_hash(file_path)
        assert hash1 == hash2
        
    finally:
        os.remove(file_path)

def test_compute_file_hash_different_content():
    """Test that different content produces different hashes."""
    # Create two temporary files with different content
    fd1, file_path1 = tempfile.mkstemp()
    fd2, file_path2 = tempfile.mkstemp()
    
    try:
        with os.fdopen(fd1, 'w') as temp_file1:
            temp_file1.write("content 1")
        with os.fdopen(fd2, 'w') as temp_file2:
            temp_file2.write("content 2")
        
        hash1 = compute_file_hash(file_path1)
        hash2 = compute_file_hash(file_path2)
        
        # Verify hashes are different
        assert hash1 != hash2
        
    finally:
        os.remove(file_path1)
        os.remove(file_path2)

def test_compute_file_hash_empty_file():
    """Test hash computation for empty file."""
    fd, file_path = tempfile.mkstemp()
    try:
        # File is created empty by default
        hash_value = compute_file_hash(file_path)
        
        # Verify we get a valid hash
        assert len(hash_value) == 64
        assert all(c in '0123456789abcdef' for c in hash_value)
        
    finally:
        os.remove(file_path)

def test_compute_file_hash_nonexistent_file():
    """Test hash computation for non-existent file."""
    with pytest.raises(FileNotFoundError):
        compute_file_hash("nonexistent_file.txt")
