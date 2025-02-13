"""Prompt management interface components and handlers."""

import gradio as gr
from typing import Dict, Any, List
from database import SessionLocal
import models
from handlers.prompt.operations import get_prompts, create_prompt, update_prompt, get_prompt_versions
import utils

SUPPORTED_LANGUAGES = ["EN", "ES", "FR", "DE", "IT", "PT", "NL", "CHT", "JA", "KO"]

def create_prompt_interface() -> Dict[str, Any]:
    """Create prompt management interface components."""
    components = {}
    with gr.Tab("Prompt Management"):
        prompt_tabs = gr.Tabs()
        # Pre-create tabs for supported languages
        with prompt_tabs:
            for lang in SUPPORTED_LANGUAGES:
                with gr.Tab(f"{lang}"):
                    prompt_text = gr.Textbox(
                        label=f"Prompt for {lang}",
                        lines=5,
                        visible=False
                    )
                    save_button = gr.Button(
                        f"Save {lang} Prompt",
                        visible=False
                    )
                    save_status = gr.Markdown(visible=False)
                    version_history = gr.Dataframe(
                        headers=["Version", "Timestamp", "Changes"],
                        label=f"Version History for {lang}",
                        value=[],
                        visible=False
                    )
                    prompt_version_dropdown = gr.Dropdown(
                        label=f"Select {lang} Prompt Version",
                        choices=[],
                        visible=False
                    )
                    
                    components[lang] = {
                        "prompt_text": prompt_text,
                        "save_button": save_button,
                        "save_status": save_status,
                        "version_history": version_history,
                        "prompt_version_dropdown": prompt_version_dropdown
                    }
    
    return components

def load_prompt_state(project_name: str, language: str) -> Dict[str, Any]:
    """Load the current state of prompts for a language."""
    if not project_name or not language:
        return {
            "prompt_text": gr.update(value="", visible=False),
            "save_button": gr.update(visible=False),
            "save_status": gr.update(visible=False),
            "version_history": gr.update(value=[], visible=False),
            "prompt_version_dropdown": gr.update(choices=[], visible=False)
        }

    db = SessionLocal()
    try:
        prompts = get_prompts(db, project_name, language)
        versions = get_prompt_versions(db, project_name, language)

        version_data = []
        if versions:
            version_data = [
                [v.version, v.created_at.strftime("%Y-%m-%d %H:%M"),
                 v.changes or "Initial version"]
                for v in versions
            ]

        current_prompt = prompts[0].prompt_text if prompts else ""
        version_choices = [f"Version {v.version}" for v in versions] if versions else []
        current_version = f"Version {versions[0].version}" if versions else None

        return {
            "prompt_text": gr.update(value=current_prompt, visible=True),
            "save_button": gr.update(visible=True),
            "save_status": gr.update(visible=False),
            "version_history": gr.update(
                value=version_data,
                headers=["Version", "Timestamp", "Changes"],
                visible=True
            ),
            "prompt_version_dropdown": gr.update(
                choices=version_choices,
                value=current_version,
                visible=bool(version_choices)
            )
        }
    except Exception as e:
        return {
            "prompt_text": gr.update(value="", visible=False),
            "save_button": gr.update(visible=False),
            "save_status": gr.update(value=f"Error loading prompts: {str(e)}", visible=True),
            "version_history": gr.update(value=[], visible=False),
            "prompt_version_dropdown": gr.update(choices=[], visible=False)
        }
    finally:
        db.close()

def save_prompt(
    project_name: str,
    language: str,
    prompt_text: str,
    changes: str = "Updated prompt"
) -> Dict[str, Any]:
    """Save a new prompt version."""
    if not all([project_name, language, prompt_text]):
        return {
            "save_status": gr.update(
                value="⚠️ Missing required information",
                visible=True
            )
        }

    db = SessionLocal()
    try:
        # Check if prompt exists
        existing_prompts = get_prompts(db, project_name, language)
        
        if existing_prompts:
            # Update existing prompt
            prompt = update_prompt(
                db,
                existing_prompts[0].id,
                prompt_text,
                changes
            )
        else:
            # Create new prompt
            prompt = create_prompt(
                db,
                project_name,
                language,
                prompt_text
            )

        # Get updated version history
        versions = get_prompt_versions(db, project_name, language)
        version_data = [
            [v.version, v.created_at.strftime("%Y-%m-%d %H:%M"),
             v.changes or "Initial version"]
            for v in versions
        ]

        return {
            "save_status": gr.update(
                value=f"✅ Prompt saved successfully (Version {prompt.version})",
                visible=True
            ),
            "version_history": gr.update(
                value=version_data,
                visible=True
            ),
            "prompt_version_dropdown": gr.update(
                choices=[f"Version {v.version}" for v in versions],
                value=f"Version {prompt.version}",
                visible=True
            )
        }

    except Exception as e:
        return {
            "save_status": gr.update(
                value=f"❌ Error saving prompt: {str(e)}",
                visible=True
            )
        }
    finally:
        db.close()

def load_prompt_version(project_name: str, language: str, version_str: str) -> Dict[str, Any]:
    """Load a specific version of a prompt."""
    if not all([project_name, language, version_str]):
        return {
            "prompt_text": gr.update(value="", visible=False),
            "save_status": gr.update(
                value="⚠️ Missing required information",
                visible=True
            )
        }

    try:
        version = int(version_str.split(" ")[1])
    except (ValueError, IndexError):
        return {
            "prompt_text": gr.update(value="", visible=False),
            "save_status": gr.update(
                value="❌ Invalid version format",
                visible=True
            )
        }

    db = SessionLocal()
    try:
        versions = get_prompt_versions(db, project_name, language)
        prompt_version = next(
            (v for v in versions if v.version == version),
            None
        )

        if not prompt_version:
            return {
                "prompt_text": gr.update(value="", visible=False),
                "save_status": gr.update(
                    value=f"❌ Prompt version {version} not found",
                    visible=True
                )
            }

        return {
            "prompt_text": gr.update(value=prompt_version.prompt_text, visible=True),
            "save_status": gr.update(visible=False)
        }

    except Exception as e:
        return {
            "prompt_text": gr.update(value="", visible=False),
            "save_status": gr.update(
                value=f"❌ Error loading prompt version: {str(e)}",
                visible=True
            )
        }
    finally:
        db.close()
