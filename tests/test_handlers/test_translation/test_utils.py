"""Tests for translation utility functions."""

import os
import pytest
from handlers.translation.utils import translate_text

def test_translate_text_integration():
    """
    Test actual translation functionality.
    Skip if no API key is available.
    """
    if not os.environ.get('ANTHROPIC_API_KEY'):
        pytest.skip("ANTHROPIC_API_KEY not set - skipping integration test")
    
    result = translate_text(
        prompt_text="Translate this text to Spanish: Hello world",
        source_language="EN",
        target_language="ES"
    )
    
    assert isinstance(result, dict)
    assert "translated_text" in result
    assert "model" in result
    assert result["translated_text"]  # Not empty
    assert "claude" in result["model"].lower()  # Should be a Claude model
