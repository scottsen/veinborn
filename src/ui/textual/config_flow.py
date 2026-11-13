"""Game configuration flow for Veinborn."""
import sys
from typing import Optional, Tuple

from core.config.user_config import ConfigManager, get_player_name
from core.character_class import CharacterClass, format_class_selection, get_class_from_choice
from core.exceptions import DataError
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
    player_name = get_player_name(args)  # ENV > config > CLI > prompt > default
    character_class = choose_class(args, config)
    seed = choose_seed(args, config)
    withdrawn_ore, is_legacy_run = legacy_vault_withdrawal_flow()
    _print_summary(player_name, character_class, seed, withdrawn_ore, is_legacy_run)
    return player_name, character_class, seed, withdrawn_ore, is_legacy_run


def choose_class(args, config) -> CharacterClass:
    """CLI --class > config player.default_class > prompt (TTY only) > Warrior."""
    if args.char_class:
        try:
            return CharacterClass.from_string(args.char_class)
        except DataError:
            print(f"⚠️  Invalid class '{args.char_class}', using interactive selection")

    default_class = config.get('player.default_class')
    if default_class:
        try:
            character_class = CharacterClass.from_string(default_class)
            print(f"Using default class from config: {character_class.value.capitalize()}")
            return character_class
        except DataError:
            pass

    if not sys.stdin.isatty():
        return CharacterClass.WARRIOR
    return _prompt_class(config)


def _prompt_class(config) -> CharacterClass:
    """Ask for a class until a valid choice; offer to save it as the default."""
    print()
    print(format_class_selection())
    valid = [str(n) for n in range(1, len(CharacterClass) + 1)]
    try:
        while True:
            choice = input(f"Select class [1-{valid[-1]}]: ").strip()
            if choice in valid:
                break
            print(f"Invalid choice. Please enter a number from 1 to {valid[-1]}.")
        character_class = get_class_from_choice(int(choice))
        if input("Set as default class? [y/N]: ").strip().lower() == 'y':
            config.set('player.default_class', character_class.value)
            config.save()
            print("✅ Saved to config")
        return character_class
    except (EOFError, KeyboardInterrupt):
        print("\n⚠️  No class selected, using Warrior (default)")
        return CharacterClass.WARRIOR


def choose_seed(args, config) -> Optional[str]:
    """CLI --seed > config game.default_seed > prompt (TTY only) > None (random)."""
    seed = args.seed if args.seed else config.get('game.default_seed')
    if seed or not sys.stdin.isatty():
        return seed

    print()
    print("╔" + "=" * 66 + "╗")
    print("║" + " " * 20 + "OPTIONAL SETTINGS" + " " * 29 + "║")
    print("╚" + "=" * 66 + "╝")
    print()
    print("Tip: Use same seed to replay exact same dungeon!")
    try:
        return input("Seed (leave empty for random): ").strip() or None
    except (EOFError, KeyboardInterrupt):
        return None


def _print_summary(player_name, character_class, seed, withdrawn_ore, is_legacy_run) -> None:
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
