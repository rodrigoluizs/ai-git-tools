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
        self.line_count += text.count("\n") + 1  # Count lines in the text

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

    def get_user_choice(self, prompt, choices):
        """
        Prompt the user to select from a list of choices.

        :param prompt: The prompt label to display.
        :param choices: A dictionary where keys are valid inputs, and values are descriptions.
        :return: The key corresponding to the user's choice.
        """
        while True:
            self.print(f"{prompt}")
            for key, description in choices.items():
                self.print(color_text(f"{key}: {description}", "34"))
            self.print("\nChoose an option:")
            key = self.get_single_keypress()
            self.clear()

            if key in choices:
                return key
            else:
                self.print(f"Invalid choice '{key}'. Please try again.")

    def get_user_input(self, label, default_value):
        """Prompt user for input with a single key press to open an editor."""
        while True:
            # Color the default value text (color code 34 = blue)
            colored_default_value = color_text(default_value, "34")
            self.print(f"\n{label}:\n{colored_default_value}")
            self.print("\nPress 'e' to edit, 'x' to exit, or any other key to confirm.")

            key = self.get_single_keypress()  # Capture single key press
            self.clear()  # Clear all dynamically printed lines

            if key.lower() == "x":  # Check if the key is 'x' (case-insensitive)
                print("Bye!")
                sys.exit(0)  # Exit the program
            elif key.lower() == "e":
                editor = os.getenv("EDITOR", "vi")
                with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
                    temp_file.write(default_value.encode("utf-8"))
                    temp_file.flush()
                    temp_path = temp_file.name

                try:
                    result = subprocess.run([editor, temp_path], check=False)
                    if result.returncode != 0:
                        print("Editor exited without saving. Keeping default value.")
                        return default_value
                    with open(temp_path, "r") as temp_file:
                        edited_value = temp_file.read().strip()
                    return edited_value
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            else:
                return default_value

    def get_direct_user_input(self, description):
        """Prompt user for input with a single key press to open an editor."""
        while True:
            self.print(f"{color_text(description, '34')}")
            self.print("Press 'x' to exit, or any other key to continue.")

            key = self.get_single_keypress()  # Capture single key press
            self.clear()

            if key.lower() == "x":
                print("Bye!")
                sys.exit(0)  # Exit the program
            else:
                editor = os.getenv("EDITOR", "vi")
                with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
                    temp_file.flush()
                    temp_path = temp_file.name

                try:
                    result = subprocess.run([editor, temp_path], check=False)
                    if result.returncode != 0:
                        print("Editor exited without saving. Exiting.")
                        sys.exit(0)
                    with open(temp_path, "r") as temp_file:
                        edited_value = temp_file.read().strip()
                    return edited_value
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
