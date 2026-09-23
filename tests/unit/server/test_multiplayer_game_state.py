"""Tests for MultiplayerGameState floor entity spawning and floor descent (VB-4)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from server.multiplayer_game_state import MultiplayerGameState


def _make_two_player_game(seed=42):
    mp = MultiplayerGameState(seed=seed, max_players=4)
    mp.add_player("p1", "Alice", "warrior")
    mp.add_player("p2", "Bob", "mage")
    return mp


def _non_player_entity_ids(mp):
    """Dict keys in game_state.entities that aren't a player's entity.

    Note: game_state.entities is keyed by the player-slot-assigned entity_id
    string (e.g. "player_p2"), not by the Entity object's own .entity_id
    dataclass field (a separate, unrelated random uuid) - the dict key is
    what every other lookup in the codebase (GameContext.get_entity,
    Action.actor_id, entity_to_player) actually uses as identity.
    """
    player_entity_ids = set(mp.entity_to_player.keys())
    return {
        entity_id for entity_id in mp.game_state.entities
        if entity_id not in player_entity_ids
    }


def test_add_player_spawns_floor_entities():
    """Before VB-4, MP mode never spawned monsters/ore veins/forges at all."""
    mp = _make_two_player_game()

    assert len(mp.game_state.entities) > 0
    assert len(_non_player_entity_ids(mp)) > 0


def test_host_player_is_in_entities():
    """VB-23: the host (first player added) used to live ONLY in
    game_state.player, invisible to game_state.entities -- the dict every
    position/id-based lookup (GameContext.get_entity, get_entity_at, Lua
    get_entity) actually scans. Confirm it's now present under its real
    entity_id, matching how guests already worked."""
    mp = _make_two_player_game()
    host_slot = mp.player_slots["p1"]

    assert host_slot.entity_id in mp.game_state.entities
    assert mp.game_state.entities[host_slot.entity_id] is host_slot.player_entity
    assert mp.game_state.entities[host_slot.entity_id] is mp.game_state.player


def test_host_player_findable_by_game_context_get_entity():
    """VB-23: GameContext.get_entity() previously missed the host entirely
    (it only reads game_state.entities). Action._get_actor() needed a
    special-case fallback (VB-16) to work around exactly this."""
    from core.base.game_context import GameContext

    mp = _make_two_player_game()
    host_slot = mp.player_slots["p1"]
    context = GameContext(game_state=mp.game_state)

    found = context.get_entity(host_slot.entity_id)

    assert found is host_slot.player_entity


def test_host_player_findable_at_own_position():
    """VB-23: get_entity_at/get_entities_in_range/get_entities_at all scan
    entities only -- the host was invisible to all of them, meaning e.g.
    monster AI could never see or target the host at their own tile."""
    from core.base.game_context import GameContext

    mp = _make_two_player_game()
    host = mp.game_state.player
    context = GameContext(game_state=mp.game_state)

    found = context.get_entity_at(host.x, host.y)

    assert found is host


def test_get_all_players_includes_host_and_guest_without_duplication():
    """VB-23: get_all_players() used to hand-merge game_state.player with
    entities and de-dup by object identity. Now entities is the single
    store, so this should just be a clean type filter with no duplicates."""
    from core.base.game_context import GameContext

    mp = _make_two_player_game()
    context = GameContext(game_state=mp.game_state)

    all_players = context.get_all_players()

    assert len(all_players) == 2
    assert mp.game_state.player in all_players
    guest_entity = mp.game_state.entities[mp.player_slots["p2"].entity_id]
    assert guest_entity in all_players


def test_get_state_dict_includes_monsters_and_map():
    mp = _make_two_player_game()
    state = mp.get_state_dict()

    assert "monsters" in state
    assert len(state["monsters"]) > 0
    assert "map" in state
    assert state["map"]["width"] == mp.game_state.dungeon_map.width
    assert state["map"]["height"] == mp.game_state.dungeon_map.height
    assert len(state["map"]["tiles"]) == state["map"]["height"]

    # Player entities must not leak into the monsters list
    monster_ids = {m["entity_id"] for m in state["monsters"]}
    assert monster_ids.isdisjoint(set(mp.entity_to_player.keys()))


def test_descend_floor_advances_floor_and_regenerates_map():
    mp = _make_two_player_game()
    old_map_id = id(mp.game_state.dungeon_map)

    mp.descend_floor()

    assert mp.game_state.current_floor == 2
    assert id(mp.game_state.dungeon_map) != old_map_id


def test_descend_floor_preserves_all_players():
    """The bug this guards: FloorManager.entities.clear() would have wiped
    non-host players since MP stores them in game_state.entities too."""
    mp = _make_two_player_game()

    mp.descend_floor()

    assert len(mp.player_slots) == 2
    assert set(mp.player_slots.keys()) == {"p1", "p2"}
    # Bob's entity (index 1) lives in game_state.entities, not .player
    bob_entity_id = mp.player_slots["p2"].entity_id
    assert bob_entity_id in mp.game_state.entities


def test_descend_floor_respawns_entities_with_new_ids():
    mp = _make_two_player_game()
    old_entity_ids = _non_player_entity_ids(mp)

    mp.descend_floor()

    new_entity_ids = _non_player_entity_ids(mp)
    assert len(new_entity_ids) > 0
    assert old_entity_ids.isdisjoint(new_entity_ids)


def test_descend_floor_at_victory_floor_ends_game(monkeypatch):
    mp = _make_two_player_game()
    # ConfigLoader.load() is a process-wide singleton - patch the instance
    # method instead of mutating shared game_constants
    monkeypatch.setattr(mp, "_get_victory_floor", lambda: 2)

    mp.descend_floor()

    assert mp.game_state.victory is True
    assert mp.game_state.game_over is True
    # Victory short-circuits before advancing current_floor
    assert mp.game_state.current_floor == 1


def test_concurrent_games_do_not_share_rng_stream():
    """VB-18: each MultiplayerGameState used to draw all randomness from
    the process-global GameRNG singleton. add_player() re-seeded it
    (GameRNG.initialize(seed)) whenever a NEW game's first player joined,
    silently rewiring every OTHER in-flight game's dungeon-gen/combat/loot
    rolls to the new game's seed. Reproduced: start game A, then start
    game B with a different seed while A is "mid-session" -- game A's own
    RNG instance (and therefore its dungeon layout) must be unaffected by
    game B's existence."""
    mp_a = _make_two_player_game(seed=111)
    layout_a_before = [[t.tile_type for t in col] for col in mp_a.game_state.dungeon_map.tiles]
    rng_a_next_before = mp_a.game_state.rng.randint(1, 1_000_000)

    # A second, differently-seeded game starts while A is already running.
    mp_b = _make_two_player_game(seed=222)

    # Game A's own RNG instance must be a different object from game B's,
    # and must not have been reseeded/advanced by game B starting.
    assert mp_a.game_state.rng is not mp_b.game_state.rng
    layout_a_after = [[t.tile_type for t in col] for col in mp_a.game_state.dungeon_map.tiles]
    assert layout_a_before == layout_a_after

    # Re-create game A fresh with the same seed and replay the same first
    # draw -- it must reproduce rng_a_next_before, proving A's stream was
    # never touched by B's setup.
    mp_a_replay = _make_two_player_game(seed=111)
    replay_layout = [[t.tile_type for t in col] for col in mp_a_replay.game_state.dungeon_map.tiles]
    assert replay_layout == layout_a_before
    assert mp_a_replay.game_state.rng.randint(1, 1_000_000) == rng_a_next_before
