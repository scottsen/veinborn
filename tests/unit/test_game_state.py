"""Unit tests for GameState's entities/player sync invariant (VB-23).

Before this fix, GameState.player and GameState.entities were two
independent stores: single-player's own player and multiplayer's host lived
ONLY in .player, invisible to every entities-based lookup (GameContext.
get_entity, get_entity_at, get_all_players, Lua get_entity). Multiplayer
guests were the third variant, stored only in entities. This is what forced
Action._get_actor() to grow a special-case fallback (VB-16) just to resolve
an actor_id that happened to equal the local player's own id.
"""
import pytest

from core.game_state import GameState
from core.entities import Player

pytestmark = pytest.mark.unit


def test_construction_puts_player_in_entities():
    player = Player(name="Hero", x=1, y=1)

    state = GameState(player=player)

    assert player.entity_id in state.entities
    assert state.entities[player.entity_id] is player


def test_reassigning_player_syncs_entities():
    """Mirrors multiplayer_game_state.add_player(): construct with a
    placeholder player, then replace it with the real one at spawn."""
    placeholder = Player(name="placeholder", x=0, y=0)
    state = GameState(player=placeholder)

    real_player = Player(name="Hero", x=5, y=5)
    real_player.entity_id = "player"
    state.player = real_player

    assert state.entities["player"] is real_player
    assert state.player is real_player


def test_reassigning_player_removes_stale_entry():
    """The placeholder's old entity_id must not linger as an orphaned
    duplicate entity once the real player replaces it."""
    placeholder = Player(name="placeholder", x=0, y=0)
    placeholder_id = placeholder.entity_id
    state = GameState(player=placeholder)

    real_player = Player(name="Hero", x=5, y=5)
    real_player.entity_id = "player"
    state.player = real_player

    assert placeholder_id not in state.entities
    assert len(state.entities) == 1


def test_reassigning_player_to_same_entity_id_does_not_lose_it():
    player = Player(name="Hero", x=1, y=1)
    player.entity_id = "player"
    state = GameState(player=player)

    updated = Player(name="Hero", x=2, y=2)
    updated.entity_id = "player"
    state.player = updated

    assert state.entities["player"] is updated
    assert len(state.entities) == 1


def test_construction_preserves_other_entities():
    player = Player(name="Hero", x=1, y=1)
    other = Player(name="Guest", x=2, y=2)
    other.entity_id = "guest"

    state = GameState(player=player, entities={"guest": other})

    assert set(state.entities.keys()) == {player.entity_id, "guest"}
