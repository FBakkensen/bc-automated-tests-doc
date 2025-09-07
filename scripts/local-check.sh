#!/bin/bash
# Local code quality checks that match CI/CD pipeline
# Run this before committing to ensure your changes will pass CI

set -e

echo "Running local code quality checks..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: Must run from project root (where pyproject.toml is located)"
    exit 1
fi

# Check if dependencies are installed
if ! command -v ruff &> /dev/null; then
    echo "Error: ruff not found. Please install dev dependencies with: pip install -e .[dev]"
    exit 1
fi

echo "1. Running ruff format check..."
ruff format --check .

echo "2. Running ruff lint..."
ruff check .

echo "3. Running mypy type check..."
mypy .

echo "4. Running pytest..."
pytest -q

echo "✅ All local checks passed! Your code is ready for CI."