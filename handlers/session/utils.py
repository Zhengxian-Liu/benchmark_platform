"""Session utilities."""

from sqlalchemy.orm import Session
from models import Session as DbSession, SessionLanguage
from handlers.project.operations import get_project_sessions
from handlers.prompt.operations import get_prompts

def generate_sessions_section(db: Session, project_name: str) -> str:
    """Generate HTML for sessions navigation section."""
    content = []
    content.append(f'<details class="navigation-section">')
    content.append(f'<summary>Sessions</summary>')
    
    # Get sessions for project
    sessions = get_project_sessions(db, project_name)
    
    if sessions:
        for session in sessions:
            session_label = f"Session {session.id} ({session.created_at.strftime('%Y-%m-%d %H:%M')})"
            content.append(f'<details class="navigation-session">')
            content.append(f'<summary>{session_label}</summary>')
            
            # Show languages in session
            if session.data and 'selected_languages' in session.data:
                languages = session.data['selected_languages']
                for language in languages:
                    content.append(f'<details class="navigation-language">')
                    content.append(f'<summary>{language}</summary>')
                    content.append('<div class="navigation-content">')
                    
                    # Get prompts for this language
                    prompts = get_prompts(db, project_name, language)
                    if prompts:
                        for prompt in prompts:
                            content.append(
                                f'Prompt Version {prompt.version} ({prompt.created_at.strftime("%Y-%m-%d %H:%M")})<br>'
                            )
                    else:
                        content.append('No prompts available<br>')
                    
                    content.append('</div>')
                    content.append('</details>')
            
            content.append('</details>')  # Close session details
    else:
        content.append('<div class="navigation-text">No sessions yet</div>')
    
    content.append('</details>')  # Close sessions section
    return "\n".join(content)
