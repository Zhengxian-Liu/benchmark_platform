# Translation Benchmark Platform

A platform for managing and evaluating translations across multiple projects and languages.

## Setup

1. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running Tests

Run all tests:
```bash
python -m pytest
```

Run specific test modules:
```bash
python -m pytest tests/test_handlers/test_project  # Run project module tests
```

## Example Usage

Try out the project module functionality:
```bash
python example_project_usage.py
```

This will:
1. Initialize the database
2. Create a sample translation session
3. Demonstrate project management functions
4. Show project statistics

## Project Structure

- `handlers/` - Core business logic modules
  - `project/` - Project management module
  - `style_guide/` - Style guide management module
  - `prompt/` - Prompt management module
  - `translation/` - Translation management module
  - `evaluation/` - Evaluation management module

- `models.py` - Database models
- `database.py` - Database configuration
- `main.py` - Main application entry point

## Available Projects and Languages

The following projects are configured:

- 原神: CHT, DE, EN, ES, FR, ID, IT, JA, KO, PT, RU, TR, VI
- RPG: CHT, DE, EN, ES, FR, ID, JA, KO, PT, RU, VI
- NAP: CHT, DE, EN, ES, FR, ID, JA, KO, PT, RU, VI
- 崩3: DE, EN, FR, ID, JP, KR, TH, VI
- NXX: EN, JP, KR

## Database Schema

Key models:
- Session: Translation session info
- SessionLanguage: Language settings for sessions
- SessionText: Text segments to translate
- Translation: Translation results
- EvaluationResult: Translation evaluations
- StyleGuide: Style guides for projects
