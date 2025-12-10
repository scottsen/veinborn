#!/usr/bin/env python3
"""
Demonstration of Veinborn's seeding system.

This script demonstrates reproducible gameplay through seeds.
Run it to see how the same seed produces identical games!
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.game import Game


def demo_same_seed_same_game():
    """Demonstrate that same seed produces identical games."""
    print("=" * 70)
    print("DEMO 1: Same Seed = Same Game")
    print("=" * 70)
    print()

    seed = 12345
    print(f"Running two games with seed {seed}...\n")

    # Game 1
    print("[Game 1]")
    game1 = Game()
    game1.start_new_game(seed=seed)

    monsters1 = [m.name for m in game1.context.get_entities_by_type(1)]
    ore_types1 = [o.stats.get('ore_type') for o in game1.context.get_entities_by_type(2)]
    rooms1 = [(r.x, r.y, r.width, r.height) for r in game1.state.dungeon_map.rooms]

    print(f"  Seed: {game1.state.seed}")
    print(f"  Monsters: {monsters1}")
    print(f"  Ore types: {ore_types1}")
    print(f"  First room: {rooms1[0] if rooms1 else 'None'}")
    print()

    # Game 2
    print("[Game 2]")
    game2 = Game()
    game2.start_new_game(seed=seed)

    monsters2 = [m.name for m in game2.context.get_entities_by_type(1)]
    ore_types2 = [o.stats.get('ore_type') for o in game2.context.get_entities_by_type(2)]
    rooms2 = [(r.x, r.y, r.width, r.height) for r in game2.state.dungeon_map.rooms]

    print(f"  Seed: {game2.state.seed}")
    print(f"  Monsters: {monsters2}")
    print(f"  Ore types: {ore_types2}")
    print(f"  First room: {rooms2[0] if rooms2 else 'None'}")
    print()

    # Verify
    print("[Verification]")
    monsters_match = monsters1 == monsters2
    ore_match = ore_types1 == ore_types2
    rooms_match = rooms1 == rooms2

    print(f"  ✓ Monsters match: {monsters_match}")
    print(f"  ✓ Ore types match: {ore_match}")
    print(f"  ✓ Room layout match: {rooms_match}")

    if monsters_match and ore_match and rooms_match:
        print("\n  🎉 SUCCESS! Same seed = identical games!")
    else:
        print("\n  ❌ ERROR: Games differ despite same seed!")

    print()


def demo_different_seeds_different_games():
    """Demonstrate that different seeds produce different games."""
    print("=" * 70)
    print("DEMO 2: Different Seeds = Different Games")
    print("=" * 70)
    print()

    seed1, seed2 = 11111, 22222
    print(f"Running two games with seeds {seed1} and {seed2}...\n")

    # Game 1
    print(f"[Game with seed {seed1}]")
    game1 = Game()
    game1.start_new_game(seed=seed1)

    monsters1 = [m.name for m in game1.context.get_entities_by_type(1)]
    rooms1 = [(r.x, r.y) for r in game1.state.dungeon_map.rooms]

    print(f"  Monsters: {monsters1}")
    print(f"  Room positions: {rooms1[:3]}...")
    print()

    # Game 2
    print(f"[Game with seed {seed2}]")
    game2 = Game()
    game2.start_new_game(seed=seed2)

    monsters2 = [m.name for m in game2.context.get_entities_by_type(1)]
    rooms2 = [(r.x, r.y) for r in game2.state.dungeon_map.rooms]

    print(f"  Monsters: {monsters2}")
    print(f"  Room positions: {rooms2[:3]}...")
    print()

    # Verify
    print("[Verification]")
    different = (monsters1 != monsters2) or (rooms1 != rooms2)

    if different:
        print("  🎉 SUCCESS! Different seeds = different games!")
    else:
        print("  ⚠️  WARNING: Games are identical (very unlikely!)")

    print()


def demo_string_seeds():
    """Demonstrate string seed support."""
    print("=" * 70)
    print("DEMO 3: String Seeds (Human-Readable)")
    print("=" * 70)
    print()

    seeds = ["epic-run", "speedrun-practice", "tournament-2025"]

    print("String seeds are human-readable and shareable!\n")

    for seed_str in seeds:
        game = Game()
        game.start_new_game(seed=seed_str)

        monsters = [m.name for m in game.context.get_entities_by_type(1)]

        print(f"[Seed: '{seed_str}']")
        print(f"  Monsters spawned: {', '.join(monsters) if monsters else 'None'}")
        print(f"  Room count: {len(game.state.dungeon_map.rooms)}")
        print()

    print("💡 Share these seeds with friends to play the same map!")
    print()


def demo_use_cases():
    """Show practical use cases for seeding."""
    print("=" * 70)
    print("DEMO 4: Practical Use Cases")
    print("=" * 70)
    print()

    print("🐛 1. BUG REPRODUCTION")
    print("   Player: 'I found a bug on seed 99999, floor 3'")
    print("   Developer: *starts game with seed 99999, goes to floor 3*")
    print("   Developer: 'Reproduced! Fixing now...'")
    print()

    print("🏆 2. TOURNAMENTS")
    print("   Tournament: 'Everyone play seed 2025-champs'")
    print("   All players get the same map → fair competition!")
    print()

    print("🎮 3. SPEEDRUNNING")
    print("   Runner: 'Practicing seed speedrun-route-v2'")
    print("   Same map every time → optimize routing!")
    print()

    print("🧪 4. TESTING")
    print("   Test: game.start_new_game(seed=12345)")
    print("   Every test run gets same map → deterministic tests!")
    print()


def main():
    """Run all demonstrations."""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "VEINBORN SEEDING SYSTEM DEMO" + " " * 27 + "║")
    print("║" + " " * 20 + "Phase 4: Reproducibility" + " " * 24 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    demos = [
        demo_same_seed_same_game,
        demo_different_seeds_different_games,
        demo_string_seeds,
        demo_use_cases,
    ]

    for i, demo in enumerate(demos, 1):
        demo()
        if i < len(demos):
            input("Press Enter to continue...")
            print()

    print("=" * 70)
    print("DEMO COMPLETE!")
    print("=" * 70)
    print()
    print("Key Takeaways:")
    print("  ✓ Same seed = identical games (100% reproducible)")
    print("  ✓ Different seeds = different games")
    print("  ✓ String seeds supported (human-readable)")
    print("  ✓ Enables bug reproduction, tournaments, speedrunning, testing")
    print()
    print("Try it yourself:")
    print("  >>> from src.core.game import Game")
    print("  >>> game = Game()")
    print("  >>> game.start_new_game(seed='my-awesome-run')")
    print()


if __name__ == "__main__":
    main()
