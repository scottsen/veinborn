"""scripts/sim_duels.py drives monsters through the real AISystem (VB-68).

The balance numbers for VB-64 come from this sim, so these tests pin the parts a
silent break would falsify: abilities actually fire when switched on, never when
off, summons find the AI, and damage is attributed to the right source.
"""
import importlib.util
from pathlib import Path

import pytest

from core.character_class import CharacterClass
from core.entity_loader import EntityLoader
from core.rng import GameRNG

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "sim_duels.py"


@pytest.fixture(scope="module")
def sim():
    spec = importlib.util.spec_from_file_location("sim_duels", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def loader():
    GameRNG.initialize(7)
    return EntityLoader()


def fights(sim, loader, monster_id, spec, n=20, level=6, cls=CharacterClass.WARRIOR, distance=3):
    base = loader.monsters
    loader.monsters = sim.monster_defs(base, spec, {})
    try:
        arena = sim.open_arena()
        return [sim.duel(cls, level, monster_id, loader, arena, start_distance=distance)
                for _ in range(n)]
    finally:
        loader.monsters = base


def test_shipped_monsters_use_no_abilities(sim, loader):
    for f in fights(sim, loader, "lich", "off"):
        assert f.ability_uses == {}
        assert f.damage["ability"] == f.damage["minion"] == 0


def test_switched_on_bolt_fires_and_counts_as_ability_damage(sim, loader):
    results = fights(sim, loader, "imp", {"imp.fire_bolt"})
    assert sum(f.ability_uses.get("fire_bolt", 0) for f in results) > 0
    assert sum(f.damage["ability"] for f in results) > 0


def test_summons_reach_the_ai_and_minion_damage_is_separate(sim, loader):
    results = fights(sim, loader, "lich", {"lich.summon_undead"})
    assert sum(f.ability_uses.get("summon_undead", 0) for f in results) > 0
    assert sum(f.damage["minion"] for f in results) > 0
    assert all("death_bolt" not in f.ability_uses for f in results)  # only what was asked


def test_overrides_change_the_ability_config(sim, loader):
    defs = sim.monster_defs(loader.monsters, "on", {("lich", "death_bolt"): {"damage": 3}})
    assert defs["lich"]["abilities"]["death_bolt"] == {**defs["lich"]["abilities"]["death_bolt"],
                                                       "enabled": True, "damage": 3}
    assert loader.monsters["lich"]["abilities"]["death_bolt"]["enabled"] is False  # base untouched


def test_a_fight_ends_with_a_winner_or_a_timeout(sim, loader):
    for f in fights(sim, loader, "goblin", "off", level=1):
        assert f.won or f.timeout or f.hp_lost == 1.0
