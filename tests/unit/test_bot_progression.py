"""scripts/bot_progression.py: the level-by-floor curve from bot floor_arrivals (VB-69)."""
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "bot_progression.py"
pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def prog():
    spec = importlib.util.spec_from_file_location("bot_progression", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_curve_groups_by_class_and_floor(prog):
    games = [  # JSON keys arrive as strings
        {'character_class': 'mage', 'floor_arrivals': {'1': [0, 1], '2': [300, 3], '3': [900, 4]}},
        {'character_class': 'mage', 'floor_arrivals': {'1': [0, 1], '2': [500, 5]}},
        {'character_class': 'warrior', 'floor_arrivals': {'1': [0, 1], '2': [200, 2]}},
    ]
    c = prog.curve(games)
    assert c['mage'][2] == {'games': 2, 'turn_median': 400, 'level_median': 4,
                            'level_p25': 3, 'level_p75': 5}
    assert c['mage'][3]['games'] == 1
    assert 'attack_median' not in c['mage'][2]          # older two-field arrivals still read
    assert c['ALL'][2]['games'] == 3 and c['ALL'][2]['level_median'] == 3


def test_curve_reads_attack_and_defense(prog):
    games = [{'character_class': 'rogue', 'floor_arrivals': {'4': [900, 5, 9, 4]}},
             {'character_class': 'rogue', 'floor_arrivals': {'4': [1100, 6, 11, 6]}}]
    row = prog.curve(games)['rogue'][4]
    assert row['attack_median'] == 10 and row['defense_median'] == 5


def test_bot_records_floor_arrivals():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fuzz"))
    from warrior_bot import WarriorBot
    stats = WarriorBot().play_one_game(max_turns=400, seed=1000)
    arrivals = stats['floor_arrivals']
    assert arrivals[1][:2] == [0, 1] and len(arrivals[1]) == 4
    assert len(arrivals) >= 2          # seed 1000 descends by turn ~340: a real arrival recorded
    assert max(arrivals) == stats['floor']
    turns = [arrivals[f][0] for f in sorted(arrivals)]
    assert all(arrivals[f][2] > 0 for f in arrivals)   # total attack recorded
    assert turns == sorted(turns)
