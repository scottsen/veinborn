"""Co-op rules: the party plays on while anyone lives, regen heals everyone, scores are per player."""

import pytest

from core.actions.wait_action import WaitAction
from core.highscore import HighScoreManager
from server.game_session import GameSession


async def _started_session(names=("Alice", "Bob")):
    game = GameSession("game1", "Test Game", max_players=4, actions_per_round=4)
    for i, name in enumerate(names):
        await game.add_player(f"player{i}", name, "warrior")
    await game.start_game(seed=42)
    return game


def _kill(game, player_id):
    entity = game.mp_game_state.player_slots[player_id].player_entity
    entity.take_damage(entity.hp)


async def _wait(game, player_id):
    entity_id = game.players[player_id].entity_id
    return await game.process_action(player_id, WaitAction(actor_id=entity_id))


def _scores(names_only=True):
    scores = HighScoreManager.get_multiplayer_instance().scores
    return [s.player_name for s in scores] if names_only else scores


@pytest.mark.asyncio
async def test_game_continues_while_any_player_is_alive():
    game = await _started_session()
    _kill(game, "player0")

    success, error = await _wait(game, "player1")

    assert success, error
    assert not game.mp_game_state.game_state.game_over
    assert not game.is_finished


@pytest.mark.asyncio
async def test_game_ends_when_every_player_is_dead():
    game = await _started_session()
    _kill(game, "player0")
    await _wait(game, "player1")
    _kill(game, "player1")

    await game._advance_round_if_complete()

    assert game.mp_game_state.game_state.game_over
    assert game.is_finished


@pytest.mark.asyncio
async def test_death_scores_that_player_only_once_at_death():
    game = await _started_session()
    _kill(game, "player0")

    await _wait(game, "player1")
    await _wait(game, "player1")

    assert _scores() == ["Alice"]


@pytest.mark.asyncio
async def test_survivors_are_scored_when_the_game_ends():
    game = await _started_session()
    _kill(game, "player0")
    await _wait(game, "player1")
    _kill(game, "player1")

    await game._advance_round_if_complete()
    await game._advance_round_if_complete()

    assert sorted(_scores()) == ["Alice", "Bob"]


@pytest.mark.asyncio
async def test_victory_scores_survivors_with_victory_bonus():
    game = await _started_session()
    _kill(game, "player0")
    await _wait(game, "player1")
    state = game.mp_game_state.game_state
    state.victory = True
    state.game_over = True

    await game._advance_round_if_complete()

    by_name = {s.player_name: s for s in _scores(names_only=False)}
    assert by_name["Bob"].victory and not by_name["Alice"].victory
    assert by_name["Bob"].score >= 50000


@pytest.mark.asyncio
async def test_coop_scores_stay_off_the_single_player_leaderboard(tmp_path):
    single_player = HighScoreManager(tmp_path / "highscores.json")
    HighScoreManager._instance = single_player
    try:
        game = await _started_session()
        _kill(game, "player0")
        await _wait(game, "player1")
    finally:
        HighScoreManager._instance = None

    assert single_player.scores == []
    assert _scores() == ["Alice"]


@pytest.mark.asyncio
async def test_leaderboard_failure_does_not_break_the_game():
    class Broken:
        def add_score(self, entry):
            raise IOError("disk full")

    game = GameSession("game1", "Test Game", high_scores=Broken())
    await game.add_player("player0", "Alice", "warrior")
    await game.add_player("player1", "Bob", "warrior")
    await game.start_game(seed=42)
    _kill(game, "player0")

    success, error = await _wait(game, "player1")

    assert success, error


@pytest.mark.asyncio
async def test_regen_heals_every_living_player_not_the_dead():
    game = await _started_session()
    mp = game.mp_game_state
    alice = mp.player_slots["player0"].player_entity
    bob = mp.player_slots["player1"].player_entity
    alice.hp = alice.max_hp - 5
    bob.hp = bob.max_hp - 5
    _kill(game, "player1")
    mp.update_player_alive_status()
    game.ai_system = None  # keep monsters from hitting anyone mid-test
    mp.game_state.turn_count = 9  # next monster turn lands on the regen interval (10)

    await game._process_monster_turn()

    assert alice.hp == alice.max_hp - 5 + 1
    assert bob.hp == 0 and not bob.is_alive


@pytest.mark.asyncio
async def test_regen_only_on_the_configured_interval():
    game = await _started_session()
    alice = game.mp_game_state.player_slots["player0"].player_entity
    alice.hp = alice.max_hp - 5
    game.ai_system = None
    game.mp_game_state.game_state.turn_count = 0  # -> 1, not a multiple of 10

    await game._process_monster_turn()

    assert alice.hp == alice.max_hp - 5


@pytest.mark.asyncio
async def test_each_player_is_scored_on_their_own_run_stats():
    game = await _started_session()
    alice = game.mp_game_state.player_slots["player0"].player_entity
    bob = game.mp_game_state.player_slots["player1"].player_entity
    alice.set_stat('monsters_killed', 3)
    bob.set_stat('monsters_killed', 7)
    _kill(game, "player0")
    await _wait(game, "player1")
    _kill(game, "player1")
    await game._advance_round_if_complete()

    by_name = {s.player_name: s for s in _scores(names_only=False)}
    assert by_name["Alice"].monsters_killed == 3
    assert by_name["Bob"].monsters_killed == 7
    assert by_name["Bob"].score - by_name["Alice"].score >= 40  # 4 more kills at 10 points
