import os
import sys


def get_resource_path(relative_path):
    """Get the absolute path to a resource."""
    # Check if running in a PyInstaller bundle
    if hasattr(sys, "_MEIPASS"):
        # Use the PyInstaller temp folder
        return os.path.join(sys._MEIPASS, relative_path)
    # Use the original path during development
    return os.path.join(os.path.abspath("."), relative_path)
