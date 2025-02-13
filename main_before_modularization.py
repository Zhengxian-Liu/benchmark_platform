import gradio as gr
from fastapi import FastAPI, Request, Depends, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import models
from database import SessionLocal, engine, init_db
from prompts import get_prompts, create_prompt, update_prompt, get_prompt_versions, get_prompt_by_version_string
from evaluation import evaluate_translation
from style_guide import process_style_guide, apply_style_guide
from session_manager import (
    create_session,
    process_excel_file,
    get_project_sessions,
    get_session_texts,
    get_session_progress,
    update_session_status,
    create_session_texts,
    update_session_data,
    get_session
)
import utils
from datetime import datetime
import tempfile
import os
import json
import pandas as pd
from llm_integration import translate_text
from models import Translation, SessionText, SessionLanguage

# Initialize database with correct schema
init_db()

app = FastAPI()

# Helper functions for navigation
def get_all_project_names(db):
    return utils.get_project_names()

def get_session_languages(db, session_id):
    # Get the session to find its project
    session = get_session(db, session_id)
    if not session:
        return []
    # Get languages for this project
    return utils.get_language_codes(session.project_name)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create Gradio Interface
def create_gradio_interface():
    with gr.Blocks() as demo:
        gr.Markdown("# Prompt Benchmark Platform")

        # Hidden state to store the current session ID
        current_session_id = gr.State(None)

        with gr.Row():  # Main Row
            with gr.Column(scale=1):  # Left Column (Navigation)
                def generate_navigation_html():
                    db = SessionLocal()
                    try:
                        content = []
                        for project_name in get_all_project_names(db):
                            content.append(f'<details class="navigation-project">')
                            content.append(f'<summary>{project_name}</summary>')
                            
                            # Style Guides Section
                            content.append(f'<details class="navigation-section">')
                            content.append(f'<summary>Style Guides</summary>')
                            languages = utils.get_language_codes(project_name)
                            if languages:
                                for language in languages:
                                    content.append(f'<details class="navigation-language">')
                                    content.append(f'<summary>{language}</summary>')
                                    # Get style guides for this language
                                    style_guides = db.query(models.StyleGuide).filter(
                                        models.StyleGuide.project_name == project_name,
                                        models.StyleGuide.language_code == language,
                                        models.StyleGuide.status == "active"
                                    ).order_by(models.StyleGuide.version.desc()).all()
                                    
                                    if style_guides:
                                        content.append('<div class="navigation-content">')
                                        for guide in style_guides:
                                            content.append(f'Version {guide.version} ({guide.created_at.strftime("%Y-%m-%d %H:%M")})<br>')
                                        content.append('</div>')
                                    else:
                                        content.append('<div class="navigation-text">No style guide yet</div>')
                                    content.append('</details>')
                            else:
                                content.append('<div class="navigation-text">No languages configured</div>')
                            content.append('</details>')
                            
                            # Sessions Section
                            content.append(f'<details class="navigation-section">')
                            content.append(f'<summary>Sessions</summary>')
                            sessions = get_project_sessions(db, project_name)
                            if sessions:
                                for session in sessions:
                                    session_label = f"Session {session.id} ({session.created_at.strftime('%Y-%m-%d %H:%M')})"
                                    content.append(f'<details class="navigation-session">')
                                    content.append(f'<summary>{session_label}</summary>')
                                    if session.data and 'selected_languages' in session.data:
                                        languages = session.data['selected_languages']
                                        for language in languages:
                                            content.append(f'<details class="navigation-language">')
                                            content.append(f'<summary>{language}</summary>')
                                            content.append('<div class="navigation-content">')
                                            content.append('Prompt A (Ongoing Evaluation)<br>')
                                            content.append('Prompt B (Production Evaluation)')
                                            content.append('</div>')
                                            content.append('</details>')
                                    content.append('</details>')
                            else:
                                content.append('<div class="navigation-text">No sessions yet</div>')
                            content.append('</details>')
                            
                            content.append('</details>')  # Close project details
                        return "\n".join(content)
                    finally:
                        db.close()

                # Create navigation panel
                with gr.Column(scale=1, min_width=200, elem_id="navigation-panel"):
                    navigation_content = gr.HTML(
                        generate_navigation_html(),
                        elem_classes=["navigation-container"]
                    )
                
                # Add styling for the navigation panel
                gr.HTML("""
                    <style>
                    #navigation-panel {
                        background-color: var(--background-fill-primary);
                        border-right: 1px solid var(--border-color-primary);
                        padding: 10px;
                        height: 100vh;
                        position: fixed;
                        left: 0;
                        top: 0;
                        width: 250px;
                        overflow-y: auto;
                    }
                    .gradio-container {
                        margin-left: 250px;
                    }
                    .navigation-container {
                        font-family: system-ui, -apple-system, sans-serif;
                    }
                    .navigation-container details {
                        margin: 5px 0;
                    }
                    .navigation-container summary {
                        cursor: pointer;
                        padding: 5px;
                        border-radius: 4px;
                    }
                    .navigation-container summary:hover {
                        background-color: var(--background-fill-secondary);
                    }
                    .navigation-project > summary {
                        font-size: 1.2em;
                        font-weight: bold;
                        color: var(--body-text-color);
                    }
                    .navigation-section > summary {
                        font-size: 1.1em;
                        font-weight: 500;
                        color: var(--body-text-color);
                        margin-left: 15px;
                        padding-left: 10px;
                        border-left: 2px solid var(--border-color-primary);
                    }
                    .navigation-session > summary {
                        font-size: 1em;
                        color: var(--body-text-color);
                        margin-left: 30px;
                    }
                    .navigation-language > summary {
                        font-size: 0.9em;
                        color: var(--body-text-color);
                        margin-left: 45px;
                    }
                    .navigation-content {
                        margin-left: 45px;
                        font-size: 0.8em;
                        color: var(--body-text-color);
                        padding: 5px 0;
                    }
                    .navigation-text {
                        color: var(--body-text-color);
                        padding-left: 15px;
                        font-size: 0.9em;
                        margin: 5px 0;
                    }
                    .style-guide-table {
                        width: 100%;
                        max-width: 900px;
                        margin: 0 auto;
                    }
                    .style-guide-table table {
                        table-layout: fixed;
                    }
                    .style-guide-table td {
                        word-wrap: break-word;
                        max-width: 300px;
                        padding: 8px;
                    }
                    </style>
                """)

            with gr.Column(scale=4):  # Right Column (Content)
                # Content display area
                content_display = gr.Markdown("Select an item from the navigation panel")
                # Project Selection
                with gr.Row():
                    project_dropdown = gr.Dropdown(label="Select Project", choices=utils.get_project_names(), interactive=True)
                    session_dropdown = gr.Dropdown(label="Select Session", choices=[])
                    project_status = gr.Markdown(visible=False)  # For showing status messages

                # Session Management Tab
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

                # Style Guide Management Tab
                with gr.Tab("Style Guide Management"):
                    with gr.Row():
                        style_guide_project = gr.Dropdown(label="Project", choices=utils.get_project_names())
                        style_guide_language = gr.Dropdown(label="Language", choices=[])
                    
                    with gr.Row():
                      with gr.Column(visible=True) as upload_column:
                        style_guide_upload = gr.File(label="Upload Style Guide Excel")
                        style_guide_preview = gr.Dataframe(
                            label="Style Guide Preview",
                            wrap=True,
                            interactive=False,
                            visible=False,
                            type="pandas",
                            row_count=(5, "fixed"),
                            elem_classes=["style-guide-table"]
                        )
                        style_guide_save_button = gr.Button("Save Style Guide", visible=False)

                      with gr.Column(visible=False) as view_column:
                        style_guide_version_dropdown = gr.Dropdown(label="Select Version", choices=[])
                        view_style_guide_preview = gr.Dataframe(
                            label="Style Guide Preview",
                            wrap=True,
                            interactive=False,
                            visible=False,
                            type="pandas",
                            row_count=(5, "fixed"),
                            elem_classes=["style-guide-table"]
                        )

                    
                    style_guide_status = gr.Markdown(visible=False)
                    
                    with gr.Row():
                        style_guide_history = gr.DataFrame(
                            headers=["Version", "Created At", "File Name", "Created By"],
                            label="Version History",
                            wrap=True,
                            interactive=False,
                            visible=False
                        )

                # Prompt Management Tab with Language-Specific Sub-Tabs
                with gr.Tab("Prompt Management"):
                    prompt_tabs = gr.Tabs()
                    # Pre-create tabs for supported languages
                    language_prompts = {}  # Store components for each language
                    supported_languages = ["EN", "ES", "FR", "DE", "IT", "PT", "NL", "CHT", "JA", "KO"]  # Add all supported languages
                    
                    with prompt_tabs:
                        for lang in supported_languages:
                            with gr.Tab(f"{lang}") as tab:
                                language_prompts[lang] = {
                                    "tab": tab,
                                    "prompt_text": gr.Textbox(label=f"Prompt for {lang}", lines=5, visible=False),
                                    "save_button": gr.Button(f"Save {lang} Prompt", visible=False),
                                    "save_status": gr.Markdown(visible=False),
                                    "version_history": gr.Dataframe(
                                        headers=["Version", "Timestamp", "Changes"],
                                        label=f"Version History for {lang}",
                                        value=[],
                                        visible=False
                                    ),
                                    "prompt_version_dropdown": gr.Dropdown(
                                        label=f"Select {lang} Prompt Version",
                                        choices=[],
                                        visible=False
                                    )
                                }

                # Translation & Evaluation Tab with Language-Specific Sub-Tabs
                with gr.Tab("Translation & Evaluation"):
                    translation_tabs = gr.Tabs()
                    language_translations = {}  # Store components for each language
                    
                    with translation_tabs:
                        for lang in supported_languages:
                            with gr.Tab(f"{lang}") as tab:
                                language_translations[lang] = {
                                    "tab": tab,
                                    "current_prompt": gr.Markdown(label=f"Current {lang} Prompt", visible=False),
                                    "source_display": gr.Dataframe(
                                        headers=["Text ID", "Source Text", "Extra Data", f"{lang} Ground Truth", f"{lang} Translation", "Details"],
                                        label=f"Texts for {lang}",
                                        wrap=True,
                                        interactive=False,
                                        type="pandas",
                                        row_count=(1, "dynamic"),
                                        col_count=(6, "fixed"),
                                        visible=False
                                    ),
                                    "translate_button": gr.Button(f"Translate All to {lang}", visible=False),
                                    "evaluation_status": gr.Markdown(visible=False),
                                    "request_response": gr.Accordion("Request and Response", open=False, visible=False),
                                    "request_text": gr.Textbox(label=f"Request Prompt", lines=10, interactive=False, visible=False),
                                    "response_text": gr.Textbox(label=f"Response", lines=10, interactive=False, visible=False),
                                    "overall_score": gr.Number(label=f"Overall Score for {lang}", visible=False),
                                    "comments": gr.Textbox(label=f"Comments for {lang}", lines=3, visible=False),
                                    "save_evaluation": gr.Button(f"Save {lang} Evaluation", interactive=True, visible=False)
                                }

        # Event Handlers
        def update_session_list(project_name, current_id):
            db = SessionLocal()
            try:
                if not project_name:
                    return {
                        session_dropdown: gr.update(choices=[], value=None),
                        project_status: gr.update(visible=False),
                        current_session_id: None
                    }

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

                return {
                    session_dropdown: gr.update(choices=choices, value=selected_value),
                    project_status: gr.update(value=f"Selected project: {project_name}", visible=True),
                    current_session_id: current_id
                }
            finally:
                db.close()

        def handle_excel_upload(file, project_name):
            if not file or not project_name:
                return {
                    session_status: gr.update(
                        value="⚠️ Please select a project and upload a file",
                        visible=True
                    ),
                    create_session_btn: gr.update(interactive=False),
                    column_mapping_row: gr.update(visible=False),
                    excel_preview_display: gr.update(visible=False),
                    language_selection: gr.update(visible=False)
                }

            db = SessionLocal()
            try:
                file_path = file.name
                success, message, language_codes, detected_mappings = process_excel_file(db, file_path)
                
                if not success:
                    return {
                        session_status: gr.update(value=f"❌ Error: {message}", visible=True),
                        create_session_btn: gr.update(interactive=False),
                        column_mapping_row: gr.update(visible=False),
                        excel_preview_display: gr.update(visible=False),
                        language_selection: gr.update(visible=False)
                    }

                # Display preview and setup column mapping
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
                    
                    return {
                        session_status: gr.update(
                            value=f"✅ File uploaded. Detected languages: {', '.join(language_codes)}\nPlease verify column mappings.",
                            visible=True
                        ),
                        column_mapping_row: gr.update(visible=True),
                        source_col: gr.update(choices=all_columns, value=source_value),
                        textid_col: gr.update(choices=all_columns, value=textid_value),
                        extra_col: gr.update(choices=all_columns, value=extra_value),
                        excel_preview_display: gr.update(
                            value=preview_df,
                            visible=True
                        ),
                        language_selection: gr.update(choices=language_codes, value=[], visible=True),
                        create_session_btn: gr.update(interactive=can_create)
                    }
                except Exception as e:
                    return {
                        session_status: gr.update(value=f"❌ Error reading Excel: {str(e)}", visible=True),
                        create_session_btn: gr.update(interactive=False),
                        column_mapping_row: gr.update(visible=False),
                        excel_preview_display: gr.update(visible=False),
                        language_selection: gr.update(visible=False)
                    }
            finally:
                db.close()

        def create_session_handler(project_name, selected_languages, file, source_column, textid_column, extra_column):
            if not all([project_name, selected_languages, file, source_column, textid_column]):
                return {
                    session_status: gr.update(
                        value="⚠️ Please select a project, upload a file, select languages, and map required columns.",
                        visible=True
                    )
                }

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
                    return {
                        session_status: gr.update(value=f"❌ Error: {message}", visible=True)
                    }

                # Update session list
                sessions = get_project_sessions(db, project_name)
                session_data = [
                    [s.id, s.created_at.strftime("%Y-%m-%d %H:%M"), s.status,
                     f"{get_session_progress(db, s.id)['evaluated']}/{get_session_progress(db, s.id)['total']} texts"]
                    for s in sessions
                ]

                # Create base update dict with common components
                updates = {
                    session_status: gr.update(value="✅ Session created successfully", visible=True),
                    session_info: gr.update(value=session_data, headers=["Session ID", "Created At", "Status", "Progress"]),
                    session_dropdown: gr.update(choices=[f"Session {s.id} ({s.created_at.strftime('%Y-%m-%d %H:%M')})"
                                          for s in sessions],
                                 value=f"Session {session.id} ({session.created_at.strftime('%Y-%m-%d %H:%M')})"
                    ),
                    excel_preview_display: gr.update(visible=False),
                    language_selection: gr.update(visible=False),
                    column_mapping_row: gr.update(visible=False),
                    navigation_content: gr.update(value=generate_navigation_html()),
                    current_session_id: session.id
                }

                # Add language-specific component updates
                for lang in supported_languages:
                    is_selected = lang in selected_languages

                    # Prompt components
                    updates[language_prompts[lang]["prompt_text"]] = gr.update(value="", visible=is_selected)
                    updates[language_prompts[lang]["version_history"]] = gr.update(
                        value=[],
                        headers=["Version", "Timestamp", "Changes"],
                        visible=is_selected
                    )
                    updates[language_prompts[lang]["prompt_version_dropdown"]] = gr.update(choices=[], visible=is_selected)
                    updates[language_prompts[lang]["save_status"]] = gr.update(visible=is_selected)

                    # Translation components
                    updates[language_translations[lang]["current_prompt"]] = gr.update(value="No prompt saved yet", visible=is_selected)
                    updates[language_translations[lang]["source_display"]] = gr.update(
                        value=[],
                        headers=["Text ID", "Source Text", "Extra Data", f"{lang} Ground Truth", f"{lang} Translation", "Details"],
                        visible=is_selected
                    )
                    updates[language_translations[lang]["evaluation_status"]] = gr.update(visible=is_selected)

                return updates

            except Exception as e:
                return {
                    session_status: gr.update(value=f"❌ Error creating session: {str(e)}", visible=True)
                }
            finally:
                db.close()

        def translate_all_texts(project_name, session_info_str, lang_code):
            if not all([project_name, session_info_str, lang_code]):
                return {
                    language_translations[lang_code]["source_display"]: gr.update(value=[]),
                    language_translations[lang_code]["evaluation_status"]: gr.update(value="Missing required information", visible=True)
                }
            
            try:
                session_id = int(session_info_str.split(" ")[1])
            except (ValueError, IndexError):
                return {
                    language_translations[lang_code]["source_display"]: gr.update(value=[]),
                    language_translations[lang_code]["evaluation_status"]: gr.update(value="Invalid session information", visible=True)
                }
            
            db = SessionLocal()
            try:
                texts = get_session_texts(db, session_id)
                
                # Get the prompt for this language
                prompt = get_prompts(db, project_name, lang_code)
                if not prompt:
                    return {
                        language_translations[lang_code]["source_display"]: gr.update(value=[]),
                        language_translations[lang_code]["evaluation_status"]: gr.update(value=f"No prompt found for {lang_code}", visible=True)
                    }
                
                results = []
                for text in texts:
                    try:
                        # Format prompt with source text
                        prompt_text = prompt[0].prompt_text
                        if "{text}" in prompt_text:
                            prompt_text = prompt_text.replace("{text}", text.source_text)
                        else:
                            prompt_text = f"{prompt_text}\n\nText to translate: {text.source_text}"

                        # Translate
                        response = translate_text(
                            prompt_text,
                            "EN",
                            lang_code
                        )

                        # Save translation
                        translation = Translation(
                            session_text_id=text.id,
                            prompt_id=prompt[0].id,
                            translated_text=response["translated_text"],
                            metrics={}
                        )
                        db.add(translation)
                        
                        # Update session data
                        if 'translations' not in text.session.data:
                            text.session.data['translations'] = {}
                        if lang_code not in text.session.data['translations']:
                            text.session.data['translations'][lang_code] = {}
                        
                        text.session.data['translations'][lang_code][text.text_id] = {
                            'text': response["translated_text"],
                            'timestamp': datetime.utcnow().isoformat(),
                            'prompt_version': prompt[0].version
                        }
                        
                        results.append({
                            'text_id': text.text_id,
                            'translation': response["translated_text"]
                        })
                        
                    except Exception as e:
                        print(f"Translation error for {lang_code}: {str(e)}")
                        results.append({
                            'text_id': text.text_id,
                            'translation': f"Error: {str(e)}"
                        })
                
                db.commit()
                
                # Update UI for the language tab
                display_data = []
                for text in texts:
                    translation = next(
                        (r['translation'] for r in results
                         if r['text_id'] == text.text_id),
                        "Not translated"
                    )
                    display_data.append([
                        text.text_id,
                        text.source_text,
                        text.extra_data,
                        text.ground_truth.get(lang_code, ""),
                        translation,
                        "Details"
                    ])
                
                return {
                    language_translations[lang_code]["source_display"]: gr.update(value=display_data),
                    language_translations[lang_code]["evaluation_status"]: gr.update(value=f"Translation completed for {lang_code}", visible=True)
                }
                
            finally:
                db.close()

        def update_style_guide_languages(project_name):
            if not project_name:
                return {
                    style_guide_language: gr.update(choices=[], value=None),
                    style_guide_status: gr.update(visible=False)
                }
            
            language_codes = utils.get_language_codes(project_name)
            return {
                style_guide_language: gr.update(choices=language_codes, value=None),
                style_guide_status: gr.update(visible=False)
            }

        def handle_style_guide_upload(file, project_name, language_code):
            if not all([file, project_name, language_code]):
                return {
                    style_guide_status: gr.update(
                        value="⚠️ Please select a project and language before uploading",
                        visible=True
                    ),
                    style_guide_preview: gr.update(visible=False),
                    style_guide_history: gr.update(visible=False),
                    style_guide_save_button: gr.update(visible=False)
                }

            db = SessionLocal()
            try:
                # Process the uploaded style guide
                try:
                    new_guide = process_style_guide(
                        db=db,
                        file_path=file.name,
                        project_name=project_name,
                        language_code=language_code,
                        created_by="admin"  # TODO: Add proper user management
                    )

                    # Read and analyze Excel file
                    df = pd.read_excel(file.name)
                    headers = df.columns.tolist()
                    
                    # Show first 5 rows with all columns
                    preview_data = df.head().values.tolist()
                    
                    # Identify key columns for style guide
                    key_columns = {
                        'name': next((col for col in headers if 'name' in col.lower() or 'chinese' in col.lower()), None),
                        'gender': next((col for col in headers if 'gender' in col.lower() or 'sex' in col.lower()), None),
                        'style': next((col for col in headers if 'style' in col.lower() or 'tone' in col.lower()), None)
                    }
                    
                    # Create status message with column info
                    column_info = []
                    if key_columns['name']:
                        column_info.append(f"Name column: {key_columns['name']}")
                    if key_columns['gender']:
                        column_info.append(f"Gender column: {key_columns['gender']}")
                    if key_columns['style']:
                        column_info.append(f"Style column: {key_columns['style']}")
                    
                    other_columns = [col for col in headers if col not in key_columns.values() and col is not None]
                    if other_columns:
                        column_info.append(f"Additional columns: {', '.join(other_columns)}")

                    # Get version history
                    style_guides = db.query(models.StyleGuide).filter(
                        models.StyleGuide.project_name == project_name,
                        models.StyleGuide.language_code == language_code
                    ).order_by(models.StyleGuide.version.desc()).all()

                    history_data = [
                        [g.version, g.created_at.strftime("%Y-%m-%d %H:%M"),
                         g.file_name, g.created_by]
                        for g in style_guides
                    ]

                    # Create status message
                    status_msg = [
                        f"✅ Style guide uploaded successfully (Version {new_guide.version})",
                        "\nDetected columns:",
                        *[f"• {info}" for info in column_info]
                    ]
                    
                    return {
                        style_guide_status: gr.update(
                            value="\n".join(status_msg),
                            visible=True
                        ),
                        style_guide_preview: gr.update(
                            value=preview_data,
                            headers=headers,
                            visible=True
                        ),
                        style_guide_history: gr.update(
                            value=history_data,
                            visible=True
                        ),
                        style_guide_save_button: gr.update(visible=True)
                    }
                except Exception as e:
                    return {
                        style_guide_status: gr.update(
                            value=f"❌ Error processing file: {str(e)}",
                            visible=True
                        ),
                        style_guide_preview: gr.update(visible=False),
                        style_guide_history: gr.update(visible=False),
                        style_guide_save_button: gr.update(visible=False)
                    }
            finally:
                db.close()

        def handle_style_guide_save(file, project_name, language_code):
            if not all([file, project_name, language_code]):
                return {
                    style_guide_status: gr.update(
                        value="⚠️ Missing required information",
                        visible=True
                    )
                }

            db = SessionLocal()
            try:
                # Process and save the style guide
                new_guide = process_style_guide(
                    db=db,
                    file_path=file.name,
                    project_name=project_name,
                    language_code=language_code,
                    created_by="admin"  # TODO: Add proper user management
                )

                # Get updated version history
                style_guides = db.query(models.StyleGuide).filter(
                    models.StyleGuide.project_name == project_name,
                    models.StyleGuide.language_code == language_code
                ).order_by(models.StyleGuide.version.desc()).all()

                history_data = [
                    [g.version, g.created_at.strftime("%Y-%m-%d %H:%M"),
                     g.file_name, g.created_by]
                    for g in style_guides
                ]

                # Switch to view mode
                return {
                    style_guide_status: gr.update(
                        value=f"✅ Style guide saved successfully (Version {new_guide.version})",
                        visible=True
                    ),
                    upload_column: gr.update(visible=False),
                    view_column: gr.update(visible=True),
                    style_guide_version_dropdown: gr.update(
                        choices=[f"Version {g.version}" for g in style_guides],
                        value=f"Version {new_guide.version}",
                        visible=True
                    ),
                    navigation_content: gr.update(value=generate_navigation_html()),
                    style_guide_history: gr.update(
                        value=history_data,
                        visible=True
                    )
                }

            except Exception as e:
                return {
                    style_guide_status: gr.update(
                        value=f"❌ Error saving style guide: {str(e)}",
                        visible=True
                    )
                }
            finally:
                db.close()

        def load_existing_style_guides(project_name, language_code):
            if not all([project_name, language_code]):
                return {
                    style_guide_status: gr.update(visible=False),
                    upload_column: gr.update(visible=True),
                    view_column: gr.update(visible=False),
                    style_guide_history: gr.update(visible=False)
                }

            db = SessionLocal()
            try:
                # Get style guides for this project/language
                style_guides = db.query(models.StyleGuide).filter(
                    models.StyleGuide.project_name == project_name,
                    models.StyleGuide.language_code == language_code
                ).order_by(models.StyleGuide.version.desc()).all()

                if not style_guides:
                    return {
                        style_guide_status: gr.update(
                            value="No existing style guides found. Please upload a new one.",
                            visible=True
                        ),
                        upload_column: gr.update(visible=True),
                        view_column: gr.update(visible=False),
                        style_guide_history: gr.update(visible=False)
                    }

                # Get latest version
                latest = style_guides[0]
                
                # Load the data
                # Convert nested dict to DataFrame
                # Convert entries to DataFrame with all available columns
                entries_list = [{"Name": name, **attrs} for name, attrs in latest.entries.items()]
                data = pd.DataFrame(entries_list)
                # Use all available columns for preview
                available_columns = data.columns.tolist()
                
                history_data = [
                    [g.version, g.created_at.strftime("%Y-%m-%d %H:%M"),
                     g.file_name, g.created_by]
                    for g in style_guides
                ]

                # Return updates with data and headers
                return {
                    style_guide_status: gr.update(visible=False),
                    upload_column: gr.update(visible=False),
                    view_column: gr.update(visible=True),
                    style_guide_version_dropdown: gr.update(
                        choices=[f"Version {g.version}" for g in style_guides],
                        value=f"Version {latest.version}",
                        visible=True
                    ),
                    view_style_guide_preview: gr.update(
                        value=data.values.tolist(),
                        headers=available_columns,
                        visible=True
                    ),
                    style_guide_history: gr.update(
                        value=history_data,
                        visible=True
                    )
                }

            except Exception as e:
                return {
                    style_guide_status: gr.update(
                        value=f"❌ Error loading style guides: {str(e)}",
                        visible=True
                    ),
                    upload_column: gr.update(visible=True),
                    view_column: gr.update(visible=False),
                    style_guide_history: gr.update(visible=False)
                }
            finally:
                db.close()

        def view_style_guide(project_name, language_code, version_str):
            if not all([project_name, language_code, version_str]):
                return {
                    style_guide_status: gr.update(
                        value="⚠️ Missing required information",
                        visible=True
                    ),
                    view_style_guide_preview: gr.update(visible=False)
                }

            try:
                version = int(version_str.split(" ")[1])
            except (ValueError, IndexError):
                return {
                    style_guide_status: gr.update(
                        value="❌ Invalid version format",
                        visible=True
                    ),
                    view_style_guide_preview: gr.update(visible=False)
                }

            db = SessionLocal()
            try:
                # Get the specific version
                style_guide = db.query(models.StyleGuide).filter(
                    models.StyleGuide.project_name == project_name,
                    models.StyleGuide.language_code == language_code,
                    models.StyleGuide.version == version
                ).first()

                if not style_guide:
                    return {
                        style_guide_status: gr.update(
                            value=f"❌ Style guide version {version} not found",
                            visible=True
                        ),
                        view_style_guide_preview: gr.update(visible=False)
                    }

                # Load the data
                # Convert nested dict to DataFrame
                # Convert entries to DataFrame with all available columns
                entries_list = [{"Name": name, **attrs} for name, attrs in style_guide.entries.items()]
                data = pd.DataFrame(entries_list)
                # Use all available columns for preview
                available_columns = data.columns.tolist()

                # Return updates with data and headers
                return {
                    style_guide_status: gr.update(visible=False),
                    view_style_guide_preview: gr.update(
                        value=data.values.tolist(),
                        headers=available_columns,
                        visible=True
                    )
                }

            except Exception as e:
                return {
                    style_guide_status: gr.update(
                        value=f"❌ Error loading style guide: {str(e)}",
                        visible=True
                    ),
                    view_style_guide_preview: gr.update(visible=False)
                }
            finally:
                db.close()

        # Register style guide event handlers
        style_guide_project.change(
            update_style_guide_languages,
            inputs=[style_guide_project],
            outputs=[style_guide_language, style_guide_status]
        )

        style_guide_language.change(
            load_existing_style_guides,
            inputs=[style_guide_project, style_guide_language],
            outputs=[
                style_guide_status,
                upload_column,
                view_column,
                style_guide_version_dropdown,
                view_style_guide_preview,
                style_guide_history
            ]
        )

        style_guide_upload.upload(
            handle_style_guide_upload,
            inputs=[style_guide_upload, style_guide_project, style_guide_language],
            outputs=[
                style_guide_status,
                style_guide_preview,
                style_guide_history,
                style_guide_save_button
            ]
        )

        style_guide_save_button.click(
            handle_style_guide_save,
            inputs=[style_guide_upload, style_guide_project, style_guide_language],
            outputs=[
                style_guide_status,
                upload_column,
                view_column,
                style_guide_version_dropdown,
                navigation_content,
                style_guide_history
            ]
        )

        style_guide_version_dropdown.change(
            view_style_guide,
            inputs=[style_guide_project, style_guide_language, style_guide_version_dropdown],
            outputs=[style_guide_status, view_style_guide_preview]
        )

        def handle_session_selection(session_info_str):
            """Update current_session_id when a session is selected"""
            if not session_info_str:
                return {"current_session_id": None}
            try:
                session_id = int(session_info_str.split(" ")[1])
                return {"current_session_id": session_id}
            except (ValueError, IndexError):
                return {"current_session_id": None}

        # Register session selection handler
        session_dropdown.change(
            handle_session_selection,
            inputs=[session_dropdown],
            outputs=[current_session_id]
        )

        # Register project selection handler with current_session_id
        project_dropdown.change(
            update_session_list,
            inputs=[project_dropdown, current_session_id],
            outputs=[session_dropdown, project_status, current_session_id]
        )

        # Register excel upload handler
        excel_upload.upload(
            handle_excel_upload,
            inputs=[excel_upload, project_dropdown],
            outputs=[
                session_status,
                create_session_btn,
                column_mapping_row,
                source_col,
                textid_col,
                extra_col,
                excel_preview_display,
                language_selection
            ]
        )

        # Register session creation handler with column mappings
        create_session_btn.click(
            create_session_handler,
            inputs=[
                project_dropdown,
                language_selection,
                excel_upload,
                source_col,
                textid_col,
                extra_col
            ],
            outputs=[
                session_status,
                session_info,
                session_dropdown,
                excel_preview_display,
                language_selection,
                column_mapping_row,
                navigation_content,
                current_session_id,
                *[comp for lang in supported_languages for comp in [
                    language_prompts[lang]["prompt_text"],
                    language_prompts[lang]["version_history"],
                    language_prompts[lang]["prompt_version_dropdown"],
                    language_prompts[lang]["save_status"],
                    language_translations[lang]["current_prompt"],
                    language_translations[lang]["source_display"],
                    language_translations[lang]["evaluation_status"]
                ]]
            ]
        )

        def reload_session_state():
            """Load the initial session state"""
            db = SessionLocal()
            try:
                # Get most recent session from database
                latest_session = db.query(models.Session).order_by(models.Session.created_at.desc()).first()
                
                # Create base update dict with default values
                updates = {
                    project_dropdown: gr.update(value=None),
                    session_dropdown: gr.update(choices=[], value=None),
                    session_info: gr.update(value=[]),
                    project_status: gr.update(visible=False),
                    current_session_id: None
                }
                
                # Add language-specific component updates with default values
                for lang in supported_languages:
                    # Prompt components
                    updates[language_prompts[lang]["prompt_text"]] = gr.update(value="", visible=False)
                    updates[language_prompts[lang]["version_history"]] = gr.update(
                        value=[],
                        headers=["Version", "Timestamp", "Changes"],
                        visible=False
                    )
                    updates[language_prompts[lang]["prompt_version_dropdown"]] = gr.update(choices=[], visible=False)
                    updates[language_prompts[lang]["save_status"]] = gr.update(visible=False)

                    # Translation components
                    updates[language_translations[lang]["current_prompt"]] = gr.update(value="No prompt saved yet", visible=False)
                    updates[language_translations[lang]["source_display"]] = gr.update(
                        value=[],
                        headers=["Text ID", "Source Text", "Extra Data", f"{lang} Ground Truth", f"{lang} Translation", "Details"],
                        visible=False
                    )
                    updates[language_translations[lang]["evaluation_status"]] = gr.update(visible=False)

                if latest_session:
                    # Get all sessions for this project
                    sessions = get_project_sessions(db, latest_session.project_name)
                    session_data = [
                        [s.id, s.created_at.strftime("%Y-%m-%d %H:%M"), s.status,
                         f"{get_session_progress(db, s.id)['evaluated']}/{get_session_progress(db, s.id)['total']} texts"]
                        for s in sessions
                    ]

                    # Update with session state
                    updates.update({
                        project_dropdown: gr.update(value=latest_session.project_name),
                        session_dropdown: gr.update(
                            choices=[f"Session {s.id} ({s.created_at.strftime('%Y-%m-%d %H:%M')})" for s in sessions],
                            value=f"Session {latest_session.id} ({latest_session.created_at.strftime('%Y-%m-%d %H:%M')})"
                        ),
                        session_info: gr.update(value=session_data),
                        project_status: gr.update(value=f"Selected project: {latest_session.project_name}", visible=True),
                        current_session_id: latest_session.id
                    })

                    # Update language components based on session languages
                    if latest_session.data and 'selected_languages' in latest_session.data:
                        selected_languages = latest_session.data['selected_languages']
                        for lang in supported_languages:
                            is_selected = lang in selected_languages
                            # Update prompt components visibility
                            updates[language_prompts[lang]["prompt_text"]] = gr.update(visible=is_selected)
                            updates[language_prompts[lang]["version_history"]] = gr.update(visible=is_selected)
                            updates[language_prompts[lang]["prompt_version_dropdown"]] = gr.update(visible=is_selected)
                            updates[language_prompts[lang]["save_status"]] = gr.update(visible=is_selected)

                            # Update translation components visibility
                            updates[language_translations[lang]["current_prompt"]] = gr.update(visible=is_selected)
                            updates[language_translations[lang]["source_display"]] = gr.update(visible=is_selected)
                            updates[language_translations[lang]["evaluation_status"]] = gr.update(visible=is_selected)

                return updates
            finally:
                db.close()

        # Load initial state on page load
        demo.load(
            reload_session_state,
            outputs=[
                project_dropdown,
                session_dropdown,
                session_info,
                project_status,
                current_session_id,
                *[comp for lang in supported_languages for comp in [
                    language_prompts[lang]["prompt_text"],
                    language_prompts[lang]["version_history"],
                    language_prompts[lang]["prompt_version_dropdown"],
                    language_prompts[lang]["save_status"],
                    language_translations[lang]["current_prompt"],
                    language_translations[lang]["source_display"],
                    language_translations[lang]["evaluation_status"]
                ]]
            ]
        )

        return demo

if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    demo = create_gradio_interface()
    app = gr.mount_gradio_app(app, demo, path="/")
    uvicorn.run(app, host="0.0.0.0", port=args.port)
