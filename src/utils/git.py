import os
import re
import subprocess

from git import Repo, GitCommandError


def find_parent_branch():
    """Find the branch from which the current branch originated."""
    repo = Repo(os.getcwd())

    # Get the current branch
    current_branch = repo.active_branch.name

    # Get all branches except the current one
    branches = [head.name for head in repo.heads if head.name != current_branch]

    # Find the closest merge base for each branch
    parent_branch = None
    closest_base = None
    for branch in branches:
        try:
            # Compute the merge base between the current branch and another branch
            merge_base = repo.git.merge_base(current_branch, branch).strip()
            if merge_base:
                # Check if this merge base is closer than the previous closest
                if not closest_base or repo.commit(merge_base).committed_date > repo.commit(
                        closest_base).committed_date:
                    closest_base = merge_base
                    parent_branch = branch
        except Exception as e:
            print(f"Error checking branch {branch}: {e}")

    return parent_branch


def get_username_from_git_email():
    """Retrieve and sanitize the user's email username (local part) from the git configuration."""
    try:
        # Initialize the repository object
        repo = Repo(os.getcwd())

        # Get the configured email
        config_reader = repo.config_reader()
        user_email = config_reader.get_value("user", "email")

        # Extract the username (part before '@') from the email
        username = user_email.split("@")[0]

        # Replace invalid characters with hyphens and strip leading/trailing invalid characters
        sanitized_username = re.sub(r"[^a-zA-Z0-9-_]", "", username).strip("-")

        return sanitized_username
    except (GitCommandError, KeyError):
        print("Error: Could not retrieve email from git configuration.")
        return None


def get_repo_name():
    """
    Retrieve the repository name from the Git remote URL.

    :return: The repository name in the format 'username/repo', or None if not found.
    """
    try:
        # Initialize the repository
        repo = Repo(os.getcwd())

        # Get the remote URL
        remote_url = next(repo.remote().urls)

        # Extract the repository name from the URL
        if remote_url.startswith("https://") or remote_url.startswith("http://"):
            repo_name = remote_url.split("/")[-2:]
        elif remote_url.startswith("git@"):
            repo_name = remote_url.split(":")[-1].split("/")
        else:
            raise ValueError(f"Unsupported URL format: {remote_url}")

        # Format as 'username/repo'
        repo_name = "/".join(repo_name).replace(".git", "").strip()
        return repo_name
    except Exception as e:
        print(f"Error retrieving repository name: {e}")
        return None


def get_git_diff():
    """
    Get staged, unstaged, and untracked changes using GitPython.

    :return: A dictionary containing diffs and untracked file contents.
    """
    try:
        repo = Repo(os.getcwd())
        unstaged = repo.git.diff()
        staged = repo.git.diff(cached=True)
        branch = repo.git.diff("main...HEAD")

        # Get untracked files and their content
        untracked_content = ""
        for untracked_file in repo.untracked_files:
            if os.path.isfile(untracked_file):
                try:
                    with open(untracked_file, "r", encoding="utf-8") as file_content:
                        untracked_content += f"\n\n--- Untracked file: {untracked_file} ---\n{file_content.read()}"
                except UnicodeDecodeError:
                    print(f"Skipping binary or unreadable file: {untracked_file}")

        return f'{unstaged}\n{staged}\n{branch}', untracked_content

    except Exception as e:
        print(f"Error retrieving Git diffs: {e}")
        return None


def get_git_diff_old():
    """Get staged, unstaged, and untracked changes."""
    # Extensions and directories to ignore
    ignored_extensions = [".pyc"]
    ignored_directories = ["__pycache__"]

    git_diff = subprocess.getoutput("git diff && git diff --cached && git diff main...HEAD")
    untracked_files = subprocess.getoutput("git status --porcelain | awk '/^\\?\\?/ {print $2}'").splitlines()
    untracked_content = ""

    def should_ignore(file_path):
        """Check if a file or directory should be ignored."""
        for ext in ignored_extensions:
            if file_path.endswith(ext):
                return True
        for dir_name in ignored_directories:
            if dir_name in file_path.split(os.sep):
                return True
        return False

    for file in untracked_files:
        if should_ignore(file):
            continue

        if os.path.isdir(file):
            for root, _, files in os.walk(file):
                for f in files:
                    path = os.path.join(root, f)
                    if should_ignore(path):
                        continue
                    try:
                        with open(path, "r", encoding="utf-8") as file_content:
                            untracked_content += f"\n\n--- Untracked file: {path} ---\n{file_content.read()}"
                    except UnicodeDecodeError:
                        print(f"Skipping binary or unreadable file: {path}")
        elif os.path.isfile(file):
            try:
                with open(file, "r", encoding="utf-8") as file_content:
                    untracked_content += f"\n\n--- Untracked file: {file} ---\n{file_content.read()}"
            except UnicodeDecodeError:
                print(f"Skipping binary or unreadable file: {file}")

    return git_diff, untracked_content


def sync_branch_and_commit(new_branch, commit_message):
    try:

        # Initialize the repository object
        repo = Repo(os.getcwd())
        current_branch = repo.active_branch.name

        # Check if the repository is in a clean state
        if repo.is_dirty(untracked_files=True):
            print("Repository has uncommitted changes.")

        if current_branch == "main":
            # Create a new branch from main
            repo.git.checkout("-b", new_branch)
            repo.git.push("-u", "origin", new_branch)
        elif current_branch != new_branch:
            # Rename the current branch
            repo.git.branch("-m", new_branch)
            repo.git.push("-u", "origin", new_branch)

        if repo.is_dirty(untracked_files=True):
            # Stage all changes and commit
            repo.git.add(A=True)
            if repo.index.diff("HEAD"):  # Only commit if there are staged changes
                repo.git.commit("-m", commit_message)
                repo.git.push()
                print("Changes committed successfully.")
            else:
                print("No staged changes to commit.")
        else:
            print("No changes detected in the repository.")

        print("Git operations completed successfully.")
    except GitCommandError as e:
        print(f"An error occurred while executing Git commands: {e}")
