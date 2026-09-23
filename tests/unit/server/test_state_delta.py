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


def _message_state(all_messages, message_count=None, window=20):
    return {
        **_base_state(),
        "recent_messages": all_messages[-window:],
        "message_count": message_count if message_count is not None else len(all_messages),
    }


def test_compute_delta_detects_new_messages_after_recent_messages_window_full():
    """VB-20: recent_messages is capped at 20 server-side. Once more than 20
    messages have ever been sent, both snapshots are permanently 20 items
    long, so the old len(new) > len(old) check never fired again for the
    rest of the game. message_count must still catch the new messages."""
    all_before = [f"msg-{i}" for i in range(20)]
    all_after = all_before + ["msg-20", "msg-21", "msg-22"]

    old_state = _message_state(all_before)
    new_state = _message_state(all_after)

    # Same length in both snapshots -- this is exactly the old bug's blind spot.
    assert len(old_state["recent_messages"]) == len(new_state["recent_messages"]) == 20

    delta = StateDelta.compute_delta(old_state, new_state)

    assert delta["changes"]["new_messages"] == ["msg-20", "msg-21", "msg-22"]


def test_compute_delta_no_new_messages_when_count_unchanged():
    all_messages = [f"msg-{i}" for i in range(25)]
    old_state = _message_state(all_messages)
    new_state = _message_state(all_messages)

    delta = StateDelta.compute_delta(old_state, new_state)

    assert "new_messages" not in delta["changes"]


def test_apply_delta_appends_new_messages_and_advances_message_count():
    all_before = [f"msg-{i}" for i in range(20)]
    all_after = all_before + ["msg-20", "msg-21", "msg-22"]

    old_state = _message_state(all_before)
    new_state = _message_state(all_after)

    delta = StateDelta.compute_delta(old_state, new_state)
    merged = StateDelta.apply_delta(old_state, delta)

    assert merged["recent_messages"][-3:] == ["msg-20", "msg-21", "msg-22"]
    assert len(merged["recent_messages"]) == 20
    assert merged["message_count"] == 23
