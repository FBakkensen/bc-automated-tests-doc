#!/bin/bash
# GitHub Copilot Agent Setup Script for pdf2md project
# Preinstalls all tools and dependencies needed for development workflows
# Reference: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/customize-the-agent-environment#preinstalling-tools-or-dependencies-in-copilots-environment

set -euo pipefail

echo "🚀 Setting up Copilot Agent environment for pdf2md project..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get OS type
get_os() {
    case "$(uname -s)" in
        Linux*)     echo "linux";;
        Darwin*)    echo "macos";;
        CYGWIN*|MINGW*|MSYS*) echo "windows";;
        *)          echo "unknown";;
    esac
}

OS=$(get_os)
print_status "Detected OS: $OS"

# 1. Install Python 3.11+ if not available
print_status "Checking Python installation..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_status "Found Python $PYTHON_VERSION"
    
    # Check if version is 3.11+
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
        print_status "Python 3.11+ requirement satisfied"
    else
        print_warning "Python 3.11+ required, found $PYTHON_VERSION"
        case $OS in
            "linux")
                print_status "Installing Python 3.11+ on Linux..."
                if command_exists apt-get; then
                    sudo apt-get update && sudo apt-get install -y python3.11 python3.11-venv python3-pip
                elif command_exists yum; then
                    sudo yum install -y python3.11 python3-pip
                elif command_exists dnf; then
                    sudo dnf install -y python3.11 python3-pip
                else
                    print_error "Package manager not found. Please install Python 3.11+ manually."
                    exit 1
                fi
                ;;
            "macos")
                print_status "Installing Python 3.11+ on macOS..."
                if command_exists brew; then
                    brew install python@3.11
                else
                    print_error "Homebrew not found. Please install Python 3.11+ manually."
                    exit 1
                fi
                ;;
            *)
                print_error "Unsupported OS for automatic Python installation. Please install Python 3.11+ manually."
                exit 1
                ;;
        esac
    fi
else
    print_error "Python3 not found. Please install Python 3.11+ manually."
    exit 1
fi

# Ensure pip is available
if ! command_exists pip; then
    if command_exists pip3; then
        alias pip=pip3
    else
        print_error "pip not found. Please ensure pip is installed."
        exit 1
    fi
fi

# 2. Install Node.js 20+ and npm for documentation tools
print_status "Checking Node.js installation..."
if command_exists node; then
    NODE_VERSION=$(node --version | sed 's/v//')
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
    print_status "Found Node.js $NODE_VERSION"
    
    if [ "$NODE_MAJOR" -ge 20 ]; then
        print_status "Node.js 20+ requirement satisfied"
    else
        print_warning "Node.js 20+ recommended, found $NODE_VERSION"
    fi
else
    print_status "Installing Node.js 20..."
    case $OS in
        "linux")
            # Install NodeSource repository for latest Node.js
            curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
            sudo apt-get install -y nodejs
            ;;
        "macos")
            if command_exists brew; then
                brew install node@20
            else
                print_error "Homebrew not found. Please install Node.js 20+ manually."
                exit 1
            fi
            ;;
        *)
            print_error "Unsupported OS for automatic Node.js installation. Please install Node.js 20+ manually."
            exit 1
            ;;
    esac
fi

# Verify npm is available
if ! command_exists npm; then
    print_error "npm not found. Please ensure npm is installed with Node.js."
    exit 1
fi

# 3. Install pandoc for document conversion
print_status "Checking pandoc installation..."
if ! command_exists pandoc; then
    print_status "Installing pandoc..."
    case $OS in
        "linux")
            if command_exists apt-get; then
                sudo apt-get update && sudo apt-get install -y pandoc
            elif command_exists yum; then
                sudo yum install -y pandoc
            elif command_exists dnf; then
                sudo dnf install -y pandoc
            else
                print_warning "Package manager not found. Please install pandoc manually."
            fi
            ;;
        "macos")
            if command_exists brew; then
                brew install pandoc
            else
                print_warning "Homebrew not found. Please install pandoc manually."
            fi
            ;;
        *)
            print_warning "Unsupported OS for automatic pandoc installation. Please install pandoc manually."
            ;;
    esac
else
    print_status "pandoc already installed: $(pandoc --version | head -n1)"
fi

# 4. Configure npm to use local directory (avoid permission issues)
print_status "Configuring npm for global packages..."
NPM_PREFIX="$HOME/.npm-global"
mkdir -p "$NPM_PREFIX"
npm config set prefix "$NPM_PREFIX"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$NPM_PREFIX/bin:"* ]]; then
    export PATH="$NPM_PREFIX/bin:$PATH"
    print_status "Added $NPM_PREFIX/bin to PATH"
fi

# 5. Install global npm packages for documentation
print_status "Installing documentation tools..."
npm install -g @mermaid-js/mermaid-cli markdownlint-cli

# Verify installations
if command_exists mmdc; then
    print_status "mermaid-cli installed: $(mmdc --version)"
else
    print_warning "mermaid-cli installation may have failed"
fi

if command_exists markdownlint; then
    print_status "markdownlint-cli installed: $(markdownlint --version)"
else
    print_warning "markdownlint-cli installation may have failed"
fi

# 6. Set up Python virtual environment and install dependencies
print_status "Setting up Python virtual environment..."
cd "$(dirname "${BASH_SOURCE[0]}")/../../../"  # Go to repository root

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    print_status "Created Python virtual environment"
else
    print_status "Python virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install project dependencies
print_status "Installing Python dependencies..."
pip install -e .[dev]

# 7. Install and setup pre-commit
print_status "Setting up pre-commit hooks..."
if command_exists pre-commit; then
    pre-commit install
    print_status "Pre-commit hooks installed"
    
    # Run pre-commit on all files to ensure everything is set up correctly
    print_status "Running pre-commit on all files..."
    if pre-commit run --all-files; then
        print_status "All pre-commit checks passed"
    else
        print_warning "Some pre-commit checks failed, but installation is complete"
    fi
else
    print_warning "pre-commit not found in PATH, it should be available after activating the virtual environment"
fi

# 8. Verify installation by running local checks
print_status "Verifying installation with local checks..."
if [ -f "scripts/local-check.sh" ]; then
    if bash scripts/local-check.sh; then
        print_status "✅ All local checks passed!"
    else
        print_warning "Some local checks failed, but core installation is complete"
    fi
else
    print_warning "local-check.sh script not found"
fi

# 9. Set environment variables for the session
export PRE_COMMIT_HOME="./.pre-commit-cache"
export PATH="$NPM_PREFIX/bin:$PATH"

print_status "🎉 Copilot Agent environment setup complete!"
echo ""
echo "📋 Summary of installed tools:"
echo "  ✓ Python $(python3 --version | cut -d' ' -f2) with pip"
echo "  ✓ Node.js $(node --version) with npm"
if command_exists pandoc; then
    echo "  ✓ pandoc $(pandoc --version | head -n1 | cut -d' ' -f2)"
fi
if command_exists mmdc; then
    echo "  ✓ mermaid-cli"
fi
if command_exists markdownlint; then
    echo "  ✓ markdownlint-cli"
fi
echo "  ✓ Python virtual environment with all dev dependencies"
echo "  ✓ Pre-commit hooks configured"
echo ""
echo "🔧 To activate the environment manually:"
echo "  source .venv/bin/activate"
echo "  export PATH=\"$NPM_PREFIX/bin:\$PATH\""
echo ""
echo "🧪 To run quality checks:"
echo "  bash scripts/local-check.sh"
echo ""
echo "📖 To validate documentation:"
echo "  bash scripts/validate-md.sh"