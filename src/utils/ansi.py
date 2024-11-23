# ANSI color codes for styling
def color_text(text, color_code):
    """Wrap text with ANSI color codes."""
    return f"\033[{color_code}m{text}\033[0m"
