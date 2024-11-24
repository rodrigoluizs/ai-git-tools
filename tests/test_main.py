import subprocess
import sys
from unittest.mock import patch

import pytest
from main import main, display_help


def test_display_help(capsys):
    """
    Test the display_help function to ensure it outputs the correct help text.
    """
    display_help()
    captured = capsys.readouterr()
    assert "AI Git Tools - Command Line Tool" in captured.out
    assert "Usage:" in captured.out
    assert "Options:" in captured.out
    assert "Examples:" in captured.out


@patch("main.git_change_manager.main")
def test_main_help_flag(mock_git_change_manager, capsys):
    """
    Test the main function when the help flag is passed.
    """
    test_args = ["main.py", "--help"]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0  # Ensure it exits with code 0

    # Verify the help text is displayed
    captured = capsys.readouterr()
    assert "AI Git Tools - Command Line Tool" in captured.out
    assert "Usage:" in captured.out
    assert "Options:" in captured.out

    # Ensure git_change_manager.main() is not called
    mock_git_change_manager.assert_not_called()


@patch("main.git_change_manager.main")
def test_main_no_args(mock_git_change_manager):
    """
    Test the main function when no arguments are passed.
    """
    test_args = ["main.py"]
    with patch.object(sys, "argv", test_args):
        main()

    # Ensure git_change_manager.main() is called
    mock_git_change_manager.assert_called_once()


@patch("main.git_change_manager.main", side_effect=subprocess.CalledProcessError(1, "mocked_command"))
def test_main_git_change_manager_error(mock_git_change_manager, capsys):
    """
    Test the main function when git_change_manager.main() raises a CalledProcessError.
    """
    test_args = ["main.py"]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1  # Ensure it exits with code 1

    # Verify error message is displayed
    captured = capsys.readouterr()
    assert "Error executing GitHub PR workflow:" in captured.out
    mock_git_change_manager.assert_called_once()


@patch("main.git_change_manager.main", side_effect=Exception("Unexpected error"))
def test_main_unexpected_error(mock_git_change_manager, capsys):
    """
    Test the main function when git_change_manager.main() raises an unexpected exception.
    """
    test_args = ["main.py"]
    with patch.object(sys, "argv", test_args):
        with pytest.raises(Exception, match="Unexpected error"):
            main()

    # Verify git_change_manager.main() was called
    mock_git_change_manager.assert_called_once()
