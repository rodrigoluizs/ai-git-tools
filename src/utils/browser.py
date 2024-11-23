import webbrowser


def open_in_default_browser(url):
    """Open the given URL in the default web browser."""
    try:
        webbrowser.open(url)
        print(f"Opened URL in default browser: {url}")
    except Exception as e:
        print(f"Failed to open URL: {e}")
