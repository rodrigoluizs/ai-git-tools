import json
import os
import sys

from git import Repo, InvalidGitRepositoryError
from src.service.github_service import GitHubService
from src.service.terminal_service import TerminalService
from src.service.vcs_service import VcsService
from src.utils.ansi import color_text
from src.utils.browser import open_in_default_browser
from src.utils.file_utils import get_resource_path
from src.utils.git import get_git_diff, sync_branch_and_commit

# Constants
PROMPT_FILE = get_resource_path("resources/prompts/git-change-manager.txt")

if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY environment variable is not set.")
    sys.exit(1)

if not os.path.isfile(PROMPT_FILE):
    print(f"Prompt file not found at {PROMPT_FILE}")
    sys.exit(1)

if not os.getenv("GITHUB_TOKEN"):
    print("Error: GITHUB_TOKEN environment variable is not set.")
    sys.exit(1)


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
            print(f"Unsupported service provider: {remote_url}")
            sys.exit(0)
        else:
            print(f"Unsupported service provider: {remote_url}")
            sys.exit(0)

    except InvalidGitRepositoryError:
        print("Error: The current directory is not a Git repository.")
        sys.exit(0)


def main():
    # Read prompt template
    with open(PROMPT_FILE, "r") as file:
        prompt_text = file.read()

    service = get_service_provider()

    # Get Git information
    change_description = 'feat git change script integrated with openai'
    # change_description = input("Enter a description of the change: ").strip()
    git_diff, untracked_content = get_git_diff()

    # Combine prompt
    prompt_combined = f"""{prompt_text}
    Description of the change: 
    {change_description}
    
    Git diff for my changes:
    {git_diff}
    
    Content of untracked files:
    {untracked_content}
    """

    # Call OpenAI API
    # TODO mocking the openapi response for now to avoid big costs
    # openai_response = call_openai_api(prompt_combined)
    with open(get_resource_path('resources/mock/openapi_response.json'), "r") as file:
        openai_response = json.loads(file.read())

    # Confirm or edit suggestions
    branch_name = f"{service.get_username()}/{openai_response.get('branch_name')}"
    # commit_message = openai_response.get('commit_message')
    # pr_title = openai_response.get('pr_title')
    # pr_body = openai_response.get('pr_body')

    terminal = TerminalService()
    branch_name = terminal.get_user_input("Branch name", branch_name)
    commit_message = terminal.get_user_input("Commit message", openai_response.get('commit_message'))
    pr_title = terminal.get_user_input("PR title", openai_response.get('pr_title'))
    pr_body = terminal.get_user_input("PR body", openai_response.get('pr_body'))

    print_colored_summary(branch_name, commit_message, pr_title, pr_body)

    # Execute commands
    print("Executing commands...")
    # Get the current branch
    sync_branch_and_commit(branch_name, commit_message)
    pr_url = service.create_pull_request(branch_name, pr_title, pr_body)

    open_in_default_browser(pr_url)
