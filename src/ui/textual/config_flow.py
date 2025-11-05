"""Game configuration flow for Brogue."""
import sys
from typing import Optional, Tuple

from core.config.user_config import ConfigManager, get_player_name
from core.character_class import CharacterClass, format_class_selection, get_class_from_choice
from core.legacy import LegacyOre
from .legacy_vault_ui import legacy_vault_withdrawal_flow


def game_start_flow(args) -> Tuple[str, CharacterClass, Optional[str], Optional[LegacyOre], bool]:
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
