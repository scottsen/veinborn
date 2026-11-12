"""Class abilities: mage force bolt, healer heal, rogue backstab (VB-51)."""

import pytest

from core.actions.ability_action import AbilityAction
from core.actions.attack_action import AttackAction
from core.base.entity import EntityType
from core.character_class import CharacterClass
from core.game import Game
from core.geometry import has_line_of_sight

pytestmark = pytest.mark.unit


def make_game(cls):
    game = Game()
    game.start_new_game(seed=7, character_class=cls)
    state = game.state
    for e in list(state.entities.values()):  # a clean floor: only the player
        if e.entity_type == EntityType.MONSTER:
            game.context.remove_entity(e.entity_id)
    return game


def place_monster(game, monster_id="goblin", min_dist=2, max_dist=3):
    """Put a monster in line of sight of the player, min..max tiles away."""
    p, m = game.state.player, game.state.dungeon_map
    for dist in range(min_dist, max_dist + 1):
        for dx, dy in [(dist, 0), (-dist, 0), (0, dist), (0, -dist), (dist, dist), (-dist, -dist)]:
            x, y = p.x + dx, p.y + dy
            if m.is_walkable(x, y) and has_line_of_sight(p.x, p.y, x, y, m.is_transparent):
                monster = game.entity_loader.create_monster(monster_id, x, y)
                game.context.add_entity(monster)
                return monster
    pytest.skip("no open tile near the player for this seed")


# --- force bolt -----------------------------------------------------------

def test_force_bolt_hits_for_rolled_damage_and_ignores_defense():
    game = make_game(CharacterClass.MAGE)
    troll = place_monster(game, "troll")  # defense 4+ would zero a melee swing
    hp = troll.hp
    outcome = AbilityAction(game.state.player.entity_id, "force_bolt").execute(game.context)
    assert outcome.is_success and outcome.took_turn
    assert 2 <= hp - troll.hp <= 6
    assert "force bolt" in outcome.messages[0]


def test_force_bolt_damage_grows_with_level():
    game = make_game(CharacterClass.MAGE)
    game.state.player.set_stat('level', 9)  # +4 at 0.5/level
    troll = place_monster(game, "troll")
    hp = troll.hp
    AbilityAction(game.state.player.entity_id, "force_bolt").execute(game.context)
    assert 6 <= hp - troll.hp <= 10


def test_force_bolt_picks_nearest_monster():
    game = make_game(CharacterClass.MAGE)
    near = place_monster(game, "orc", 2, 2)
    far = place_monster(game, "orc", 3, 3)
    AbilityAction(game.state.player.entity_id, "force_bolt").execute(game.context)
    assert near.hp < near.max_hp and far.hp == far.max_hp


def test_force_bolt_with_no_target_fails_without_spending_a_turn():
    game = make_game(CharacterClass.MAGE)
    outcome = AbilityAction(game.state.player.entity_id, "force_bolt").execute(game.context)
    assert not outcome.is_success and not outcome.took_turn
    assert "No target" in outcome.messages[0]
    assert game.state.player.get_stat('cooldowns', {}) == {}


def test_force_bolt_out_of_range_has_no_target():
    game = make_game(CharacterClass.MAGE)
    monster = place_monster(game, "goblin", 2, 3)
    monster.x += 20  # far outside the 6-tile range, wherever it lands
    outcome = AbilityAction(game.state.player.entity_id, "force_bolt").execute(game.context)
    assert not outcome.is_success


def test_force_bolt_kill_awards_xp_like_melee():
    game = make_game(CharacterClass.MAGE)
    bat = place_monster(game, "bat")
    bat.hp = 1
    xp_before = game.state.player.get_stat('xp', 0)
    outcome = AbilityAction(game.state.player.entity_id, "force_bolt").execute(game.context)
    assert not bat.is_alive
    assert game.state.player.get_stat('xp', 0) > xp_before
    assert any("died" in m for m in outcome.messages)


def test_force_bolt_cooldown_blocks_then_expires():
    game = make_game(CharacterClass.MAGE)
    place_monster(game, "ogre")
    pid = game.state.player.entity_id
    assert AbilityAction(pid, "force_bolt").execute(game.context).is_success
    again = AbilityAction(pid, "force_bolt").execute(game.context)
    assert not again.is_success and "isn't ready" in again.messages[0]
    game.state.turn_count += 4  # cooldown 3 (+1 for the casting turn)
    assert AbilityAction(pid, "force_bolt").execute(game.context).is_success


def test_wall_blocks_force_bolt():
    game = make_game(CharacterClass.MAGE)
    monster = place_monster(game, "goblin", 3, 3)
    p, m = game.state.player, game.state.dungeon_map
    # wall off the tile between caster and target
    from core.geometry import bresenham_line
    mid = [pt for pt in bresenham_line(p.x, p.y, monster.x, monster.y)][1]
    from core.world import Tile, TileType
    m.tiles[mid[0]][mid[1]] = Tile(TileType.WALL)
    assert not AbilityAction(p.entity_id, "force_bolt").execute(game.context).is_success


# --- heal ------------------------------------------------------------------

def test_heal_restores_hp_and_starts_cooldown():
    game = make_game(CharacterClass.HEALER)
    player = game.state.player
    player.hp = 10
    outcome = AbilityAction(player.entity_id, "heal").execute(game.context)
    assert outcome.is_success and outcome.took_turn
    assert player.hp == 16
    assert not AbilityAction(player.entity_id, "heal").execute(game.context).is_success


def test_heal_never_overheals():
    game = make_game(CharacterClass.HEALER)
    player = game.state.player
    player.hp = player.max_hp - 2
    AbilityAction(player.entity_id, "heal").execute(game.context)
    assert player.hp == player.max_hp


def test_heal_at_full_health_fails_without_a_turn():
    game = make_game(CharacterClass.HEALER)
    outcome = AbilityAction(game.state.player.entity_id, "heal").execute(game.context)
    assert not outcome.is_success and not outcome.took_turn


# --- who can use what --------------------------------------------------------

def test_class_cannot_use_another_classes_ability():
    game = make_game(CharacterClass.WARRIOR)
    outcome = AbilityAction(game.state.player.entity_id, "heal").execute(game.context)
    assert not outcome.is_success and "doesn't know" in outcome.messages[0]


def test_factory_defaults_to_the_class_ability():
    game = make_game(CharacterClass.MAGE)
    assert game.action_factory.create('ability').ability == "force_bolt"
    healer = make_game(CharacterClass.HEALER)
    assert healer.action_factory.create('ability').ability == "heal"


def test_factory_reports_a_class_with_no_ability():
    game = make_game(CharacterClass.WARRIOR)
    assert game.action_factory.create('ability') is None
    assert "no ability" in game.state.messages[-1]


def test_ability_through_the_game_loop_takes_a_turn():
    game = make_game(CharacterClass.MAGE)
    place_monster(game, "ogre")
    turn = game.state.turn_count
    assert game.handle_player_action('ability') is True
    assert game.state.turn_count == turn + 1


def test_ability_action_round_trips_over_the_wire():
    action = AbilityAction("p1", "heal")
    assert AbilityAction.from_dict(action.to_dict()) == action


# --- rogue backstab ---------------------------------------------------------

def test_backstab_doubles_the_first_hit_only(sure_hit):
    game = make_game(CharacterClass.ROGUE)
    goblin = game.entity_loader.create_monster("ogre", 0, 0)  # lots of HP
    rogue = game.state.player
    base = rogue.get_total_attack() - goblin.defense
    first = AttackAction(rogue.entity_id, goblin.entity_id)
    dealt1 = first._calculate_and_apply_damage(rogue, goblin)
    assert first.backstabbed and dealt1 == max(1, base) * 2
    second = AttackAction(rogue.entity_id, goblin.entity_id)
    dealt2 = second._calculate_and_apply_damage(rogue, goblin)
    assert not second.backstabbed and dealt2 == max(1, base)


def test_backstab_message_names_it(sure_hit):
    game = make_game(CharacterClass.ROGUE)
    monster = place_monster(game, "ogre", 1, 1)
    outcome = AttackAction(game.state.player.entity_id, monster.entity_id).execute(game.context)
    assert "backstabs" in outcome.messages[0]


def test_warrior_does_not_backstab(sure_hit):
    game = make_game(CharacterClass.WARRIOR)
    ogre = game.entity_loader.create_monster("ogre", 0, 0)
    attack = AttackAction(game.state.player.entity_id, ogre.entity_id)
    attack._calculate_and_apply_damage(game.state.player, ogre)
    assert not attack.backstabbed
