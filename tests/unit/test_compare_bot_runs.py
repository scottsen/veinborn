"""scripts/compare_bot_runs.py pairs seeded bot games and reports paired differences (VB-68)."""
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "compare_bot_runs.py"


@pytest.fixture(scope="module")
def cmp():
    spec = importlib.util.spec_from_file_location("compare_bot_runs", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def game(seed, floor, cls="mage", died=False, crash=False):
    return {'game_number': seed, 'character_class': cls, 'seed': seed, 'floor_reached': floor,
            'turns_survived': 100, 'player_level': 1, 'monsters_killed': 0, 'damage_taken': 0,
            'completed': not (died or crash),
            'death_cause': 'crash' if crash else ('Killed by Orc' if died else None), 'errors': 0,
            'burst_death': False, 'potions_used': 0, 'killed_by_type': 'orc' if died else None}


def write(tmp_path, name, games):
    path = tmp_path / name
    path.write_text(json.dumps({'metadata': {'character_class': 'mage'}, 'games': games}))
    return path


def test_pairs_by_class_and_seed_and_finds_a_consistent_shift(cmp, tmp_path):
    before, _ = cmp.load([write(tmp_path, "b.json", [game(s, 3 + s % 3) for s in range(20)])])
    after, _ = cmp.load([write(tmp_path, "a.json", [game(s, 4 + s % 3) for s in range(20)])])
    keys = sorted(before)
    r = cmp.paired(before, after, keys, lambda g: g['floor_reached'])
    assert r['n'] == 20 and r['diff'] == 1.0 and r['significant']


def test_identical_runs_show_no_difference(cmp, tmp_path):
    games = [game(s, 2 + s % 4, died=s % 5 == 0) for s in range(10)]
    before, _ = cmp.load([write(tmp_path, "b.json", games)])
    after, _ = cmp.load([write(tmp_path, "a.json", games)])
    for _, _, read in cmp.METRICS:
        r = cmp.paired(before, after, sorted(before), read)
        assert r['diff'] == 0 and not r['significant']


def test_noise_without_a_shift_is_not_significant(cmp, tmp_path):
    before, _ = cmp.load([write(tmp_path, "b.json", [game(s, 3) for s in range(12)])])
    after, _ = cmp.load([write(tmp_path, "a.json", [game(s, 3 + (1 if s % 2 else -1)) for s in range(12)])])
    r = cmp.paired(before, after, sorted(before), lambda g: g['floor_reached'])
    assert r['diff'] == 0 and not r['significant']


def test_died_and_crashed_are_counted_separately(cmp):
    died = dict(cmp.METRICS[i][::2] for i in range(len(cmp.METRICS)))
    assert died['died'](game(1, 1, died=True)) == 1 and died['crashed'](game(1, 1, died=True)) == 0
    assert died['died'](game(1, 1, crash=True)) == 0 and died['crashed'](game(1, 1, crash=True)) == 1


def test_unseeded_results_are_rejected(cmp, tmp_path):
    g = game(1, 1)
    g['seed'] = None
    with pytest.raises(SystemExit):
        cmp.load([write(tmp_path, "b.json", [g])])


def test_damage_by_monster_isolates_the_monster_that_changed(cmp, tmp_path):
    def with_damage(seed, orc, imp):
        g = game(seed, 3)
        g['damage_taken_by'] = {'orc': orc + seed % 3, 'imp': imp}
        return g
    before, _ = cmp.load([write(tmp_path, "b.json", [with_damage(s, 10, 0) for s in range(12)])])
    after, _ = cmp.load([write(tmp_path, "a.json", [with_damage(s, 10, 5) for s in range(12)])])
    rows = cmp.damage_by_monster(before, after, sorted(before))
    assert list(rows) == ['orc', 'imp']                       # most damage first
    assert rows['orc']['diff'] == 0 and not rows['orc']['significant']
    assert rows['imp']['diff'] == 5 and rows['imp']['significant']


def test_damage_by_monster_skips_runs_without_it(cmp, tmp_path):
    before, _ = cmp.load([write(tmp_path, "b.json", [game(s, 3) for s in range(4)])])
    assert cmp.damage_by_monster(before, before, sorted(before)) == {}
