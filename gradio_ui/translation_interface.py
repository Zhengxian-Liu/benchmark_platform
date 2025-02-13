"""Translation and evaluation interface components and handlers."""

import gradio as gr
from typing import Dict, Any
from datetime import datetime
import pandas as pd
from database import SessionLocal
from handlers.session.operations import get_session_texts, get_session
from handlers.prompt.operations import get_prompts
from handlers.translation.operations import translate_text
from models import Translation
from .navigation import generate_navigation_html

SUPPORTED_LANGUAGES = ["EN", "ES", "FR", "DE", "IT", "PT", "NL", "CHT", "JA", "KO"]

def create_translation_interface() -> Dict[str, Any]:
    """Create translation and evaluation interface components."""
    components = {}
    with gr.Tab("Translation & Evaluation"):
        translation_tabs = gr.Tabs()
        with translation_tabs:
            for lang in SUPPORTED_LANGUAGES:
                with gr.Tab(f"{lang}"):
                    current_prompt = gr.Markdown(
                        label=f"Current {lang} Prompt",
                        visible=False
                    )
                    source_display = gr.Dataframe(
                        headers=[
                            "Text ID",
                            "Source Text",
                            "Extra Data",
                            f"{lang} Ground Truth",
                            f"{lang} Translation",
                            "Details"
                        ],
                        label=f"Texts for {lang}",
                        wrap=True,
                        interactive=False,
                        type="pandas",
                        row_count=(1, "dynamic"),
                        col_count=(6, "fixed"),
                        visible=False
                    )
                    translate_button = gr.Button(
                        f"Translate All to {lang}",
                        visible=False
                    )
                    evaluation_status = gr.Markdown(visible=False)
                    
                    with gr.Accordion("Request and Response", open=False, visible=False) as request_response:
                        request_text = gr.Textbox(
                            label=f"Request Prompt",
                            lines=10,
                            interactive=False,
                            visible=False
                        )
                        response_text = gr.Textbox(
                            label=f"Response",
                            lines=10,
                            interactive=False,
                            visible=False
                        )
                    
                    overall_score = gr.Number(
                        label=f"Overall Score for {lang}",
                        visible=False
                    )
                    comments = gr.Textbox(
                        label=f"Comments for {lang}",
                        lines=3,
                        visible=False
                    )
                    save_evaluation = gr.Button(
                        f"Save {lang} Evaluation",
                        interactive=True,
                        visible=False
                    )
                    
                    components[lang] = {
                        "current_prompt": current_prompt,
                        "source_display": source_display,
                        "translate_button": translate_button,
                        "evaluation_status": evaluation_status,
                        "request_text": request_text,
                        "response_text": response_text,
                        "request_response": request_response,
                        "overall_score": overall_score,
                        "comments": comments,
                        "save_evaluation": save_evaluation
                    }
    
    return components

def translate_all_texts(
    project_name: str,
    session_info_str: str,
    lang_code: str
) -> Dict[str, Any]:
    """Translate all texts in a session to the specified language."""
    if not all([project_name, session_info_str, lang_code]):
        return {
            "source_display": gr.update(value=[]),
            "evaluation_status": gr.update(
                value="Missing required information",
                visible=True
            )
        }
    
    try:
        session_id = int(session_info_str.split(" ")[1])
    except (ValueError, IndexError):
        return {
            "source_display": gr.update(value=[]),
            "evaluation_status": gr.update(
                value="Invalid session information",
                visible=True
            )
        }
    
    db = SessionLocal()
    try:
        texts = get_session_texts(db, session_id)
        
        # Get the prompt for this language
        prompt = get_prompts(db, project_name, lang_code)
        if not prompt:
            return {
                "source_display": gr.update(value=[]),
                "evaluation_status": gr.update(
                    value=f"No prompt found for {lang_code}",
                    visible=True
                )
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
                    "EN",  # Source language is always English in this case
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
                    'translation': response["translated_text"],
                    'request': prompt_text,
                    'response': response["raw_response"]
                })
                
            except Exception as e:
                print(f"Translation error for {lang_code}: {str(e)}")
                results.append({
                    'text_id': text.text_id,
                    'translation': f"Error: {str(e)}",
                    'request': prompt_text,
                    'response': str(e)
                })
        
        db.commit()
        
        # Update UI for the language tab
        display_data = []
        for text in texts:
            translation_result = next(
                (r for r in results if r['text_id'] == text.text_id),
                {'translation': "Not translated", 'request': "", 'response': ""}
            )
            display_data.append([
                text.text_id,
                text.source_text,
                text.extra_data,
                text.ground_truth.get(lang_code, ""),
                translation_result['translation'],
                "Details"
            ])
        
        return {
            "source_display": gr.update(value=display_data),
            "evaluation_status": gr.update(
                value=f"Translation completed for {lang_code}",
                visible=True
            ),
            "request_text": gr.update(
                value=results[0]['request'] if results else "",
                visible=True
            ),
            "response_text": gr.update(
                value=results[0]['response'] if results else "",
                visible=True
            ),
            "request_response": gr.update(visible=True),
            "overall_score": gr.update(visible=True),
            "comments": gr.update(visible=True),
            "save_evaluation": gr.update(visible=True)
        }
        
    finally:
        db.close()

def update_translation_displays(project_name: str, session_id: int) -> Dict[str, Any]:
    """Update translation displays for all languages."""
    if not all([project_name, session_id]):
        return {}

    db = SessionLocal()
    try:
        session = get_session(db, session_id)
        if not session or 'selected_languages' not in session.data:
            return {}

        updates = {}
        for lang in SUPPORTED_LANGUAGES:
            if lang not in session.data['selected_languages']:
                continue

            # Get texts and translations
            texts = get_session_texts(db, session_id)
            prompt = get_prompts(db, project_name, lang)

            # Update components
            display_data = []
            for text in texts:
                translation = None
                if ('translations' in session.data and
                    lang in session.data['translations'] and
                    text.text_id in session.data['translations'][lang]):
                    translation = session.data['translations'][lang][text.text_id]['text']

                display_data.append([
                    text.text_id,
                    text.source_text,
                    text.extra_data,
                    text.ground_truth.get(lang, ""),
                    translation or "Not translated yet",
                    "Details"
                ])

            updates.update({
                f"{lang}_current_prompt": gr.update(
                    value=prompt[0].prompt_text if prompt else "No prompt saved yet",
                    visible=True
                ),
                f"{lang}_source_display": gr.update(
                    value=display_data,
                    visible=True
                ),
                f"{lang}_translate_button": gr.update(visible=True),
                f"{lang}_evaluation_status": gr.update(visible=True)
            })

        return updates

    finally:
        db.close()
