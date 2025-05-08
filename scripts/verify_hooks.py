#!/usr/bin/env python3
"""
Verify that pre-commit hooks are installed and running.

This script checks if the pre-commit hooks are installed and verifies that they work
by attempting to commit a file with style issues.
Usage:
    python scripts/verify_hooks.py
"""
import subprocess
import sys
from pathlib import Path

from colorama import Fore, Style


def check_hook_installation():
    """Check if pre-commit hooks are installed."""
    print(f"{Fore.GREEN}Checking pre-commit hook installation...{Style.RESET_ALL}")

    repo_root = Path(__file__).parent.parent
    hook_path = repo_root / ".git" / "hooks" / "pre-commit"

    if hook_path.exists():
        print(f"{Fore.GREEN}✓ Pre-commit hook is installed at: {hook_path}{Style.RESET_ALL}")

        # Check content to make sure it's the pre-commit hook
        with open(hook_path, "r") as f:
            content = f.read()
            if "pre-commit" in content:
                print(f"{Fore.GREEN}✓ Hook content is a valid pre-commit hook{Style.RESET_ALL}")
            else:
                print(
                    f"{Fore.RED}✗ Hook exists but doesn't seem to be a pre-commit hook.{Style.RESET_ALL}"
                )
                return False
    else:
        print(f"{Fore.RED}✗ Pre-commit hook is not installed!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Run 'python scripts/setup_dev.py' to install hooks.{Style.RESET_ALL}")
        return False

    return True


def verify_hooks_run():
    """Create a test file with an intentional style issue to verify hooks catch it."""
    print(f"\n{Fore.GREEN}Testing that hooks will detect issues...{Style.RESET_ALL}")

    # Create a temporary file with an obvious style issue
    repo_root = Path(__file__).parent.parent
    test_file = repo_root / "test_hooks_verification.py"

    try:
        # Create a file with style issues (no newline at end, bad indentation, long line)
        with open(test_file, "w") as f:
            f.write(
                '"""Test file for verifying pre-commit hooks."""\ndef bad_function():\n'
                '  print("This is indented with 2 spaces and not 4, which should be caught by hooks")'
                '\n\nprint("This is a very long line that should definitely be caught by the Black '
                'formatter since it exceeds the line length limit")'
            )

        # Try to commit the file
        print(
            f"{Fore.YELLOW}Attempting to commit a file with style issues. This should fail.{Style.RESET_ALL}"
        )
        print(f"{Fore.YELLOW}If hooks are working, the commit will be aborted.{Style.RESET_ALL}")

        # Add the file to git
        subprocess.run(["git", "add", str(test_file)], check=True)

        # Try to commit (this should fail if hooks are working)
        result = subprocess.run(
            ["git", "commit", "-m", "Testing pre-commit hooks"], capture_output=True, text=True
        )

        # Clean up
        subprocess.run(["git", "reset", "HEAD", str(test_file)], check=True)
        test_file.unlink()

        if result.returncode != 0:
            print(f"{Fore.GREEN}✓ Pre-commit hooks correctly blocked the commit!{Style.RESET_ALL}")
            print(f"{Fore.GREEN}✓ Hooks are working properly.{Style.RESET_ALL}")
            return True
        else:
            print(
                f"{Fore.RED}✗ Pre-commit hooks failed to block the commit with style issues.{Style.RESET_ALL}"
            )
            print(f"{Fore.YELLOW}Output: {result.stdout}{Style.RESET_ALL}")
            return False

    except Exception as e:
        print(f"{Fore.RED}Error during verification: {e}{Style.RESET_ALL}")
        # Clean up in case of error
        if test_file.exists():
            test_file.unlink()
        return False


def main():
    """Verify hooks."""
    print(f"{Fore.CYAN}Pre-commit Hook Verification{Style.RESET_ALL}")
    print(f"{Fore.CYAN}========================={Style.RESET_ALL}")

    # First check that hooks are installed
    if not check_hook_installation():
        sys.exit(1)

    # Then verify they work by attempting a commit that should fail
    if verify_hooks_run():
        print(
            f"\n{Fore.GREEN}All checks passed! Pre-commit hooks are properly installed and working.{Style.RESET_ALL}"
        )
    else:
        print(
            f"\n{Fore.RED}Verification failed. Please run 'python scripts/setup_dev.py' to fix issues.{Style.RESET_ALL}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
