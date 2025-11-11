#!/usr/bin/env bash
# Brogue Installation Script
# Optionally install 'brogue' command system-wide

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "================================================"
echo "Brogue Installation"
echo "================================================"
echo ""

# Check if running with sudo
if [ "$EUID" -eq 0 ]; then
    INSTALL_DIR="/usr/local/bin"
    NEEDS_SUDO=false
else
    INSTALL_DIR="$HOME/.local/bin"
    NEEDS_SUDO=false

    # Create local bin if doesn't exist
    mkdir -p "$INSTALL_DIR"

    # Check if it's in PATH
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        echo "Note: $INSTALL_DIR is not in your PATH"
        echo "Add this to your ~/.bashrc or ~/.zshrc:"
        echo ""
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo ""
    fi
fi

# Install dependencies
echo "1. Installing Python dependencies..."
pip install -q -r "$SCRIPT_DIR/requirements.txt"
echo "   ✓ Dependencies installed"
echo ""

# Create symlink
echo "2. Creating 'brogue' command..."
ln -sf "$SCRIPT_DIR/brogue" "$INSTALL_DIR/brogue"
echo "   ✓ Installed to: $INSTALL_DIR/brogue"
echo ""

# Verify installation
if command -v brogue &> /dev/null; then
    echo "================================================"
    echo "✓ Installation successful!"
    echo "================================================"
    echo ""
    echo "You can now run the game with:"
    echo "  brogue"
    echo ""
    echo "Options:"
    echo "  brogue --debug    Run with debug logging"
    echo "  brogue --safe     Run with terminal reset"
    echo "  brogue --help     Show help"
    echo ""
else
    echo "================================================"
    echo "⚠ Installation may need PATH update"
    echo "================================================"
    echo ""
    echo "Run the game with:"
    echo "  $INSTALL_DIR/brogue"
    echo ""
    echo "Or add to PATH:"
    echo "  export PATH=\"$INSTALL_DIR:\$PATH\""
    echo ""
fi
