"""Session management interface components and handlers."""

import gradio as gr
from typing import Dict, Any, List
import pandas as pd
from database import SessionLocal
import models
from handlers.session.operations import (
    create_session,
    process_excel_file,
    get_session_texts,
    get_session_progress,
    create_session_texts,
    get_session
)
from handlers.project.operations import get_project_sessions
import utils
from .navigation import generate_navigation_html

def create_session_interface() -> Dict[str, Any]:
    """Create session management interface components."""
    # Project Selection
    with gr.Row():
        project_dropdown = gr.Dropdown(
            label="Select Project",
            choices=utils.get_project_names(),
            interactive=True
        )
        session_dropdown = gr.Dropdown(
            label="Select Session",
            choices=[],
            interactive=True
        )
        project_status = gr.Markdown(visible=False)

    # Session Management Components
    with gr.Tab("Session Management"):
        with gr.Row():
            excel_upload = gr.File(label="Upload Source Excel")
            create_session_btn = gr.Button("Create New Session", interactive=False)
        session_status = gr.Markdown(visible=False)
        
        # Column mapping components
        with gr.Row(visible=False) as column_mapping_row:
            with gr.Column():
                source_col = gr.Dropdown(
                    label="Source Text Column",
                    choices=[],
                    interactive=True,
                    info="Column containing the text to translate"
                )
            with gr.Column():
                textid_col = gr.Dropdown(
                    label="Text ID Column",
                    choices=[],
                    interactive=True,
                    info="Column containing unique text identifiers"
                )
            with gr.Column():
                extra_col = gr.Dropdown(
                    label="Extra Data Column (Optional)",
                    choices=[],
                    interactive=True,
                    info="Column containing additional context"
                )
        
        # Session preview components
        excel_preview_display = gr.Dataframe(
            label="Excel File Preview",
            type="pandas",
            wrap=True,
            visible=False
        )
        language_selection = gr.CheckboxGroup(
            label="Select Languages",
            choices=[],
            value=[],
            visible=False
        )
        
        with gr.Row():
            session_info = gr.Dataframe(
                headers=["Session ID", "Created At", "Status", "Progress"],
                label="Sessions",
                type="array",
                value=[]
            )
    
    return {
        "project_dropdown": project_dropdown,
        "session_dropdown": session_dropdown,
        "project_status": project_status,
        "excel_upload": excel_upload,
        "create_session_btn": create_session_btn,
        "session_status": session_status,
        "column_mapping_row": column_mapping_row,
        "source_col": source_col,
        "textid_col": textid_col,
        "extra_col": extra_col,
        "excel_preview_display": excel_preview_display,
        "language_selection": language_selection,
        "session_info": session_info
    }

def update_session_list(project_name: str, current_id: int) -> tuple[Any, Any, int | None]:
    """Update session dropdown list when project is selected."""
    db = SessionLocal()
    try:
        if not project_name:
            return (
                gr.update(choices=[], value=None),  # session_dropdown
                gr.update(visible=False),  # project_status
                None  # current_session_id
            )

        sessions = get_project_sessions(db, project_name)
        choices = [
            f"Session {s.id} ({s.created_at.strftime('%Y-%m-%d %H:%M')})"
            for s in sessions
        ]

        # If we have a current session ID, try to select it in the dropdown
        selected_value = None
        if current_id:
            matching_choice = next(
                (choice for choice in choices if f"Session {current_id}" in choice),
                None
            )
            if matching_choice:
                selected_value = matching_choice

        return (
            gr.update(choices=choices, value=selected_value),  # session_dropdown
            gr.update(value=f"Selected project: {project_name}", visible=True),  # project_status
            current_id  # current_session_id
        )
    finally:
        db.close()

def handle_excel_upload(file: gr.File, project_name: str) -> tuple[Any, Any, Any, Any, Any, Any, Any, Any]:
    """Handle Excel file upload and validation.
    
    Returns:
        tuple: (session_status, create_session_btn, column_mapping_row, source_col,
               textid_col, extra_col, excel_preview_display, language_selection)
    """
    if not file or not project_name:
        return (
            gr.update(value="⚠️ Please select a project and upload a file", visible=True),  # session_status
            gr.update(interactive=False),  # create_session_btn
            gr.update(visible=False),  # column_mapping_row
            gr.update(choices=[], value=None),  # source_col
            gr.update(choices=[], value=None),  # textid_col
            gr.update(choices=[], value=None),  # extra_col
            gr.update(visible=False),  # excel_preview_display
            gr.update(visible=False)   # language_selection
        )

    db = SessionLocal()
    try:
        file_path = file.name
        success, message, language_codes, detected_mappings = process_excel_file(db, file_path)
        
        if not success:
            return (
                gr.update(value=f"❌ Error: {message}", visible=True),  # session_status
                gr.update(interactive=False),  # create_session_btn
                gr.update(visible=False),  # column_mapping_row
                gr.update(choices=[], value=None),  # source_col
                gr.update(choices=[], value=None),  # textid_col
                gr.update(choices=[], value=None),  # extra_col
                gr.update(visible=False),  # excel_preview_display
                gr.update(visible=False)   # language_selection
            )

        try:
            # Read Excel file and get preview
            df = pd.read_excel(file_path)
            preview_df = df.head()
            all_columns = df.columns.tolist()
            
            # Set detected mappings in dropdowns
            source_value = detected_mappings.get('source', None)
            textid_value = detected_mappings.get('textid', None)
            extra_value = detected_mappings.get('extra', None)
            
            # Enable create button if required mappings are detected
            can_create = bool(source_value and textid_value)
            
            return (
                gr.update(value=f"✅ File uploaded. Detected languages: {', '.join(language_codes)}\nPlease verify column mappings.", visible=True),  # session_status
                gr.update(interactive=can_create),  # create_session_btn
                gr.update(visible=True),  # column_mapping_row
                gr.update(choices=all_columns, value=source_value),  # source_col
                gr.update(choices=all_columns, value=textid_value),  # textid_col
                gr.update(choices=all_columns, value=extra_value),  # extra_col
                gr.update(value=preview_df, visible=True),  # excel_preview_display
                gr.update(choices=language_codes, value=[], visible=True)  # language_selection
            )
        except Exception as e:
            return (
                gr.update(value=f"❌ Error reading Excel: {str(e)}", visible=True),  # session_status
                gr.update(interactive=False),  # create_session_btn
                gr.update(visible=False),  # column_mapping_row
                gr.update(choices=[], value=None),  # source_col
                gr.update(choices=[], value=None),  # textid_col
                gr.update(choices=[], value=None),  # extra_col
                gr.update(visible=False),  # excel_preview_display
                gr.update(visible=False)   # language_selection
            )
    finally:
        db.close()

def create_session_handler(
    project_name: str,
    selected_languages: List[str],
    file: gr.File,
    source_column: str,
    textid_column: str,
    extra_column: str | None = None
) -> tuple[Any, Any, Any, Any, Any, Any, Any, Any]:
    """Create a new session with the provided parameters.
    
    Returns:
        tuple: (session_status, session_info, session_dropdown, excel_preview,
               language_selection, column_mapping_row, navigation_content, current_session_id)
    """
    if not all([project_name, selected_languages, file, source_column, textid_column]):
        return (
            gr.update(value="⚠️ Please select a project, upload a file, select languages, and map required columns.", visible=True),  # session_status
            gr.update(),  # session_info
            gr.update(),  # session_dropdown
            gr.update(visible=False),  # excel_preview
            gr.update(visible=False),  # language_selection
            gr.update(visible=False),  # column_mapping_row
            gr.update(),  # navigation_content
            None  # current_session_id
        )

    db = SessionLocal()
    try:
        # Create column mappings dict
        column_mappings = {
            'source': source_column,
            'textid': textid_column
        }
        if extra_column:
            column_mappings['extra'] = extra_column

        # Create new session with selected languages and mappings
        session = create_session(
            db,
            project_name,
            file.name,
            file.name,
            selected_languages,
            column_mappings
        )

        # Create session texts and languages
        success, message = create_session_texts(
            db,
            session.id,
            file.name,
            selected_languages
        )

        if not success:
            return (
                gr.update(value=f"❌ Error: {message}", visible=True),  # session_status
                gr.update(),  # session_info
                gr.update(),  # session_dropdown
                gr.update(visible=False),  # excel_preview
                gr.update(visible=False),  # language_selection
                gr.update(visible=False),  # column_mapping_row
                gr.update(),  # navigation_content
                None  # current_session_id
            )

        # Get updated session list
        sessions = get_project_sessions(db, project_name)
        session_data = [
            [s.id, s.created_at.strftime("%Y-%m-%d %H:%M"), s.status,
             f"{get_session_progress(db, s.id)['evaluated']}/{get_session_progress(db, s.id)['total']} texts"]
            for s in sessions
        ]

        return (
            gr.update(value="✅ Session created successfully", visible=True),  # session_status
            gr.update(value=session_data, headers=["Session ID", "Created At", "Status", "Progress"]),  # session_info
            gr.update(  # session_dropdown
                choices=[f"Session {s.id} ({s.created_at.strftime('%Y-%m-%d %H:%M')})"
                        for s in sessions],
                value=f"Session {session.id} ({session.created_at.strftime('%Y-%m-%d %H:%M')})"
            ),
            gr.update(visible=False),  # excel_preview_display
            gr.update(visible=False),  # language_selection
            gr.update(visible=False),  # column_mapping_row
            gr.update(value=generate_navigation_html()),  # navigation_content
            session.id  # current_session_id
        )

    except Exception as e:
        return (
            gr.update(value=f"❌ Error creating session: {str(e)}", visible=True),  # session_status
            gr.update(),  # session_info
            gr.update(),  # session_dropdown
            gr.update(visible=False),  # excel_preview_display
            gr.update(visible=False),  # language_selection
            gr.update(visible=False),  # column_mapping_row
            gr.update(),  # navigation_content
            None  # current_session_id
        )
    finally:
        db.close()

def handle_session_selection(session_info_str: str) -> tuple[int | None]:
    """Update current_session_id when a session is selected.
    
    Returns:
        tuple: A single-element tuple containing the current_session_id
    """
    if not session_info_str:
        return (None,)
    try:
        session_id = int(session_info_str.split(" ")[1])
        return (session_id,)
    except (ValueError, IndexError):
        return (None,)

def reload_session_state() -> tuple[Any, Any, Any, Any, int | None]:
    """Load the initial session state."""
    db = SessionLocal()
    try:
        # Get most recent session from database
        latest_session = db.query(models.Session).order_by(models.Session.created_at.desc()).first()
        
        if latest_session:
            # Get all sessions for this project
            sessions = get_project_sessions(db, latest_session.project_name)
            session_data = [
                [s.id, s.created_at.strftime("%Y-%m-%d %H:%M"), s.status,
                 f"{get_session_progress(db, s.id)['evaluated']}/{get_session_progress(db, s.id)['total']} texts"]
                for s in sessions
            ]
            
            return (
                gr.update(value=latest_session.project_name),  # project_dropdown
                gr.update(  # session_dropdown
                    choices=[f"Session {s.id} ({s.created_at.strftime('%Y-%m-%d %H:%M')})" for s in sessions],
                    value=f"Session {latest_session.id} ({latest_session.created_at.strftime('%Y-%m-%d %H:%M')})"
                ),
                gr.update(value=session_data),  # session_info
                gr.update(value=f"Selected project: {latest_session.project_name}", visible=True),  # project_status
                latest_session.id  # current_session_id
            )
        else:
            return (
                gr.update(value=None),  # project_dropdown
                gr.update(choices=[], value=None),  # session_dropdown
                gr.update(value=[]),  # session_info
                gr.update(visible=False),  # project_status
                None  # current_session_id
            )
    finally:
        db.close()
