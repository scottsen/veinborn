"""Bot routing (VB-123): paths go around ore veins and forges, the random fallback does not
bump them, and it does not mine with a full pack (the ore would fall on the floor)."""
import pytest

from core.base.entity import EntityType
from core.loot import LootGenerator
from core.world import Tile, TileType
from tests.fuzz.services import action_planner as planner_module
from tests.unit.test_planner_abilities import make

pytestmark = pytest.mark.unit


def open_room(game, cx, cy, r=3):
    m = game.state.dungeon_map
    for x in range(cx - r, cx + r + 1):
        for y in range(cy - r, cy + r + 1):
            m.tiles[x][y] = Tile(TileType.FLOOR)


def clear_blockers(game):
    for e in list(game.state.entities.values()):
        if e.entity_type in (EntityType.ORE_VEIN, EntityType.FORGE):
            game.context.remove_entity(e.entity_id)


def setup_line(game):
    """Player, forge right of it, goal right of the forge, in an open room."""
    p = game.state.player
    open_room(game, p.x, p.y)
    clear_blockers(game)
    from core.entities import Forge
    forge = Forge(name="Forge", content_id="forge", x=p.x + 1, y=p.y)
    game.context.add_entity(forge)
    return p, forge


def test_static_blockers_are_veins_and_forges():
    game, planner = make("warrior")
    _, forge = setup_line(game)
    assert (forge.x, forge.y) in planner.static_blockers(game)


def test_a_path_goes_around_a_forge_not_into_it():
    game, planner = make("warrior")
    p, forge = setup_line(game)
    from core.base.entity import Entity
    goal = Entity(entity_type=EntityType.PLAYER, name="goal", x=p.x + 2, y=p.y)
    action, args = planner.move_towards(game, goal)
    assert action == 'move' and (p.x + args['dx'], p.y + args['dy']) != (forge.x, forge.y)


def test_random_fallback_never_steps_into_a_forge():
    game, planner = make("warrior")
    p, forge = setup_line(game)
    for _ in range(200):
        action, args = planner.get_random_action(game)
        if action == 'move':
            assert (p.x + args['dx'], p.y + args['dy']) != (forge.x, forge.y)


def test_random_fallback_does_not_mine_with_a_full_pack():
    from core.entity_loader import EntityLoader
    game, planner = make("warrior")
    p = game.state.player
    open_room(game, p.x, p.y)
    clear_blockers(game)
    game.context.add_entity(EntityLoader().create_ore_vein('copper', p.x + 1, p.y, floor=1))
    vein = EntityLoader().create_ore_vein('copper', 0, 0, floor=1)
    while p.ore_count() < p.MAX_ORE_BAG:
        p.inventory.append(vein.get_ore_item())
    assert all(planner.get_random_action(game)[0] != 'mine' for _ in range(200))


def test_random_fallback_still_mines_with_a_full_pack():
    """VB-131: ore has its own bag, so a full pack does not block mining."""
    from core.entity_loader import EntityLoader
    game, planner = make("warrior")
    p = game.state.player
    open_room(game, p.x, p.y)
    clear_blockers(game)
    game.context.add_entity(EntityLoader().create_ore_vein('copper', p.x + 1, p.y, floor=1))
    while p.has_room():
        p.add_to_inventory(LootGenerator.get_instance().create_item('bread'))
    assert p.ore_count() == 0 and not p.has_room()
    assert any(planner.get_random_action(game)[0] == 'mine' for _ in range(400))
