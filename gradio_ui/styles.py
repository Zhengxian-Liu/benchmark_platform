"""Common UI styles for the application."""

def get_navigation_styles():
    """Return CSS styles for the navigation panel."""
    return """
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
    """

def get_style_guide_styles():
    """Return CSS styles for style guide components."""
    return """
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
    """

def get_all_styles():
    """Return all application styles combined."""
    return "\n".join([
        get_navigation_styles(),
        get_style_guide_styles()
    ])
