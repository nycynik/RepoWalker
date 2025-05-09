#!/usr/bin/env python3
"""
RepoWalker.

Walk through GitHub repositories that you own or from your organizations.

This script is the entry point for the RepoWalker package. It handles command
line arguments and delegates to the appropriate functions in the repowalker package.

Usage:
    python main.py [command] [options]

Commands:
    list        List repositories
    process     Process repositories with AI enhancements

See --help for details on available options for each command.
"""
import sys

from repowalker.main import main

if __name__ == "__main__":
    sys.exit(main())
