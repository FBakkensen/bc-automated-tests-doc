# Copilot Agent Environment Setup

This document describes how to set up the GitHub Copilot Agent environment for the
pdf2md project, following GitHub's recommendations for [preinstalling tools and
dependencies](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/customize-the-agent-environment#preinstalling-tools-or-dependencies-in-copilots-environment).

## Overview

The setup script automatically installs and configures all tools and dependencies
needed for Copilot Agents to work effectively with this project, including:

- **Python 3.11+** with all project dependencies
- **Node.js 20+** and npm for documentation tools
- **Documentation tools**: markdownlint-cli, mermaid-cli, pandoc
- **Code quality tools**: ruff, mypy, pytest
- **Pre-commit hooks** for automated quality checks

## Quick Start

To set up the Copilot Agent environment, run the setup script:

```bash
bash .github/copilot/agent/setup.sh
```

The script is idempotent and can be run multiple times safely.

## What the Setup Script Does

### 1. System Dependencies

- **Python 3.11+**: Installs Python if not available or version is too old
- **Node.js 20+**: Installs Node.js for documentation tools
- **pandoc**: Installs pandoc for document conversion (supports Linux, macOS)

### 2. Node.js Global Packages

- Configures npm to use `~/.npm-global` to avoid permission issues
- Installs `@mermaid-js/mermaid-cli` for Mermaid diagram rendering
- Installs `markdownlint-cli` for Markdown linting

### 3. Python Environment

- Creates `.venv` virtual environment if it doesn't exist
- Installs all project dependencies: `pip install -e .[dev]`
- Includes both runtime and development dependencies

### 4. Pre-commit Setup

- Installs and configures pre-commit hooks
- Runs initial validation to ensure everything works

### 5. Verification

- Runs `scripts/local-check.sh` to verify code quality tools
- Provides summary of installed tools and usage instructions

## Platform Support

The setup script supports:

- **Linux**: Full automatic installation (Ubuntu/Debian, RHEL/CentOS/Fedora)
- **macOS**: Full automatic installation (requires Homebrew)
- **Windows**: Partial support (Python and Node.js detection, manual install instructions)

## Environment Variables

The script sets up these environment variables:

- `PRE_COMMIT_HOME="./.pre-commit-cache"` - Local pre-commit cache
- `PATH` - Adds `~/.npm-global/bin` for global npm packages

## Manual Environment Activation

If you need to activate the environment manually:

```bash
# Activate Python virtual environment
source .venv/bin/activate

# Add npm global packages to PATH
export PATH="$HOME/.npm-global/bin:$PATH"

# Set pre-commit cache location
export PRE_COMMIT_HOME="./.pre-commit-cache"
```

## Verification Commands

After setup, you can verify the installation:

```bash
# Run code quality checks
bash scripts/local-check.sh

# Validate documentation
bash scripts/validate-md.sh

# Run tests
pytest

# Check pre-commit
pre-commit run --all-files
```

## Dependencies Overview

### Python Dependencies (from pyproject.toml)

**Runtime:**

- pdfplumber, pdfminer.six, pypdf, pdf2image (PDF processing)
- pydantic (data validation)
- typer (CLI framework)
- python-slugify, Pygments (text processing)

**Development:**

- pytest, pytest-cov (testing)
- ruff (linting and formatting)
- mypy (type checking)
- pre-commit (git hooks)
- reportlab (test PDF generation)

### System Tools

- **pandoc**: Document conversion
- **markdownlint-cli**: Markdown linting
- **@mermaid-js/mermaid-cli**: Mermaid diagram rendering

## Troubleshooting

### Common Issues

1. **Permission errors with npm**: The script configures npm to use
   `~/.npm-global` to avoid this
2. **Python version too old**: The script will attempt to install Python 3.11+
   automatically
3. **Missing system packages**: Install your OS package manager (apt, yum, brew)
   first
4. **Pre-commit hooks fail**: Run `pre-commit run --all-files` to see specific
   issues

### Manual Installation

If automatic installation fails, refer to the manual installation instructions
in `README.md`:

- [Python and Pre-commit](../README.md#install-python-and-pre-commit)
- [Validation Tools](../README.md#install-validation-tools)

### Environment-Specific Notes

**GitHub Codespaces/Copilot Agent Environment:**

- The script is designed to work in constrained environments
- Uses system package managers when available
- Falls back to manual installation instructions when needed
- Respects existing tool installations

## Integration with Existing Workflows

The setup script integrates with existing project workflows:

- **CI/CD**: Same tools used in GitHub Actions
- **Local development**: Compatible with existing setup instructions
- **Documentation validation**: Full toolchain for markdown processing
- **Pre-commit hooks**: Automatically configured and tested

## Maintenance

To update the environment:

1. Run the setup script again (it's idempotent)
2. Update dependencies: `pip install -e .[dev] --upgrade`
3. Update global npm packages: `npm update -g @mermaid-js/mermaid-cli markdownlint-cli`

## Reference

For more information about Copilot Agent environment customization, see:
[GitHub Documentation: Preinstalling tools or dependencies in Copilot's environment](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/customize-the-agent-environment#preinstalling-tools-or-dependencies-in-copilots-environment)
