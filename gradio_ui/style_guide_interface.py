"""Style guide management interface components and handlers."""

import gradio as gr
from typing import Dict, Any
import pandas as pd
from database import SessionLocal
import models
from handlers.style_guide.operations import process_style_guide
from .navigation import generate_navigation_html
import utils

def create_style_guide_interface() -> Dict[str, Any]:
    """Create style guide management interface components."""
    with gr.Tab("Style Guide Management"):
        with gr.Row():
            style_guide_project = gr.Dropdown(
                label="Project",
                choices=utils.get_project_names()
            )
            style_guide_language = gr.Dropdown(
                label="Language",
                choices=[]
            )
        
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
                style_guide_version_dropdown = gr.Dropdown(
                    label="Select Version",
                    choices=[]
                )
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
                headers=["Version", "Created At", "Created By"],
                label="Version History",
                wrap=True,
                interactive=False,
                visible=False
            )

    return {
        "style_guide_project": style_guide_project,
        "style_guide_language": style_guide_language,
        "style_guide_upload": style_guide_upload,
        "style_guide_preview": style_guide_preview,
        "style_guide_save_button": style_guide_save_button,
        "view_column": view_column,
        "upload_column": upload_column,
        "style_guide_version_dropdown": style_guide_version_dropdown,
        "view_style_guide_preview": view_style_guide_preview,
        "style_guide_status": style_guide_status,
        "style_guide_history": style_guide_history
    }

def update_style_guide_languages(project_name: str) -> tuple[Any, Any]:
    """Update language dropdown when project is selected."""
    if not project_name:
        return (
            gr.update(choices=[], value=None),  # style_guide_language
            gr.update(visible=False)  # style_guide_status
        )
    
    language_codes = utils.get_language_codes(project_name)
    return (
        gr.update(choices=language_codes, value=None),  # style_guide_language
        gr.update(visible=False)  # style_guide_status
    )

def handle_style_guide_upload(file: gr.File, project_name: str, language_code: str) -> tuple[Any, Any, Any, Any]:
    """Handle style guide file upload and validation.
    
    Returns:
        tuple: (status, preview, history, save_button)
    """
    if not all([file, project_name, language_code]):
        return (
            gr.update(  # style_guide_status
                value="⚠️ Please select a project and language before uploading",
                visible=True
            ),
            gr.update(visible=False),  # style_guide_preview
            gr.update(visible=False),  # style_guide_history
            gr.update(visible=False)   # style_guide_save_button
        )

    db = SessionLocal()
    try:
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

        next_version = (style_guides[0].version + 1) if style_guides else 1

        history_data = [
            [g.version, g.created_at.strftime("%Y-%m-%d %H:%M"),
             g.created_by]
            for g in style_guides
        ]

        # Create status message
        status_msg = [
            f"✅ Style guide ready for upload (Will be Version {next_version})",
            "\nDetected columns:",
            *[f"• {info}" for info in column_info]
        ]
        
        return (
            gr.update(  # style_guide_status
                value="\n".join(status_msg),
                visible=True
            ),
            gr.update(  # style_guide_preview
                value=preview_data,
                headers=headers,
                visible=True
            ),
            gr.update(  # style_guide_history
                value=history_data,
                visible=True
            ),
            gr.update(visible=True)  # style_guide_save_button
        )
    except Exception as e:
        return (
            gr.update(  # style_guide_status
                value=f"❌ Error processing file: {str(e)}",
                visible=True
            ),
            gr.update(visible=False),  # style_guide_preview
            gr.update(visible=False),  # style_guide_history
            gr.update(visible=False)   # style_guide_save_button
        )
    finally:
        db.close()

def handle_style_guide_save(file: gr.File, project_name: str, language_code: str) -> tuple[Any, Any, Any, Any, Any, Any]:
    """Save the uploaded style guide.
    
    Returns:
        tuple: (status, upload_column, view_column, version_dropdown, navigation, history)
    """
    if not all([file, project_name, language_code]):
        return (
            gr.update(value="⚠️ Missing required information", visible=True),  # style_guide_status
            gr.update(visible=True),   # upload_column
            gr.update(visible=False),  # view_column
            gr.update(visible=False),  # style_guide_version_dropdown
            gr.update(visible=False),  # navigation_content
            gr.update(visible=False)   # style_guide_history
        )

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
             g.created_by]
            for g in style_guides
        ]

        # Switch to view mode
        return (
            gr.update(  # style_guide_status
                value=f"✅ Style guide saved successfully (Version {new_guide.version})",
                visible=True
            ),
            gr.update(visible=False),  # upload_column
            gr.update(visible=True),   # view_column
            gr.update(  # style_guide_version_dropdown
                choices=[f"Version {g.version}" for g in style_guides],
                value=f"Version {new_guide.version}",
                visible=True
            ),
            gr.update(value=generate_navigation_html()),  # navigation_content
            gr.update(value=history_data, visible=True)  # style_guide_history
        )

    except Exception as e:
        return (
            gr.update(value=f"❌ Error saving style guide: {str(e)}", visible=True),  # style_guide_status
            gr.update(visible=True),   # upload_column
            gr.update(visible=False),  # view_column
            gr.update(visible=False),  # style_guide_version_dropdown
            gr.update(visible=True),   # navigation_content
            gr.update(visible=False)   # style_guide_history
        )
    finally:
        db.close()

def load_existing_style_guides(project_name: str, language_code: str) -> tuple[Any, Any, Any, Any, Any, Any]:
    """Load existing style guides for the selected project and language.
    
    Returns:
        tuple: (status, upload_column, view_column, version_dropdown, preview, history)
    """
    if not all([project_name, language_code]):
        return (
            gr.update(visible=False),  # style_guide_status
            gr.update(visible=True),   # upload_column
            gr.update(visible=False),  # view_column
            gr.update(visible=False),  # style_guide_version_dropdown
            gr.update(visible=False),  # view_style_guide_preview
            gr.update(visible=False)   # style_guide_history
        )

    db = SessionLocal()
    try:
        # Get style guides for this project/language
        style_guides = db.query(models.StyleGuide).filter(
            models.StyleGuide.project_name == project_name,
            models.StyleGuide.language_code == language_code
        ).order_by(models.StyleGuide.version.desc()).all()

        if not style_guides:
            return (
                gr.update(  # style_guide_status
                    value="No existing style guides found. Please upload a new one.",
                    visible=True
                ),
                gr.update(visible=True),   # upload_column
                gr.update(visible=False),  # view_column
                gr.update(visible=False),  # style_guide_version_dropdown
                gr.update(visible=False),  # view_style_guide_preview
                gr.update(visible=False)   # style_guide_history
            )

        # Get latest version
        latest = style_guides[0]
        
        # Parse content from stored text
        data = pd.read_json(latest.content)
        available_columns = data.columns.tolist()
        
        history_data = [
            [g.version, g.created_at.strftime("%Y-%m-%d %H:%M"),
             g.created_by]
            for g in style_guides
        ]

        return (
            gr.update(visible=False),  # style_guide_status
            gr.update(visible=False),  # upload_column
            gr.update(visible=True),   # view_column
            gr.update(  # style_guide_version_dropdown
                choices=[f"Version {g.version}" for g in style_guides],
                value=f"Version {latest.version}",
                visible=True
            ),
            gr.update(  # view_style_guide_preview
                value=data.values.tolist(),
                headers=available_columns,
                visible=True
            ),
            gr.update(  # style_guide_history
                value=history_data,
                visible=True
            )
        )

    except Exception as e:
        return (
            gr.update(  # style_guide_status
                value=f"❌ Error loading style guides: {str(e)}",
                visible=True
            ),
            gr.update(visible=True),   # upload_column
            gr.update(visible=False),  # view_column
            gr.update(visible=False),  # style_guide_version_dropdown
            gr.update(visible=False),  # view_style_guide_preview
            gr.update(visible=False)   # style_guide_history
        )
    finally:
        db.close()

def view_style_guide(project_name: str, language_code: str, version_str: str) -> tuple[Any, Any]:
    """View a specific version of a style guide.
    
    Returns:
        tuple: (status, preview)
    """
    if not all([project_name, language_code, version_str]):
        return (
            gr.update(value="⚠️ Missing required information", visible=True),  # style_guide_status
            gr.update(visible=False)  # view_style_guide_preview
        )

    try:
        version = int(version_str.split(" ")[1])
    except (ValueError, IndexError):
        return (
            gr.update(value="❌ Invalid version format", visible=True),  # style_guide_status
            gr.update(visible=False)  # view_style_guide_preview
        )

    db = SessionLocal()
    try:
        # Get the specific version
        style_guide = db.query(models.StyleGuide).filter(
            models.StyleGuide.project_name == project_name,
            models.StyleGuide.language_code == language_code,
            models.StyleGuide.version == version
        ).first()

        if not style_guide:
            return (
                gr.update(value=f"❌ Style guide version {version} not found", visible=True),  # style_guide_status
                gr.update(visible=False)  # view_style_guide_preview
            )

        # Parse content from stored text
        data = pd.read_json(style_guide.content)
        available_columns = data.columns.tolist()

        return (
            gr.update(visible=False),  # style_guide_status
            gr.update(  # view_style_guide_preview
                value=data.values.tolist(),
                headers=available_columns,
                visible=True
            )
        )

    except Exception as e:
        return (
            gr.update(value=f"❌ Error loading style guide: {str(e)}", visible=True),  # style_guide_status
            gr.update(visible=False)  # view_style_guide_preview
        )
    finally:
        db.close()
