import json
import os
import sys

import pyperclip
from git import Repo, InvalidGitRepositoryError
from src.service.bitbucket_service import BitbucketService
from src.service.git_service import GitService
from src.service.github_service import GitHubService
from src.service.openai_service import OpenAiService
from src.service.terminal_service import TerminalService
from src.service.vcs_service import VcsService
from src.utils.ansi import color_text
from src.utils.browser import open_in_default_browser
from src.utils.file_utils import get_resource_path


def validate_env_vars():
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)
    if not os.getenv("GITHUB_TOKEN"):
        print("Error: GITHUB_TOKEN environment variable is not set.")
        sys.exit(1)


def get_prompt_file():
    """Get the path to the prompt file."""
    path = get_resource_path("resources/prompts/git-change-manager.txt")
    if not os.path.isfile(path):
        print(f"Prompt file not found at {path}")
        sys.exit(1)
    return path


# Define colors for different sections
def print_colored_summary(branch_name, commit_message, pr_title, pr_body):
    """Print all the collected information with colors."""
    print("\nCollected Information:\n")
    print(f"Branch Name:\n{color_text(branch_name, '34')}\n")
    print(f"Commit Message:\n{color_text(commit_message, '32')}\n")
    print(f"PR Title:\n{color_text(pr_title, '36')}\n")
    print(f"PR Body:\n{color_text(pr_body, '33')}\n")


def get_service_provider() -> VcsService:
    """
    Determine the service provider for the given Git repository.

    :return: The service provider (e.g., "GitHub", "GitLab", "Bitbucket", or None if unknown).
    """
    try:
        # Initialize the repository object for the given path
        repo = Repo(os.getcwd())

        # Ensure the repo is valid
        if repo.bare:
            print("Error: The directory is a bare Git repository.")
            sys.exit(0)

        # Get the remote URL (assuming 'origin' exists)
        remote_url = next(repo.remote().urls, None)

        if not remote_url:
            print("Error: No remote URL found for the repository.")
            sys.exit(0)

        if "github.com" in remote_url:
            return GitHubService()
        elif "gitlab.com" in remote_url:
            print(f"Unsupported service provider: {remote_url}")
            sys.exit(0)
        elif "bitbucket.org" in remote_url:
            return BitbucketService()
        else:
            print(f"Unsupported service provider: {remote_url}")
            sys.exit(0)

    except InvalidGitRepositoryError:
        print("Error: The current directory is not a Git repository.")
        sys.exit(0)


def main():
    validate_env_vars()
    # Read prompt template

    with open(get_prompt_file(), "r") as file:
        prompt_text = file.read()

    service = get_service_provider()
    git = GitService()
    terminal = TerminalService()

    # Get Git information
    change_description = input("Enter a description of the change: ").strip()
    git_diff, untracked_content = git.get_diff()

    # Combine prompt
    prompt_combined = f"""{prompt_text}
Description of the change:
{change_description}

Git diff for my changes:
{git_diff}

Content of untracked files:
{untracked_content}
"""
    choices = {"1": "Copy prompt to clipboard", "2": "Call OpenAI"}
    choice = terminal.get_user_choice("How would you like to proceed?\n", choices)

    if choice == "1":
        pyperclip.copy(prompt_combined)
        openai_response = json.loads(
            terminal.get_direct_user_input(
                "The prompt was copied to your clipboard, press any key to paste the response from your model in the editor.\n\n"
            )
        )
    elif choice == "2":
        openai_response = OpenAiService().call(prompt_combined)
    else:
        print("Invalid choice, exiting.")
        sys.exit(0)

    # Confirm or edit suggestions
    branch_name = terminal.get_user_input(
        "Branch name", f"{service.get_username()}/{openai_response.get('branch_name')}"
    )
    commit_message = terminal.get_user_input("Commit message", openai_response.get("commit_message"))
    pr_title = terminal.get_user_input("PR title", openai_response.get("pr_title"))
    pr_body = terminal.get_user_input("PR body", openai_response.get("pr_body"))

    print_colored_summary(branch_name, commit_message, pr_title, pr_body)

    # Execute commands
    print("Executing commands...")
    # Get the current branch
    git.sync_branch_and_commit(branch_name, commit_message)
    pr_url = service.create_pull_request(branch_name, pr_title, pr_body)

    open_in_default_browser(pr_url)
