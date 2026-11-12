"""Abilities for any actor (VB-63, ADR-019): hostility, resolution, the engine ability step."""

import copy

import pytest

from core.actions.ability_action import AbilityAction
from core.base.action import ActionOutcome
from core.base.entity import EntityType
from core.extensions import ability, abilities
from core.systems.ai_system import AISystem, validate_monster_ai
from tests.unit.systems.test_ai_perception import PX, PY, add, ai, arena, tick

pytestmark = pytest.mark.unit


@pytest.fixture
def game():
    return arena()


@pytest.fixture
def give(game):
    """give(monster_id, {ability: config}) patches monsters.yaml abilities for the test."""
    saved = {}

    def _give(monster_id, block):
        saved.setdefault(monster_id, copy.deepcopy(game.entity_loader.monsters[monster_id]))
        game.entity_loader.monsters[monster_id]['abilities'] = block

    yield _give
    for monster_id, definition in saved.items():
        game.entity_loader.monsters[monster_id] = definition


# --- hostility ------------------------------------------------------------------

def test_players_and_monsters_are_hostile_to_each_other_only(game):
    p = game.state.player
    a, b = add(game, 3), add(game, -3)
    ctx = game.context
    assert ctx.is_hostile(p, a) and ctx.is_hostile(a, p)
    assert not ctx.is_hostile(a, b)
    assert not ctx.is_hostile(p, p)
    assert {e.entity_id for e in ctx.hostiles_of(p)} == {a.entity_id, b.entity_id}
    assert [e.entity_id for e in ctx.hostiles_of(a)] == [p.entity_id]


def test_ore_veins_and_forges_are_never_hostile(game):
    vein = game.entity_loader.create_ore_vein("copper", PX + 2, PY)
    game.context.add_entity(vein)
    assert not game.context.is_hostile(game.state.player, vein)


# --- resolution -----------------------------------------------------------------

def test_no_shipped_monster_has_an_ability_yet(game):
    """VB-63 changes no gameplay: every monster ability in monsters.yaml is still disabled."""
    system = ai(game)
    for monster_id in game.entity_loader.monsters:
        mon = game.entity_loader.create_monster(monster_id, 1, 1)
        assert system.abilities_for(mon) == {}, monster_id


def test_a_behaviour_brings_its_abilities(game):
    mon = add(game, 5, ai_type='sniper')
    usable = ai(game).abilities_for(mon)
    assert set(usable) == {'ranged_attack'}
    assert usable['ranged_attack']['range'] == 6


def test_monster_yaml_enables_an_ability_over_shared_tuning(game, give):
    give('goblin', {'force_bolt': {'enabled': True, 'damage_max': 9, 'description': 'x'}})
    usable = ai(game).abilities_for(add(game, 5))
    assert set(usable) == {'force_bolt'}
    cfg = usable['force_bolt']
    assert cfg['damage_max'] == 9                              # monster override
    assert cfg['range'] == game.config.formulas['abilities']['force_bolt']['range']  # shared tuning
    assert 'enabled' not in cfg and 'description' not in cfg


def test_monster_yaml_can_disable_what_its_behaviour_brings(game, give):
    give('goblin', {'ranged_attack': {'enabled': False}})
    assert ai(game).abilities_for(add(game, 5, ai_type='sniper')) == {}


def test_disabled_and_undeclared_abilities_are_absent(game, give):
    give('goblin', {'force_bolt': {'enabled': False}})
    assert ai(game).abilities_for(add(game, 5)) == {}


# --- the engine ability step ------------------------------------------------------

def test_a_monster_with_force_bolt_casts_it_at_a_perceived_player(game, give):
    give('goblin', {'force_bolt': {'enabled': True, 'cooldown': 3}})
    p = game.state.player
    mon = add(game, 4)
    tick(game)
    assert p.hp < p.max_hp
    assert any("force bolt hits" in m for m in game.state.messages)
    assert mon.get_stat('cooldowns')['force_bolt'] > game.state.turn_count


def test_cooldown_makes_it_fall_back_to_its_behaviour(game, give):
    give('goblin', {'force_bolt': {'enabled': True, 'cooldown': 5}})
    p = game.state.player
    mon = add(game, 4)
    tick(game)            # bolt
    start = ai(game).distance(mon, p)
    tick(game)            # on cooldown: aggressive tactics close in
    assert ai(game).distance(mon, p) < start


def test_no_perceived_target_means_no_ability(game, give):
    give('goblin', {'force_bolt': {'enabled': True}})
    mon = add(game, 4, aggro_range=2)
    tick(game)
    assert not mon.get_stat('cooldowns')


def test_an_ability_without_should_use_is_never_used_by_monsters(game, give):
    used = []

    @ability("_test_player_only", replace=True)
    def player_only(context, actor, config, target=None):
        used.append(actor.entity_id)
        return ActionOutcome.success(took_turn=True)

    try:
        give('goblin', {'_test_player_only': {'enabled': True}})
        game.context.register_system('ai', AISystem(game.context, game.entity_loader, game.event_bus))
        add(game, 3)
        tick(game, 3)
        assert used == []
    finally:
        abilities.unregister("_test_player_only")


def test_monster_ability_events_reach_the_bus_and_count_as_damage_taken(game, give):
    give('goblin', {'force_bolt': {'enabled': True}})
    add(game, 4)
    tick(game)
    assert game.stats_tracker.attacks_received == 1
    assert game.stats_tracker.total_damage_taken == game.state.player.max_hp - game.state.player.hp


def test_summoner_summons_through_the_ability(game):
    mon = add(game, 6, ai_type='summoner')
    tick(game)
    assert len(mon.get_stat('minion_ids')) == 1
    assert 'summon' in mon.get_stat('cooldowns')


def test_sniper_shoots_through_the_ability_and_holds_position(game):
    p = game.state.player
    mon = add(game, 5, ai_type='sniper')
    pos = (mon.x, mon.y)
    for _ in range(40):
        tick(game)
        if p.hp < p.max_hp:
            break
    assert p.hp < p.max_hp
    assert (mon.x, mon.y) == pos


# --- player side unchanged ---------------------------------------------------------

def test_player_force_bolt_still_aims_at_monsters_only():
    from core.character_class import CharacterClass
    game = arena(CharacterClass.MAGE)
    mon = add(game, 3)
    assert game.handle_player_action('ability', ability='force_bolt')
    assert mon.hp < mon.max_hp


def test_ability_action_target_survives_the_wire():
    action = AbilityAction("a", "force_bolt", target_id="b", config={'range': 6})
    back = AbilityAction.from_dict(action.to_dict())
    assert back.target_id == "b" and back.config is None


# --- validation ---------------------------------------------------------------------

def test_a_behaviour_bringing_an_unknown_ability_is_reported():
    problems = validate_monster_ai(
        {}, {'sniper': {'abilities': {'laser': {}}}}, ['sniper'], ['ranged_attack'], {}
    )
    assert len(problems) == 1 and "laser" in problems[0]


def test_abilities_is_not_an_ai_block_key():
    problems = validate_monster_ai(
        {'gob': {'ai': {'type': 'sniper', 'abilities': {}}}},
        {'sniper': {'abilities': {}}}, ['sniper'], [], {},
    )
    assert len(problems) == 1 and "ai.abilities" in problems[0]


def test_co_op_players_do_not_bump_attack_each_other(game):
    from core.actions.move_action import MoveAction
    from core.entities import Player
    p = game.state.player
    ally = Player(name="Ally", x=PX + 1, y=PY, hp=20, max_hp=20, attack=3, defense=1)
    game.context.add_entity(ally)
    outcome = MoveAction(p.entity_id, 1, 0).execute(game.context)
    assert not outcome.is_success
    assert ally.hp == ally.max_hp
