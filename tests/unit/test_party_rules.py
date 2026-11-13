"""Party-aware turn rules (MP plan 2a / VB-89): the same code serves one player or many."""

from unittest.mock import MagicMock

from core.base.game_context import GameContext
from core.entities import Player
from core.floor_manager import FloorManager
from core.game_state import GameState
from core.turn_processor import TurnProcessor
from core.world import Map


def _party(n=2):
    players = [Player(name=f"P{i}", x=1 + i, y=1) for i in range(n)]
    players[0].entity_id = "player"
    for i, p in enumerate(players[1:], 1):
        p.entity_id = f"player_{i}"
    state = GameState(player=players[0], dungeon_map=Map(width=10, height=10))
    for p in players[1:]:
        state.entities[p.entity_id] = p
    return state, GameContext(game_state=state), players


def test_regen_heals_every_living_player_not_just_the_first():
    state, ctx, (a, b) = _party()
    a.hp = b.hp = 1
    state.turn_count = 9  # process_turn increments to 10 = regen interval
    TurnProcessor(ctx, hp_regen_interval=10, hp_regen_amount=3, on_run_end=MagicMock()).process_turn()
    assert (a.hp, b.hp) == (4, 4)


def test_game_continues_while_any_player_lives_and_ends_once_when_all_die():
    state, ctx, (a, b) = _party()
    hook = MagicMock()
    tp = TurnProcessor(ctx, on_run_end=hook)

    a.hp, a.is_alive = 0, False
    tp._check_game_over()
    assert not state.game_over
    hook.assert_not_called()

    b.hp, b.is_alive = 0, False
    tp._check_game_over()
    assert state.game_over
    hook.assert_called_once_with(state, False)


def test_victory_calls_the_run_end_hook_with_victory_true(monkeypatch):
    state, ctx, _ = _party()
    hook = MagicMock()
    monkeypatch.setattr("core.floor_manager.get_victory_floor", lambda config: 3)
    assert FloorManager(ctx, MagicMock(), on_run_end=hook)._check_victory(3) is True
    assert state.victory and state.game_over
    hook.assert_called_once_with(state, True)


def test_single_player_death_writes_exactly_one_score_and_one_vault_record(tmp_path, monkeypatch):
    """A/B can't see side-effect order or duplicates, so pin them here."""
    from core import run_end
    calls = []
    hsm = MagicMock()
    hsm.add_score.side_effect = lambda entry: calls.append("score") or 1
    vault = MagicMock()
    vault.add_ores_from_inventory.side_effect = lambda inv, floor: calls.append("ore") or 0
    vault.record_run.side_effect = lambda run_type, victory: calls.append(f"run:{victory}")
    monkeypatch.setattr(run_end.HighScoreManager, "get_instance", staticmethod(lambda: hsm))
    monkeypatch.setattr(run_end, "get_vault", lambda: vault)

    state, ctx, (only,) = _party(1)
    only.hp, only.is_alive = 0, False
    TurnProcessor(ctx)._check_game_over()
    TurnProcessor(ctx)  # constructing again must not record anything

    assert calls == ["score", "ore", "run:False"]
