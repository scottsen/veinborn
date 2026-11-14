"""VB-92: the multiplayer session runs on the same engine events as single-player."""

import pytest

from core.actions.wait_action import WaitAction
from core.content.events.achievements import AchievementTracker
from core.events import GameEventType
from core.highscore import HighScoreManager
from server.game_session import GameSession


async def _session(names=("Alice", "Bob")):
    game = GameSession("g", "Test", max_players=4)
    seen = []
    for t in (GameEventType.GAME_STARTED, GameEventType.TURN_ENDED,
              GameEventType.PLAYER_DIED, GameEventType.RUN_ENDED):
        game.event_bus.subscribe(t, lambda e, seen=seen: seen.append(e.event_type), subscriber_name="rec")
    for i, name in enumerate(names):
        await game.add_player(f"p{i}", name, "warrior")
    await game.start_game(seed=42)
    return game, seen


async def _wait(game, pid):
    return await game.process_action(pid, WaitAction(actor_id=game.players[pid].entity_id))


@pytest.mark.asyncio
async def test_game_started_is_published_and_content_handlers_are_installed():
    game, seen = await _session()
    assert seen == [GameEventType.GAME_STARTED]
    assert any(isinstance(h, AchievementTracker) for h in game.event_handlers)


@pytest.mark.asyncio
async def test_a_round_publishes_turn_ended_and_content_sees_it():
    game, seen = await _session()
    tracker = next(h for h in game.event_handlers if isinstance(h, AchievementTracker))

    await _wait(game, "p0")
    assert GameEventType.TURN_ENDED not in seen  # Bob still owes his action
    await _wait(game, "p1")

    assert seen.count(GameEventType.TURN_ENDED) == 1
    assert tracker.stats["turns_survived"] == 1


@pytest.mark.asyncio
async def test_each_death_is_announced_once_and_the_wipe_ends_the_run_once():
    game, seen = await _session()
    mp = game.mp_game_state
    for pid in ("p0", "p1"):
        entity = mp.player_slots[pid].player_entity
        entity.take_damage(entity.hp)
        game._finish_action(entity.entity_id, False)
        game._finish_action(entity.entity_id, False)  # nothing repeats

    assert seen.count(GameEventType.PLAYER_DIED) == 2
    assert seen.count(GameEventType.RUN_ENDED) == 1
    assert game.is_finished
    names = [s.player_name for s in HighScoreManager.get_multiplayer_instance().scores]
    assert names.count("Alice") <= 1 and names.count("Bob") <= 1
