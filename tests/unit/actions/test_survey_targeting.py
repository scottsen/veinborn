"""Survey/mine with several adjacent ore veins: the survey must reach all of them."""

import pytest

from core.base.entity import EntityType
from core.game import Game

pytestmark = pytest.mark.unit


@pytest.fixture
def game_with_three_veins():
    g = Game()
    g.start_new_game(seed=1)
    for e in list(g.state.entities.values()):
        if e.entity_type in (EntityType.MONSTER, EntityType.ORE_VEIN):
            g.context.remove_entity(e.entity_id)
    p = g.state.player
    veins = []
    for dx in (-1, 0, 1):
        vein = g.entity_loader.create_ore_vein("copper", p.x + dx, p.y + 1) \
            if hasattr(g.entity_loader, "create_ore_vein") else None
        if vein is None:
            from core.entities import OreVein
            vein = OreVein.generate_random("copper", p.x + dx, p.y + 1)
        g.context.add_entity(vein)
        veins.append(vein)
    return g, veins


def test_survey_goes_to_an_unsurveyed_vein_when_the_first_is_done(game_with_three_veins):
    g, veins = game_with_three_veins
    veins[0].set_stat('surveyed', True)
    action = g.action_factory.create('survey')
    assert action.ore_vein_id in {veins[1].entity_id, veins[2].entity_id}


def test_repeated_survey_eventually_covers_every_adjacent_vein(game_with_three_veins):
    g, veins = game_with_three_veins
    for _ in range(3):
        assert g.handle_player_action('survey')
    assert all(v.get_stat('surveyed') for v in veins)


def test_survey_can_target_a_specific_adjacent_vein(game_with_three_veins):
    g, veins = game_with_three_veins
    action = g.action_factory.create('survey', ore_vein_id=veins[2].entity_id)
    assert action.ore_vein_id == veins[2].entity_id


def test_a_non_adjacent_target_falls_back_to_an_adjacent_vein(game_with_three_veins):
    g, veins = game_with_three_veins
    from core.entities import OreVein
    far = OreVein.generate_random("copper", g.state.player.x + 20, g.state.player.y + 20)
    g.context.add_entity(far)
    action = g.action_factory.create('survey', ore_vein_id=far.entity_id)
    assert action.ore_vein_id in {v.entity_id for v in veins}


def test_mine_can_target_a_specific_adjacent_vein(game_with_three_veins):
    g, veins = game_with_three_veins
    action = g.action_factory.create('mine', ore_vein_id=veins[2].entity_id)
    assert action.ore_vein_id == veins[2].entity_id
