"""Legacy Vault withdrawal UI for Brogue."""
import sys
from typing import Optional, Tuple

from core.legacy import get_vault, LegacyOre


def legacy_vault_withdrawal_flow() -> Tuple[Optional[LegacyOre], bool]:
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
