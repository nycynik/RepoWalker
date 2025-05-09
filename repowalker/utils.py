"""
Utility functions for RepoWalker.

This module provides utility functions for displaying repository information.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from colorama import Fore, Style


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


def display_repository_details(repo: Dict[str, Any], index: str = None) -> None:
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
        display_repository_details(repo, str(i))

    if len(repos) > display_limit:
        print(f"... and {len(repos) - display_limit} more repositories.")


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
    bar_width = 50  # Maximum width of the bar in characters
    bar_char = "█"  # Character used for the bar
    total_width = max_lang_length + max_count_length + bar_width + 25  # Total width of the report

    # Print report header with more spacing and a nice title
    print(f"\n{Fore.CYAN}╔{'═' * total_width}╗{Style.RESET_ALL}")
    title = "LANGUAGE DISTRIBUTION REPORT"
    padding = (total_width - len(title)) // 2
    print(
        f"{Fore.CYAN}║{' ' * padding}{Fore.GREEN}{title}{Style.RESET_ALL}"
        f"{' ' * (total_width - padding - len(title))}{Fore.CYAN}║{Style.RESET_ALL}"
    )
    print(f"{Fore.CYAN}╠{'═' * total_width}╣{Style.RESET_ALL}")

    # Calculate column header positions for alignment
    lang_header = "LANGUAGE"
    count_header = "COUNT"
    pct_header = "PERCENTAGE"
    bar_header = "DISTRIBUTION (each █ = 2%)"

    # Print column headers with better spacing
    print(
        f"{Fore.CYAN}║ {Fore.YELLOW}{lang_header:<{max_lang_length}}  "
        f"{count_header:>{max_count_length}}  "
        f"{pct_header:<10}  "
        f"{bar_header}{' ' * (bar_width - len(bar_header) + 4)}{Fore.CYAN}║{Style.RESET_ALL}"
    )

    # Separator line
    print(f"{Fore.CYAN}╠{'─' * total_width}╣{Style.RESET_ALL}")

    # Print language statistics with bar graph
    for language, count in sorted_languages:
        percentage = (count / len(repos)) * 100

        # Calculate the bar length proportional to the percentage
        # Each block represents 2% for a more visually appealing graph
        bar_length = int((percentage / 2))

        # Format percentage with consistent width
        pct_str = f"{percentage:5.1f}%"

        # Determine color based on percentage
        if percentage > 50:
            bar_color = Fore.GREEN
        elif percentage > 20:
            bar_color = Fore.YELLOW
        else:
            bar_color = Fore.RED

        # Format the bar with color
        bar = f"{bar_color}{bar_char * bar_length}{Style.RESET_ALL}"

        # Print the formatted line with aligned columns and more spacing
        print(
            f"{Fore.CYAN}║ {Fore.WHITE}{language:<{max_lang_length}}  "
            f"{count:>{max_count_length}}  "
            f"{pct_str:<10}  "
            f"{bar}{' ' * (bar_width - bar_length)}{Fore.CYAN}║{Style.RESET_ALL}"
        )

    # Print footer
    print(f"{Fore.CYAN}╚{'═' * total_width}╝{Style.RESET_ALL}")

    # Print summary of language breakdown
    print(
        f"\n{Fore.GREEN}Summary:{Style.RESET_ALL} Found "
        f"{len(sorted_languages)} different languages "
        f"across {len(repos)} repositories"
    )

    # Group languages by category
    if len(sorted_languages) > 5:
        top_langs = sorted_languages[:5]
        top_count = sum(count for _, count in top_langs)
        top_pct = (top_count / len(repos)) * 100
        print(
            f"{Fore.YELLOW}Top 5 languages account for {top_pct:.1f}% of all repositories{Style.RESET_ALL}"
        )
