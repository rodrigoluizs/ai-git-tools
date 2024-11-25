import os
import unittest
from unittest.mock import patch, MagicMock

import requests
from src.service.bitbucket_service import BitbucketService


class TestBitbucketService(unittest.TestCase):
    def setUp(self):
        self.service = BitbucketService()
        self.service.username = "test_user"
        self.service.password = "test_password"
        self.service.api_url = "https://api.bitbucket.org/2.0"

    @patch.dict(os.environ, {"BITBUCKET_USERNAME": "test_user", "BITBUCKET_APP_PASSWORD": "test_password"})
    def test_validate_environment(self):
        # Ensure the method does not raise an exception when the environment is valid
        try:
            self.service.validate_environment()
        except SystemExit:
            self.fail("validate_environment raised SystemExit unexpectedly!")

    @patch.dict(os.environ, {"BITBUCKET_USERNAME": '', "BITBUCKET_APP_PASSWORD": ''})
    def test_validate_environment_missing_env_vars(self):
        # Ensure the method exits when the environment variables are missing
        with self.assertRaises(SystemExit):
            self.service.validate_environment()

    @patch("requests.get")
    def test_get_username_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"username": "test_user"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        username = self.service.get_username()
        self.assertEqual(username, "test_user")
        mock_get.assert_called_once_with(
            f"{self.service.api_url}/user",
            auth=(self.service.username, self.service.password),
        )

    @patch("requests.get")
    def test_get_username_failure(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Error fetching username")

        with self.assertRaises(SystemExit):
            self.service.get_username()

    def test_build_pull_request_data(self):
        head_branch = "feature/test"
        base_branch = "main"
        pr_title = "Test PR"
        pr_body = "This is a test PR."
        data = self.service.build_pull_request_data(head_branch, base_branch, pr_title, pr_body)

        expected_data = {
            "title": pr_title,
            "description": pr_body,
            "source": {"branch": {"name": head_branch}},
            "destination": {"branch": {"name": base_branch}},
            "close_source_branch": True,
        }
        self.assertEqual(data, expected_data)

    @patch("requests.post")
    @patch("src.service.git_service.GitService.get_repo_name", return_value="test_project/test_repo")
    @patch("src.service.git_service.GitService.find_parent_branch", return_value="main")
    def test_create_pull_request_success(self, mock_find_branch, mock_get_repo, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "links": {"html": {"href": "https://bitbucket.org/test_project/test_repo/pull-requests/1"}}
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        pr_url = self.service.create_pull_request(
            head_branch="feature/test",
            pr_title="Test PR",
            pr_body="This is a test pull request."
        )
        self.assertEqual(pr_url, "https://bitbucket.org/test_project/test_repo/pull-requests/1")

        mock_post.assert_called_once_with(
            f"{self.service.api_url}/repositories/test_project/test_repo/pullrequests",
            json={
                "title": "Test PR",
                "description": "This is a test pull request.",
                "source": {"branch": {"name": "feature/test"}},
                "destination": {"branch": {"name": "main"}},
                "close_source_branch": True,
            },
            auth=(self.service.username, self.service.password),
        )

    @patch("requests.post")
    @patch("src.service.git_service.GitService.get_repo_name", return_value="test_project/test_repo")
    @patch("src.service.git_service.GitService.find_parent_branch", return_value="main")
    def test_create_pull_request_failure(self, mock_find_branch, mock_get_repo, mock_post):
        mock_post.side_effect = requests.exceptions.RequestException("Error creating PR")

        with self.assertRaises(SystemExit):
            self.service.create_pull_request(
                head_branch="feature/test",
                pr_title="Test PR",
                pr_body="This is a test pull request."
            )

if __name__ == "__main__":
    unittest.main()