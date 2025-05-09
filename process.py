#!/usr/bin/env python3
"""
RepoWalker Script.

This script provides a command-line interface for the RepoWalker package.
It allows listing repositories and processing them with AI enhancements.
"""
import sys

from repowalker.main import main

if __name__ == "__main__":
    sys.exit(main())
