#!/usr/bin/env python3
"""
Minimal Textual app test - simplest possible TUI.
If this doesn't work, Textual is incompatible with your terminal.
"""
from textual.app import App
from textual.widgets import Static

class MinimalApp(App):
    """Absolute minimal Textual app."""

    ENABLE_MOUSE = False  # No mouse tracking

    def compose(self):
        yield Static("Hello! Press Q to quit.")
        yield Static("If you can see this, Textual works!")
        yield Static("If screen is blank, Textual is incompatible.")

    BINDINGS = [("q", "quit", "Quit")]

if __name__ == "__main__":
    print("Starting minimal Textual test...")
    print("Press Q to quit")
    print("If you see nothing, press Ctrl+C and run: reset")
    print()
    app = MinimalApp()
    try:
        app.run()
    finally:
        # Clean up
        import sys, os
        sys.stdout.write('\033[?25h')  # Show cursor
        sys.stdout.flush()
        os.system('stty sane 2>/dev/null')
    print("\nMinimal test complete!")
