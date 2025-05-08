#!/usr/bin/env python3
"""
Setup development environment for RepoWalker.

This script installs development dependencies and sets up pre-commit hooks.
It should be run from the root of the repository.
Usage:
    python scripts/setup_dev.py
"""
import os
import subprocess
import sys
from pathlib import Path


def install_deps():
    """Install development dependencies."""
    print("Installing development dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", ".[dev]"])


def setup_pre_commit():
    """Set up pre-commit hooks."""
    print("Setting up pre-commit hooks...")
    # First check if pre-commit is installed
    try:
        subprocess.check_call(["pre-commit", "--version"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("pre-commit not found, installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pre-commit"])

    # Install the git hook
    subprocess.check_call(["pre-commit", "install"])
    print("Pre-commit hooks installed and will run automatically on each commit!")

    # Run once to initialize
    print("\nRunning pre-commit once to initialize...")
    subprocess.call(
        ["pre-commit", "run", "--all-files"]
    )  # Using call instead of check_call as this might fail on first run


def main():
    """Run the setup."""
    root_dir = Path(__file__).parent.parent
    print(f"Setting up development environment in {root_dir}")

    # Change to the project root directory
    os.chdir(root_dir)

    # Install dependencies
    install_deps()

    # Setup pre-commit
    setup_pre_commit()

    print("\nDevelopment environment setup complete!")
    print("You can now run pre-commit on all files with:")
    print("pre-commit run --all-files")


if __name__ == "__main__":
    main()
