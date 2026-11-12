"""Actions record the per-player run stats that HighScoreEntry scores.

HighScoreEntry reads monsters_killed / damage_dealt / damage_taken / ore_mined /
ore_surveyed / best_ore_purity / death_cause from player.stats, but nothing wrote
them, so combat and mining never counted toward any score (single- or multiplayer).
"""

import pytest

from core.actions.attack_action import AttackAction
from core.actions.mine_action import MineAction
from core.actions.survey_action import SurveyAction
from core.highscore import HighScoreEntry

# These test stat bookkeeping, not combat dice: every swing hits.
pytestmark = pytest.mark.usefixtures("sure_hit")


def _attack(context, actor, target):
    return AttackAction(actor_id=actor.entity_id, target_id=target.entity_id).execute(context)


def test_player_hit_records_damage_dealt(game_context, weak_goblin):
    game_context.add_entity(weak_goblin)
    player = game_context.get_player()
    weak_goblin.hp = weak_goblin.max_hp = 500  # survive the hit

    hp_before = weak_goblin.hp
    _attack(game_context, player, weak_goblin)

    dealt = hp_before - weak_goblin.hp
    assert dealt > 0
    assert player.get_stat('damage_dealt') == dealt
    assert player.get_stat('monsters_killed') == 0


def test_killing_a_monster_counts_one_kill(game_context, weak_goblin):
    game_context.add_entity(weak_goblin)
    player = game_context.get_player()
    weak_goblin.hp = 1

    _attack(game_context, player, weak_goblin)

    assert not weak_goblin.is_alive
    assert player.get_stat('monsters_killed') == 1
    assert player.get_stat('damage_dealt') == 1  # clamped to the HP that was left


def test_monster_hit_records_damage_taken_not_damage_dealt(game_context, weak_goblin):
    game_context.add_entity(weak_goblin)
    player = game_context.get_player()
    hp_before = player.hp
    player.hp = player.max_hp = 500
    hp_before = player.hp

    _attack(game_context, weak_goblin, player)

    taken = hp_before - player.hp
    assert taken > 0
    assert player.get_stat('damage_taken') == taken
    assert weak_goblin.get_stat('damage_dealt') == 0  # monsters don't accumulate run stats


def test_player_death_records_cause(game_context, weak_goblin):
    game_context.add_entity(weak_goblin)
    player = game_context.get_player()
    player.hp = 1

    _attack(game_context, weak_goblin, player)

    assert not player.is_alive
    assert player.get_stat('death_cause') == f"Killed by {weak_goblin.name}"


def test_completed_mining_counts_ore_and_best_purity(mining_context, copper_ore):
    player = mining_context.get_player()
    copper_ore.x, copper_ore.y = player.x + 1, player.y
    copper_ore.set_stat('mining_turns', 1)
    action = MineAction(actor_id=player.entity_id, ore_vein_id=copper_ore.entity_id,
                        turns_remaining=0)

    while mining_context.get_entity(copper_ore.entity_id) is not None:
        assert action.execute(mining_context).is_success

    assert player.get_stat('ore_mined') == 1
    assert player.get_stat('best_ore_purity') == copper_ore.purity


def test_best_ore_purity_keeps_the_highest(mining_context, copper_ore):
    player = mining_context.get_player()
    player.set_stat('best_ore_purity', 999)
    copper_ore.x, copper_ore.y = player.x + 1, player.y
    copper_ore.set_stat('mining_turns', 1)
    action = MineAction(actor_id=player.entity_id, ore_vein_id=copper_ore.entity_id,
                        turns_remaining=0)

    while mining_context.get_entity(copper_ore.entity_id) is not None:
        action.execute(mining_context)

    assert player.get_stat('best_ore_purity') == 999


def test_survey_counts_ore_surveyed(mining_context, copper_ore):
    player = mining_context.get_player()
    copper_ore.x, copper_ore.y = player.x + 1, player.y

    outcome = SurveyAction(actor_id=player.entity_id,
                           ore_vein_id=copper_ore.entity_id).execute(mining_context)

    assert outcome.is_success
    assert player.get_stat('ore_surveyed') == 1


def test_stats_reach_the_high_score_entry(game_context, weak_goblin):
    game_context.add_entity(weak_goblin)
    player = game_context.get_player()
    weak_goblin.hp = 1
    _attack(game_context, player, weak_goblin)

    entry = HighScoreEntry.from_game_state(game_context.game_state, "Tester")

    assert entry.monsters_killed == 1
    assert entry.damage_dealt == 1
    assert HighScoreEntry.calculate_score(game_context.game_state) >= 10  # 10 per kill
