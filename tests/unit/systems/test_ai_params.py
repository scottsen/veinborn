"""Per-monster AI parameters and monster AI data validation (VB-59, ADR-019)."""

import copy

import pytest

from core.base.entity import EntityType
from core.exceptions import ContentValidationError
from core.extensions import abilities, ai_behavior, ai_behaviors
from core.game import Game
from core.systems.ai_system import AISystem, validate_monster_ai

pytestmark = pytest.mark.unit


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=42)
    for e in list(g.state.entities.values()):
        if e.entity_type == EntityType.MONSTER:
            g.context.remove_entity(e.entity_id)
    return g


@pytest.fixture
def ai(game):
    return game.context.get_system('ai')


def make(game, monster_id="goblin"):
    mon = game.entity_loader.create_monster(monster_id, 1, 1)
    game.context.add_entity(mon)
    return mon


# --- params_for ---------------------------------------------------------------

def test_params_start_from_universal_then_behaviour_defaults(game, ai):
    mon = make(game, "goblin")
    mon.content_id = None  # no monsters.yaml layer
    mon.set_stat('ai_type', 'defensive')
    params = ai.params_for(mon)
    assert params['memory_turns'] == game.config.ai_behaviors['defaults']['memory_turns']
    assert params['chase_range'] == game.config.get_ai_behavior_config('defensive')['chase_range']
    # the behaviour's section beats the universal defaults
    assert params['flee_threshold'] == game.config.get_ai_behavior_config('defensive')['flee_threshold']


def test_monster_ai_block_overrides_and_extends_defaults(game, ai):
    troll = make(game, "troll")
    params = ai.params_for(troll)
    assert params['aggro_range'] == 6       # from monsters.yaml troll ai:
    assert params['move_speed'] == 0.8


def test_type_and_description_are_not_params(game, ai):
    params = ai.params_for(make(game, "troll"))
    assert 'type' not in params and 'description' not in params


def test_instance_override_wins(game, ai):
    mon = make(game, "troll")
    mon.set_stat('ai_params', {'aggro_range': 2})
    assert ai.params_for(mon)['aggro_range'] == 2


def test_params_are_looked_up_live_so_yaml_tuning_reaches_existing_monsters(game, ai):
    mon = make(game, "goblin")
    saved = copy.deepcopy(game.entity_loader.monsters['goblin'])
    try:
        game.entity_loader.monsters['goblin']['ai']['aggro_range'] = 3
        assert ai.params_for(mon)['aggro_range'] == 3
        assert 'aggro_range' not in mon.stats  # nothing was copied into the save
    finally:
        game.entity_loader.monsters['goblin'] = saved


def test_monster_without_content_id_gets_the_defaults(game, ai):
    mon = make(game, "troll")  # troll's own aggro_range is 6
    mon.content_id = None
    assert ai.params_for(mon)['aggro_range'] == game.config.ai_behaviors['defaults']['aggro_range']


def test_update_hands_behaviours_the_resolved_params(game):
    seen = []

    @ai_behavior("_test_params", replace=True)
    def capture(ai, monster, config):
        seen.append(dict(config))

    try:
        mon = make(game, "troll")
        mon.set_stat('ai_type', '_test_params')
        mon.set_stat('ai_params', {'chase_range': 99, 'move_speed': 1.0})  # troll is 0.8: act on round 1
        game.context.register_system('ai', AISystem(game.context, game.entity_loader))
        game.context.get_system('ai').update()
        assert seen and seen[0]['aggro_range'] == 6 and seen[0]['chase_range'] == 99
    finally:
        ai_behaviors.unregister("_test_params")


# --- validation ---------------------------------------------------------------

BEHAVIORS = {'aggressive': {'chase_range': 10, 'description': 'x'}, 'guard': {'guard_radius': 4}}


UNIVERSAL = {'aggro_range': 8, 'memory_turns': 10, 'move_speed': 1.0, 'flee_threshold': 0.0}


def check(monsters, abilities_known=()):
    return validate_monster_ai(monsters, BEHAVIORS, BEHAVIORS.keys(), abilities_known, UNIVERSAL)


def test_shipped_monster_data_is_valid(game):
    assert validate_monster_ai(
        game.entity_loader.monsters,
        game.config.ai_behaviors['behaviors'],
        ai_behaviors.names(),
        abilities.names(),
        game.config.ai_behaviors['defaults'],
    ) == []


def test_unknown_ai_type_is_reported():
    problems = check({'gob': {'ai': {'type': 'agressive'}}})
    assert len(problems) == 1 and "agressive" in problems[0]


def test_unknown_ai_key_is_reported():
    problems = check({'gob': {'ai': {'type': 'aggressive', 'agro_range': 5}}})
    assert len(problems) == 1 and "agro_range" in problems[0]


def test_universal_and_behaviour_keys_are_allowed():
    assert check({
        'gob': {'ai': {'type': 'aggressive', 'aggro_range': 5, 'move_speed': 1.2,
                       'flee_threshold': 0.1, 'chase_range': 4, 'description': 'd'}},
        'spi': {'ai': {'type': 'guard', 'guard_radius': 2}},
    }) == []


def test_a_key_of_another_behaviour_is_reported():
    problems = check({'gob': {'ai': {'type': 'aggressive', 'guard_radius': 2}}})
    assert len(problems) == 1 and "guard_radius" in problems[0]


def test_enabled_ability_without_implementation_is_reported():
    monsters = {'lich': {'ai': {'type': 'aggressive'},
                         'abilities': {'death_bolt': {'enabled': True}, 'phylactery': {'enabled': False}}}}
    problems = check(monsters)
    assert len(problems) == 1 and "death_bolt" in problems[0]
    assert check(monsters, abilities_known={'death_bolt'}) == []


def test_ai_system_refuses_invalid_monster_data(game):
    saved = copy.deepcopy(game.entity_loader.monsters['goblin'])
    try:
        game.entity_loader.monsters['goblin']['ai']['type'] = 'no_such_behaviour'
        with pytest.raises(ContentValidationError, match="no_such_behaviour"):
            AISystem(game.context, game.entity_loader)
    finally:
        game.entity_loader.monsters['goblin'] = saved
