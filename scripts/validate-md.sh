#!/bin/bash

# Cross-platform Markdown validation script for dev documents.
# Validates syntax, Mermaid diagrams, and rendering using markdownlint-cli, mmdc, and pandoc.
# Supports batch processing of doc/*.md or single files.
# Exits non-zero if total errors exceed threshold (default: 5).

set -e

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

    if ! command_exists markdownlint; then
        missing_tools+=("markdownlint")
    fi

    if ! command_exists mmdc; then
        missing_tools+=("mmdc")
    fi

    if ! command_exists pandoc; then
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

    # Lint with markdownlint
    if ! markdownlint_output=$(markdownlint --json "$file_path" 2>&1); then
        echo "  ERROR: Lint failed: $markdownlint_output"
        ((file_errors++))
    else
        # Parse JSON output
        if [ -n "$markdownlint_output" ] && [ "$markdownlint_output" != "[]" ]; then
            echo "$markdownlint_output" | jq -r --arg file_path "$file_path" '
                if type == "array" then
                    .[]
                elif type == "object" and has($file_path) then
                    .[$file_path][]
                else
                    empty
                end |
                "  ERROR: Lint error on line \(.lineNumber): \(.ruleDescription) - \(.errorContext // "No context")"
            ' 2>/dev/null || echo "  ERROR: Failed to parse lint output"
            ((file_errors++))
        fi
    fi

    # Extract Mermaid blocks
    local mermaid_blocks=()
    while IFS= read -r line; do
        mermaid_blocks+=("$line")
    done < <(sed -n '/^```mermaid/,/^```/p' "$file_path" | sed '1d;$d')

    # Validate Mermaid blocks
    local temp_mmd=$(mktemp --suffix=.mmd)
    local temp_svg=$(mktemp --suffix=.svg)
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
            if ! mmdc -i "$temp_mmd" -o "$temp_svg" >/dev/null 2>&1; then
                echo "  ERROR: Mermaid Parse error in block $block_count (approx. line in file): unescaped parentheses or syntax—recommend quoting."
                ((file_errors++))
            fi
        elif [[ "$in_block" == true ]]; then
            block_content+="$line"$'\n'
        fi
    done < "$file_path"

    # Render with pandoc
    if ! pandoc "$file_path" -t html -o /dev/null >/dev/null 2>&1; then
        echo "  ERROR: Pandoc render error"
        ((file_errors++))
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