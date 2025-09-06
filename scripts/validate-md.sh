#!/bin/bash

# Cross-platform Markdown validation script for dev documents.
# Validates syntax, Mermaid diagrams, and rendering using markdownlint-cli, mmdc, and pandoc.
# Supports batch processing of doc/*.md or single files.
# Exits non-zero if total errors exceed threshold (default: 5).

set -e

# Behavior flags via environment:
#  - VALIDATE_MERMAID: strict|warn_on_sandbox|skip (default: strict)
#  - SKIP_PANDOC: true|false (default: false)
#  - LINT_ONLY: true|false (default: false)
#  - LINT_FALLBACK_OK: true|false (default: false)

# Default values
THRESHOLD=5
ERROR_COUNT=0

# Function to print usage
usage() {
    echo "Usage: $0 [OPTIONS] [FILES...]"
    echo "Validate Markdown files."
    echo ""
    echo "Options:"
    echo "  --threshold N   Max allowed errors before exit non-zero (default: $THRESHOLD)"
    echo "  --help          Show this help message"
    echo ""
    echo "If no files are specified, defaults to doc/*.md"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check required tools
check_tools() {
    local missing_tools=()

    # Determine which tools are required based on flags
    local need_markdownlint=true
    local need_mmdc=true
    local need_pandoc=true
    if [ "${LINT_ONLY:-false}" = "true" ]; then
        need_mmdc=false
        need_pandoc=false
    fi
    if [ "${VALIDATE_MERMAID:-strict}" = "skip" ]; then
        need_mmdc=false
    fi
    if [ "${SKIP_PANDOC:-false}" = "true" ]; then
        need_pandoc=false
    fi

    if $need_markdownlint && ! command_exists markdownlint; then
        if [ "${LINT_FALLBACK_OK:-false}" = "true" ]; then
            echo "markdownlint not found; using minimal fallback checks." >&2
        else
            missing_tools+=("markdownlint")
        fi
    fi

    if $need_mmdc && ! command_exists mmdc; then
        missing_tools+=("mmdc")
    fi

    if $need_pandoc && ! command_exists pandoc; then
        missing_tools+=("pandoc")
    fi

    if [ ${#missing_tools[@]} -ne 0 ]; then
        echo "Required tools missing: ${missing_tools[*]}"
        echo "Install with:"
        echo "  npm install -g markdownlint-cli @mermaid-js/mermaid-cli"
        echo "  brew install pandoc (Linux/macOS) or choco install pandoc (Windows)"
        exit 1
    fi
}

# Function to validate a single Markdown file
validate_file() {
    local file_path="$1"
    local file_errors=0

    if [[ ! "$file_path" =~ \.md$ ]]; then
        return 0
    fi

    echo "Validating $file_path..."

    # Lint with markdownlint or fallback
    if command_exists markdownlint; then
        if ! markdownlint_output=$(markdownlint --json "$file_path" 2>&1); then
            echo "  ERROR: Lint failed: $markdownlint_output"
            ((file_errors++))
        else
            if [ -n "$markdownlint_output" ] && [ "$markdownlint_output" != "[]" ]; then
                echo "$markdownlint_output" | jq -r --arg file_path "$file_path" '
                    if type == "array" then
                        .[]
                    elif type == "object" and has($file_path) then
                        .[$file_path][]
                    else
                        empty
                    end |
                    "  ERROR: Lint error on line \(.lineNumber): \(.ruleDescription) - \(.errorContext // "No context")"' 2>/dev/null \
                    || echo "  ERROR: Failed to parse lint output"
                ((file_errors++))
            fi
        fi
    else
        # Minimal fallback: trailing whitespace and long lines > 100 chars
        if grep -nE "[[:space:]]+$" "$file_path" >/dev/null; then
            echo "  ERROR: Trailing whitespace detected."
            ((file_errors++))
        fi
        if awk 'length($0) > 100 {print NR; exit 1}' "$file_path" >/dev/null; then
            :
        else
            echo "  ERROR: Lines exceeding 100 characters detected."
            ((file_errors++))
        fi
    fi

    # Mermaid validation (optional)
    if [ "${VALIDATE_MERMAID:-strict}" != "skip" ]; then
        local mermaid_blocks=()
        while IFS= read -r line; do
            mermaid_blocks+=("$line")
        done < <(sed -n '/^```mermaid/,/^```/p' "$file_path" | sed '1d;$d')

        local temp_mmd=$(mktemp --suffix=.mmd)
        local temp_svg=$(mktemp --suffix=.svg)
        local puppeteer_cfg="scripts/puppeteer-ns.json"
        trap "rm -f $temp_mmd $temp_svg" EXIT

        local block_count=0
        local in_block=false
        local block_content=""

        while IFS= read -r line; do
            if [[ "$line" == '```mermaid' ]]; then
                in_block=true
                block_content=""
                ((block_count++))
            elif [[ "$line" == '```' ]] && [[ "$in_block" == true ]]; then
                in_block=false
                echo "$block_content" > "$temp_mmd"
                tmp_err=$(mktemp)
                mmdc -i "$temp_mmd" -o "$temp_svg" -p "$puppeteer_cfg" >/dev/null 2> "$tmp_err" || true
                if grep -qiE 'sandbox_host_linux|Failed to launch the browser process' "$tmp_err"; then
                    if [ "${VALIDATE_MERMAID:-strict}" = "warn_on_sandbox" ]; then
                        echo "  WARN: Mermaid rendering skipped due to browser sandbox; diagrams retained as-is."
                    else
                        echo "  ERROR: Mermaid rendering failed due to browser sandbox; strict mode requires rendering to pass."
                        ((file_errors++))
                    fi
                else
                    if [ -s "$tmp_err" ]; then
                        echo "  ERROR: Mermaid error in block $block_count. Details:" >&2
                        sed -n '1,5p' "$tmp_err" | sed 's/^/    /'
                        ((file_errors++))
                    fi
                fi
                rm -f "$tmp_err"
            elif [[ "$in_block" == true ]]; then
                block_content+="$line"$'\n'
            fi
        done < "$file_path"
    fi

    # Render with pandoc unless skipped
    if [ "${SKIP_PANDOC:-false}" != "true" ]; then
        if ! pandoc -f gfm "$file_path" -t html -o /dev/null >/dev/null 2>&1; then
            echo "  ERROR: Pandoc render error"
            ((file_errors++))
        fi
    fi

    return $file_errors
}

# Parse command line arguments
FILES=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --threshold)
            THRESHOLD="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        -*)
            echo "Unknown option $1"
            usage
            exit 1
            ;;
        *)
            FILES+=("$1")
            shift
            ;;
    esac
done

# If no files specified, default to doc/*.md
if [ ${#FILES[@]} -eq 0 ]; then
    shopt -s nullglob
    FILES=(doc/*.md)
    shopt -u nullglob
fi

# Check required tools
check_tools

# Validate each file
for file in "${FILES[@]}"; do
    if validate_file "$file"; then
        echo "  No errors found in $file"
    else
        ((ERROR_COUNT+=$?))
    fi
done

echo "Total errors: $ERROR_COUNT"

if [ $ERROR_COUNT -gt $THRESHOLD ]; then
    exit 1
else
    exit 0
fi
