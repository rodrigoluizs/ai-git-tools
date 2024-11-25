import os
import sys

import requests
from src.service.git_service import GitService
from src.service.vcs_service import VcsService


class BitbucketService(VcsService):
    git: GitService

    def __init__(self):
        super().__init__()

        self.git = GitService()
        self.api_url = "https://api.bitbucket.org/2.0"
        self.username = os.getenv("BITBUCKET_USERNAME")
        self.password = os.getenv("BITBUCKET_APP_PASSWORD")

    def validate_environment(self):
        """Ensure BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD are set."""
        if not os.getenv("BITBUCKET_USERNAME") or not os.getenv("BITBUCKET_APP_PASSWORD"):
            print("Error: BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD environment variables are not set.")
            sys.exit(1)

    def get_username(self):
        """
        Retrieve the current authenticated username from Bitbucket Cloud.
        """
        try:
            response = requests.get(
                f"{self.api_url}/user",
                auth=(self.username, self.password),
            )
            response.raise_for_status()  # Raise an exception for HTTP errors
            user_data = response.json()
            return user_data.get("username")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Bitbucket username: {e}")
            sys.exit(1)

    @staticmethod
    def build_pull_request_data(head_branch, base_branch, pr_title, pr_body):
        """
        Build the data object for creating a pull request on Bitbucket.

        :param head_branch: The source branch for the pull request.
        :param base_branch: The target branch for the pull request.
        :param pr_title: The title of the pull request.
        :param pr_body: The description of the pull request.
        :return: A dictionary containing the PR data.
        """
        data = {
            "title": pr_title,
            "description": pr_body,
            "source": {
                "branch": {
                    "name": head_branch
                }
            },
            "destination": {
                "branch": {
                    "name": base_branch
                }
            },
            "close_source_branch": True
        }

        return data

    def create_pull_request(self, head_branch, pr_title, pr_body):
        """
        Create a pull request on Bitbucket using requests.

        :param head_branch: The branch to merge from.
        :param pr_title: The title of the pull request.
        :param pr_body: The description of the pull request.
        :return: The URL of the created pull request.
        """
        try:
            # Use GitService to get repo details
            git = GitService()
            repo_slug = git.get_repo_name()
            base_branch = git.find_parent_branch()

            # Build the URL for the repository
            project_key, repo_name = repo_slug.split("/")
            repo_url = f"{self.api_url}/repositories/{project_key}/{repo_name}/pullrequests"

            # Build the payload
            data = self.build_pull_request_data(head_branch, base_branch, pr_title, pr_body)

            # Send the POST request to create the pull request
            response = requests.post(
                repo_url,
                json=data,
                auth=(self.username, self.password)
            )

            # Raise an exception for HTTP errors
            response.raise_for_status()

            # Extract the PR URL
            pr_url = response.json().get("links", {}).get("html", {}).get("href", "Pull request URL not available.")

            return pr_url

        except requests.exceptions.RequestException as e:
            print(f"Failed to create pull request: {e}")
            sys.exit(1)


if __name__ == '__main__':
    print(BitbucketService().get_username())
