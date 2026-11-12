"""Achievements, quests and kill streaks, driven by real game events."""

import pytest

from core.base.entity import EntityType
from core.character_class import CharacterClass
from core.content.events.achievements import AchievementTracker
from core.content.events.kill_streaks import KillStreaks
from core.content.events.quests import QuestTracker, QUESTS
from core.events import GameEvent, GameEventType
from core.game import Game

pytestmark = pytest.mark.unit


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=7, character_class=CharacterClass.WARRIOR)
    for e in list(g.state.entities.values()):
        if e.entity_type == EntityType.MONSTER:
            g.context.remove_entity(e.entity_id)
    g.state.messages.clear()
    return g


def handler(game, cls):
    return next(h for h in game.event_handlers if isinstance(h, cls))


def death(game, victim, killer=None):
    killer = killer or game.state.player
    game.event_bus.publish(GameEvent(
        GameEventType.ENTITY_DIED,
        {'entity_id': victim.entity_id, 'entity_name': victim.name, 'killer_id': killer.entity_id},
        turn=game.state.turn_count,
    ))


def victim(game, monster_id="goblin"):
    mon = game.entity_loader.create_monster(monster_id, 1, 1)
    game.context.add_entity(mon)
    return mon


# --- wiring: the events the handlers need are really published -------------------

def test_handlers_are_installed_per_game(game):
    names = {type(h).__name__ for h in game.event_handlers}
    assert {"AchievementTracker", "QuestTracker", "KillStreaks"} <= names
    other = Game()
    other.start_new_game(seed=7)
    assert handler(game, AchievementTracker) is not handler(other, AchievementTracker)


def test_game_start_announces_the_first_quest():
    g = Game()
    g.start_new_game(seed=7)
    assert any("New Quest: Goblin Slayer" in m for m in g.state.messages)


def test_turns_are_published_so_survival_is_tracked(game):
    before = handler(game, AchievementTracker).stats["turns_survived"]
    game.handle_player_action('wait')
    assert handler(game, AchievementTracker).stats["turns_survived"] == before + 1 == game.state.turn_count
    assert game.stats_tracker.turns_played >= 1


def test_descending_publishes_floor_changed(game):
    seen = []
    game.event_bus.subscribe(GameEventType.FLOOR_CHANGED, seen.append)
    game.descend_floor()
    assert [(e.data['from_floor'], e.data['to_floor']) for e in seen] == [(1, 2)]
    assert handler(game, AchievementTracker).stats["deepest_floor"] == 2
    assert game.stats_tracker.floors_descended == 1


def test_a_real_kill_through_the_game_loop_reaches_the_handlers(game, sure_hit):
    p = game.state.player
    mon = game.entity_loader.create_monster("goblin", p.x + 1, p.y)
    if not game.state.dungeon_map.is_walkable(mon.x, mon.y):
        pytest.skip("no open tile next to the player for this seed")
    mon.hp = 1
    game.context.add_entity(mon)
    game.handle_player_action('attack', target_id=mon.entity_id)
    assert not mon.is_alive
    assert handler(game, AchievementTracker).stats["kills"] == 1
    assert handler(game, QuestTracker).progress["goblin_slayer"] == 1
    assert any("Quest: Goblin Slayer [1/5]" in m for m in game.state.messages)


# --- achievements ----------------------------------------------------------------

def test_kill_milestones_unlock_and_announce_once(game):
    ach = handler(game, AchievementTracker)
    ach.stats["kills"] = 99
    death(game, victim(game))
    assert "centurion" in ach.unlocked
    assert sum("Achievement Unlocked: Centurion" in m for m in game.state.messages) == 1
    death(game, victim(game))
    assert sum("Achievement Unlocked: Centurion" in m for m in game.state.messages) == 1


def test_a_monster_killing_something_is_not_a_player_kill(game):
    ach = handler(game, AchievementTracker)
    killer = victim(game, "orc")
    death(game, victim(game), killer=killer)
    assert ach.stats["kills"] == 0


def test_crafting_counts_equipment_crafted_events(game):
    ach = handler(game, AchievementTracker)
    game.event_bus.publish(GameEvent(GameEventType.EQUIPMENT_CRAFTED, {}))
    assert ach.stats["items_crafted"] == 1


# --- quests ------------------------------------------------------------------------

def test_only_matching_monsters_advance_a_quest(game):
    quests = handler(game, QuestTracker)
    death(game, victim(game, "orc"))
    assert quests.progress["goblin_slayer"] == 0
    death(game, victim(game, "goblin"))
    assert quests.progress["goblin_slayer"] == 1


def test_completing_a_quest_pays_xp_and_unlocks_the_next(game):
    quests = handler(game, QuestTracker)
    goblin_quest = QUESTS[0]
    xp_before = game.state.player.get_stat('xp', 0)
    for _ in range(goblin_quest.target):
        death(game, victim(game, "goblin"))
    assert "goblin_slayer" in quests.completed and "goblin_slayer" not in quests.active
    assert game.state.player.get_stat('xp') == xp_before + goblin_quest.reward_xp
    assert "bat_hunter" in quests.active
    assert any("New Quest: Bat Hunter" in m for m in game.state.messages)


def test_a_locked_quest_does_not_advance(game):
    quests = handler(game, QuestTracker)
    death(game, victim(game, "bat"))
    assert quests.progress["bat_hunter"] == 0


# --- kill streaks --------------------------------------------------------------------

def test_quick_kills_build_and_slow_ones_reset_a_streak(game):
    streaks = handler(game, KillStreaks)
    for turn in (1, 2, 3):
        game.state.turn_count = turn
        death(game, victim(game))
    assert streaks.streak == 3
    assert any("Kill Streak x3!" in m for m in game.state.messages)
    game.state.turn_count = 3 + 4  # past the timeout
    death(game, victim(game))
    assert streaks.streak == 1


def test_a_streak_ends_with_a_message_when_time_runs_out(game):
    streaks = handler(game, KillStreaks)
    for turn in (1, 2, 3):
        game.state.turn_count = turn
        death(game, victim(game))
    game.event_bus.publish(GameEvent(GameEventType.TURN_ENDED, {}, turn=20))
    assert streaks.streak == 0 and any("Kill streak ended." in m for m in game.state.messages)


# --- load_game does not double-subscribe -------------------------------------------------

def test_reinitialising_does_not_double_deliver(game):
    game._initialize_subsystems()
    game._initialize_subsystems()
    ach = handler(game, AchievementTracker)
    game.event_bus.publish(GameEvent(GameEventType.EQUIPMENT_CRAFTED, {}))
    assert ach.stats["items_crafted"] == 1
    assert len([h for h in game.event_handlers if isinstance(h, AchievementTracker)]) == 1
