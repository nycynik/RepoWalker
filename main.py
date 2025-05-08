#!/usr/bin/env python3
"""
RepoWalker - Walk through GitHub repositories that you own or from your organizations.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
from colorama import Fore, Style
from dotenv import load_dotenv
from tqdm import tqdm

# Load .env file if it exists
load_dotenv()

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
            print(f"{Fore.RED}Error: GitHub token not found.{Style.RESET_ALL}")
            print(f"Please run: {Fore.GREEN}python scripts/auth.py{Style.RESET_ALL}")
            sys.exit(1)

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "RepoWalker",
        })

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

    def list_user_repositories(self, limit: Optional[int] = None, per_page: int = 100) -> List[Dict[str, Any]]:
        """List repositories for the authenticated user.

        Args:
            limit: Maximum number of repositories to return
            per_page: Number of repositories per page

        Returns:
            List of repositories
        """
        repositories = []
        page = 1

        print(f"{Fore.GREEN}Fetching your personal repositories...{Style.RESET_ALL}")

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
                print(f"{Fore.BLUE}Fetched {len(repositories)} repositories so far...{Style.RESET_ALL}")

        return repositories

    def list_organization_repositories(self, org_name: str, limit: Optional[int] = None, per_page: int = 100) -> List[Dict[str, Any]]:
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

        print(f"{Fore.GREEN}Fetching repositories for organization {Fore.CYAN}{org_name}{Style.RESET_ALL}...")

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
                print(f"{Fore.BLUE}Fetched {len(repositories)} repositories so far...{Style.RESET_ALL}")

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


def select_organization(organizations: List[Dict[str, Any]]) -> Optional[str]:
    """Prompt user to select an organization.

    Args:
        organizations: List of organizations

    Returns:
        Selected organization login name or None for personal repositories
    """
    print(f"\n{Fore.GREEN}Your Organizations:{Style.RESET_ALL}")
    print(f"0. {Fore.CYAN}Personal Repositories{Style.RESET_ALL}")

    for i, org in enumerate(organizations, 1):
        print(f"{i}. {Fore.CYAN}{org['login']}{Style.RESET_ALL} - {org.get('description', 'No description')}")

    while True:
        try:
            choice = input(f"\n{Fore.GREEN}Select an organization (0-{len(organizations)}) or press Enter for personal repos: {Style.RESET_ALL}")

            # Default to personal repositories
            if not choice.strip():
                return None

            choice_num = int(choice)
            if choice_num == 0:
                return None
            elif 1 <= choice_num <= len(organizations):
                return organizations[choice_num - 1]["login"]
            else:
                print(f"{Fore.RED}Invalid choice. Please select a number between 0 and {len(organizations)}.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")


def display_repository_summary(repos: List[Dict[str, Any]], limit: Optional[int] = 20) -> None:
    """Display a summary of repositories.

    Args:
        repos: List of repository information
        limit: Maximum number of repositories to display
    """
    if not repos:
        print(f"\n{Fore.YELLOW}No repositories found.{Style.RESET_ALL}")
        return

    # Sort repositories by popularity (stars + watchers)
    sorted_repos = sorted(
        repos,
        key=lambda r: (r.get("stargazers_count", 0) + r.get("watchers_count", 0)),
        reverse=True
    )

    display_limit = min(limit, len(repos)) if limit else len(repos)
    repos_to_display = sorted_repos[:display_limit]

    print(f"\n{Fore.GREEN}Found {len(repos)} repositories:{Style.RESET_ALL}\n")

    for i, repo in enumerate(repos_to_display, 1):
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        language = repo.get("language", "Unknown")

        print(f"{i:2d}. {Fore.CYAN}{repo['full_name']}{Style.RESET_ALL}")
        print(f"    Description: {repo.get('description', 'No description')}")
        print(f"    Language: {language} | Stars: {stars} | Forks: {forks}")
        print(f"    URL: {repo['html_url']}")
        print()

    if len(repos) > display_limit:
        print(f"... and {len(repos) - display_limit} more repositories.")


def display_repository_languages(repos: List[Dict[str, Any]]) -> None:
    """Display language statistics for repositories.

    Args:
        repos: List of repository information
    """
    if not repos:
        return

    # Count languages
    language_count = {}
    for repo in repos:
        language = repo.get("language")
        if language:
            language_count[language] = language_count.get(language, 0) + 1

    # Sort by count
    sorted_languages = sorted(language_count.items(), key=lambda x: x[1], reverse=True)

    print(f"\n{Fore.GREEN}Language distribution:{Style.RESET_ALL}")
    for language, count in sorted_languages:
        percentage = (count / len(repos)) * 100
        print(f"{language}: {count} ({percentage:.1f}%)")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Walk through GitHub repositories")
    parser.add_argument(
        "--languages", "-l", action="store_true",
        help="Show language statistics"
    )
    parser.add_argument(
        "--output", "-o",
        help="Save repository data to JSON file"
    )
    parser.add_argument(
        "--limit", "-m", type=int,
        help="Limit the number of repositories to fetch (useful for testing)"
    )
    parser.add_argument(
        "--org",
        help="Organization name (skip the organization selection prompt)"
    )
    parser.add_argument(
        "--personal", action="store_true",
        help="Use personal repositories (skip the organization selection prompt)"
    )
    return parser.parse_args()


def main() -> None:
    """Main function."""
    args = parse_args()

    # Create GitHub API client
    github = GitHubAPI()

    try:
        # Get user information
        user = github.get_user()
        print(f"{Fore.GREEN}Authenticated as {Fore.CYAN}{user['login']}{Style.RESET_ALL}")

        org_name = None

        # Handle organization selection
        if args.personal:
            print(f"{Fore.GREEN}\nUsing {Fore.CYAN}personal{Fore.GREEN} repositories.{Style.RESET_ALL}")
        elif args.org:
            org_name = args.org
            print(f"{Fore.GREEN}\nUsing organization: {Fore.CYAN}{org_name}{Style.RESET_ALL}")
        else:
            # List organizations
            organizations = github.list_organizations()

            if organizations:
                # Prompt user to select an organization
                org_name = select_organization(organizations)

                if org_name:
                    print(f"{Fore.GREEN}\nSelected organization: {Fore.CYAN}{org_name}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.GREEN}\nUsing {Fore.CYAN}personal{Fore.GREEN} repositories.{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}\nNo organizations found. Using personal repositories.{Style.RESET_ALL}")

        # Fetch repositories based on selection
        if org_name:
            repositories = github.list_organization_repositories(org_name, limit=args.limit)
        else:
            repositories = github.list_user_repositories(limit=args.limit)

        # Display repository summary
        display_repository_summary(repositories)

        # Display language statistics if requested
        if args.languages:
            display_repository_languages(repositories)

        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            with open(output_path, "w") as f:
                json.dump(repositories, f, indent=2)
            print(f"\n{Fore.GREEN}Saved repository data to {output_path}{Style.RESET_ALL}")

    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
