#!/usr/bin/env python3
"""Paired before/after comparison of seeded bot runs (VB-68).

Both runs must use the same --seed-base and --max-turns (see tests/fuzz/veinborn_bot.py).
Games are paired by (class, seed): with the dungeon, dice and bot choices fixed by the
seed, the per-pair difference is the effect of the code change, and the noise that
made 8-game unseeded runs unreadable mostly cancels.

Usage:
    python3 scripts/compare_bot_runs.py --before logs/before_*.json --after logs/after_*.json
    python3 scripts/compare_bot_runs.py --before a.json --after b.json --json diff.json

Per metric: mean before, mean after, mean paired difference with a 95% confidence
interval. '*' marks a difference whose interval excludes 0.
"""
import argparse
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

METRICS = [
    # (name, label, how to read a game)
    ('floor', 'floor reached', lambda g: g['floor_reached']),
    ('turns', 'turns survived', lambda g: g['turns_survived']),
    ('level', 'player level', lambda g: g['player_level']),
    ('kills', 'monsters killed', lambda g: g['monsters_killed']),
    ('dmg_taken', 'damage taken', lambda g: g['damage_taken']),
    ('died', 'died (0/1)', lambda g: int(not g['completed'] and g['death_cause'] != 'crash')),
    ('crashed', 'crashed (0/1)', lambda g: int(g['death_cause'] == 'crash')),
    ('errors', 'errors', lambda g: g.get('errors', 0)),
    ('burst', 'burst death 0/1', lambda g: int(bool(g['burst_death']))),
    ('potions', 'potions used', lambda g: g['potions_used']),
]
# Fields added after the first results files: a metric is skipped unless every game has it
_NEEDS = {'burst': 'burst_death', 'potions': 'potions_used'}

# Two-sided 95% t critical values by degrees of freedom (normal beyond 30)
_T95 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26,
        10: 2.23, 12: 2.18, 15: 2.13, 20: 2.09, 25: 2.06, 30: 2.04}


def t95(df):
    if df >= 30:
        return 1.96 if df > 60 else 2.0
    return _T95.get(df) or _T95[max(k for k in _T95 if k <= df)]


def load(paths):
    """{(class, seed): game} plus the runs' metadata."""
    games, meta = {}, []
    for path in paths:
        data = json.loads(Path(path).read_text())
        meta.append({'file': str(path), **data.get('metadata', {})})
        for g in data['games']:
            if g.get('seed') is None:
                sys.exit(f"{path}: game {g['game_number']} has no seed; rerun with --seed-base")
            key = (g['character_class'], g['seed'])
            if key in games:
                sys.exit(f"{path}: {key} appears twice in the 'before' or 'after' set")
            games[key] = g
    return games, meta


def paired(before, after, keys, read):
    diffs = [read(after[k]) - read(before[k]) for k in keys]
    n = len(diffs)
    mean_b = statistics.fmean(read(before[k]) for k in keys)
    mean_a = statistics.fmean(read(after[k]) for k in keys)
    mean_d = statistics.fmean(diffs)
    half = t95(n - 1) * statistics.stdev(diffs) / math.sqrt(n) if n > 1 else float('inf')
    return {'n': n, 'before': mean_b, 'after': mean_a, 'diff': mean_d,
            'ci_low': mean_d - half, 'ci_high': mean_d + half,
            'significant': n > 1 and (mean_d - half > 0 or mean_d + half < 0)}


def print_killers(before, after, keys):
    """Which monster types killed the bot, before vs after (when recorded)."""
    if not all('killed_by_type' in before[k] and 'killed_by_type' in after[k] for k in keys):
        return
    counts = defaultdict(lambda: [0, 0])
    for k in keys:
        for side, g in ((0, before[k]), (1, after[k])):
            if g['killed_by_type']:
                counts[g['killed_by_type']][side] += 1
    if counts:
        print("  killed by: " + ", ".join(
            f"{m} {b}->{a}" for m, (b, a) in sorted(counts.items(), key=lambda kv: -sum(kv[1]))))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--before', nargs='+', required=True)
    ap.add_argument('--after', nargs='+', required=True)
    ap.add_argument('--json', help='also write the comparison to this file')
    args = ap.parse_args()

    before, meta_b = load(args.before)
    after, meta_a = load(args.after)

    for side, meta in (('before', meta_b), ('after', meta_a)):
        for m in meta:
            code = m.get('code') or {}
            print(f"{side:6} {m.get('character_class', '?'):8} commit {code.get('commit')}"
                  f"{' (dirty)' if code.get('dirty') else ''}  seeds from {m.get('seed_base')}"
                  f"  max_turns {m.get('max_turns')}  {m['file']}")
    turns = {m.get('max_turns') for m in meta_b + meta_a}
    if len(turns) > 1:
        print(f"WARNING: runs used different --max-turns {sorted(turns, key=str)}; turns/floor are not comparable")

    common = sorted(set(before) & set(after))
    unmatched = len(set(before) ^ set(after))
    if unmatched:
        print(f"note: {unmatched} games have no partner (different seeds or classes) and are skipped")
    if not common:
        sys.exit("no (class, seed) pairs in common")

    by_class = defaultdict(list)
    for key in common:
        by_class[key[0]].append(key)
    groups = sorted(by_class.items())
    if len(groups) > 1:
        groups.append(('ALL', common))

    report = {}
    for cls, keys in groups:
        print(f"\n{cls}  ({len(keys)} pairs)")
        print(f"  {'metric':16} {'before':>8} {'after':>8} {'diff':>8}   95% CI")
        report[cls] = {}
        for name, label, read in METRICS:
            field = _NEEDS.get(name)
            if field and not all(field in g for k in keys for g in (before[k], after[k])):
                print(f"  {label:16} (not in both runs)")
                continue
            r = paired(before, after, keys, read)
            report[cls][name] = r
            mark = '*' if r['significant'] else ' '
            print(f"  {label:16} {r['before']:8.2f} {r['after']:8.2f} {r['diff']:+8.2f}{mark}  "
                  f"[{r['ci_low']:+.2f}, {r['ci_high']:+.2f}]")
        shared = [read for name, _, read in METRICS if name in report[cls]]
        identical = sum(all(read(before[k]) == read(after[k]) for read in shared) for k in keys)
        print_killers(before, after, keys)
        print(f"  identical games: {identical}/{len(keys)}")

    if args.json:
        Path(args.json).write_text(json.dumps(
            {'before': meta_b, 'after': meta_a, 'pairs': len(common), 'report': report}, indent=2))
        print(f"\nwrote {args.json}")


if __name__ == '__main__':
    main()
