"""Project configuration."""

# Define supported projects and their languages
PROJECT_CONFIG = {
    "原神": [
        "CHT", "DE", "EN", "ES", "FR",
        "ID", "IT", "JA", "KO", "PT",
        "RU", "TR", "VI"
    ],
    "RPG": [
        "CHT", "DE", "EN", "ES", "FR",
        "ID", "JA", "KO", "PT", "RU",
        "VI"
    ],
    "NAP": [
        "CHT", "DE", "EN", "ES", "FR",
        "ID", "JA", "KO", "PT", "RU",
        "VI"
    ],
    "崩3": [
        "DE", "EN", "FR", "ID", "JP",
        "KR", "TH", "VI"
    ],
    "NXX": [
        "EN", "JP", "KR"
    ]
}

# Project metadata
PROJECT_METADATA = {
    "原神": {
        "display_name": "原神",
        "description": "A popular open-world action RPG",
        "source_language": "CHT",
        "default_style_guide": "general_games",
    },
    "RPG": {
        "display_name": "RPG Project",
        "description": "A classic turn-based RPG",
        "source_language": "CHT",
        "default_style_guide": "general_games",
    },
    "NAP": {
        "display_name": "NAP Project",
        "description": "A narrative adventure game",
        "source_language": "CHT",
        "default_style_guide": "general_games",
    },
    "崩3": {
        "display_name": "崩坏：星穹铁道",
        "description": "A space fantasy RPG",
        "source_language": "CHT",
        "default_style_guide": "general_games",
    },
    "NXX": {
        "display_name": "NXX Project",
        "description": "A visual novel game",
        "source_language": "JP",
        "default_style_guide": "general_games",
    }
}

# Valid session statuses
VALID_SESSION_STATUSES = [
    "draft",
    "in_progress",
    "reviewing",
    "completed",
    "archived"
]
