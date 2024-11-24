import os
import sys

from github import Github
from src.service.vcs_service import VcsService
from src.utils.git import get_repo_name, find_parent_branch


class GitHubService(VcsService):

    def validate_environment(self):
        """
        Ensure GITHUB_TOKEN is set.
        """
        if not os.getenv("GITHUB_TOKEN"):
            print("Error: GITHUB_TOKEN environment variable is not set.")
            sys.exit(1)

    def get_username(self):
        """Retrieve the GitHub username using PyGithub."""
        # Fetch the GitHub personal access token from the environment variable
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            print("Error: GITHUB_TOKEN environment variable is not set.")
            return None

        # Authenticate with GitHub using the token
        g = Github(github_token)

        # Get the authenticated user
        user = g.get_user()

        # Return the username
        return user.login

    def create_pull_request(self, head_branch, pr_title, pr_body):
        """
        Create a pull request using PyGitHub.

        :param base_branch: The branch you want to merge into
        :param head_branch: The branch for the pull request
        :param pr_title: Title of the pull request
        :param pr_body: Body/description of the pull request
        """
        # Authenticate using a personal access token
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            print("Error: GITHUB_TOKEN environment variable is not set.")
            return

        g = Github(github_token)

        try:
            # Access the repository
            repo = g.get_repo(get_repo_name())
            base_branch = find_parent_branch()

            # Check for an existing PR
            pull_request = None
            open_pulls = repo.get_pulls(state="open", base=base_branch, head=f"{repo.owner.login}:{head_branch}")
            for pr in open_pulls:
                pull_request = pr
                break  # If there's an open PR, use it

            if pull_request:
                print(f"Pull request already exists: {pull_request.html_url}")
                # Update the title and body
                pull_request.edit(title=pr_title, body=pr_body)
                print(f"Pull request updated: {pull_request.html_url}")
            else:
                # Create the pull request
                pull_request = repo.create_pull(
                    title=pr_title,
                    body=pr_body,
                    base=base_branch,  # The branch you want to merge into
                    head=head_branch,  # The branch you want to merge from
                )
                print("Pull request created")

            return pull_request.html_url
        except Exception as e:
            print(f"Failed to create pull request: {e}")
