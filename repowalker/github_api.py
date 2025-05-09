"""
GitHub API client for RepoWalker.

This module provides a client for interacting with the GitHub API, including
fetching repository information and creating pull requests.
"""
import os
from typing import Any, Dict, List, Optional

import requests
from colorama import Fore, Style

# Environment variable for the GitHub token
TOKEN_ENV_VAR = "REPOWALKER_AUTH_TOKEN"


class GitHubAPI:
    """GitHub API client wrapper."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        """Initialize the GitHub API client.

        Args:
            token: GitHub API token
        """
        self.token = token or os.environ.get(TOKEN_ENV_VAR)
        if not self.token:
            raise ValueError(
                f"{Fore.RED}Error: GitHub token not found.{Style.RESET_ALL}"
                f"\nPlease run: {Fore.GREEN}python scripts/auth.py{Style.RESET_ALL}"
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "RepoWalker",
            }
        )

    def get_user(self) -> Dict[str, Any]:
        """Get information about the authenticated user.

        Returns:
            User information
        """
        response = self.session.get(f"{self.BASE_URL}/user")
        response.raise_for_status()
        return response.json()

    def list_organizations(self) -> List[Dict[str, Any]]:
        """List organizations for the authenticated user.

        Returns:
            List of organizations
        """
        organizations = []
        page = 1

        print(f"{Fore.GREEN}Fetching organizations...{Style.RESET_ALL}")

        while True:
            response = self.session.get(
                f"{self.BASE_URL}/user/orgs",
                params={
                    "per_page": 100,
                    "page": page,
                },
            )
            response.raise_for_status()

            page_orgs = response.json()
            if not page_orgs:
                break

            organizations.extend(page_orgs)
            page += 1

        return organizations

    def list_owned_repositories(
        self, limit: Optional[int] = None, per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """List repositories owned by the authenticated user.

        Args:
            limit: Maximum number of repositories to return
            per_page: Number of repositories per page

        Returns:
            List of repositories owned by the user
        """
        # First get the authenticated user's login name
        user = self.get_user()
        username = user["login"]

        repositories = []
        page = 1

        print(f"{Fore.GREEN}Fetching repositories owned by you...{Style.RESET_ALL}")

        while True:
            response = self.session.get(
                f"{self.BASE_URL}/users/{username}/repos",
                params={
                    "per_page": per_page,
                    "page": page,
                    "sort": "updated",
                    "direction": "desc",
                    "type": "owner",  # Only fetch repos the user owns
                },
            )
            response.raise_for_status()

            page_repos = response.json()
            if not page_repos:
                break

            repositories.extend(page_repos)

            # If we've reached the limit, stop fetching
            if limit and len(repositories) >= limit:
                repositories = repositories[:limit]
                break

            page += 1

            # If we have more pages, print a progress indicator
            if len(page_repos) == per_page:
                print(
                    f"{Fore.BLUE}Fetched {len(repositories)} repositories so far...{Style.RESET_ALL}"
                )

        return repositories

    def list_user_repositories(
        self, limit: Optional[int] = None, per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """List all repositories the authenticated user has access to.

        Args:
            limit: Maximum number of repositories to return
            per_page: Number of repositories per page

        Returns:
            List of repositories
        """
        repositories = []
        page = 1

        print(f"{Fore.GREEN}Fetching all accessible repositories...{Style.RESET_ALL}")

        while True:
            response = self.session.get(
                f"{self.BASE_URL}/user/repos",
                params={
                    "per_page": per_page,
                    "page": page,
                    "sort": "updated",
                    "direction": "desc",
                },
            )
            response.raise_for_status()

            page_repos = response.json()
            if not page_repos:
                break

            repositories.extend(page_repos)

            # If we've reached the limit, stop fetching
            if limit and len(repositories) >= limit:
                repositories = repositories[:limit]
                break

            page += 1

            # If we have more pages, print a progress indicator
            if len(page_repos) == per_page:
                print(
                    f"{Fore.BLUE}Fetched {len(repositories)} repositories so far...{Style.RESET_ALL}"
                )

        return repositories

    def list_organization_repositories(
        self, org_name: str, limit: Optional[int] = None, per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """List repositories for a specific organization.

        Args:
            org_name: Organization name
            limit: Maximum number of repositories to return
            per_page: Number of repositories per page

        Returns:
            List of repositories
        """
        repositories = []
        page = 1

        print(
            f"{Fore.GREEN}Fetching repositories for organization {Fore.CYAN}{org_name}{Style.RESET_ALL}..."
        )

        while True:
            response = self.session.get(
                f"{self.BASE_URL}/orgs/{org_name}/repos",
                params={
                    "per_page": per_page,
                    "page": page,
                    "sort": "updated",
                    "direction": "desc",
                },
            )
            response.raise_for_status()

            page_repos = response.json()
            if not page_repos:
                break

            repositories.extend(page_repos)

            # If we've reached the limit, stop fetching
            if limit and len(repositories) >= limit:
                repositories = repositories[:limit]
                break

            page += 1

            # If we have more pages, print a progress indicator
            if len(page_repos) == per_page:
                print(
                    f"{Fore.BLUE}Fetched {len(repositories)} repositories so far...{Style.RESET_ALL}"
                )

        return repositories

    def get_repository_details(self, repo_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific repository.

        Args:
            repo_name: Full repository name (owner/repo)

        Returns:
            Repository details
        """
        response = self.session.get(f"{self.BASE_URL}/repos/{repo_name}")
        response.raise_for_status()
        return response.json()

    def create_pull_request(
        self, repo_name: str, head: str, base: str, title: str, body: str
    ) -> Dict[str, Any]:
        """Create a pull request in the specified repository.

        Args:
            repo_name: Full repository name (owner/repo)
            head: The name of the branch where your changes are implemented
            base: The name of the branch you want to merge your changes into
            title: The title of the pull request
            body: The contents of the pull request

        Returns:
            Pull request details
        """
        print(f"{Fore.BLUE}Creating pull request in {repo_name}...{Style.RESET_ALL}")

        url = f"{self.BASE_URL}/repos/{repo_name}/pulls"
        data = {
            "title": title,
            "head": head,
            "base": base,
            "body": body,
        }

        response = self.session.post(url, json=data)
        response.raise_for_status()
        pr_data = response.json()

        print(
            f"{Fore.GREEN}Pull request created successfully: "
            f"{Fore.CYAN}{pr_data['html_url']}{Style.RESET_ALL}"
        )

        return pr_data
