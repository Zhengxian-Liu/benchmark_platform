import anthropic
from anthropic import Anthropic

def translate_text(prompt_text: str, source_language: str, target_language: str) -> str:
    """
    Translates text using Anthropic's Claude 3.5 Sonnet model.

    Args:
        prompt_text: The text to translate, with any additional prompt instructions.
        source_language: Source language code (not currently used, but kept for future use with AWS Bedrock).
        target_language: The target language code.

    Returns:
        A dictionary containing the translated text and the model used.
    """

    client = Anthropic(api_key="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") # API Key hardcoded for now

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