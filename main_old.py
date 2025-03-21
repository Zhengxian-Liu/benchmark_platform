import gradio as gr
from fastapi import FastAPI, Request, Depends, UploadFile, File
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
    update_session_status
)
import utils
from datetime import datetime
import tempfile
import os
import json
from llm_integration import translate_text
from models import Translation

# Initialize database with correct schema
init_db()

app = FastAPI()

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

        # Project Selection
        with gr.Row():
            project_dropdown = gr.Dropdown(label="Select Project", choices=utils.get_project_names())
            session_dropdown = gr.Dropdown(label="Select Session", choices=[])
            project_status = gr.Markdown(visible=False)  # For showing status messages

        # Session Management Tab
        with gr.Tab("Session Management"):
            with gr.Row():
                excel_upload = gr.File(label="Upload Source Excel")
                create_session_btn = gr.Button("Create New Session")
            session_status = gr.Markdown(visible=False)
            
            with gr.Row():
                session_info = gr.Dataframe(
                    headers=["Session ID", "Created At", "Status", "Progress"],
                    label="Sessions"
                )

        # Prompt Management Tab
        with gr.Tab("Prompt Management"):
            language_dropdown = gr.Dropdown(label="Select Language", choices=[])
            prompt_version_dropdown = gr.Dropdown(label="Select Prompt Version", choices=[]) # New dropdown
            with gr.Row():
                prompt_text = gr.Textbox(label="Prompt", lines=5)
                save_button = gr.Button("Save Prompt")
            save_status = gr.Markdown(visible=False)  # For showing save status
            version_history = gr.Dataframe(
                headers=["Version", "Timestamp", "Changes"],
                label="Version History",
                value=[]
            )

        # Translation & Evaluation Tab
        with gr.Tab("Translation & Evaluation"):
            current_prompt_display = gr.Markdown(label="Current Prompt") # Added display for the current prompt
            with gr.Column():
                source_display = gr.Dataframe(
                    headers=["Text ID", "Source Text", "Extra Data", "Translated Text", "Details", "Translation ID"],
                    label="Source Texts",
                    wrap=True,
                    interactive=False,
                    type="pandas",
                    row_count=(1, "dynamic"),
                    col_count=(6, "fixed")
                )
                translate_all_button = gr.Button("Translate All")

            #translated_text = gr.Textbox(label="Translated Text", lines=5) # Display translation, removed for now
            evaluation_status = gr.Markdown(visible=False)

            # Accordion for displaying request/response
            request_response_accordion = gr.Accordion("Request and Response", open=False)
            with request_response_accordion:
                request_textbox = gr.Textbox(label="Request Prompt", lines=10, interactive=False)
                response_textbox = gr.Textbox(label="Response", lines=10, interactive=False)

            with gr.Row():
                overall_score_input = gr.Number(label="Overall Score")
                comments_input = gr.Textbox(label="Comments", lines=3)
            save_evaluation_button = gr.Button("Save Evaluation", interactive=True)

        # Event Handlers
        def update_session_list(project_name):
            db = SessionLocal()
            try:
                if not project_name:
                    return {
                        session_dropdown: gr.update(choices=[], value=None),
                        project_status: gr.update(visible=False)
                    }

                sessions = get_project_sessions(db, project_name)
                choices = [
                    f"Session {s.id} ({s.created_at.strftime('%Y-%m-%d %H:%M')})"
                    for s in sessions
                ]

                return {
                    session_dropdown: gr.update(choices=choices, value=None),
                    project_status: gr.update(value=f"Selected project: {project_name}", visible=True)
                }
            finally:
                db.close()

        def handle_excel_upload(file, project_name):
            if not file or not project_name:
                return {
                    session_status: gr.update(
                        value="⚠️ Please select a project and upload a file",
                        visible=True
                    )
                }

            db = SessionLocal()
            try:
                # Access file path directly from the Gradio File object
                file_path = file.name

                # Create new session
                session = create_session(db, project_name, file.name)
                
                # Process Excel file
                success, message = process_excel_file(
                    db,
                    file_path,
                    session.id,
                    utils.get_language_codes(project_name)
                )

                if not success:
                    return {
                        session_status: gr.update(
                            value=f"❌ Error: {message}",
                            visible=True
                        )
                    }

                # Update session list
                sessions = get_project_sessions(db, project_name)
                session_data = [
                    [s.id, s.created_at.strftime("%Y-%m-%d %H:%M"), s.status, 
                     f"{get_session_progress(db, s.id)['evaluated']}/{get_session_progress(db, s.id)['total']} texts"]
                    for s in sessions
                ]

                return {
                    session_status: gr.update(
                        value="✅ Session created successfully",
                        visible=True
                    ),
                    session_info: session_data,
                    session_dropdown: gr.update(choices=[f"Session {s.id} ({s.created_at.strftime('%Y-%m-%d %H:%M')})" for s in sessions])
                }

            except Exception as e:
                return {
                    session_status: gr.update(
                        value=f"❌ Error: {str(e)}",
                        visible=True
                    )
                }
            finally:
                db.close()

        def update_prompt_versions(project_name, language_code):
            print(f"update_prompt_versions called with project: {project_name}, language: {language_code}")
            if project_name and language_code:
                db = SessionLocal()
                prompt_versions = get_prompt_versions(db, project_name, language_code)
                db.close()
                print(f"Prompt versions found: {prompt_versions}")
                return {prompt_version_dropdown: gr.update(choices=prompt_versions, value = prompt_versions[0] if prompt_versions else None)}
            else:
                print("project_name or language_code is None")
                return {prompt_version_dropdown: gr.update(choices=[], value=None)}  # Clear choices if project/language not selected

        def update_language_choices(project_name):
            print(f"update_language_choices called with: {project_name}")
            languages = utils.get_language_codes(project_name)
            return {
                language_dropdown: gr.update(choices=languages, value=None),
                prompt_version_dropdown: gr.update(choices=[], value=None) #clear prompt version
            }
        
        def load_session_texts(session_info_str: str):
            if not session_info_str:
                return gr.update(value=[])
            
            try:
                session_id = int(session_info_str.split(" ")[1]) # Extract session ID
            except (ValueError, IndexError):
                return gr.update(value=[])
            
            db = SessionLocal()
            try:
                texts = get_session_texts(db, session_id)
                data = []
                for text in texts:
                    data.append([text.text_id, text.source_text, text.extra_data, "", "Details", text.translation_id if hasattr(text, "translation_id") else ""])

                return gr.update(value=data)
            finally:
                db.close()
                
        def update_current_prompt(project_name: str, language_code: str, version_string: str):
            print(f"update_current_prompt called with project: {project_name}, language: {language_code}, version: {version_string}")
            if project_name and language_code and version_string:
                db = SessionLocal()
                prompt = get_prompt_by_version_string(db, project_name, language_code, version_string)
                db.close()
                if prompt:
                    return {
                        current_prompt_display: gr.update(
                            value=f"**Project:** {project_name}, **Language:** {language_code}, **Version:** {version_string}\\n\\n**Prompt:** {prompt.prompt_text}",
                            visible=True
                        )
                    }
                else:
                    return {
                        current_prompt_display: gr.update(
                            value=f"**Project:** {project_name}, **Language:** {language_code}, **Version:** Error loading prompt",
                            visible=True
                        )
                    }
            else:
                return {
                    current_prompt_display: gr.update(
                        value=f"**Project:**, **Language:**, **Version:** ",
                        visible=False
                    )
                }

        def save_prompt(project_name, language_code, prompt_text):
            print(f"Project: {project_name}, Language: {language_code}, Prompt: {prompt_text}")
            if not all([project_name, language_code, prompt_text]):
                return {
                    save_status: gr.update(
                        value="⚠️ Please fill in all fields (Project, Language, and Prompt)",
                        visible=True
                    ),
                    version_history: []
                }

            # Create a new database session
            db = SessionLocal()
            try:
                # Get existing prompts for this project/language
                existing_prompts = get_prompts(db, project_name, language_code)
                
                if not existing_prompts:
                    # Create new prompt
                    prompt = create_prompt(db, project_name, language_code, prompt_text, "Initial version")
                else:
                    # Update existing prompt
                    prompt = update_prompt(db, existing_prompts[0].id, prompt_text, "Updated version")

                # Get version history
                versions = get_prompt_versions(db, project_name, language_code)
                version_data = []
                for v in versions:
                    version_number = int(v.split(" ")[1])
                    timestamp = datetime.strptime(v.split(" (")[1][:-1], "%Y-%m-%d %H:%M")
                    version_data.append([version_number, timestamp, ""])

                return {
                    save_status: gr.update(value="✅ Prompt saved successfully!", visible=True),
                    version_history: version_data,
                    prompt_version_dropdown: gr.update(choices=versions, value=versions[0] if versions else None)
                }
            except Exception as e:
                return {
                    save_status: gr.update(value=f"❌ Error saving prompt: {str(e)}", visible=True),
                    version_history: [],
                    prompt_version_dropdown: gr.update(choices=[])
                }

        # Register all event handlers in order
        project_dropdown.change(
            update_session_list,
            inputs=[project_dropdown],
            outputs=[session_dropdown, project_status]
        )

        project_dropdown.change(
            update_language_choices,
            inputs=[project_dropdown],
            outputs=[language_dropdown, prompt_version_dropdown]
        )

        language_dropdown.change(
            update_prompt_versions,
            inputs=[project_dropdown, language_dropdown],
            outputs=[prompt_version_dropdown]
        )

        # Update current prompt display when project, language, or version changes
        project_dropdown.change(
            update_current_prompt,
            inputs=[project_dropdown, language_dropdown, prompt_version_dropdown],
            outputs=[current_prompt_display]
        )
        language_dropdown.change(
            update_current_prompt,
            inputs=[project_dropdown, language_dropdown, prompt_version_dropdown],
            outputs=[current_prompt_display]
        )
        prompt_version_dropdown.change(
            update_current_prompt,
            inputs=[project_dropdown, language_dropdown, prompt_version_dropdown],
            outputs=[current_prompt_display]
        )

        create_session_btn.click(
            handle_excel_upload,
            inputs=[excel_upload, project_dropdown],
            outputs=[session_status, session_info, session_dropdown]
        )
        
        session_dropdown.change(
            load_session_texts,
            inputs=[session_dropdown],
            outputs=[source_display]
        )

        save_button.click(
            save_prompt,
            inputs=[project_dropdown, language_dropdown, prompt_text],
            outputs=[save_status, version_history, prompt_version_dropdown]
        )

        def translate_all_texts(project_name, language_code, session_info_str, prompt_version):
            if not all([project_name, language_code, session_info_str, prompt_version]):
                return gr.update(value=[])
            
            try:
                session_id = int(session_info_str.split(" ")[1])
            except (ValueError, IndexError):
                return gr.update(value=[])
            
            db = SessionLocal()
            try:
                texts = get_session_texts(db, session_id)
                data = []
                for text in texts:
                    # Get the prompt text for translation
                    prompt = get_prompt_by_version_string(db, project_name, language_code, prompt_version)
                    if not prompt:
                        continue
                        
                    try:
                        # Get the prompt text and combine with source text
                        prompt_text = prompt.prompt_text
                        if "{text}" in prompt_text:
                            prompt_text = prompt_text.replace("{text}", text.source_text)
                        else:
                            prompt_text = f"{prompt_text}\n\nText to translate: {text.source_text}"

                        # Translate the text
                        response = translate_text(
                            prompt_text,  # The complete prompt with text to translate
                            "EN",  # Source language is English
                            language_code  # Target language from dropdown
                        )
                        # Save translation to database
                        translation = Translation(
                            session_text_id=text.id,
                            prompt_id=prompt.id,
                            translated_text=response["translated_text"],
                            metrics={}  # We'll store other metrics here if needed in the future
                        )
                        db.add(translation)
                        db.commit()
                    except Exception as e:
                        print(f"Translation error: {str(e)}")
                        translated_text = f"Error: {str(e)}"
                        response = None

                    # Add to display data
                    data.append([
                        text.text_id,
                        text.source_text,
                        text.extra_data,
                        response["translated_text"] if response else "Error: Translation failed",
                        "Details",
                        translation.id if 'translation' in locals() else ""
                    ])

                return gr.update(value=data), gr.update(interactive=True)
            finally:
                db.close()

        def handle_save_evaluation(session_info_str, overall_score, comments, translation_id):
            print(f"Saving evaluation for session: {session_info_str}, score: {overall_score}, comments: {comments}, translation_id: {translation_id}")

            if not session_info_str or overall_score is None or translation_id == -1:
                return gr.update(value="⚠️ Please fill in all evaluation fields (Overall Score and Comments) and select a text.", visible=True)

            try:
                session_id = int(session_info_str.split(" ")[1])
            except (ValueError, IndexError):
                return gr.update(value="⚠️ Invalid session selected.", visible=True)

            db = SessionLocal()
            try:
                evaluate_translation(db, [translation_id], overall_score, comments)
                return gr.update(value="✅ Evaluation saved successfully!", visible=True)
            except Exception as e:
                return gr.update(value=f"❌ Error saving evaluation: {str(e)}", visible=True)
            finally:
                db.close()

        translation_id_state = gr.State(-1)

        def show_request_response(project_name, language_code, prompt_version, session_info_str, data: gr.SelectData):
            if not session_info_str:
                return [
                    gr.update(value="No session selected", visible=True),
                    gr.update(value="No session selected", visible=True),
                    gr.update(visible=True),
                    -1
                ]
            
            try:
                session_id = int(session_info_str.split(" ")[1])
            except (ValueError, IndexError):
                return [
                    gr.update(value="Invalid session information", visible=True),
                    gr.update(value="Invalid session information", visible=True),
                    gr.update(visible=True),
                    -1
                ]
            if not all([project_name, language_code, prompt_version]):
                return [
                    gr.update(value="", visible=True),
                    gr.update(value="", visible=True),
                    gr.update(visible=True),
                    -1
                ]

            db = SessionLocal()
            try:
                prompt = get_prompt_by_version_string(db, project_name, language_code, prompt_version)
                if prompt:
                    # Get the row data from the source display using indices
                    try:
                        row_idx = data.index[0]  # Get the row index from the click event
                        texts = get_session_texts(db, session_id)  # Get all texts for the current session
                        text = texts[row_idx]  # Get the specific text that was clicked
                        
                        text_id = text.text_id
                        source_text = text.source_text
                        
                        # Get the translation record from the database
                        translation = db.query(Translation)\
                            .filter(Translation.session_text_id == text.id)\
                            .order_by(Translation.timestamp.desc())\
                            .first()
                        
                        # Even if no translation is found, we'll still show the request
                        translated_text = translation.translated_text if translation else None
                        translation_id = translation.id if translation else -1
                    except Exception as e:
                        print(f"Error accessing row data: {str(e)}")
                        return [
                            gr.update(value="Error accessing data", visible=True),
                            gr.update(value="Error accessing data", visible=True),
                            gr.update(visible=True),
                            -1
                        ]

                    # Format the complete prompt with the source text
                    complete_prompt = prompt.prompt_text
                    if source_text:
                        if "{text}" in complete_prompt:
                            complete_prompt = complete_prompt.replace("{text}", source_text)
                        else:
                            complete_prompt = f"{complete_prompt}\n\nText to translate: {source_text}"

                    # Format the request JSON as it's sent to the model
                    request_json = {
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": 1024,
                        "messages": [
                            {"role": "user", "content": complete_prompt}
                        ]
                    }
                    
                    # Format the response data based on whether translation exists
                    if translation:
                        # Ensure proper encoding of translated text
                        response_data = {
                            "translated_text": translation.translated_text,
                            "model": "claude-3-5-sonnet-20241022",
                            "timestamp": translation.timestamp.isoformat(),
                            "metrics": translation.metrics if translation.metrics else {},
                            "translation_id": translation.id
                        }
                    else:
                        response_data = {
                            "message": "No translation found for this text",
                            "timestamp": datetime.now().isoformat()
                        }

                    # Convert response data to JSON with ensure_ascii=False to properly handle non-ASCII characters
                    response_json = json.dumps(response_data, indent=2, ensure_ascii=False)
                    return [
                        gr.update(value=json.dumps(request_json, indent=2), visible=True),
                        gr.update(value=response_json, visible=True),
                        gr.update(visible=True),
                        translation_id
                    ]

                else:
                    return [
                        gr.update(value="Error loading prompt", visible=True),
                        gr.update(value="", visible=True),
                        gr.update(visible=True),
                        -1
                    ]
            finally:
                db.close()

        translate_all_button.click(
            translate_all_texts,
            inputs=[project_dropdown, language_dropdown, session_dropdown, prompt_version_dropdown],
            outputs=[source_display, save_evaluation_button]
        )

        source_display.select(
            show_request_response,
            inputs=[project_dropdown, language_dropdown, prompt_version_dropdown, session_dropdown],
            outputs=[request_textbox, response_textbox, request_response_accordion, translation_id_state]
        )

        session_dropdown.change(
            load_session_texts,
            inputs=[session_dropdown],
            outputs=[source_display]
        )
      
        save_evaluation_button.click(
            handle_save_evaluation,
            inputs=[session_dropdown, overall_score_input, comments_input, translation_id_state],
            outputs=[evaluation_status]
        )

        return demo

# Mount Gradio app in FastAPI
gradio_app = create_gradio_interface()
app = gr.mount_gradio_app(app, gradio_app, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)