#!/usr/bin/env python3
"""
Setup development environment for RepoWalker.
"""
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
    subprocess.check_call(["pre-commit", "install"])
    print("Pre-commit hooks installed!")


def main():
    """Main setup function."""
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
    import os
    main()