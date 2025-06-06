#!/usr/bin/env python3
"""
RepoWalker.

Walk through GitHub repositories that you own or from your organizations.

This script fetches repositories from the authenticated user's GitHub account or
from a specified organization. It displays a summary of the repositories, including
the number of stars, forks, and languages used. It also allows saving the repository
data to a JSON file.
Usage:
    python main.py [OPTIONS]
Options:
    -l, --languages        Show language statistics
    -o, --output TEXT      Save repository data to JSON file
    -m, --limit INTEGER    Limit the number of repositories to fetch (useful for testing)
    --org TEXT             Organization name (skip the organization selection prompt)
    --personal             Use personal repositories (skip the organization selection prompt)
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from colorama import Fore, Style
from dotenv import load_dotenv

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
        print(
            f"{i}. {Fore.CYAN}{org['login']}{Style.RESET_ALL} - {org.get('description', 'No description')}"
        )

    while True:
        try:
            choice = input(
                f"\n{Fore.GREEN}Select an organization (0-{len(organizations)}) or press Enter for personal "
                f"repos: {Style.RESET_ALL}"
            )

            # Default to personal repositories
            if not choice.strip():
                return None

            choice_num = int(choice)
            if choice_num == 0:
                return None
            elif 1 <= choice_num <= len(organizations):
                return organizations[choice_num - 1]["login"]
            else:
                print(
                    f"{Fore.RED}Invalid choice. Please select a number between 0 and {len(organizations)}."
                    f"{Style.RESET_ALL}"
                )
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
        reverse=True,
    )

    display_limit = min(limit, len(repos)) if limit else len(repos)
    repos_to_display = sorted_repos[:display_limit]

    print(f"\n{Fore.GREEN}Found {len(repos)} repositories:{Style.RESET_ALL}\n")

    for i, repo in enumerate(repos_to_display, 1):
        display_respository_details(repo, str(i))

    if len(repos) > display_limit:
        print(f"... and {len(repos) - display_limit} more repositories.")


def format_relative_time(time_str: str) -> str:
    """Format a time string into a human-readable relative time.

    Args:
        time_str: ISO-formatted time string from GitHub API

    Returns:
        Human-readable relative time (e.g., "2 days ago")
    """
    try:
        # Parse the GitHub timestamp format
        time_obj = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
        now = datetime.utcnow()

        # Calculate the difference
        diff = now - time_obj

        # Convert to appropriate units
        seconds = diff.total_seconds()
        minutes = seconds // 60
        hours = minutes // 60
        days = diff.days
        months = days // 30
        years = days // 365

        if years > 0:
            return f"{int(years)} year{'s' if years != 1 else ''} ago"
        elif months > 0:
            return f"{int(months)} month{'s' if months != 1 else ''} ago"
        elif days > 0:
            return f"{int(days)} day{'s' if days != 1 else ''} ago"
        elif hours > 0:
            return f"{int(hours)} hour{'s' if hours != 1 else ''} ago"
        elif minutes > 0:
            return f"{int(minutes)} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "just now"
    except Exception:
        # Fallback to original string if parsing fails
        return time_str


def display_respository_details(repo: Dict[str, Any], index: str = None) -> None:
    """Display detailed information about a repository.

    Args:
        repo: Repository information
        index: Optional index for listing repositories
    """
    bar = f"{Fore.LIGHTBLACK_EX} | {Style.RESET_ALL}"

    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    language = repo.get("language", "Unknown")
    number = " " * 3 if not index else f"{int(index):2d}."

    # Format the timestamps
    updated_at = format_relative_time(repo.get("updated_at", ""))
    created_at = format_relative_time(repo.get("created_at", ""))

    # Format for size
    size_kb = repo.get("size", 0)
    if size_kb >= 1024:
        size_str = f"{size_kb/1024:.1f} MB"
    else:
        size_str = f"{size_kb} KB"

    print(f"{number} {Fore.CYAN}{repo['full_name']}{Style.RESET_ALL}")
    print(
        f"    {Fore.GREEN}Description:{Style.RESET_ALL} {repo.get('description', 'No description')}"
    )
    print(
        f"    {Fore.GREEN}Language:{Style.RESET_ALL} {language}{bar}{Fore.GREEN}Stars:{Style.RESET_ALL} {stars} "
        f"{bar} {Fore.GREEN}Forks:{Style.RESET_ALL} {forks}{bar}{Fore.GREEN}Size:{Style.RESET_ALL} {size_str}"
    )
    print(
        f"    {Fore.GREEN}Updated:{Style.RESET_ALL} {updated_at}{bar}{Fore.GREEN}"
        f"Created:{Style.RESET_ALL} {created_at}{Style.RESET_ALL}"
    )
    print(f"    {Fore.GREEN}URL:{Style.RESET_ALL} {repo['html_url']}")
    print()


def display_repository_languages(repos: List[Dict[str, Any]]) -> None:
    """Display language statistics for repositories with a bar graph.

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

    # Calculate the longest language name for alignment
    max_lang_length = max([len(lang) for lang, _ in sorted_languages], default=10)
    max_count_length = max([len(str(count)) for _, count in sorted_languages], default=3)

    # Define bar graph settings
    bar_width = 40  # Maximum width of the bar in characters
    bar_char = "█"  # Character used for the bar

    # Print header
    print(
        f"\n{Fore.CYAN}╔{'═' * (max_lang_length + max_count_length + bar_width + 15)}╗{Style.RESET_ALL}"
    )
    print(
        f"{Fore.CYAN}║ {Fore.GREEN}LANGUAGE DISTRIBUTION"
        f"{' ' * (max_lang_length + max_count_length + bar_width - 12)}     {Fore.CYAN}║{Style.RESET_ALL}"
    )
    print(
        f"{Fore.CYAN}╠{'═' * (max_lang_length + max_count_length + bar_width + 15)}╣{Style.RESET_ALL}"
    )

    # Calculate column header positions for alignment
    lang_header = "LANGUAGE"
    count_header = "#"
    pct_header = "%"
    bar_header = "DISTRIBUTION"

    # Print column headers
    print(
        f"{Fore.CYAN}║ {Fore.YELLOW}{lang_header}{' ' * (max_lang_length - len(lang_header) + 2)}"
        f"{count_header}{' ' * (max_count_length - len(count_header) + 2)}"
        f" {pct_header}{' ' * 4}{bar_header}{' ' * (bar_width - len(bar_header) - 2)}"
        f"{Fore.CYAN}      ║{Style.RESET_ALL}"
    )
    print(
        f"{Fore.CYAN}╠{'─' * (max_lang_length + max_count_length + bar_width + 15)}╣{Style.RESET_ALL}"
    )

    # Print language statistics with bar graph
    for language, count in sorted_languages:
        percentage = (count / len(repos)) * 100
        # Calculate the bar length proportional to the percentage (max is bar_width)
        bar_length = int((percentage / 100) * bar_width)

        # Determine color based on percentage
        if percentage > 50:
            bar_color = Fore.GREEN
        elif percentage > 20:
            bar_color = Fore.YELLOW
        else:
            bar_color = Fore.RED

        # Format the bar with color
        bar = f"{bar_color}{bar_char * bar_length}{Style.RESET_ALL}"

        # Print the formatted line with aligned columns
        print(
            f"{Fore.CYAN}║ {Fore.WHITE}{language:{max_lang_length}} {count:{max_count_length}} "
            f"{percentage:6.1f}% {bar}{' ' * (bar_width - bar_length + 4)}{Fore.CYAN}║{Style.RESET_ALL}"
        )

    # Print footer
    print(
        f"{Fore.CYAN}╚{'═' * (max_lang_length + max_count_length + bar_width + 15)}╝{Style.RESET_ALL}"
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Walk through GitHub repositories")
    parser.add_argument("--languages", "-l", action="store_true", help="Show language statistics")
    parser.add_argument("--output", "-o", help="Save repository data to JSON file")
    parser.add_argument(
        "--limit",
        "-m",
        type=int,
        help="Limit the number of repositories to fetch (useful for testing)",
    )
    parser.add_argument("--org", help="Organization name (skip the organization selection prompt)")
    parser.add_argument(
        "--personal",
        action="store_true",
        help="Show only repositories owned by you (default when no organization is selected)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all repositories you have access to, including collaborations and organization repositories",
    )
    return parser.parse_args()


def main() -> None:
    """Process all the repositories."""
    args = parse_args()

    # Create GitHub API client
    github = GitHubAPI()

    try:
        # Get user information
        user = github.get_user()
        print(f"{Fore.GREEN}Authenticated as {Fore.CYAN}{user['login']}{Style.RESET_ALL}")

        org_name = None

        # Handle repository selection
        if args.all:
            print(
                f"{Fore.GREEN}\nFetching {Fore.CYAN}all accessible{Fore.GREEN} repositories.{Style.RESET_ALL}"
            )
            repositories = github.list_user_repositories(limit=args.limit)
        elif args.personal:
            print(
                f"{Fore.GREEN}\nFetching {Fore.CYAN}personal{Fore.GREEN} repositories (owned by you).{Style.RESET_ALL}"
            )
            repositories = github.list_owned_repositories(limit=args.limit)
        elif args.org:
            org_name = args.org
            print(f"{Fore.GREEN}\nUsing organization: {Fore.CYAN}{org_name}{Style.RESET_ALL}")
            repositories = github.list_organization_repositories(org_name, limit=args.limit)
        else:
            # List organizations and prompt for selection
            organizations = github.list_organizations()

            if organizations:
                # Prompt user to select an organization
                org_name = select_organization(organizations)

                if org_name:
                    print(
                        f"{Fore.GREEN}\nSelected organization: {Fore.CYAN}{org_name}{Style.RESET_ALL}"
                    )
                    repositories = github.list_organization_repositories(org_name, limit=args.limit)
                else:
                    print(
                        f"{Fore.GREEN}\nFetching {Fore.CYAN}personal{Fore.GREEN} "
                        f"repositories (owned by you).{Style.RESET_ALL}"
                    )
                    repositories = github.list_owned_repositories(limit=args.limit)
            else:
                print(
                    f"{Fore.YELLOW}\nNo organizations found. Using personal repositories.{Style.RESET_ALL}"
                )
                repositories = github.list_owned_repositories(limit=args.limit)

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
