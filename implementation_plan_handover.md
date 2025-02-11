# Implementation Plan Handoff: Prompt Benchmark Platform

This document outlines the current state of the Prompt Benchmark Platform project and provides guidance for the next developer taking over.

## Project Overview

The goal of this project is to create a platform for experimenting with and evaluating different prompts for LLM translation tasks. It's built using Gradio for the frontend, a Python backend (FastAPI), and PostgreSQL for data persistence. The platform allows users to:

*   Manage projects and languages.
*   Create, edit, and version prompts.
*   Integrate with a style guide (uploaded as an Excel file) to dynamically replace placeholders in prompts.
*   Invoke an LLM (currently intended to be AWS Bedrock's Claude 3.5 Haiku) to perform translations.
*   Evaluate translations using both automated metrics and human evaluation.
*   View and analyze evaluation results.

## Current Status (2025-02-11)

The project is currently in a partially implemented state.  Significant progress has been made on the backend and database structure, and the basic Gradio UI is laid out. However, there are several critical areas that require further development and debugging.

**Files:**

*   `main.py`: The main application file (Gradio interface and FastAPI server).
*   `models.py`: Defines the database models (SQLAlchemy).
*   `database.py`: Handles database connection and initialization.
*   `prompts.py`: Contains functions for managing prompts (CRUD operations).
*   `evaluation.py`:  Intended for evaluation logic (currently minimal).
*   `style_guide.py`:  Handles style guide processing (parsing Excel, validation, dynamic replacement).
*   `session_manager.py`: Manages session data (from uploaded Excel files).
*   `llm_integration.py`:  Handles communication with the LLM (currently contains a placeholder `translate_text` function).
*   `utils.py`: Utility functions (e.g., getting project names, language codes).
*   `requirements.txt`: Lists project dependencies.
*   `alembic.ini`, `migrations/`:  Database migration files (using Alembic).
*   `Prompt_Benchmark_Platform_PRD.md`: The project requirements document.
* `sample_texts.xlsx`: sample data file
* `Sample_style_guid_KR.xlsx`: sample style guide

**Completed:**

*   **Database Schema:** The database schema (using SQLAlchemy and PostgreSQL) is fully defined and implemented.  Migrations are set up using Alembic. The following tables exist:
    *   `users` (simplified for internal use)
    *   `projects`
    *   `languages`
    *   `prompts` (with versioning)
    *   `sessions`
    *   `session_texts` (stores the text data from uploaded Excel files)
    *   `session_languages` (stores selected languages for a session)
    *   `translations` (stores LLM outputs and evaluation results)
    *   `style_guides` (stores parsed style guide data)
*   **Backend Logic:**
    *   Functions for creating, reading, updating, and deleting (CRUD operations) for most database models are implemented in their respective Python files (e.g., `prompts.py`, `session_manager.py`, `style_guide.py`).
    *   Excel file parsing (for session data and style guides) is implemented using `pandas`.
    *   Style guide validation (checking for required columns) is implemented.
    *   File hash computation for style guide versioning is implemented.
    *   Session creation (including parsing and storing data from Excel) is partially implemented.
*   **Gradio Interface (Basic Structure):**
    *   The main layout with tabs for "Session Management," "Style Guide Management," "Prompt Management," and "Translation & Evaluation" is set up.
    *   Project and language selection dropdowns are implemented.
    *   Basic components for file uploads, previews, and status messages are in place.
    *   Dynamic navigation panel generation is implemented (but needs to be reliably updated).

**Incomplete/Needs Work:**

*   **Navigation Updates:** The navigation panel does *not* reliably update after creating sessions or uploading/saving style guides. This is a high-priority issue. The `generate_navigation_html` function exists, but the event handlers are not correctly updating the `navigation_content` component in all cases.
*   **Style Guide Save/View:**
    *   The "Save Style Guide" button has been added, and the UI switches to a "view" mode, but the version dropdown and loading of existing style guides are not fully functional. The `load_existing_style_guides` and `view_style_guide` functions are placeholders and need to be completed.
*   **Prompt Management:** This entire section is largely unimplemented.  All CRUD operations for prompts, versioning, and the diff view need to be built.
*   **LLM Integration:** The `translate_text` function in `llm_integration.py` is a placeholder.  Integration with AWS Bedrock (or any other LLM) needs to be implemented.
*   **Translation & Evaluation:** This section is mostly unimplemented.  The UI components are placeholders.  This includes:
    *   Triggering translation requests.
    *   Displaying translation results.
    *   Implementing automated evaluation metrics.
    *   Implementing the human evaluation interface (scoring, annotations).
    *   Saving evaluation results.
*   **Dynamic Tag Replacement:** The `apply_style_guide` function in `style_guide.py` exists, but it's not fully integrated into the prompt processing pipeline. The logic for matching entries in the "Extra" column and replacing tags in the prompt needs to be thoroughly tested and connected to the UI.
*   **Session Deletion:**  No functionality for deleting/archiving sessions has been implemented.
*   **Error Handling:** Error handling is basic and needs to be made more robust and user-friendly.
*   **Loading Indicators:**  There are no loading indicators for asynchronous operations (file uploads, LLM calls), which can lead to a poor user experience.
*   **Testing:**  There are currently no unit tests or integration tests.

## Immediate Next Steps (Prioritized)

1.  **Fix Navigation:**  This is the most critical issue to address first. Ensure that `generate_navigation_html` is called and `navigation_content` is updated correctly after *any* change that affects the navigation structure (session creation, style guide upload/save/delete).  Carefully review the event handlers in `main.py` and ensure they are correctly updating the necessary components.
2.  **Complete Style Guide Save/View:**
    *   Implement the `handle_style_guide_save` function to correctly switch between the upload/view modes and update the navigation.
    *   Implement the `load_existing_style_guides` function to load and display existing style guides when the project/language is changed.
    *   Implement the `view_style_guide` function to load and display a specific version of a style guide when selected from the dropdown.
    *   Ensure that the style guide data persists across page refreshes. This likely involves correctly loading the data from the database when the Gradio interface is initialized.
3.  **Implement Prompt Management:** Start with basic CRUD operations for prompts, and then add versioning.
4.  **Integrate LLM:** Implement the `translate_text` function in `llm_integration.py` to communicate with the chosen LLM (AWS Bedrock Claude 3.5 Haiku).

## Debugging Notes

*   **Diff Application Issues:** I encountered repeated issues with the `apply_diff` tool. It often failed to find matching lines, even when the changes seemed correct. This was likely due to ongoing changes in the file and the tool's sensitivity to line numbers. Creating a new file (`main_fixed.py`) was a workaround, but a more robust solution is needed. Consider using a different diffing library or approach if this continues to be a problem.
*   **Gradio Component Updates:** Pay close attention to the `outputs` of Gradio event handlers. Make sure you are updating *all* necessary components to reflect changes in the application state.  Use `gr.update()` to modify component properties (e.g., `visible`, `value`, `choices`).
*   **Database Interactions:** Always use a `try...finally` block with `db.close()` to ensure that database sessions are closed, even if errors occur.

## Recommendations

*   **Prioritize Navigation:**  Fixing the navigation updates is crucial for usability.
*   **Incremental Development:**  Work on one feature at a time, testing thoroughly after each change.
*   **Version Control:**  Use Git to track changes and create branches for new features.
*   **Error Handling:**  Implement robust error handling and provide informative messages to the user.
*   **Testing:**  Write unit tests and integration tests to ensure code quality and prevent regressions.

This handover document should provide a solid foundation for the next developer to continue building the Prompt Benchmark Platform. Good luck!