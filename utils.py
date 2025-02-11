import re
import unicodedata

# Utility functions

def sanitize_string(text: str) -> str:
    """
    Sanitize Chinese text by:
    1. Normalizing Unicode characters
    2. Removing control characters
    3. Trimming whitespace
    4. Ensuring consistent spacing
    """
    if not text:
        return ""
        
    # Normalize Unicode characters (especially for Chinese text)
    text = unicodedata.normalize('NFKC', str(text))
    
    # Remove control characters but keep newlines and tabs
    text = ''.join(char for char in text if unicodedata.category(char)[0] != "C"
                  or char in ('\n', '\t'))
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Trim whitespace
    return text.strip()

def get_project_names():
    return ["原神", "RPG", "NAP", "崩3", "NXX"]

def get_language_codes(project_name):
    project_languages = {
        "原神": ["CHT", "DE", "EN", "ES", "FR", "ID", "IT", "JA", "KO", "PT", "RU", "TR", "VI"],
        "RPG": ["CHT", "DE", "EN", "ES", "FR", "ID", "JA", "KO", "PT", "RU", "VI"],
        "NAP": ["CHT", "DE", "EN", "ES", "FR", "ID", "JA", "KO", "PT", "RU", "VI"],
        "崩3": ["DE", "EN", "FR", "ID", "JP", "KR", "TH", "VI"],
        "NXX": ["EN", "JP", "KR"]
    }
    return project_languages.get(project_name, [])