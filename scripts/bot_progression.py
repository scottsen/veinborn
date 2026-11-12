#!/usr/bin/env python3
"""Level-by-floor curve from bot results (VB-69).

Each bot game records, per floor, the turn and player level on arrival
(`floor_arrivals` in tests/fuzz/veinborn_bot.py results). This prints, per class and
floor, how many games got there, and the median arrival turn and level (with the
25th-75th percentile of level). Use it to pick the player level that sim_duels should
test a monster at for the floors it is placed on.

Usage:
    python3 scripts/bot_progression.py logs/long_*.json
    python3 scripts/bot_progression.py logs/long_*.json --json curve.json
"""
import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def quantile(values, q):
    """Nearest-rank quantile of a non-empty list."""
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))]


def curve(games):
    """{class: {floor: row}} from per-game results that carry floor_arrivals."""
    by = defaultdict(lambda: defaultdict(list))
    for g in games:
        for floor, (turn, level) in (g.get('floor_arrivals') or {}).items():
            by[g['character_class']][int(floor)].append((turn, level))
            by['ALL'][int(floor)].append((turn, level))
    out = {}
    for cls, floors in by.items():
        out[cls] = {}
        for floor in sorted(floors):
            turns = [t for t, _ in floors[floor]]
            levels = [lv for _, lv in floors[floor]]
            out[cls][floor] = {
                'games': len(levels),
                'turn_median': statistics.median(turns),
                'level_median': statistics.median(levels),
                'level_p25': quantile(levels, 0.25),
                'level_p75': quantile(levels, 0.75),
            }
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('results', nargs='+')
    ap.add_argument('--json', help='also write the curve to this file')
    args = ap.parse_args()

    games = []
    for path in args.results:
        games.extend(json.loads(Path(path).read_text())['games'])
    if not any(g.get('floor_arrivals') for g in games):
        sys.exit("no floor_arrivals in these results (recorded by bots since this script was added)")

    result = curve(games)
    for cls in sorted(result, key=lambda c: (c == 'ALL', c)):
        print(f"\n{cls}")
        print(f"  {'floor':>5} {'games':>5} {'turn':>7} {'level':>6} {'p25-p75':>8}")
        for floor, r in result[cls].items():
            print(f"  {floor:5} {r['games']:5} {r['turn_median']:7.0f} {r['level_median']:6.1f} "
                  f"{r['level_p25']:>4}-{r['level_p75']:<3}")
    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=2))
        print(f"\nwrote {args.json}")


if __name__ == '__main__':
    main()
