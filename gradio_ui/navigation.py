"""Navigation panel components and functions."""

import gradio as gr
from typing import Dict, Any
from database import SessionLocal
from handlers.session.operations import get_session
from handlers.project.operations import get_project_sessions
from handlers.style_guide.utils import generate_style_guide_section
from handlers.session.utils import generate_sessions_section
import utils
from .styles import get_navigation_styles

def generate_navigation_html() -> str:
    """Generate HTML for the navigation panel."""
    db = SessionLocal()
    try:
        content = []
        for project_name in utils.get_project_names():
            # Project section
            content.append(f'<details class="navigation-project">')
            content.append(f'<summary>{project_name}</summary>')
            
            # Add style guides section
            content.append(generate_style_guide_section(db, project_name))
            
            # Add sessions section
            content.append(generate_sessions_section(db, project_name))
            
            content.append('</details>')  # Close project details
        return "\n".join(content)
    finally:
        db.close()

def create_navigation_panel() -> Dict[str, Any]:
    """Create the navigation panel components."""
    with gr.Column(scale=1, min_width=200, elem_id="navigation-panel"):
        navigation_content = gr.HTML(
            generate_navigation_html(),
            elem_classes=["navigation-container"]
        )
        
        # Add navigation styling
        gr.HTML(f"<style>{get_navigation_styles()}</style>")
    
    return {
        "navigation_content": navigation_content
    }
