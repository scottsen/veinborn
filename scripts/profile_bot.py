#!/usr/bin/env python3
"""
Profile bot performance to identify bottlenecks.

Runs a bot with cProfile and reports hotspots.
"""

import cProfile
import pstats
import sys
from pathlib import Path

# Add src and tests/fuzz to path
src_path = Path(__file__).parent / "src"
tests_fuzz_path = Path(__file__).parent / "tests" / "fuzz"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(tests_fuzz_path))

# Import after path setup
from brogue_bot import BrogueBot


def profile_bot_game():
    """Run a single bot game with profiling."""
    bot = BrogueBot(verbose=False, mode='strategic')
    bot.play_one_game(max_turns=500)  # Shorter game for faster profiling
    return bot.stats


if __name__ == '__main__':
    print("Profiling bot performance...")
    print("=" * 60)

    # Run profiler
    profiler = cProfile.Profile()
    profiler.enable()

    stats = profile_bot_game()

    profiler.disable()

    # Print results
    print("\nGame Statistics:")
    print(f"  Total turns: {stats.total_turns}")
    print(f"  Avg turns/game: {stats.avg_turns_per_game:.1f}")

    print("\n" + "=" * 60)
    print("PERFORMANCE HOTSPOTS (Top 30 functions by cumulative time)")
    print("=" * 60)

    # Analyze profile data
    ps = pstats.Stats(profiler)
    ps.strip_dirs()
    ps.sort_stats('cumulative')
    ps.print_stats(30)

    print("\n" + "=" * 60)
    print("PERFORMANCE HOTSPOTS (Top 30 functions by total time)")
    print("=" * 60)
    ps.sort_stats('tottime')
    ps.print_stats(30)

    print("\nDone! Check output above for bottlenecks.")
