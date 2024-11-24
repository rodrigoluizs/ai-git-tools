from unittest.mock import patch, MagicMock, mock_open

import pytest
from src.service.terminal_service import TerminalService
from src.utils.ansi import color_text


@pytest.fixture
def terminal_service():
    """Fixture to create a TerminalService instance."""
    return TerminalService()


@patch("builtins.print")
def test_print(mock_print, terminal_service):
    """Test the print method."""
    terminal_service.print("Hello, World!")
    assert terminal_service.line_count == 1
    mock_print.assert_called_once_with("Hello, World!")


@patch("sys.stdout.write")
def test_clear(mock_write, terminal_service):
    """Test the clear method."""
    terminal_service.line_count = 2
    terminal_service.clear()
    assert terminal_service.line_count == 0
    assert mock_write.call_count == 4  # 2 lines, each with '\033[F' and '\033[K'


@patch("termios.tcsetattr")
@patch("termios.tcgetattr", return_value=[0, 0, 0, 0])
@patch("tty.setraw")
@patch("sys.stdin", spec=["fileno", "read"])
def test_get_single_keypress(mock_stdin, mock_setraw, mock_tcgetattr, mock_tcsetattr, terminal_service):
    """Test capturing a single keypress."""
    # Mock sys.stdin.fileno() and sys.stdin.read()
    mock_stdin.fileno.return_value = 0
    mock_stdin.read.return_value = "a"

    # Call the method
    key = terminal_service.get_single_keypress()

    # Assertions
    assert key == "a"
    mock_stdin.fileno.assert_called_once()
    mock_stdin.read.assert_called_once()
    mock_setraw.assert_called_once()
    mock_tcgetattr.assert_called_once()
    mock_tcsetattr.assert_called_once()


@patch("src.service.terminal_service.TerminalService.get_single_keypress", side_effect=["1", "x"])
@patch("src.service.terminal_service.TerminalService.print")
def test_get_user_choice_valid(mock_print, mock_keypress, terminal_service):
    """Test get_user_choice with valid input."""
    choices = {"1": "Option 1", "2": "Option 2"}
    choice = terminal_service.get_user_choice("Choose:", choices)
    assert choice == "1"
    mock_print.assert_any_call(color_text("1: Option 1", "34"))
    mock_print.assert_any_call(color_text("2: Option 2", "34"))


@patch("src.service.terminal_service.TerminalService.get_single_keypress", side_effect=["invalid", "1"])
@patch("src.service.terminal_service.TerminalService.print")
def test_get_user_choice_invalid(mock_print, mock_keypress, terminal_service):
    """Test get_user_choice with invalid input."""
    choices = {"1": "Option 1", "2": "Option 2"}
    choice = terminal_service.get_user_choice("Choose:", choices)
    assert choice == "1"
    mock_print.assert_any_call("Invalid choice 'invalid'. Please try again.")


@patch("src.service.terminal_service.TerminalService.get_single_keypress", side_effect=["e", "other"])
@patch("tempfile.NamedTemporaryFile", new_callable=mock_open)
@patch("subprocess.run", return_value=MagicMock(returncode=0))
@patch("builtins.open", new_callable=mock_open, read_data="Edited value")
@patch("os.remove")
def test_get_user_input_edit(
        mock_remove, mock_open_file, mock_subprocess, mock_tempfile, mock_keypress
):
    """Test editing user input using an external editor."""
    terminal_service = TerminalService()

    # Call the method
    result = terminal_service.get_user_input("Test Label", "Default Value")

    # Assertions
    assert result == "Edited value"
    mock_open_file.assert_called_once_with(mock_tempfile().name, "r")
    mock_remove.assert_called_once_with(mock_tempfile().name)
    mock_subprocess.assert_called_once_with(["vi", mock_tempfile().name], check=False)
    mock_keypress.assert_any_call()


@patch("src.service.terminal_service.TerminalService.get_single_keypress", side_effect=["other"])
@patch("src.service.terminal_service.TerminalService.print")
def test_get_user_input_default(mock_print, mock_keypress, terminal_service):
    """Test get_user_input with any key to confirm default value."""
    result = terminal_service.get_user_input("Label", "Default Value")
    assert result == "Default Value"


@patch("builtins.print")
@patch("src.service.terminal_service.TerminalService.get_single_keypress", side_effect=["x"])
def test_get_user_input_exit(mock_keypress, mock_print):
    """Test get_user_input with 'x' key to exit."""
    terminal_service = TerminalService()  # Use the real implementation
    with pytest.raises(SystemExit) as excinfo:
        terminal_service.get_user_input("Test Label", "Default Value")
    assert excinfo.value.code == 0  # Verify that the exit code is 0
    mock_print.assert_called_with("Bye!")  # Ensure the exit message is printed


@patch("builtins.print")
@patch("src.service.terminal_service.TerminalService.get_single_keypress", side_effect=["x"])
def test_get_direct_user_input_exit(mock_keypress, mock_print):
    """Test get_direct_user_input with 'x' key to exit."""
    terminal_service = TerminalService()  # Use the real implementation
    with pytest.raises(SystemExit) as excinfo:
        terminal_service.get_direct_user_input("Test Description")
    assert excinfo.value.code == 0  # Verify the program exits with code 0
    mock_print.assert_any_call("Bye!")  # Ensure the exit message is printed


@patch("src.service.terminal_service.TerminalService.get_single_keypress", side_effect=["any"])
@patch("tempfile.NamedTemporaryFile", new_callable=mock_open)
@patch("subprocess.run", return_value=MagicMock(returncode=0))
@patch("builtins.open", new_callable=mock_open, read_data="Direct Input")
@patch("os.remove")
def test_get_direct_user_input_edit(mock_remove, mock_open_file, mock_subprocess, mock_tempfile, mock_keypress):
    """Test get_direct_user_input with editing in an external editor."""
    terminal_service = TerminalService()

    # Call the method
    result = terminal_service.get_direct_user_input("Test Description")

    # Assertions
    assert result == "Direct Input"  # The value edited and returned by the editor
    mock_tempfile.assert_called_once()  # Ensure tempfile was used
    mock_subprocess.assert_called_once_with(["vi", mock_tempfile().name], check=False)  # Ensure the editor was run
    mock_open_file.assert_called_once_with(mock_tempfile().name, "r")  # Ensure the temp file was read
    mock_remove.assert_called_once_with(mock_tempfile().name)  # Ensure the temp file was removed
