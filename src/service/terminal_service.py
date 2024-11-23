import os
import subprocess
import sys
import tempfile
import termios
import tty

from src.utils.ansi import color_text


class TerminalService:
    """Manages interactions with terminal."""

    def __init__(self):
        self.line_count = 0

    def print(self, text):
        """Print text to the terminal and track the number of lines."""
        print(text)
        self.line_count += text.count('\n') + 1  # Count lines in the text

    def clear(self):
        """Clear all tracked lines from the terminal."""
        for _ in range(self.line_count):
            sys.stdout.write("\033[F")  # Move the cursor up one line
            sys.stdout.write("\033[K")  # Clear the line
        sys.stdout.flush()
        self.line_count = 0  # Reset the line count

    def get_single_keypress(self):
        """Capture a single key press."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return key

    def get_user_input(self, label, default_value):
        """Prompt user for input with a single key press to open an editor."""
        terminal_manager = TerminalService()
        while True:
            # Color the default value text (color code 34 = blue)
            colored_default_value = color_text(default_value, "34")
            terminal_manager.print(f"{label}:\n{colored_default_value}")
            terminal_manager.print("Press 'e' to edit, 'x' to exit, or any other key to confirm.")

            key = self.get_single_keypress()  # Capture single key press
            terminal_manager.clear()  # Clear all dynamically printed lines

            if key.lower() == "x":  # Check if the key is 'x' (case-insensitive)
                print("Bye!")
                sys.exit(0)  # Exit the program
            elif key.lower() == "e":
                editor = os.getenv("EDITOR", "vi")
                with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
                    temp_file.write(default_value.encode('utf-8'))
                    temp_file.flush()
                    temp_path = temp_file.name

                try:
                    result = subprocess.run([editor, temp_path], check=False)
                    if result.returncode != 0:
                        print("Editor exited without saving. Keeping default value.")
                        return default_value
                    with open(temp_path, "r") as temp_file:
                        edited_value = temp_file.read().strip()
                    os.remove(temp_path)
                    return edited_value
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            else:
                return default_value
