"""A seed replays the same game (VB-68).

start_new_game(seed) promises reproducible play, and paired bot comparisons
depend on it: the same seed on the same code must give the same game, turn by
turn. Loot rolled on a fresh unseeded GameRNG() broke this from the first kill.
"""
import sys
from pathlib import Path

import pytest

from core.game import Game

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fuzz"))
from mage_bot import MageBot  # noqa: E402


def trace_of(seed, turns):
    """Every player action with the full world state, for one seeded bot game."""
    trace = []
    original = Game.handle_player_action

    def traced(self, action_type, **kwargs):
        world = sorted(
            (str(e.entity_type), e.name, e.x, e.y, e.hp)
            for e in self.state.entities.values() if e.x is not None
        )
        trace.append((self.state.turn_count, action_type, world))
        return original(self, action_type, **kwargs)

    Game.handle_player_action = traced
    try:
        stats = MageBot().play_one_game(max_turns=turns, seed=seed)
    finally:
        Game.handle_player_action = original
    return stats, trace


@pytest.mark.slow
def test_same_seed_replays_the_same_game():
    # Seed 51: a kill with loot on turn 4 and an ongoing spawn on turn 64
    first_stats, first = trace_of(51, 120)
    second_stats, second = trace_of(51, 120)
    assert len(first) > 100
    diverged = next((i for i, (a, b) in enumerate(zip(first, second)) if a != b), None)
    assert diverged is None, f"replay diverged at action {diverged}: {first[diverged]} vs {second[diverged]}"
    assert first_stats == second_stats


def test_kill_loot_rolls_on_the_game_rng(monkeypatch):
    from core.actions import attack_action
    from core.loot import LootGenerator

    seen = []
    original = LootGenerator.generate_loot

    def spy(self, monster_type, floor_number=1, rng=None):
        seen.append(rng)
        return original(self, monster_type, floor_number=floor_number, rng=rng)

    monkeypatch.setattr(LootGenerator, "generate_loot", spy)
    game = Game()
    game.start_new_game(seed=5)
    goblin = game.entity_loader.create_monster("goblin", 1, 1)
    game.context.add_entity(goblin)
    goblin.hp = 0
    action = attack_action.AttackAction(game.state.player.entity_id, goblin.entity_id,
                                        loot_generator=LootGenerator.get_instance())
    action._generate_shared_loot(game.context, goblin, "goblin", attack_action.ActionOutcome.success())
    assert seen and seen[0] is game.context.get_rng()
