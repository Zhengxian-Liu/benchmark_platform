# Implementation Plan: Add Evaluation Features

**Objective:** Implement the overall evaluation functionality, allowing users to provide a numerical score and comments for each translation.

**Steps:**

1.  **Modify Database Models (`models.py`):**
    *   Ensure the `EvaluationResult` model has fields for `score` (Integer) and `comments` (Text). It already has these, so no changes are needed here.

2.  **Update `evaluation.py`:**
    *   Create a function `evaluate_translation(db: Session, translation_id: int, overall_score: float, comments: str)` to store the evaluation results.

3.  **Modify `main.py`:**
    *   Add Gradio components for overall score (e.g., `gr.Number`) and comments (e.g., `gr.Textbox`) in the "Translation & Evaluation" tab.
    *   Create an event handler (e.g., a "Save Evaluation" button) that calls `evaluate_translation` with the input values and the `translation_id`.
    *   Update the UI to display saved evaluations (e.g., in a table or below the translated text).

4.  **(Optional) Implement Per-Segment Evaluation:**
    *   Add a mechanism to dynamically generate input fields for each segment.
    *   Modify the database model and `evaluation.py` to handle per-segment scores and comments.
    *   Update the UI to display per-segment evaluations.

5. **Switch to Code Mode:** Implement the changes.