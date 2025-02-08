# Utility functions

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