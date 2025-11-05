#!/usr/bin/env python3
"""
Brogue: Walking in Big Brother's Footsteps (Textual Version)

Run the Textual-based version of Brogue.
"""
import sys
import argparse
import logging
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ui.textual.app import run_game
from core.config.user_config import ConfigManager, get_player_name
from core.character_class import CharacterClass, format_class_selection, get_class_from_choice
from core.legacy import get_vault, LegacyOre


def setup_logging():
    """Configure logging for Brogue MVP."""
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,  # INFO for normal, DEBUG for development
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'brogue.log'),
            logging.StreamHandler()  # Also print to console
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("Brogue logging initialized")
    logger.info(f"Log file: {log_dir / 'brogue.log'}")


def legacy_vault_withdrawal_flow():
    """
    Allow player to withdraw ore from Legacy Vault.

    Returns:
        Tuple of (withdrawn_ore: Optional[LegacyOre], is_legacy_run: bool)
    """
    vault = get_vault()
    ores = vault.get_ores()

    if not ores:
        # No ore in vault, skip withdrawal
        return None, False

    # Show vault contents
    print()
    print("╔" + "=" * 66 + "╗")
    print("║" + " " * 22 + "LEGACY VAULT" + " " * 31 + "║")
    print("╚" + "=" * 66 + "╝")
    print()
    print("You have rare ore from previous runs stored in your Legacy Vault!")
    print("You may withdraw ONE ore to start with (or none for a Pure run).")
    print()
    print("Note: Using Legacy Vault ore will mark this run as 'Legacy Victory'")
    print("      instead of 'Pure Victory' (Pure = street cred!).")
    print()

    # Show vault stats
    stats = vault.get_stats()
    print(f"Vault Stats:")
    print(f"  Total Runs: {stats['total_runs']}")
    print(f"  Pure Victories: {stats['total_pure_victories']}")
    print(f"  Legacy Victories: {stats['total_legacy_victories']}")
    print()

    # Display ore options
    print("Available Ore:")
    print("-" * 68)
    for i, ore in enumerate(ores):
        quality = ore.get_quality_tier()
        print(f"  [{i+1}] {ore.ore_type.capitalize()} ore - {quality} (Purity: {ore.purity})")
        print(f"      Stats: H:{ore.hardness} C:{ore.conductivity} M:{ore.malleability} D:{ore.density}")
        print(f"      Found on floor {ore.floor_found}")
        print()

    print(f"  [0] No thanks, I'll do a Pure run")
    print("-" * 68)

    # Get selection
    if not sys.stdin.isatty():
        # Non-interactive, default to Pure run
        return None, False

    while True:
        try:
            choice = input(f"Select ore [0-{len(ores)}]: ").strip()

            if choice == '0':
                print()
                print("✨ Starting Pure run! Good luck, brave adventurer!")
                return None, False

            choice_int = int(choice)
            if 1 <= choice_int <= len(ores):
                selected_ore = vault.withdraw_ore(choice_int - 1)
                print()
                print(f"✅ Withdrew {selected_ore.ore_type.capitalize()} ore ({selected_ore.get_quality_tier()})!")
                print(f"   This will be a Legacy run.")
                return selected_ore, True
            else:
                print(f"Invalid choice. Please enter 0-{len(ores)}.")
        except ValueError:
            print(f"Invalid input. Please enter a number 0-{len(ores)}.")
        except (EOFError, KeyboardInterrupt):
            print("\n⚠️  No ore selected, starting Pure run")
            return None, False


def game_start_flow(args):
    """
    Game start flow: get player name, class, and seed.

    Uses CLI args if provided, otherwise prompts interactively.

    Args:
        args: Parsed command-line arguments

    Returns:
        Tuple of (player_name, character_class, seed, withdrawn_ore, is_legacy_run)
    """
    config = ConfigManager.get_instance()

    # 1. Get player name (ENV > config > CLI > prompt > default)
    player_name = get_player_name(args)

    # 2. Get character class
    character_class = None
    if args.char_class:
        # CLI argument provided
        try:
            character_class = CharacterClass.from_string(args.char_class)
        except ValueError:
            print(f"⚠️  Invalid class '{args.char_class}', using interactive selection")

    if not character_class:
        # Check config for default class
        default_class = config.get('player.default_class')
        if default_class:
            try:
                character_class = CharacterClass.from_string(default_class)
                print(f"Using default class from config: {character_class.value.capitalize()}")
            except ValueError:
                pass

    if not character_class:
        # Interactive prompt
        if sys.stdin.isatty():
            print()
            print(format_class_selection())

            while True:
                try:
                    choice = input("Select class [1-3]: ").strip()
                    if choice in ['1', '2', '3']:
                        character_class = get_class_from_choice(int(choice))

                        # Ask to save as default
                        save = input("Set as default class? [y/N]: ").strip().lower()
                        if save == 'y':
                            config.set('player.default_class', character_class.value)
                            config.save()
                            print("✅ Saved to config")
                        break
                    else:
                        print("Invalid choice. Please enter 1, 2, or 3.")
                except (EOFError, KeyboardInterrupt):
                    print("\n⚠️  No class selected, using Warrior (default)")
                    character_class = CharacterClass.WARRIOR
                    break
        else:
            # Non-interactive, use default
            character_class = CharacterClass.WARRIOR

    # 3. Get seed
    seed = args.seed if args.seed else config.get('game.default_seed')

    if not seed and sys.stdin.isatty():
        print()
        print("╔" + "=" * 66 + "╗")
        print("║" + " " * 20 + "OPTIONAL SETTINGS" + " " * 29 + "║")
        print("╚" + "=" * 66 + "╝")
        print()
        print("Tip: Use same seed to replay exact same dungeon!")
        try:
            seed_input = input("Seed (leave empty for random): ").strip()
            seed = seed_input if seed_input else None
        except (EOFError, KeyboardInterrupt):
            seed = None

    # 4. Legacy Vault withdrawal (if vault has ore)
    withdrawn_ore, is_legacy_run = legacy_vault_withdrawal_flow()

    # Display summary
    print()
    print("=" * 60)
    print("STARTING GAME")
    print("=" * 60)
    print(f"  Player: {player_name}")
    print(f"  Class: {character_class.value.capitalize()}")
    print(f"  Seed: {seed or 'random'}")
    print(f"  Run Type: {'Legacy' if is_legacy_run else 'Pure'}")
    if withdrawn_ore:
        print(f"  Starting Ore: {withdrawn_ore.ore_type.capitalize()} ({withdrawn_ore.get_quality_tier()})")
    print("=" * 60)
    print()
    print("Good luck, brave adventurer!")
    print()

    return player_name, character_class, seed, withdrawn_ore, is_legacy_run


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


if __name__ == "__main__":
    # Parse arguments
    args = parse_arguments()

    # Handle --create-config
    if args.create_config:
        config = ConfigManager.get_instance()
        config.create_default_config()
        sys.exit(0)

    # Setup logging
    setup_logging()

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
