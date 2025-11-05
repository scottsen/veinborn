#!/bin/bash
# Fix Terminal - Disable Mouse Tracking
# Run this script if your terminal gets stuck showing mouse escape sequences

echo "🔧 Fixing terminal mouse tracking..."

# Disable all mouse tracking modes
printf '\033[?1000l'  # Disable normal mouse tracking
printf '\033[?1002l'  # Disable button event tracking
printf '\033[?1003l'  # Disable any event tracking
printf '\033[?1006l'  # Disable SGR extended mouse mode
printf '\033[?1015l'  # Disable urxvt mouse mode
printf '\033[?1005l'  # Disable UTF-8 mouse mode

# Reset terminal to sane state
stty sane

echo "✅ Terminal fixed! Mouse tracking disabled."
echo ""
echo "Test: Move your mouse - you should see nothing printed."
