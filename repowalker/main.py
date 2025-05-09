"""
Main module for RepoWalker.

This module provides the entry points for the RepoWalker command-line interface.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from colorama import Fore, Style
from dotenv import load_dotenv

from .ai_service import get_ai_service
from .github_api import GitHubAPI
from .processor import RepoProcessor

# from .repository import RepositoryManager

# Load .env file if it exists
load_dotenv()

TOKEN_ENV_VAR = "REPOWALKER_AUTH_TOKEN"


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


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Walk through GitHub repositories")

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # 'list' command for listing repositories
    list_parser = subparsers.add_parser("list", help="List repositories")
    list_parser.add_argument(
        "--languages", "-l", action="store_true", help="Show language statistics"
    )
    list_parser.add_argument("--output", "-o", help="Save repository data to JSON file")
    list_parser.add_argument(
        "--limit",
        "-m",
        type=int,
        help="Limit the number of repositories to fetch (useful for testing)",
    )
    list_parser.add_argument(
        "--org", help="Organization name (skip the organization selection prompt)"
    )
    list_parser.add_argument(
        "--personal",
        action="store_true",
        help="Show only repositories owned by you (default when no organization is selected)",
    )
    list_parser.add_argument(
        "--all",
        action="store_true",
        help="Show all repositories you have access to, including collaborations and organization repositories",
    )

    # 'process' command for enhancing repositories
    process_parser = subparsers.add_parser(
        "process", help="Process repositories with AI enhancements"
    )
    process_parser.add_argument(
        "--limit",
        "-m",
        type=int,
        help="Limit the number of repositories to fetch (useful for testing)",
    )
    process_parser.add_argument(
        "--org", help="Organization name (skip the organization selection prompt)"
    )
    process_parser.add_argument(
        "--personal",
        action="store_true",
        help="Process only repositories owned by you (default when no organization is selected)",
    )
    process_parser.add_argument(
        "--all",
        action="store_true",
        help="Process all repositories you have access to, including collaborations and organization repositories",
    )
    process_parser.add_argument(
        "--file",
        default="README.md",
        help="Name of the file to generate (default: README.md)",
    )
    process_parser.add_argument(
        "--branch-prefix",
        default="docs/auto-gen",
        help="Prefix for branch names (default: docs/auto-gen)",
    )
    process_parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Do not clean up repository directories after processing",
    )
    process_parser.add_argument(
        "--service",
        default="mock",
        choices=["mock"],
        help="AI service to use for generating content (default: mock)",
    )

    # If no command is provided, default to 'list'
    if len(sys.argv) == 1:
        return parser.parse_args(["list"])

    return parser.parse_args()


def fetch_repositories(github: GitHubAPI, args: argparse.Namespace) -> List[Dict[str, Any]]:
    """Fetch repositories based on command-line arguments.

    Args:
        github: GitHub API client
        args: Command-line arguments

    Returns:
        List of repository information
    """
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

    return repositories


def list_command(args: argparse.Namespace, github: GitHubAPI) -> None:
    """Run the 'list' command.

    Args:
        args: Command-line arguments
        github: GitHub API client
    """
    from repowalker.utils import display_repository_languages, display_repository_summary

    try:
        # Fetch repositories
        repositories = fetch_repositories(github, args)

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

    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


def process_command(args: argparse.Namespace, github: GitHubAPI) -> None:
    """Run the 'process' command.

    Args:
        args: Command-line arguments
        github: GitHub API client
    """
    try:
        # Fetch repositories
        repositories = fetch_repositories(github, args)

        if not repositories:
            print(f"{Fore.YELLOW}No repositories found to process.{Style.RESET_ALL}")
            return

        # Ask for confirmation before processing
        print(f"\n{Fore.YELLOW}About to process {len(repositories)} repositories:{Style.RESET_ALL}")
        for i, repo in enumerate(repositories[:5], 1):
            print(f"  {i}. {Fore.CYAN}{repo['full_name']}{Style.RESET_ALL}")

        if len(repositories) > 5:
            print(f"  ... and {len(repositories) - 5} more repositories")

        confirm = input(f"\n{Fore.YELLOW}Do you want to continue? (yes/no): {Style.RESET_ALL}")
        if confirm.lower() != "yes":
            print(f"{Fore.YELLOW}Operation cancelled.{Style.RESET_ALL}")
            return

        # Create AI service and repository processor
        ai_service = get_ai_service(args.service)
        repo_processor = RepoProcessor(
            github_api=github, ai_service=ai_service, cleanup_after_processing=not args.no_cleanup
        )

        # Process repositories
        results = repo_processor.process_repositories(
            repositories, branch_prefix=args.branch_prefix, output_file=args.file
        )

        # Show results
        if results["success"]:
            print(f"\n{Fore.GREEN}Successfully processed repositories:{Style.RESET_ALL}")
            for result in results["success"]:
                repo_name = result["repo"]["full_name"]
                pr_url = result["pr"]["html_url"]
                print(f"  {Fore.CYAN}{repo_name}{Style.RESET_ALL} -> {pr_url}")

        if results["failure"]:
            print(f"\n{Fore.RED}Failed to process repositories:{Style.RESET_ALL}")
            for result in results["failure"]:
                repo_name = result["repo"]["full_name"]
                print(f"  {Fore.RED}{repo_name}{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


def main() -> None:
    """Run the main function."""
    args = parse_args()

    # Create GitHub API client
    github = GitHubAPI()

    # Handle commands
    if args.command == "list":
        list_command(args, github)
    elif args.command == "process":
        process_command(args, github)
    else:
        print(f"{Fore.RED}Unknown command: {args.command}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()
