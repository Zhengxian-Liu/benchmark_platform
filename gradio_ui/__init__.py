"""Gradio UI module for the Translation Benchmark Platform."""

from .navigation import create_navigation_panel
from .session_interface import (
    create_session_interface,
    update_session_list,
    handle_excel_upload,
    create_session_handler,
    handle_session_selection,
    reload_session_state
)
from .style_guide_interface import (
    create_style_guide_interface,
    update_style_guide_languages,
    handle_style_guide_upload,
    handle_style_guide_save,
    load_existing_style_guides,
    view_style_guide
)
from .prompt_interface import (
    create_prompt_interface,
    load_prompt_state,
    save_prompt,
    load_prompt_version
)
from .translation_interface import (
    create_translation_interface,
    translate_all_texts,
    update_translation_displays
)
from .styles import get_all_styles, get_navigation_styles, get_style_guide_styles

__all__ = [
    'create_navigation_panel',
    'create_session_interface',
    'update_session_list',
    'handle_excel_upload',
    'create_session_handler',
    'handle_session_selection',
    'reload_session_state',
    'create_style_guide_interface',
    'update_style_guide_languages',
    'handle_style_guide_upload',
    'handle_style_guide_save',
    'load_existing_style_guides',
    'view_style_guide',
    'create_prompt_interface',
    'load_prompt_state',
    'save_prompt',
    'load_prompt_version',
    'create_translation_interface',
    'translate_all_texts',
    'update_translation_displays',
    'get_all_styles',
    'get_navigation_styles',
    'get_style_guide_styles'
]
