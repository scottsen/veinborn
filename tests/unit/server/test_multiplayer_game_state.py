"""Tests for MultiplayerGameState: the run built from the seats (VB-94), floor spawning (VB-4), descent."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from server.multiplayer_game_state import MultiplayerGameState, Seat, seat_entity_id


def _make_two_player_game(seed=42):
    return MultiplayerGameState(
        [Seat("p1", "Alice", "warrior"), Seat("p2", "Bob", "mage")], seed=seed, max_players=4
    )


def _non_player_entity_ids(mp):
    """Keys of game_state.entities that aren't a seat's entity (each seat's
    entity_id is both its dict key and the entity's own .entity_id)."""
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
    position/id-based lookup (GameContext.get_entity, get_entity_at)
    actually scans. Confirm it's now present under its real
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


def test_a_viewers_snapshot_includes_monsters_map_and_the_other_players():
    from core.snapshot import build_snapshot
    mp = _make_two_player_game()
    viewer = mp.player_slots["p1"].player_entity
    snap = build_snapshot(mp.game_state, viewer=viewer)

    monsters = [e for e in snap.entities if e.entity_type == "monster"]
    assert len(monsters) > 0
    assert snap.map.width == mp.game_state.dungeon_map.width
    assert snap.map.height == mp.game_state.dungeon_map.height
    assert len(snap.map.tiles) == snap.map.height

    # The viewer is the snapshot's player; the other seat is an entity in their world
    others = {e.entity_id for e in snap.entities if e.entity_type == "player"}
    assert snap.player.entity_id == viewer.entity_id
    assert others == {mp.player_slots["p2"].entity_id}


def _descend(mp):
    """The party descends through the same FloorManager single-player uses."""
    from core.base.game_context import GameContext
    from core.floor_manager import FloorManager

    FloorManager(
        GameContext(mp.game_state), mp.spawner
    ).descend_floor()


def test_descend_floor_advances_floor_and_regenerates_map():
    mp = _make_two_player_game()
    old_map_id = id(mp.game_state.dungeon_map)

    _descend(mp)

    assert mp.game_state.current_floor == 2
    assert id(mp.game_state.dungeon_map) != old_map_id


def test_descend_floor_preserves_all_players():
    """The bug this guards: clearing the old floor would have wiped
    non-host players since MP stores them in game_state.entities too."""
    mp = _make_two_player_game()

    _descend(mp)

    assert len(mp.player_slots) == 2
    assert set(mp.player_slots.keys()) == {"p1", "p2"}
    # Bob's entity (index 1) lives in game_state.entities, not .player
    bob_entity_id = mp.player_slots["p2"].entity_id
    assert bob_entity_id in mp.game_state.entities


def test_descend_floor_puts_every_player_on_a_distinct_walkable_spawn():
    mp = _make_two_player_game()

    _descend(mp)

    entities = [slot.player_entity for slot in mp.player_slots.values()]
    positions = [(e.x, e.y) for e in entities]
    assert len(set(positions)) == len(positions)
    assert all(mp.game_state.dungeon_map.is_walkable(x, y) for x, y in positions)


def test_descend_floor_respawns_entities_with_new_ids():
    mp = _make_two_player_game()
    old_entity_ids = _non_player_entity_ids(mp)

    _descend(mp)

    new_entity_ids = _non_player_entity_ids(mp)
    assert len(new_entity_ids) > 0
    assert old_entity_ids.isdisjoint(new_entity_ids)


def test_descend_floor_at_victory_floor_ends_game(monkeypatch):
    mp = _make_two_player_game()
    # ConfigLoader.load() is a process-wide singleton - patch the lookup
    # instead of mutating shared game_constants
    monkeypatch.setattr("core.floor_manager.get_victory_floor", lambda config: 2)

    _descend(mp)

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


def test_snapshot_player_carries_the_sidebar_numbers():
    """VB-78: totals include gear; equipment, level, xp and ability cooldowns are sent."""
    from core.snapshot import build_snapshot
    mp = _make_two_player_game()
    for slot in mp.player_slots.values():
        entity = slot.player_entity
        view = build_snapshot(mp.game_state, viewer=entity).player
        assert view.attack == entity.get_total_attack()
        assert view.defense == entity.get_total_defense()
        assert view.level == entity.get_stat('level', 1)
        assert view.xp_next == (entity.xp_for_next_level() or None)
        weapon = entity.equipped_weapon
        assert (view.weapon.name if view.weapon else None) == (weapon.name if weapon else None)
    mage = mp.player_slots["p2"].player_entity
    assert [a.name for a in build_snapshot(mp.game_state, viewer=mage).player.abilities]


def test_equipment_change_shows_in_the_next_snapshot():
    from core.snapshot import build_snapshot
    mp = _make_two_player_game()
    entity = mp.player_slots["p1"].player_entity
    before = build_snapshot(mp.game_state, viewer=entity).player
    assert before.weapon is not None

    entity.equipped_weapon = None
    entity.equipped_armor = None

    after = build_snapshot(mp.game_state, viewer=entity).player
    assert after.weapon is None and after.armor is None


# --- VB-94: the run is built once from the seated players ---------------------

def test_every_seat_gets_the_same_id_scheme_and_no_fixed_player_id():
    mp = MultiplayerGameState(
        [Seat("aaaaaaaa-1", "Alice", "warrior"), Seat("bbbbbbbb-2", "Bob", "mage"), Seat("cccccccc-3", "Cy", "rogue")],
        seed=7,
    )
    ids = [slot.entity_id for slot in mp.player_slots.values()]
    assert ids == ["player_aaaaaaaa", "player_bbbbbbbb", "player_cccccccc"]
    assert "player" not in mp.game_state.entities
    for slot in mp.player_slots.values():
        assert slot.player_entity.entity_id == slot.entity_id
        assert mp.game_state.entities[slot.entity_id] is slot.player_entity
        assert mp.entity_to_player[slot.entity_id] == slot.player_id


def test_seats_keep_their_order_class_and_name():
    mp = MultiplayerGameState([Seat("p1", "Alice", "warrior"), Seat("p2", "Bob", "mage")], seed=3)
    assert list(mp.player_slots) == ["p1", "p2"]
    alice, bob = (mp.player_slots[p].player_entity for p in ("p1", "p2"))
    assert (alice.name, alice.stats.get("class_type")) == ("Alice", "warrior")
    assert (bob.name, bob.stats.get("class_type")) == ("Bob", "mage")
    # Compatibility only: the first seat is state.player
    assert mp.game_state.player is alice


def test_every_seat_starts_on_its_own_walkable_tile():
    seats = [Seat(f"p{i}", f"P{i}") for i in range(4)]
    mp = MultiplayerGameState(seats, seed=11)
    positions = [(s.player_entity.x, s.player_entity.y) for s in mp.player_slots.values()]
    assert len(set(positions)) == 4
    assert all(mp.game_state.dungeon_map.is_walkable(x, y) for x, y in positions)


def test_the_map_has_the_configured_size():
    mp = _make_two_player_game()
    dims = mp.config.game_constants["map"]
    assert (mp.game_state.dungeon_map.width, mp.game_state.dungeon_map.height) == (
        dims["default_width"], dims["default_height"])


def test_same_seed_and_seats_build_the_same_run():
    a, b = _make_two_player_game(seed=99), _make_two_player_game(seed=99)
    pos = lambda mp: [(s.player_entity.x, s.player_entity.y) for s in mp.player_slots.values()]
    assert pos(a) == pos(b)
    kinds = lambda mp: sorted((e.content_id or "", e.x, e.y) for k, e in mp.game_state.entities.items()
                              if k not in mp.entity_to_player)
    assert kinds(a) == kinds(b)


def test_unknown_class_falls_back_to_a_default_character():
    mp = MultiplayerGameState([Seat("p1", "Alice", "bard")], seed=1)
    alice = mp.player_slots["p1"].player_entity
    assert alice.name == "Alice" and alice.is_alive


@pytest.mark.parametrize("seats, max_players", [
    ([], 4),
    ([Seat(f"p{i}", f"P{i}") for i in range(3)], 2),
    ([Seat("p1", "Alice"), Seat("p1", "Alice again")], 4),
])
def test_invalid_seatings_are_refused(seats, max_players):
    with pytest.raises(ValueError):
        MultiplayerGameState(seats, seed=1, max_players=max_players)


def test_seat_entity_id_falls_back_to_the_full_id_on_a_prefix_collision():
    first = seat_entity_id("12345678-aaaa")
    assert first == "player_12345678"
    assert seat_entity_id("12345678-bbbb", taken={first}) == "player_12345678-bbbb"
