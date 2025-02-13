"""Style guide utilities."""

from datetime import datetime
from sqlalchemy.orm import Session
from models import StyleGuide
from sqlalchemy import select

def generate_style_guide_section(db: Session, project_name: str) -> str:
    """Generate HTML for style guide navigation section."""
    content = []
    content.append(f'<details class="navigation-section">')
    content.append(f'<summary>Style Guides</summary>')
    
    # Get languages with style guides - only select necessary columns
    style_guides = (
        db.query(
            StyleGuide.language_code,
            StyleGuide.version,
            StyleGuide.created_at
        )
        .filter(StyleGuide.project_name == project_name)
        .order_by(StyleGuide.language_code, StyleGuide.version.desc())
        .all()
    )
    
    if style_guides:
        # Group by language
        by_language = {}
        for guide in style_guides:
            if guide.language_code not in by_language:
                by_language[guide.language_code] = []
            by_language[guide.language_code].append(guide)
        
        # Generate content for each language
        for lang_code, guides in by_language.items():
            content.append(f'<details class="navigation-language">')
            content.append(f'<summary>{lang_code}</summary>')
            content.append('<div class="navigation-content">')
            
            # Show version history
            for guide in guides:
                created = guide.created_at.strftime("%Y-%m-%d %H:%M")
                content.append(
                    f'Version {guide.version} ({created})<br>'
                )
            
            content.append('</div>')
            content.append('</details>')
    else:
        content.append('<div class="navigation-text">No style guides yet</div>')
    
    content.append('</details>')
    return "\n".join(content)
