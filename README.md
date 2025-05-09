# RepoWalker
Walk repositories that you own in Python.

## Setup

First add your GitHub token, you will need a token that has access to 'repo' for this script, and you can generate it at GitHub (personal token, classic) [here](https://github.com/settings/tokens).

Then you can add it to the .env file, or you can run the auth script to do so:

```bash
python scripts/auth.py
```

## Usage

Once you have set up your token, you can use the main script to list your repositories:

```bash
# List repositories with interactive organization selection
python main.py

# Show language statistics with visual bar graph
python main.py --languages

# Save repository data to a JSON file
python main.py --output repos.json

# List only repositories you own (skip organization selection)
python main.py --personal

# List all repositories you have access to (including collaborations)
python main.py --all

# List repositories for a specific organization
python main.py --org your-org-name

# Limit the number of repositories (useful for testing)
python main.py --limit 5
```

By default, the script will:
1. List your organizations
2. Ask you to select which organization's repositories to list (or your personal repos)
3. If personal repositories are selected, show only repositories you own (not collaborations)
4. Show those repositories sorted by popularity (stars + watchers), including:
   - Repository name and description
   - Programming language, star count, fork count, and size
   - Human-readable relative times for when repositories were updated and created ("2 days ago" vs date)

# Development Setup

To set up the development environment with pre-commit hooks:

```bash
# Install dependencies and pre-commit hooks
python scripts/setup_dev.py

# Run pre-commit on all files manually (helpful when setting up initially)
pre-commit run --all-files
```

## Pre-commit hooks

This project uses pre-commit to maintain code quality. The hooks run automatically when you commit changes, ensuring that all code meets the project's quality standards.

If a hook fails during a commit:
1. The failed files will be modified by the hooks to meet the standards
2. You'll need to add those changes and commit again

The following hooks are installed and run automatically before each commit:

- trailing-whitespace: Trims trailing whitespace
- end-of-file-fixer: Makes sure files end with a newline
- check-yaml: Validates YAML files
- check-toml: Validates TOML files
- black: Formats Python code
- isort: Sorts imports
- flake8: Lints Python code
