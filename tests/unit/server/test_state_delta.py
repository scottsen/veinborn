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


# --- apply_delta characterization (VB-26) -----------------------------------

import copy


def _player(player_id, hp=10, x=0, y=0):
    return {"player_id": player_id, "name": player_id.title(), "hp": hp, "x": x, "y": y}


def _delta(changes=None, **counters):
    return {"type": "delta", "changes": changes or {}, **counters}


def test_apply_delta_full_replaces_state():
    fresh = _base_state(floor=3)
    assert StateDelta.apply_delta(_base_state(), {"type": "full", "state": fresh}) is fresh


def test_apply_delta_no_changes_returns_current_state():
    state = _base_state()
    assert StateDelta.apply_delta(state, {"type": "delta", "no_changes": True}) is state


def test_apply_delta_advances_counters():
    merged = StateDelta.apply_delta(
        _base_state(),
        _delta(turn_count=7, round_number=2, actions_this_round=3, message_count=9),
    )
    assert (merged["turn_count"], merged["round_number"]) == (7, 2)
    assert (merged["actions_this_round"], merged["message_count"]) == (3, 9)


def test_apply_delta_player_added_updated_removed():
    state = _base_state()
    state["players"] = [_player("a", hp=10), _player("b", hp=10)]
    delta = _delta({"players": [
        {"type": "player_added", "player": _player("c")},
        {"type": "player_updated", "player_id": "a", "changes": {"hp": 4, "x": 5}},
        {"type": "player_removed", "player_id": "b"},
    ]})

    merged = StateDelta.apply_delta(state, delta)

    by_id = {p["player_id"]: p for p in merged["players"]}
    assert set(by_id) == {"a", "c"}
    assert (by_id["a"]["hp"], by_id["a"]["x"]) == (4, 5)


def test_apply_delta_ignores_updates_and_removals_for_unknown_ids():
    state = _base_state(monsters=[_monster("m1")])
    state["players"] = [_player("a")]
    delta = _delta({
        "players": [
            {"type": "player_updated", "player_id": "ghost", "changes": {"hp": 1}},
            {"type": "player_removed", "player_id": "ghost"},
        ],
        "monsters": [
            {"type": "entity_updated", "entity_id": "ghost", "changes": {"hp": 1}},
            {"type": "entity_removed", "entity_id": "ghost"},
        ],
    })

    merged = StateDelta.apply_delta(state, delta)

    assert [p["player_id"] for p in merged["players"]] == ["a"]
    assert [m["entity_id"] for m in merged["monsters"]] == ["m1"]


def test_apply_delta_monster_added_updated_removed():
    state = _base_state(monsters=[_monster("m1", hp=10), _monster("m2")])
    delta = _delta({"monsters": [
        {"type": "entity_added", "entity": _monster("m3")},
        {"type": "entity_updated", "entity_id": "m1", "changes": {"hp": 3}},
        {"type": "entity_removed", "entity_id": "m2"},
    ]})

    merged = StateDelta.apply_delta(state, delta)

    by_id = {m["entity_id"]: m for m in merged["monsters"]}
    assert set(by_id) == {"m1", "m3"}
    assert by_id["m1"]["hp"] == 3


def test_apply_delta_game_over_victory_and_floor():
    merged = StateDelta.apply_delta(
        _base_state(),
        _delta({"game_over": True, "victory": True, "current_floor": 4}),
    )
    assert merged["game_over"] is True
    assert merged["victory"] is True
    assert merged["current_floor"] == 4


def test_apply_delta_message_window_is_last_20():
    state = _base_state()
    state["recent_messages"] = [f"old{i}" for i in range(20)]

    merged = StateDelta.apply_delta(state, _delta({"new_messages": ["n1", "n2"]}))

    assert len(merged["recent_messages"]) == 20
    assert merged["recent_messages"][-2:] == ["n1", "n2"]
    assert merged["recent_messages"][0] == "old2"


def test_apply_delta_does_not_mutate_the_state_it_was_given():
    """apply_delta used to shallow-copy then mutate nested player/monster
    dicts in place, corrupting any snapshot the caller still held."""
    state = _base_state(monsters=[_monster("m1", hp=10)])
    state["players"] = [_player("a", hp=10)]
    snapshot = copy.deepcopy(state)
    delta = _delta({
        "players": [{"type": "player_updated", "player_id": "a", "changes": {"hp": 1}}],
        "monsters": [{"type": "entity_updated", "entity_id": "m1", "changes": {"hp": 1}}],
        "new_messages": ["hi"],
    })

    merged = StateDelta.apply_delta(state, delta)

    assert state == snapshot
    assert merged["players"][0]["hp"] == 1
    assert merged["monsters"][0]["hp"] == 1


def test_compute_delta_sends_full_state_when_the_game_starts():
    """A real two-client playtest found the lobby->started transition went out as a delta:
    clients never got is_started/initialized or their entity_id, so they could not act."""
    lobby = {"is_started": False, "initialized": False, "players": [
        {"player_id": "p1", "player_name": "Alice", "is_ready": True}]}
    started = {"is_started": True, "initialized": True, "players": [
        {"player_id": "p1", "player_name": "Alice", "entity_id": "player_p1",
         "position": {"x": 1, "y": 2}, "health": {"current": 30, "max": 30}}]}

    delta = StateDelta.compute_delta(lobby, started)

    assert delta == {"type": "full", "state": started}
    assert StateDelta.apply_delta(lobby, delta) == started


def test_compute_delta_sends_full_state_when_the_game_finishes():
    running = {"is_started": True, "is_finished": False, "initialized": True, "players": []}
    finished = {"is_started": True, "is_finished": True, "initialized": True, "players": []}

    assert StateDelta.compute_delta(running, finished)["type"] == "full"


def test_compute_delta_stays_a_delta_while_the_game_is_running():
    state = {"is_started": True, "is_finished": False, "initialized": True, "players": [],
             "turn_count": 1}

    assert StateDelta.compute_delta(state, {**state, "turn_count": 2})["type"] == "delta"
