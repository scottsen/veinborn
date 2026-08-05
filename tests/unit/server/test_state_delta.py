"""Tests for StateDelta floor/monster diffing (VB-4)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from server.state_delta import StateDelta


def _base_state(floor=1, monsters=None, tiles=None):
    return {
        "players": [],
        "current_floor": floor,
        "map": {"width": 2, "height": 1, "tiles": tiles or ["##"]},
        "monsters": monsters or [],
        "recent_messages": [],
        "game_over": False,
        "victory": False,
    }


def _monster(entity_id, x=0, y=0, hp=10):
    return {
        "entity_id": entity_id,
        "entity_type": "monster",
        "name": "Goblin",
        "x": x,
        "y": y,
        "hp": hp,
        "max_hp": 10,
        "attack": 1,
        "defense": 1,
        "stats": {},
        "is_alive": True,
        "is_active": True,
        "content_id": "goblin",
    }


def test_compute_delta_diffs_current_floor():
    old_state = _base_state(floor=1)
    new_state = _base_state(floor=2)

    delta = StateDelta.compute_delta(old_state, new_state)

    assert delta["changes"]["current_floor"] == 2


def test_compute_delta_omits_floor_when_unchanged():
    old_state = _base_state(floor=1)
    new_state = _base_state(floor=1)

    delta = StateDelta.compute_delta(old_state, new_state)

    assert "current_floor" not in delta["changes"]
    assert delta.get("no_changes") is True


def test_compute_delta_includes_map_only_when_it_changes():
    old_state = _base_state(floor=1, tiles=["##"])
    same_map_state = _base_state(floor=1, tiles=["##"])
    new_map_state = _base_state(floor=2, tiles=[".."])

    unchanged_delta = StateDelta.compute_delta(old_state, same_map_state)
    assert "map" not in unchanged_delta["changes"]

    changed_delta = StateDelta.compute_delta(old_state, new_map_state)
    assert changed_delta["changes"]["map"]["tiles"] == [".."]


def test_compute_delta_detects_monster_added_updated_removed():
    old_state = _base_state(monsters=[_monster("m1", hp=10), _monster("m2")])
    new_state = _base_state(monsters=[_monster("m1", hp=5), _monster("m3")])

    delta = StateDelta.compute_delta(old_state, new_state)
    changes_by_type = {c["type"] for c in delta["changes"]["monsters"]}

    assert changes_by_type == {"entity_added", "entity_updated", "entity_removed"}


def test_apply_delta_merges_floor_map_and_monsters():
    old_state = _base_state(floor=1, monsters=[_monster("m1", hp=10)], tiles=["##"])
    new_state = _base_state(floor=2, monsters=[_monster("m2", hp=8)], tiles=[".."])

    delta = StateDelta.compute_delta(old_state, new_state)
    merged = StateDelta.apply_delta(old_state, delta)

    assert merged["current_floor"] == 2
    assert merged["map"]["tiles"] == [".."]
    assert [m["entity_id"] for m in merged["monsters"]] == ["m2"]


def test_apply_delta_updates_monster_fields_in_place():
    old_state = _base_state(monsters=[_monster("m1", x=1, y=1, hp=10)])
    new_state = _base_state(monsters=[_monster("m1", x=2, y=1, hp=6)])

    delta = StateDelta.compute_delta(old_state, new_state)
    merged = StateDelta.apply_delta(old_state, delta)

    merged_monster = merged["monsters"][0]
    assert merged_monster["x"] == 2
    assert merged_monster["hp"] == 6
