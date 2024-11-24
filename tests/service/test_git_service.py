from unittest.mock import patch, MagicMock, mock_open

import pytest
from src.service.git_service import GitService


# Fixture for mocking Repo
@pytest.fixture
def mock_repo():
    """Patch Repo to return a mock instance."""
    with patch("src.service.git_service.Repo") as mock_repo:
        mock_repo_instance = MagicMock()
        mock_repo.return_value = mock_repo_instance
        yield mock_repo_instance


def build_git_service(mock_repo):
    service = GitService()
    service.repo = mock_repo

    return service


def test_find_parent_branch_success(mock_repo):
    """Test finding the parent branch successfully."""
    # Set up active branch
    mock_repo.active_branch.name = "feature-branch"

    # Set up mock branches
    main_branch = MagicMock()
    develop_branch = MagicMock()
    main_branch.name = "main"
    develop_branch.name = "develop"
    mock_repo.heads = [main_branch, develop_branch]

    # Mock merge_base behavior
    mock_repo.git.merge_base.side_effect = lambda a, b: {
        ("feature-branch", "main"): "merge_base_main",
        ("feature-branch", "develop"): "merge_base_develop",
    }[(a, b)]

    # Mock commit behavior
    mock_repo.commit.side_effect = lambda commit: {
        "merge_base_main": MagicMock(committed_date=100),
        "merge_base_develop": MagicMock(committed_date=200),
    }[commit]

    # Create GitService and test
    git_service = build_git_service(mock_repo)
    parent_branch = git_service.find_parent_branch()

    assert parent_branch == "develop"


def test_find_parent_branch_no_merge_base(mock_repo):
    """Test finding the parent branch with no valid merge base."""
    mock_repo.active_branch.name = "feature-branch"
    mock_repo.heads = [MagicMock(name="main")]

    mock_repo.git.merge_base.side_effect = Exception("No merge base")
    git_service = build_git_service(mock_repo)
    parent_branch = git_service.find_parent_branch()
    assert parent_branch is None


# Test get_repo_name
def test_get_repo_name_https(mock_repo):
    """Test extracting repository name from HTTPS URL."""
    mock_repo.remote.return_value.urls = iter(["https://github.com/user/repo.git"])

    git_service = build_git_service(mock_repo)
    repo_name = git_service.get_repo_name()
    assert repo_name == "user/repo"


def test_get_repo_name_ssh(mock_repo):
    """Test extracting repository name from SSH URL."""
    mock_repo.remote.return_value.urls = iter(["git@github.com:user/repo.git"])

    git_service = build_git_service(mock_repo)
    repo_name = git_service.get_repo_name()
    assert repo_name == "user/repo"


def test_get_repo_name_invalid_url(mock_repo):
    """Test repository name extraction with an invalid URL."""
    mock_repo.remote.return_value.urls = iter(["ftp://example.com/repo"])

    git_service = build_git_service(mock_repo)
    repo_name = git_service.get_repo_name()
    assert repo_name is None


# Test get_diff
@patch("src.service.git_service.os.path.isfile", return_value=True)
@patch("src.service.git_service.open", new_callable=mock_open, read_data="untracked content")
def test_get_diff(mock_open, mock_isfile, mock_repo):
    """Test retrieving Git diffs."""
    mock_repo.git.diff.side_effect = ["unstaged diff", "staged diff", "branch diff"]
    mock_repo.untracked_files = ["untracked_file.txt"]

    git_service = build_git_service(mock_repo)
    diff, untracked_content = git_service.get_diff()
    assert "unstaged diff" in diff
    assert "staged diff" in diff
    assert "branch diff" in diff
    assert "--- Untracked file: untracked_file.txt ---" in untracked_content
    assert "untracked content" in untracked_content


@patch("src.service.git_service.os.path.isfile", return_value=False)
def test_get_diff_no_untracked_files(mock_isfile, mock_repo):
    """Test retrieving Git diffs with no untracked files."""
    mock_repo.git.diff.side_effect = ["unstaged diff", "staged diff", "branch diff"]
    mock_repo.untracked_files = []

    git_service = build_git_service(mock_repo)
    diff, untracked_content = git_service.get_diff()
    assert "unstaged diff" in diff
    assert "staged diff" in diff
    assert "branch diff" in diff
    assert untracked_content == ""


# Test sync_branch_and_commit
def test_sync_branch_and_commit_new_branch(mock_repo):
    """Test syncing branch and committing changes to a new branch."""
    mock_repo.active_branch.name = "main"
    mock_repo.is_dirty.return_value = True

    git_service = build_git_service(mock_repo)
    git_service.sync_branch_and_commit("new-feature-branch", "Commit message")

    # Assertions for new branch creation
    mock_repo.git.checkout.assert_called_once_with("-b", "new-feature-branch")
    mock_repo.git.push.assert_any_call("-u", "origin", "new-feature-branch")
    mock_repo.git.add.assert_called_once_with(A=True)
    mock_repo.git.commit.assert_called_once_with("-m", "Commit message")
    mock_repo.git.push.assert_any_call()


def test_sync_branch_and_commit_rename_branch(mock_repo):
    """Test renaming the current branch."""
    mock_repo.active_branch.name = "old-feature-branch"
    mock_repo.is_dirty.return_value = True

    git_service = build_git_service(mock_repo)

    git_service.sync_branch_and_commit("new-feature-branch", "Commit message")

    # Assertions for branch rename
    mock_repo.git.branch.assert_called_once_with("-m", "new-feature-branch")
    mock_repo.git.push.assert_any_call("-u", "origin", "new-feature-branch")
    mock_repo.git.add.assert_called_once_with(A=True)
    mock_repo.git.commit.assert_called_once_with("-m", "Commit message")
    mock_repo.git.push.assert_any_call()


def test_sync_branch_and_commit_no_changes(mock_repo):
    """Test syncing branch with no changes."""
    mock_repo.active_branch.name = "main"
    mock_repo.is_dirty.return_value = False

    git_service = build_git_service(mock_repo)

    git_service.sync_branch_and_commit("new-feature-branch", "Commit message")

    # No changes should result in no Git commands being called
    mock_repo.git.add.assert_not_called()
    mock_repo.git.commit.assert_not_called()
