"""Print the single-player or co-op leaderboard: `veinborn-scores [--coop] [--limit N]`."""

import argparse
from pathlib import Path
from typing import List, Optional

from .highscore import HighScoreManager


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="veinborn-scores", description=__doc__)
    parser.add_argument("--coop", action="store_true",
                        help="show the multiplayer (co-op) leaderboard instead of single-player")
    parser.add_argument("--limit", type=int, default=10, help="entries to show (default 10)")
    parser.add_argument("--file", type=Path, help="read this high score file instead of the default")
    args = parser.parse_args(argv)

    if args.file:
        manager = HighScoreManager(args.file)
    elif args.coop:
        manager = HighScoreManager.get_multiplayer_instance()
    else:
        manager = HighScoreManager.get_instance()

    title = "CO-OP HIGH SCORES" if args.coop else "HIGH SCORES"
    print(manager.format_leaderboard(manager.get_all_scores(args.limit), title))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
