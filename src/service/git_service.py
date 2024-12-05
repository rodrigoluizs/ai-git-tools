import os

from git import Repo, GitCommandError


class GitService:
    repo = Repo(os.getcwd())

    def find_parent_branch(self):
        """Find the branch from which the current branch originated."""

        # Get the current branch
        current_branch = self.repo.active_branch.name

        # Get all branches except the current one
        branches = [head.name for head in self.repo.heads if head.name != current_branch]

        # Find the closest merge base for each branch
        parent_branch = None
        closest_base = None
        for branch in branches:
            try:
                # Compute the merge base between the current branch and another branch
                merge_base = self.repo.git.merge_base(current_branch, branch).strip()
                if merge_base:
                    # Check if this merge base is closer than the previous closest
                    if (
                        not closest_base
                        or self.repo.commit(merge_base).committed_date > self.repo.commit(closest_base).committed_date
                    ):
                        closest_base = merge_base
                        parent_branch = branch
            except Exception as e:
                print(f"Error checking branch {branch}: {e}")

        return parent_branch

    def get_repo_name(self):
        """
        Retrieve the repository name from the Git remote URL.

        :return: The repository name in the format 'username/repo', or None if not found.
        """
        try:

            # Get the remote URL
            remote_url = next(self.repo.remote().urls)

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

    def get_diff(self):
        """
        Get staged, unstaged, and untracked changes using GitPython.

        :return: A dictionary containing diffs and untracked file contents.
        """
        try:
            unstaged = self.repo.git.diff()
            staged = self.repo.git.diff(cached=True)

            parent_branch = self.find_parent_branch()

            if not parent_branch:
                print("Unable to determine the parent branch. Defaulting to 'main'.")
                parent_branch = "main"

            branch = self.repo.git.diff(f"{parent_branch}...HEAD")

            # Get untracked files and their content
            untracked_content = ""
            for untracked_file in self.repo.untracked_files:
                if os.path.isfile(untracked_file):
                    try:
                        with open(untracked_file, "r", encoding="utf-8") as file_content:
                            untracked_content += f"\n\n--- Untracked file: {untracked_file} ---\n{file_content.read()}"
                    except UnicodeDecodeError:
                        print(f"Skipping binary or unreadable file: {untracked_file}")

            return f"{unstaged}\n{staged}\n{branch}", untracked_content

        except Exception as e:
            print(f"Error retrieving Git diffs: {e}")
            return None

    def sync_branch_and_commit(self, new_branch, commit_message):
        try:

            current_branch = self.repo.active_branch.name

            # Check if the repository is in a clean state
            if self.repo.is_dirty(untracked_files=True):
                print("Repository has uncommitted changes.")

            if current_branch == "main":
                # Create a new branch from main
                self.repo.git.checkout("-b", new_branch)
                self.repo.git.push("-u", "origin", new_branch)
            elif current_branch != new_branch:
                # Rename the current branch
                self.repo.git.branch("-m", new_branch)
                self.repo.git.push("-u", "origin", new_branch)

            if self.repo.is_dirty(untracked_files=True):
                # Stage all changes and commit
                self.repo.git.add(A=True)
                if self.repo.index.diff("HEAD"):  # Only commit if there are staged changes
                    self.repo.git.commit("-m", commit_message)
                    self.repo.git.push()
                    print("Changes committed successfully.")
                else:
                    print("No staged changes to commit.")
            else:
                print("No changes detected in the repository.")

            print("Git operations completed successfully.")
        except GitCommandError as e:
            print(f"An error occurred while executing Git commands: {e}")
