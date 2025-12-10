#!/usr/bin/env python3
"""
Safe runner for Veinborn with terminal cleanup on errors.
Use this if you're having terminal compatibility issues.
"""
import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """Run with proper terminal cleanup."""
    try:
        from ui.textual.app import run_game

        print("Starting Veinborn with Textual UI...")
        print("Controls: Arrow keys or HJKL to move, YUBN for diagonal")
        print("Press R to restart, Q to quit")
        print()

        # Check terminal compatibility
        if not sys.stdout.isatty():
            print("ERROR: Not running in a terminal (no TTY)")
            return 1

        # Try to detect problematic environments
        term = os.environ.get('TERM', '')
        if 'screen' in term or 'tmux' in term:
            print("WARNING: Running inside tmux/screen may cause display issues")
            print("Recommend: Run in a regular terminal window")
            input("Press Enter to continue anyway, or Ctrl+C to quit...")

        run_game()
        return 0

    except KeyboardInterrupt:
        print("\n\nGame interrupted - cleaning up...")
        return 0
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Ensure terminal is reset
        try:
            # Disable mouse tracking
            sys.stdout.write('\033[?1000l')  # Disable X11 mouse tracking
            sys.stdout.write('\033[?1002l')  # Disable cell motion tracking
            sys.stdout.write('\033[?1003l')  # Disable all motion tracking
            sys.stdout.write('\033[?1006l')  # Disable SGR mouse mode
            # Reset terminal to normal mode
            sys.stdout.write('\033[?25h')    # Show cursor
            sys.stdout.write('\033[?47l')    # Exit alternate screen
            sys.stdout.flush()
            # Reset terminal settings
            os.system('stty sane 2>/dev/null')
        except:
            pass
        print("\n\nTerminal cleanup complete. If display is still broken, type: reset")

if __name__ == "__main__":
    sys.exit(main())
