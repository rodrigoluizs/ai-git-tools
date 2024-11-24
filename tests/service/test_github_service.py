import os
import pytest
from unittest.mock import MagicMock, patch
from src.service.github_service import GitHubService


@pytest.fixture
def github_service():
    """Fixture to initialize GitHubService with mocked parameters."""
    with patch("src.service.github_service.Github") as MockGithub:
        mock_github_instance = MockGithub.return_value
        yield GitHubService(), mock_github_instance


def test_validate_environment_with_token(github_service):
    """Test validate_environment when GITHUB_TOKEN is set."""
    service, _ = github_service
    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake-token"}):
        # The method should run without exiting
        service.validate_environment()


def test_validate_environment_without_token(github_service):
    """Test validate_environment when GITHUB_TOKEN is missing."""
    service, _ = github_service
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SystemExit):
            service.validate_environment()


def test_get_username_with_valid_token(github_service):
    """Test get_username with a valid GITHUB_TOKEN."""
    service, mock_github = github_service
    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake-token"}):
        mock_github.get_user.return_value.login = "test-user"
        username = service.get_username()
        assert username == "test-user"


def test_get_username_without_token(github_service):
    """Test get_username when GITHUB_TOKEN is missing."""
    service, _ = github_service
    with patch.dict(os.environ, {}, clear=True):
        username = service.get_username()
        assert username is None


@patch("src.service.github_service.GitService")
def test_create_pull_request_existing_pr(mock_git_service, github_service):
    """Test create_pull_request with an existing pull request."""
    service, mock_github = github_service
    mock_git = mock_git_service.return_value
    mock_git.get_repo_name.return_value = "test-user/test-repo"
    mock_git.find_parent_branch.return_value = "main"

    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake-token"}):
        mock_repo = MagicMock()
        mock_github.get_repo.return_value = mock_repo
        mock_repo.owner.login = "test-user"

        # Mock existing pull requests
        mock_pr = MagicMock()
        mock_repo.get_pulls.return_value = iter([mock_pr])
        mock_pr.html_url = "https://github.com/test-user/test-repo/pull/1"

        result = service.create_pull_request("feature-branch", "Test PR", "This is a test.")
        assert result == "https://github.com/test-user/test-repo/pull/1"
        mock_pr.edit.assert_called_once_with(title="Test PR", body="This is a test.")


@patch("src.service.github_service.GitService")
def test_create_pull_request_new_pr(mock_git_service, github_service):
    """Test create_pull_request when no existing PR is found."""
    service, mock_github = github_service
    mock_git = mock_git_service.return_value
    mock_git.get_repo_name.return_value = "test-user/test-repo"
    mock_git.find_parent_branch.return_value = "main"

    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake-token"}):
        mock_repo = MagicMock()
        mock_github.get_repo.return_value = mock_repo
        mock_repo.owner.login = "test-user"

        # Mock no existing pull requests
        mock_repo.get_pulls.return_value = iter([])
        mock_new_pr = MagicMock()
        mock_new_pr.html_url = "https://github.com/test-user/test-repo/pull/2"
        mock_repo.create_pull.return_value = mock_new_pr

        result = service.create_pull_request("feature-branch", "Test PR", "This is a test.")
        assert result == "https://github.com/test-user/test-repo/pull/2"
        mock_repo.create_pull.assert_called_once_with(
            title="Test PR", body="This is a test.", base="main", head="feature-branch"
        )


@patch("src.service.github_service.GitService")
def test_create_pull_request_failure(mock_git_service, github_service):
    """Test create_pull_request when an exception occurs."""
    service, mock_github = github_service
    mock_git = mock_git_service.return_value
    mock_git.get_repo_name.return_value = "test-user/test-repo"
    mock_git.find_parent_branch.return_value = "main"

    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake-token"}):
        mock_github.get_repo.side_effect = Exception("GitHub API error")

        result = service.create_pull_request("feature-branch", "Test PR", "This is a test.")
        assert result is None


@patch("src.service.github_service.GitService")
def test_create_pull_request_no_token(mock_git_service, github_service):
    """Test create_pull_request when GITHUB_TOKEN is not set."""
    service, _ = github_service
    with patch.dict(os.environ, {}, clear=True):
        result = service.create_pull_request("feature-branch", "Test PR", "This is a test.")
        assert result is None