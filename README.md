# pdf2md (Scaffold)

Early scaffold for the Technical PDF to Structured Markdown Conversion Tool described in `doc/prd.md`.

## Features (planned)
See PRD for comprehensive requirements. Current scaffold provides:
- Config model (`ToolConfig`)
- Core data structures (`Span`, `Node`, etc.)
- Utility helpers (slug generation, hyphenation repair, heading heuristic)
- Typer CLI skeleton with `convert` and `dry-run` commands (stubs)
- Initial pytest tests for utilities

## Local Development

### 1. Create & activate virtual environment (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

(Unix / WSL)
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies
```powershell
pip install -e .[dev]
```

### 3. Run tests
```powershell
pytest
```

### 4. Run CLI (stub)
```powershell
pdf2md convert .\pdf\AUTOMATED_TESTING_IN_MICROSOFT_DYNAMICS_365_BUSI.pdf --out output --manifest
```

## Documentation Validation Workflow

This project includes a system for validating Markdown files in the `doc/` directory for syntax errors, including Markdown linting, Mermaid diagram validation, and rendering with Pandoc. It is integrated as a pre-commit hook and a GitHub Actions CI step to catch issues early.

### Prerequisites
- Git installed.
- Node.js and npm for Mermaid CLI and markdownlint.
- Pandoc for rendering. Required tools (markdownlint-cli, mmdc, pandoc) must be installed globally; the validation script will fail with an error if any are missing.
- Python 3.11+ installed (for the validation script and pre-commit).
- Pre-commit for local hooks (optional but recommended).
- GitHub repository for CI (optional).

### Installation

#### Install Python and Pre-commit
For cross-platform compatibility, ensure Python 3.11+ is installed, then install pre-commit:

- On Windows: Download Python from python.org or `choco install python`; then `pip install pre-commit`
- On Linux (Ubuntu): `sudo apt update && sudo apt install python3.11 python3-pip`; then `pip install pre-commit`
- On macOS: `brew install python@3.11`; then `pip install pre-commit`

#### Install Validation Tools
Run the following commands to install the required CLI tools globally:

```bash
# Install Mermaid CLI and markdownlint CLI via npm (cross-platform)
npm install -g @mermaid-js/mermaid-cli markdownlint-cli

# Install Pandoc
# On macOS:
brew install pandoc

# On Ubuntu/Debian:
sudo apt update && sudo apt install pandoc

# On Windows:
choco install pandoc
```

#### Verify Installation
Test that tools are installed correctly:

```bash
markdownlint-cli --version
mmdc --version
pandoc --version
```

### Pre-commit Hook Setup

The validation is integrated via a pre-commit hook to run automatically on staged `.md` files in `doc/`.

1. Install pre-commit:
   ```bash
   pip install pre-commit
   ```

2. Install the hooks in your repository:
   ```bash
   pre-commit install
   ```

3. (Optional) Install hooks only for this repo:
   ```bash
   pre-commit install --install-hooks -t validate-md
   ```

Now, whenever you `git commit` changes to `doc/*.md` files, the validation script `bash scripts/validate-md.sh` will run automatically. If validation fails, the commit is aborted, and errors are reported.

To manually run the hook on all staged files:
```bash
pre-commit run --all-files
```

Or run only the Markdown validation:
```bash
pre-commit run validate-md --all-files
```

### GitHub Actions CI Setup

The CI workflow is defined in `.github/workflows/validate-docs.yml`. It triggers on push/PR to `main` for changes in `doc/`.

1. Ensure your repository is on GitHub.
2. The workflow automatically installs tools (including Python) and runs `bash scripts/validate-md.sh doc/*.md` on all `doc/*.md` files.
3. On failure, the CI job fails, and errors are reported in the GitHub Actions logs.

No additional setup is needed; it runs on `ubuntu-latest` with Node.js 20 and installs dependencies.

### Usage

#### Manual Validation
Run the validation script manually on all `doc/*.md` files (cross-platform on Linux/Windows/macOS):
```bash
bash scripts/validate-md.sh
```

To validate specific files (e.g., for pre-commit simulation):
```bash
bash scripts/validate-md.sh doc/design.md
```

#### Example Output
On success:
```
Validating design.md...
All Markdown files in doc validated successfully.
```

On failure (example with Mermaid error):
```
Validating design.md...
Validation error in design.md on line 8: Mermaid Parse error: unescaped parentheses—recommend quoting
Recommendation: quote labels with parentheses or escape special chars
Validation failed with 1 errors.
```

#### Troubleshooting
- **Tool not found**: The script will fail immediately with an error message providing installation instructions. Ensure tools are globally installed.
- **Pre-commit fails**: Check output for specific errors. Fix Markdown/Mermaid issues, then retry commit.
- **CI fails**: View GitHub Actions logs for detailed error reporting.
- **Cross-platform issues**: The Python script works on Windows, Linux, macOS. Use Command Prompt/PowerShell on Windows or any terminal on Linux/macOS. Ensure Python and tools are in PATH.

#### Testing the Workflow
To test locally:
1. Make a change to `doc/design.md` (e.g., add invalid Mermaid).
2. `git add doc/design.md`
3. `git commit -m "Test validation"` – should fail with error.
4. Fix the issue and commit again – should pass.

Verification on doc/design.md: After fixes (e.g., quoted Mermaid labels), run `bash scripts/validate-md.sh doc/design.md` and expect 0 errors.

The system ensures early detection of issues, maintaining documentation quality without altering existing project files.

## Next Implementation Steps
1. Implement PDF ingestion producing `Span` objects (pdfplumber).
2. Font size clustering & heading tree builder.
3. Paragraph/list assembly & code block detection.
4. Image extraction (pypdf + pdf2image fallback) with captions.
5. Table detection pipeline.
6. Markdown file rendering + manifest & optional TOC export.
7. Cross-reference linking & footnotes.
8. Performance tuning & deterministic hashing.

## Config
Create a YAML file and pass with `--config`:
```yaml
font_cluster_epsilon: 1.0
slug_prefix_width: 2
```

## License
MIT (adjust as needed).
