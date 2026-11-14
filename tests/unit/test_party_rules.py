"""Party-aware turn rules (MP plan 2a / VB-89): the same code serves one player or many."""

from unittest.mock import MagicMock

from core.events import EventBus, GameEventType

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
    TurnProcessor(ctx, hp_regen_interval=10, hp_regen_amount=3).process_turn()
    assert (a.hp, b.hp) == (4, 4)


def _record(bus, *types):
    seen = []
    for t in types:
        bus.subscribe(t, lambda e, seen=seen: seen.append((e.event_type, e.data)), subscriber_name="rec")
    return seen


def test_game_continues_while_any_player_lives_and_ends_once_when_all_die():
    state, ctx, (a, b) = _party()
    bus = EventBus()
    seen = _record(bus, GameEventType.PLAYER_DIED, GameEventType.RUN_ENDED)
    tp = TurnProcessor(ctx, event_bus=bus)

    a.hp, a.is_alive = 0, False
    tp.announce_deaths()
    tp.check_game_over()
    assert not state.game_over
    assert [t for t, _ in seen] == [GameEventType.PLAYER_DIED]

    b.hp, b.is_alive = 0, False
    tp.check_game_over()
    tp.check_game_over()  # idempotent
    assert state.game_over
    assert [t for t, _ in seen] == [
        GameEventType.PLAYER_DIED, GameEventType.PLAYER_DIED, GameEventType.RUN_ENDED
    ]
    assert seen[-1][1]['victory'] is False


def test_victory_publishes_run_ended_with_victory_true(monkeypatch):
    state, ctx, _ = _party()
    bus = EventBus()
    seen = _record(bus, GameEventType.RUN_ENDED)
    monkeypatch.setattr("core.floor_manager.get_victory_floor", lambda config: 3)
    assert FloorManager(ctx, MagicMock(), event_bus=bus)._check_victory(3) is True
    assert state.victory and state.game_over
    assert [d['victory'] for _, d in seen] == [True]


def test_a_turn_publishes_turn_ended_and_a_death_is_announced_before_the_purge():
    state, ctx, (a, b) = _party()
    bus = EventBus()
    seen = _record(bus, GameEventType.TURN_ENDED, GameEventType.PLAYER_DIED)
    b.hp, b.is_alive = 0, False
    TurnProcessor(ctx, event_bus=bus).process_turn()
    assert [t for t, _ in seen] == [GameEventType.PLAYER_DIED, GameEventType.TURN_ENDED]


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
    from core.run_end import single_player_bus
    TurnProcessor(ctx, event_bus=single_player_bus(state)).check_game_over()

    assert calls == ["score", "ore", "run:False"]
