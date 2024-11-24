import os
from unittest.mock import patch

import pytest
from git import InvalidGitRepositoryError
from src.core.git_change_manager import (
    get_prompt_file,
    get_service_provider,
    print_colored_summary,
    validate_env_vars
)
from src.service.github_service import GitHubService


@pytest.fixture
def mock_repo():
    with patch("src.core.git_change_manager.Repo") as mock_repo:
        mock_repo_instance = MagicMock()
        mock_repo_instance.bare = False
        mock_repo.return_value = mock_repo_instance
        yield mock_repo_instance


@pytest.fixture
def mock_prompt_file(tmp_path):
    """Mock the prompt file path."""
    prompts_dir = tmp_path / "resources" / "prompts"
    prompts_dir.mkdir(parents=True)
    mock_prompt = prompts_dir / "git-change-manager.txt"
    mock_prompt.write_text("This is a test prompt.")

    with patch("src.core.git_change_manager.get_resource_path", return_value=str(mock_prompt)):
        yield mock_prompt


# Test validate_env_vars

def test_validate_env_vars_success():
    """Test validate_env_vars when both environment variables are set."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "mock_openai_key", "GITHUB_TOKEN": "mock_github_token"}):
        # The function should run without any exceptions
        validate_env_vars()


def test_validate_env_vars_missing_openai_api_key():
    """Test validate_env_vars when OPENAI_API_KEY is missing."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": "mock_github_token"}, clear=True):
        with pytest.raises(SystemExit) as excinfo:
            validate_env_vars()
        assert excinfo.value.code == 1


def test_validate_env_vars_missing_github_token():
    """Test validate_env_vars when GITHUB_TOKEN is missing."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "mock_openai_key"}, clear=True):
        with pytest.raises(SystemExit) as excinfo:
            validate_env_vars()
        assert excinfo.value.code == 1


def test_validate_env_vars_both_missing():
    """Test validate_env_vars when both environment variables are missing."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SystemExit) as excinfo:
            validate_env_vars()
        assert excinfo.value.code == 1


# Test get_prompt_file

@patch("src.core.git_change_manager.os.path.isfile", return_value=True)
@patch("src.core.git_change_manager.get_resource_path", return_value="/mock/path/to/git-change-manager.txt")
def test_get_prompt_file_success(mock_get_resource_path, mock_isfile):
    """Test successful retrieval of the prompt file."""
    result = get_prompt_file()
    assert result == "/mock/path/to/git-change-manager.txt"


@patch("src.core.git_change_manager.os.path.isfile", return_value=False)
@patch("src.core.git_change_manager.get_resource_path", return_value="/mock/path/to/git-change-manager.txt")
def test_get_prompt_file_missing(mock_get_resource_path, mock_isfile):
    """Test behavior when the prompt file is missing."""
    with pytest.raises(SystemExit):
        get_prompt_file()


# Test get_service_provider

def test_get_service_provider_github(mock_repo):
    """Test service provider detection for GitHub."""

    mock_repo.remote.return_value.urls = iter(["https://github.com/test/repo"])

    service = get_service_provider()
    assert isinstance(service, GitHubService)


def test_get_service_provider_gitlab(mock_repo):
    """Test service provider detection for GitHub."""

    mock_repo.remote.return_value.urls = iter(["https://gitlab.com/test/repo"])

    with pytest.raises(SystemExit):
        get_service_provider()


def test_get_service_provider_bitbucket(mock_repo):
    """Test service provider detection for GitHub."""

    mock_repo.remote.return_value.urls = iter(["https://bitbucket.org/test/repo"])

    with pytest.raises(SystemExit):
        get_service_provider()


@patch("src.core.git_change_manager.Repo")
def test_get_service_provider_invalid_repo(mock_repo):
    """Test invalid repository handling."""
    mock_repo.side_effect = InvalidGitRepositoryError
    with pytest.raises(SystemExit):
        get_service_provider()


def test_get_service_provider_bare_repo(mock_repo):
    """Test invalid repository handling."""
    mock_repo.bare = True
    with pytest.raises(SystemExit):
        get_service_provider()


def test_get_service_provider_no_remote(mock_repo):
    """Test handling of missing remote URLs."""
    mock_repo.remote.return_value.urls = iter([])
    with pytest.raises(SystemExit):
        get_service_provider()


def test_get_service_provider_unsupported_provider(mock_repo):
    """Test unsupported provider handling."""
    mock_repo.return_value.remote.return_value.urls = iter(["https://unsupported.com/test/repo"])
    with pytest.raises(SystemExit):
        get_service_provider()


# Test print_colored_summary

@patch("src.core.git_change_manager.color_text", side_effect=lambda text, color: f"{color}:{text}")
def test_print_colored_summary(mock_color_text, capsys):
    """Test print_colored_summary for correct output."""
    print_colored_summary("test-branch", "test commit", "test PR", "test body")
    captured = capsys.readouterr()
    assert "34:test-branch" in captured.out
    assert "32:test commit" in captured.out
    assert "36:test PR" in captured.out
    assert "33:test body" in captured.out


# Test main

import pytest
from unittest.mock import patch, MagicMock
from src.core.git_change_manager import main


@patch("src.core.git_change_manager.get_prompt_file", return_value="/mock/path/to/git-change-manager.txt")
@patch("src.core.git_change_manager.get_service_provider")
@patch("src.core.git_change_manager.GitService")
@patch("src.core.git_change_manager.TerminalService")
@patch("src.core.git_change_manager.call_openai_api", return_value={
    "branch_name": "test-branch",
    "commit_message": "test commit",
    "pr_title": "test PR",
    "pr_body": "test body"
})
@patch("src.core.git_change_manager.open_in_default_browser")
@patch("builtins.open", new_callable=MagicMock)
def test_main(
        mock_open, mock_browser, mock_api, mock_terminal, mock_git_service, mock_service_provider, mock_prompt_file,
        tmp_path
):
    """Test main function with all dependencies mocked."""

    # Mock the prompt file's content
    mock_file = MagicMock()
    mock_file.read.return_value = "Mocked Prompt Content"
    mock_open.return_value.__enter__.return_value = mock_file

    # Mock GitService methods
    mock_git_instance = mock_git_service.return_value
    mock_git_instance.get_diff.return_value = ("mock_diff", "mock_untracked")
    mock_git_instance.sync_branch_and_commit.return_value = None

    # Mock service provider behavior
    mock_service_instance = mock_service_provider.return_value
    mock_service_instance.get_username.return_value = "mock-user"
    mock_service_instance.create_pull_request.return_value = "https://mock-pr-url"

    # Mock TerminalService behavior
    mock_terminal_instance = mock_terminal.return_value
    mock_terminal_instance.get_user_choice.return_value = "2"
    mock_terminal_instance.get_user_input.side_effect = lambda *args: args[1]

    # Mock input
    with patch("builtins.input", return_value="Test change description"):
        main()

    # Assertions
    mock_git_instance.get_diff.assert_called_once()
    mock_git_instance.sync_branch_and_commit.assert_called_once_with("mock-user/test-branch", "test commit")
    mock_service_instance.create_pull_request.assert_called_once_with("mock-user/test-branch", "test PR", "test body")
    mock_browser.assert_called_once_with("https://mock-pr-url")
    mock_open.assert_called_once_with("/mock/path/to/git-change-manager.txt", "r")


@patch("src.core.git_change_manager.open_in_default_browser")
@patch("src.core.git_change_manager.GitService")
@patch("src.core.git_change_manager.call_openai_api", return_value={
    "branch_name": "test-branch",
    "commit_message": "test commit",
    "pr_title": "test PR",
    "pr_body": "test body"
})
@patch("src.core.git_change_manager.TerminalService")
@patch("src.core.git_change_manager.get_service_provider")
@patch("src.core.git_change_manager.get_prompt_file", return_value="/mock/path/to/git-change-manager.txt")
@patch("builtins.open", new_callable=MagicMock)
def test_main_create_pull_request_params(
        mock_open, mock_prompt, mock_service_provider, mock_terminal, mock_api, mock_git_service, mock_browser
):
    """Test that create_pull_request is called with correct parameters."""
    # Mock file behavior
    mock_file = MagicMock()
    mock_file.read.return_value = "Test Prompt Content"
    mock_open.return_value.__enter__.return_value = mock_file

    # Mock GitService behavior
    mock_git_instance = mock_git_service.return_value
    mock_git_instance.get_diff.return_value = ("mock_diff", "mock_untracked")

    # Mock service provider behavior
    mock_service_instance = mock_service_provider.return_value
    mock_service_instance.get_username.return_value = "mock-user"
    mock_service_instance.create_pull_request.return_value = "https://mock-pr-url"

    # Mock TerminalService behavior
    mock_terminal_instance = mock_terminal.return_value
    mock_terminal_instance.get_user_choice.return_value = "2"
    mock_terminal_instance.get_user_input.side_effect = lambda *args: args[1]

    # Simulate user input
    with patch("builtins.input", return_value="Test Change Description"):
        main()

    # Assertions
    mock_service_instance.create_pull_request.assert_called_once_with(
        "mock-user/test-branch", "test PR", "test body"
    )


@patch("src.core.git_change_manager.open_in_default_browser")
@patch("src.core.git_change_manager.GitService")
@patch("src.core.git_change_manager.call_openai_api", return_value={
    "branch_name": "test-branch",
    "commit_message": "test commit",
    "pr_title": "test PR",
    "pr_body": "test body"
})
@patch("src.core.git_change_manager.TerminalService")
@patch("src.core.git_change_manager.get_service_provider")
@patch("src.core.git_change_manager.get_prompt_file", return_value="/mock/path/to/git-change-manager.txt")
@patch("builtins.open", new_callable=MagicMock)
def test_main_choice_1(
        mock_open, mock_prompt, mock_service_provider, mock_terminal, mock_api, mock_git_service, mock_browser
):
    """Test main function for choice 1 (Copy to Clipboard)."""
    # Mock file behavior
    mock_file = MagicMock()
    mock_file.read.return_value = "Test Prompt Content"
    mock_open.return_value.__enter__.return_value = mock_file

    # Mock GitService behavior
    mock_git_instance = mock_git_service.return_value
    mock_git_instance.get_diff.return_value = ("mock_diff", "mock_untracked")

    # Mock service provider behavior
    mock_service_instance = mock_service_provider.return_value
    mock_service_instance.get_username.return_value = "mock-user"

    # Mock TerminalService behavior
    mock_terminal_instance = mock_terminal.return_value
    mock_terminal_instance.get_user_choice.return_value = "1"
    mock_terminal_instance.get_user_input.side_effect = lambda *args: args[1]
    mock_terminal_instance.get_direct_user_input.return_value = '{"branch_name": "test-branch", "commit_message": "test commit", "pr_title": "test PR", "pr_body": "test body"}'

    with patch("pyperclip.copy") as mock_copy:
        with patch("builtins.input", return_value="Test Change Description"):
            main()

        # Assertions
        mock_copy.assert_called_once_with(
            """Test Prompt Content
Description of the change:
Test Change Description

Git diff for my changes:
mock_diff

Content of untracked files:
mock_untracked
"""
        )


@patch("src.core.git_change_manager.open_in_default_browser")
@patch("src.core.git_change_manager.GitService")
@patch("src.core.git_change_manager.call_openai_api")
@patch("src.core.git_change_manager.TerminalService")
@patch("src.core.git_change_manager.get_service_provider")
@patch("src.core.git_change_manager.get_prompt_file", return_value="/mock/path/to/git-change-manager.txt")
@patch("builtins.open", new_callable=MagicMock)
def test_main_invalid_choice(
        mock_open, mock_prompt, mock_service_provider, mock_terminal, mock_api, mock_git_service, mock_browser
):
    """Test main function for invalid choice (else clause)."""
    # Mock file behavior
    mock_file = MagicMock()
    mock_file.read.return_value = "Test Prompt Content"
    mock_open.return_value.__enter__.return_value = mock_file

    # Mock GitService behavior
    mock_git_instance = mock_git_service.return_value
    mock_git_instance.get_diff.return_value = ("mock_diff", "mock_untracked")

    # Mock TerminalService behavior
    mock_terminal_instance = mock_terminal.return_value
    mock_terminal_instance.get_user_choice.return_value = "invalid_choice"

    # Simulate user input
    with patch("builtins.input", return_value="Test Change Description"):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0
