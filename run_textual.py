#!/usr/bin/env python3
"""
Brogue: Walking in Big Brother's Footsteps (Textual Version)

Run the Textual-based version of Brogue.
"""
import sys
import argparse
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ui.textual.app import run_game
from ui.textual.game_init import setup_logging
from ui.textual.config_flow import game_start_flow
from core.config.user_config import ConfigManager


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Brogue - A roguelike adventure game",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_textual.py                              # Interactive mode
  python run_textual.py --name Alice                 # Set player name
  python run_textual.py --class warrior              # Set character class
  python run_textual.py --seed 12345                 # Use specific seed
  python run_textual.py --name Bob --class rogue --seed test  # Full config
  python run_textual.py --create-config              # Create default config file

Environment Variables:
  BROGUE_PLAYER_NAME    Override player name
  BROGUE_PLAYER_DEFAULT_CLASS    Override default class

Config File:
  ~/.broguerc           User configuration (INI format)
        """
    )

    parser.add_argument(
        '--name',
        type=str,
        help='Player name (overrides config)'
    )
    parser.add_argument(
        '--class',
        dest='char_class',
        type=str,
        choices=['warrior', 'rogue', 'mage'],
        help='Character class'
    )
    parser.add_argument(
        '--seed',
        type=str,
        help='Game seed (for reproducible gameplay)'
    )
    parser.add_argument(
        '--create-config',
        action='store_true',
        help='Create default config file at ~/.broguerc and exit'
    )

    return parser.parse_args()


def main():
    """Main entry point for Brogue."""
    # Parse arguments
    args = parse_arguments()

    # Handle --create-config
    if args.create_config:
        config = ConfigManager.get_instance()
        config.create_default_config()
        sys.exit(0)

    # Setup logging
    log_dir = Path(__file__).parent / "logs"
    setup_logging(log_dir)

    # Display welcome banner
    print("╔" + "=" * 66 + "╗")
    print("║" + " " * 20 + "WELCOME TO BROGUE" + " " * 29 + "║")
    print("╚" + "=" * 66 + "╝")
    print()
    print("Controls: Arrow keys or HJKL to move, YUBN for diagonal")
    print("Actions: 's' to survey ore, 'm' to mine, '>' to descend stairs")
    print("Press 'R' to restart, 'Q' to quit")
    print()

    # Run game start flow
    player_name, character_class, seed, withdrawn_ore, is_legacy_run = game_start_flow(args)

    # Start the game with configuration
    run_game(
        player_name=player_name,
        character_class=character_class,
        seed=seed,
        withdrawn_ore=withdrawn_ore,
        is_legacy_run=is_legacy_run
    )


if __name__ == "__main__":
    main()
