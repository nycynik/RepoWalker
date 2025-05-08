# RepoWalker
Walk repositories that you own in python.

# Setup

First add your github token, you will need a token that has access to 'repo' for this script, and you can generate it at gitHub (personal token, classic) [here](https://github.com/settings/tokens).

Then you can add it to the .env file, or you can run the script under auth to do so.

```bash
python scripts/auth.py
```

# Development Setup

To set up the development environment with pre-commit hooks:

```bash
# Install dependencies and pre-commit hooks
python scripts/setup_dev.py

# Run pre-commit on all files
pre-commit run --all-files
```

## Pre-commit hooks

This project uses pre-commit to maintain code quality. The following hooks are installed:

- trailing-whitespace: Trims trailing whitespace
- end-of-file-fixer: Makes sure files end with a newline
- check-yaml: Validates YAML files
- check-toml: Validates TOML files
- black: Formats Python code
- isort: Sorts imports
- flake8: Lints Python code
- mypy: Type checks Python code

