[![Continuous Integration](https://github.com/nearform/pyspark-common-utilities/actions/workflows/ci.yml/badge.svg)](https://github.com/nearform/pyspark-common-utilities/actions/workflows/ci.yml)

# Python Project Template

Standard Python project template for Nearform projects. Includes linting, type checking, testing, and commit message validation.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

## Quick Start

```bash
# Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install python version
uv python install 3.13

# Create venv
uv venv .venv --python 3.13

# Activate venv
source .venv/bin/activate

# Install dependencies
uv sync --extra dev

# Install pre-commit hooks
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg
```

## Configuration

Update `pyproject.toml` with your project details.

## Development Commands
```bash
# Run all checks manually
uv run ruff check .              # Lint
uv run ruff format .             # Format
uv run mypy .                    # Type check
uv run pytest                    # Test
```

## Pre-commit Hooks

- **ruff**: Lints (check only, no auto-fix, only on staged files)
- **ruff-format**: Format validation (check only, no auto-format, only on staged files)
- **mypy**: Type checking (only on staged files)
- **pytest**: Full test suite
- **conventional-pre-commit**: Commit message validation

### Commit workflow
```bash
# 1. Commit triggers pre-commit checks
git commit -m "feat: add new feature"

# 2. If checks fail, fix manually
uv run ruff check --fix .
uv run ruff format .

# 3. Review and stage changes
git diff
git add .

# 4. Commit again
git commit -m "feat: add new feature"
```

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):
```
type(scope): subject

[optional body]
```

**Valid types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

## CI/CD

GitHub Actions runs on every push and PR:
- Linting (ruff)
- Type checking (mypy)
- Tests (pytest)
- Auto-merge for Dependabot PRs (after checks pass)

## Versioning and publishing (Optional)

### Manual Release Workflow

The repository includes a manual release workflow that can be triggered from GitHub Actions.
**Note**: The workflow is configured to release from the `master` branch.

1. Go to **Actions** → **Publish to PyPI**
2. Click **Run workflow**
3. Select version bump type (`patch`, `minor`, or `major`)
4. The workflow will:
   - Bump the version in `pyproject.toml`
   - Create a commit and Git tag
   - Build the package
   - Create a GitHub Release
   - Publish to PyPI (if configured)

### PyPI Publication (Optional)

PyPI publication uses **Trusted Publishing** (OIDC) and is **optional**. If not configured, the package will still be released on GitHub but not published to PyPI.

#### Setup PyPI Trusted Publishing

If you want to publish to PyPI, configure Trusted Publishing:

1. **Create a PyPI account** at https://pypi.org (or https://test.pypi.org for testing)

2. **Go to your PyPI account settings** → **Publishing** → **Add a new pending publisher**

3. **Fill in the form**:
   - **PyPI Project Name**: `your-project-name` (must match `name` in `pyproject.toml`)
   - **Owner**: Your GitHub username or organization
   - **Repository name**: `your-repo-name`
   - **Workflow name**: `release.yml` (or whatever you named your workflow file)
   - **Environment name**: Leave empty (or use `release` if you configure one)

4. **Save** - The publisher will be in "pending" state until the first successful publish

5. **Run the workflow** - On first run, PyPI will activate the trusted publisher

[![banner](https://raw.githubusercontent.com/nearform/.github/refs/heads/master/assets/os-banner-green.svg)](https://www.nearform.com/contact/?utm_source=open-source&utm_medium=banner&utm_campaign=os-project-pages)
