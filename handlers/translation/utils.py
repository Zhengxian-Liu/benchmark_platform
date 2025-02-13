"""Translation utility functions."""

import os
from typing import Dict

import anthropic
from anthropic import Anthropic

def get_llm_client() -> Anthropic:
    """
    Get a configured LLM client.
    
    Returns:
        Anthropic client instance
    
    Raises:
        ValueError: If API key is not configured
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable must be set")
    
    return Anthropic(api_key=api_key)

def translate_text(prompt_text: str, source_language: str, target_language: str) -> Dict[str, str]:
    """
    Translates text using Anthropic's Claude model.

    Args:
        prompt_text: The text to translate, with any additional prompt instructions
        source_language: Source language code
        target_language: Target language code

    Returns:
        Dictionary containing the translated text and model used
        
    Raises:
        ValueError: If API key is not configured
    """
    client = get_llm_client()

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt_text}
        ]
    )
    
    return {
        "translated_text": message.content[0].text,
        "model": message.model
    }
