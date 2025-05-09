"""
Repository management module for RepoWalker.

This module handles the git operations for cloning, fetching, and managing branches.
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from colorama import Fore, Style

# Environment variable for the GitHub token
TOKEN_ENV_VAR = "REPOWALKER_AUTH_TOKEN"


class RepositoryManager:
    """Manager for git operations on repositories."""

    def __init__(self, working_dir: Optional[Path] = None):
        """Initialize repository manager.

        Args:
            working_dir: Directory to store repositories (defaults to temp directory)
        """
        self.working_dir = working_dir or Path(tempfile.mkdtemp(prefix="repowalker_"))
        self.repos_dir = self.working_dir / "repos"
        self.repos_dir.mkdir(exist_ok=True)

        # Get GitHub token
        self.token = os.environ.get(TOKEN_ENV_VAR)
        if not self.token:
            raise ValueError(
                f"{Fore.RED}Error: GitHub token not found in environment variable {TOKEN_ENV_VAR}."
                f"{Style.RESET_ALL}\nPlease run: {Fore.GREEN}python scripts/auth.py{Style.RESET_ALL}"
            )

    def setup_repository(self, repo_info: Dict[str, Any]) -> Path:
        """Clone or fetch the main branch of a repository.

        Args:
            repo_info: Repository information from GitHub API

        Returns:
            Path to the local repository directory
        """
        repo_name = repo_info["full_name"]
        repo_url = repo_info["clone_url"]
        default_branch = repo_info.get("default_branch", "main")

        # Create a sanitized directory name from the repository full name
        dir_name = repo_name.replace("/", "_")
        repo_dir = self.repos_dir / dir_name

        if repo_dir.exists():
            # Repository already exists locally, fetch latest changes
            print(
                f"{Fore.BLUE}Repository {repo_name} already cloned, fetching updates...{Style.RESET_ALL}"
            )

            subprocess.run(
                ["git", "fetch", "origin", default_branch],
                cwd=repo_dir,
                check=True,
                capture_output=True,
            )

            # Reset to the latest version of the default branch
            subprocess.run(
                ["git", "checkout", default_branch],
                cwd=repo_dir,
                check=True,
                capture_output=True,
            )

            subprocess.run(
                ["git", "reset", "--hard", f"origin/{default_branch}"],
                cwd=repo_dir,
                check=True,
                capture_output=True,
            )

            print(f"{Fore.GREEN}Repository {repo_name} updated successfully{Style.RESET_ALL}")
        else:
            # Repository doesn't exist locally, clone it
            print(f"{Fore.BLUE}Cloning repository {repo_name}...{Style.RESET_ALL}")

            # Construct clone URL with authentication token
            auth_url = repo_url.replace("https://", f"https://{self.token}@")

            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--branch",
                    default_branch,
                    auth_url,
                    str(repo_dir),
                ],
                check=True,
                capture_output=True,
            )

            print(f"{Fore.GREEN}Repository {repo_name} cloned successfully{Style.RESET_ALL}")

        return repo_dir

    def create_branch(self, repo_dir: Path, branch_name: str) -> bool:
        """Create a new branch in the repository.

        Args:
            repo_dir: Path to the repository directory
            branch_name: Name of the branch to create

        Returns:
            True if branch was created successfully, False otherwise
        """
        try:
            # Create a new branch
            print(f"{Fore.BLUE}Creating branch {branch_name}...{Style.RESET_ALL}")

            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=repo_dir,
                check=True,
                capture_output=True,
            )

            print(f"{Fore.GREEN}Branch {branch_name} created successfully{Style.RESET_ALL}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}Error creating branch {branch_name}: {e}{Style.RESET_ALL}")
            return False

    def commit_and_push(self, repo_dir: Path, branch_name: str, commit_message: str) -> bool:
        """Commit and push changes to the repository.

        Args:
            repo_dir: Path to the repository directory
            branch_name: Name of the branch to push
            commit_message: Commit message

        Returns:
            True if changes were committed and pushed successfully, False otherwise
        """
        try:
            # Add all changes
            subprocess.run(
                ["git", "add", "."],
                cwd=repo_dir,
                check=True,
                capture_output=True,
            )

            # Check if there are changes to commit
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            if not status:
                print(f"{Fore.YELLOW}No changes to commit{Style.RESET_ALL}")
                return False

            # Commit changes
            print(f"{Fore.BLUE}Committing changes...{Style.RESET_ALL}")
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=repo_dir,
                check=True,
                capture_output=True,
            )

            # Push changes
            print(f"{Fore.BLUE}Pushing changes to {branch_name}...{Style.RESET_ALL}")

            # Construct remote URL with authentication token
            remote_url = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            auth_remote = remote_url.replace("https://", f"https://{self.token}@")

            # Set the remote URL with authentication token
            subprocess.run(
                ["git", "remote", "set-url", "origin", auth_remote],
                cwd=repo_dir,
                check=True,
                capture_output=True,
            )

            # Push the changes
            subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=repo_dir,
                check=True,
                capture_output=True,
            )

            # Restore the original remote URL
            subprocess.run(
                ["git", "remote", "set-url", "origin", remote_url],
                cwd=repo_dir,
                check=True,
                capture_output=True,
            )

            print(f"{Fore.GREEN}Changes pushed successfully{Style.RESET_ALL}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}Error committing or pushing changes: {e}{Style.RESET_ALL}")
            return False

    def cleanup_branch(self, repo_dir: Path, branch_name: str):
        """Clean up a specific branch in a repository.

        Args:
            repo_dir: Repository directory
            branch_name: Name of the branch to clean up
        """
        if not repo_dir.exists() or not repo_dir.is_dir():
            print(f"{Fore.YELLOW}Repository directory {repo_dir} not found{Style.RESET_ALL}")
            return

        print(f"{Fore.BLUE}Cleaning up branch {branch_name}...{Style.RESET_ALL}")

        try:
            # Get default branch name
            default_branch_cmd = subprocess.run(
                ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
            )

            if default_branch_cmd.returncode != 0:
                # Fallback to main or master if we can't get the default branch name
                default_branches = ["main", "master"]
                default_branch = None

                for branch in default_branches:
                    branch_check = subprocess.run(
                        ["git", "rev-parse", "--verify", f"origin/{branch}"],
                        cwd=repo_dir,
                        capture_output=True,
                        text=True,
                    )

                    if branch_check.returncode == 0:
                        default_branch = branch
                        break

                if not default_branch:
                    print(f"{Fore.YELLOW}Could not determine default branch{Style.RESET_ALL}")
                    return
            else:
                # Extract default branch name from symbolic-ref output
                default_branch = default_branch_cmd.stdout.strip().replace("origin/", "")

            # Switch to default branch
            subprocess.run(
                ["git", "checkout", default_branch],
                cwd=repo_dir,
                check=True,
                capture_output=True,
            )

            # Delete local branch
            subprocess.run(
                ["git", "branch", "-D", branch_name],
                cwd=repo_dir,
                capture_output=True,
            )

            print(f"{Fore.GREEN}Branch {branch_name} cleaned up successfully{Style.RESET_ALL}")
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}Error cleaning up branch {branch_name}: {e}{Style.RESET_ALL}")

    def cleanup(self, repo_dir: Optional[Path] = None):
        """Clean up repository working directory.

        Args:
            repo_dir: Specific repository directory to clean up.
                     If None, cleans up all repositories.
        """
        if repo_dir:
            # Clean up specific repository
            if repo_dir.exists() and repo_dir.is_dir():
                print(f"{Fore.BLUE}Cleaning up repository at {repo_dir}{Style.RESET_ALL}")
                shutil.rmtree(repo_dir)
        else:
            # Clean up all repositories
            if self.repos_dir.exists() and self.repos_dir.is_dir():
                print(f"{Fore.BLUE}Cleaning up all repositories{Style.RESET_ALL}")
                shutil.rmtree(self.repos_dir)
                self.repos_dir.mkdir(exist_ok=True)

    def __del__(self):
        """Clean up all resources when the manager is destroyed."""
        # Delete the entire working directory
        if hasattr(self, "working_dir") and self.working_dir.exists() and self.working_dir.is_dir():
            try:
                shutil.rmtree(self.working_dir)
            except Exception:
                # Ignore errors during cleanup in destructor
                pass
