#!/usr/bin/env python3
"""
Authentication token management for RepoWalker.
"""
import os
import sys
import json
import getpass
from pathlib import Path

TOKEN_ENV_VAR = "REPOWALKER_AUTH_TOKEN"


def get_token_from_user():
    """Prompt user for authentication token."""
    print("Please enter your authentication token:")
    token = getpass.getpass()
    return token


def store_token(token):
    """Store token in .env file."""
    env_path = Path(".env")

    # Read existing .env file if it exists
    if env_path.exists():
        with open(env_path, "r") as f:
            lines = f.readlines()

        # Filter out any existing TOKEN_ENV_VAR lines
        lines = [line for line in lines if not line.startswith(f"{TOKEN_ENV_VAR}=")]
    else:
        lines = []

    # Add the token line
    lines.append(f"{TOKEN_ENV_VAR}={token}\n")

    # Write back to .env file
    with open(env_path, "w") as f:
        f.writelines(lines)

    print(f"Token saved to .env file. To use in your shell, run:")
    print(f"export {TOKEN_ENV_VAR}=\"{token}\"")
    print("Or add this to your ~/.bashrc or ~/.zshrc file")


def export_token(token):
    """Export token to environment variable for current session."""
    os.environ[TOKEN_ENV_VAR] = token
    print(f"Token exported to environment variable {TOKEN_ENV_VAR} for this session")


def main():
    """Main function to get and store authentication token."""
    # Check if token is already in environment
    token = os.environ.get(TOKEN_ENV_VAR)

    if not token:
        token = get_token_from_user()

    # Store token in .env file
    store_token(token)

    # Export to environment variable for current session
    export_token(token)

    print(f"\nToken is ready for use. Access it in Python with:")
    print(f"import os")
    print(f"token = os.environ.get('{TOKEN_ENV_VAR}')")


if __name__ == "__main__":
    main()