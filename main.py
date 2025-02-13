"""Main application entry point."""

import gradio as gr
import uvicorn
import argparse
from api import app
from database import init_db
from gradio_ui.navigation import create_navigation_panel
from gradio_ui.session_interface import (
    create_session_interface,
    update_session_list,
    handle_excel_upload,
    create_session_handler,
    handle_session_selection,
    reload_session_state
)
from gradio_ui.style_guide_interface import (
    create_style_guide_interface,
    update_style_guide_languages,
    handle_style_guide_upload,
    handle_style_guide_save,
    load_existing_style_guides,
    view_style_guide
)
from gradio_ui.prompt_interface import (
    create_prompt_interface,
    load_prompt_state,
    save_prompt,
    load_prompt_version
)
from gradio_ui.translation_interface import (
    create_translation_interface,
    translate_all_texts,
    update_translation_displays
)

# Initialize database with correct schema
init_db()

def create_gradio_interface():
    """Create the Gradio web interface."""
    with gr.Blocks() as demo:
        gr.Markdown("# Translation Benchmark Platform")

        # Hidden state for current session
        current_session_id = gr.State(None)

        with gr.Row():  # Main Row
            # Left Column (Navigation)
            with gr.Column(scale=1):
                navigation = create_navigation_panel()
            
            # Right Column (Content)
            with gr.Column(scale=4):
                # Get interface components
                session_components = create_session_interface()
                style_guide_components = create_style_guide_interface()
                prompt_components = create_prompt_interface()
                translation_components = create_translation_interface()

                # Register event handlers
                # Session Management
                session_components["project_dropdown"].change(
                    update_session_list,
                    inputs=[
                        session_components["project_dropdown"],
                        current_session_id
                    ],
                    outputs=[
                        session_components["session_dropdown"],
                        session_components["project_status"],
                        current_session_id
                    ]
                )
                
                session_components["excel_upload"].upload(
                    handle_excel_upload,
                    inputs=[
                        session_components["excel_upload"],
                        session_components["project_dropdown"]
                    ],
                    outputs=[
                        session_components["session_status"],
                        session_components["create_session_btn"],
                        session_components["column_mapping_row"],
                        session_components["source_col"],
                        session_components["textid_col"],
                        session_components["extra_col"],
                        session_components["excel_preview_display"],
                        session_components["language_selection"]
                    ]
                )
                
                session_components["create_session_btn"].click(
                    create_session_handler,
                    inputs=[
                        session_components["project_dropdown"],
                        session_components["language_selection"],
                        session_components["excel_upload"],
                        session_components["source_col"],
                        session_components["textid_col"],
                        session_components["extra_col"]
                    ],
                    outputs=[
                        session_components["session_status"],
                        session_components["session_info"],
                        session_components["session_dropdown"],
                        session_components["excel_preview_display"],
                        session_components["language_selection"],
                        session_components["column_mapping_row"],
                        navigation["navigation_content"],
                        current_session_id
                    ]
                )

                session_components["session_dropdown"].change(
                    handle_session_selection,
                    inputs=[session_components["session_dropdown"]],
                    outputs=[current_session_id]
                )

                # Style Guide Management
                style_guide_components["style_guide_project"].change(
                    update_style_guide_languages,
                    inputs=[style_guide_components["style_guide_project"]],
                    outputs=[
                        style_guide_components["style_guide_language"],
                        style_guide_components["style_guide_status"]
                    ]
                )

                style_guide_components["style_guide_language"].change(
                    load_existing_style_guides,
                    inputs=[
                        style_guide_components["style_guide_project"],
                        style_guide_components["style_guide_language"]
                    ],
                    outputs=[
                        style_guide_components["style_guide_status"],
                        style_guide_components["upload_column"],
                        style_guide_components["view_column"],
                        style_guide_components["style_guide_version_dropdown"],
                        style_guide_components["view_style_guide_preview"],
                        style_guide_components["style_guide_history"]
                    ]
                )

                style_guide_components["style_guide_upload"].upload(
                    handle_style_guide_upload,
                    inputs=[
                        style_guide_components["style_guide_upload"],
                        style_guide_components["style_guide_project"],
                        style_guide_components["style_guide_language"]
                    ],
                    outputs=[
                        style_guide_components["style_guide_status"],
                        style_guide_components["style_guide_preview"],
                        style_guide_components["style_guide_history"],
                        style_guide_components["style_guide_save_button"]
                    ]
                )

                style_guide_components["style_guide_save_button"].click(
                    handle_style_guide_save,
                    inputs=[
                        style_guide_components["style_guide_upload"],
                        style_guide_components["style_guide_project"],
                        style_guide_components["style_guide_language"]
                    ],
                    outputs=[
                        style_guide_components["style_guide_status"],
                        style_guide_components["upload_column"],
                        style_guide_components["view_column"],
                        style_guide_components["style_guide_version_dropdown"],
                        navigation["navigation_content"],
                        style_guide_components["style_guide_history"]
                    ]
                )

                style_guide_components["style_guide_version_dropdown"].change(
                    view_style_guide,
                    inputs=[
                        style_guide_components["style_guide_project"],
                        style_guide_components["style_guide_language"],
                        style_guide_components["style_guide_version_dropdown"]
                    ],
                    outputs=[
                        style_guide_components["style_guide_status"],
                        style_guide_components["view_style_guide_preview"]
                    ]
                )

                # Translation & Evaluation
                for lang, components in translation_components.items():
                    components["translate_button"].click(
                        translate_all_texts,
                        inputs=[
                            session_components["project_dropdown"],
                            session_components["session_dropdown"],
                            gr.State(lang)
                        ],
                        outputs=[
                            components["source_display"],
                            components["evaluation_status"],
                            components["request_text"],
                            components["response_text"],
                            components["request_response"],
                            components["overall_score"],
                            components["comments"],
                            components["save_evaluation"]
                        ]
                    )

        # Load initial state on page load
        demo.load(
            reload_session_state,
            outputs=[
                session_components["project_dropdown"],
                session_components["session_dropdown"],
                session_components["session_info"],
                session_components["project_status"],
                current_session_id
            ]
        )

        return demo

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    demo = create_gradio_interface()
    app = gr.mount_gradio_app(app, demo, path="/")
    uvicorn.run(app, host="0.0.0.0", port=args.port)
