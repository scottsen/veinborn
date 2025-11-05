#!/usr/bin/env python3
"""
Brogue: Walking in Big Brother's Footsteps

A memory-driven roguelike about courage, growth, and legacy.
"""
import sys
import traceback

from core.game import Game
from ui.display import Display


def main():
    """Main entry point for Brogue."""
    try:
        # Create game and display
        game = Game()
        display = Display()

        # Check terminal compatibility
        if not display.check_terminal_size():
            print("Please resize your terminal and try again.")
            return 1

        # Welcome message
        print("Welcome to Brogue: Walking in Big Brother's Footsteps")
        print("A memory-driven roguelike about family, courage, and growth.")
        print("\nPress any key to start...")
        display.term.inkey()

        # Start the game
        game.start_new_game()
        display.run_game(game)

        print("\nThanks for playing Brogue!")
        return 0

    except KeyboardInterrupt:
        print("\nGame interrupted by user.")
        return 0
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())