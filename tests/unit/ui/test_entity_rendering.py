"""
Tests for entity rendering to prevent invisible entity bugs.

Ensures every EntityType has proper rendering logic in MapWidget.
"""
import pytest
from core.base.entity import EntityType, Entity
from core.entities import Player, Monster, OreVein, Forge
from core.game import Game
from core.snapshot import build_snapshot
from ui.textual.widgets.map_widget import MapWidget


# Terrain symbols that indicate entity didn't render
TERRAIN_SYMBOLS = {'·', '█', '+', '<', '>', ' ', '?'}


def cell(player, *entities, x=5, y=5):
    """Render map cell (x, y) of a real game state holding `player` and `entities`."""
    game = Game()
    game.start_new_game(seed=3)
    state = game.state
    state.entities.clear()
    state.player = player
    state.entities[player.entity_id] = player
    for ent in entities:
        state.entities[ent.entity_id] = ent
    widget = MapWidget()
    return widget._render_cell(x, y, build_snapshot(state))


def create_entity_by_type(entity_type: EntityType, x: int = 5, y: int = 5) -> Entity:
    """Factory to create entities of each type for testing."""
    if entity_type == EntityType.PLAYER:
        return Player(name="Test Player", x=x, y=y, hp=20, max_hp=20, attack=5, defense=2)

    elif entity_type == EntityType.MONSTER:
        return Monster(
            name="Goblin",
            x=x, y=y,
            hp=10, max_hp=10,
            attack=3, defense=1,
            xp_reward=5
        )

    elif entity_type == EntityType.ORE_VEIN:
        return OreVein(
            ore_type="copper",
            x=x, y=y,
            hardness=50, conductivity=50,
            malleability=50, purity=50, density=50
        )

    elif entity_type == EntityType.FORGE:
        return Forge(forge_type="basic_forge", x=x, y=y)

    elif entity_type == EntityType.ITEM:
        # Generic item (not in world, but test it anyway)
        item = Entity(
            entity_type=EntityType.ITEM,
            name="Test Item",
            x=x, y=y
        )
        item.set_stat('display_symbol', ')')
        return item

    elif entity_type == EntityType.NPC:
        return Entity(
            entity_type=EntityType.NPC,
            name="Test NPC",
            x=x, y=y
        )

    else:
        # Fallback for unknown types
        return Entity(entity_type=entity_type, name=f"Test {entity_type.value}", x=x, y=y)


@pytest.mark.parametrize("entity_type", [e for e in EntityType if e != EntityType.PLAYER])
def test_all_entity_types_have_visible_symbols(entity_type):
    """
    Every non-player entity type must render with a visible, non-terrain symbol.

    This test prevents bugs where entities are invisible (render as floor/wall).
    """
    # Setup
    player = Player(name="Player", x=0, y=0, hp=20, max_hp=20, attack=5, defense=2)
    entity = create_entity_by_type(entity_type, x=5, y=5)

    segment = cell(player, entity)

    # Assertions
    assert segment.text not in TERRAIN_SYMBOLS, \
        f"{entity_type.value} renders as terrain symbol '{segment.text}' (invisible bug!)"

    assert len(segment.text) == 1, \
        f"{entity_type.value} symbol must be exactly 1 character, got: '{segment.text}'"

    assert segment.style is not None, \
        f"{entity_type.value} must have a style (color)"

    # Log for debugging (helpful when test fails)
    print(f"✓ {entity_type.value}: '{segment.text}' (color: {segment.style.color})")


def test_player_renders_distinctly():
    """Player must always render as '@' in bright yellow."""
    player = Player(name="Player", x=5, y=5, hp=20, max_hp=20, attack=5, defense=2)

    segment = cell(player)

    assert segment.text == '@', "Player must render as '@'"
    assert 'yellow' in segment.style.color.name.lower(), "Player must be yellow/bright_yellow"


def test_forge_visibility_regression():
    """
    Regression test for forge rendering bug (2026-01-13).

    Forges were invisible (rendered as floor '·') but blocked movement.
    """
    player = Player(name="Player", x=0, y=0, hp=20, max_hp=20, attack=5, defense=2)
    forge = Forge(forge_type="basic_forge", x=5, y=5)

    segment = cell(player, forge)

    # Forges should render as '&' (from forges.yaml spec)
    assert segment.text == '&', f"Forge should render as '&', got '{segment.text}'"
    assert segment.text != '·', "Forge must not render as floor (invisible bug)"


def test_multiple_entities_same_cell_priority():
    """
    When multiple entities occupy same cell, test rendering priority.

    Expected priority: Player > Monster > Other entities > Terrain
    """
    player = Player(name="Player", x=5, y=5, hp=20, max_hp=20, attack=5, defense=2)
    monster = Monster(name="Goblin", x=5, y=5, hp=10, max_hp=10, attack=3, defense=1, xp_reward=5)

    segment = cell(player, monster)

    # Player should render (higher priority)
    assert segment.text == '@', "Player should have rendering priority over monsters"


@pytest.mark.parametrize("ore_type,expected_color", [
    ("copper", "yellow"),
    ("iron", "white"),
    ("mithril", "cyan"),
    ("adamantite", "magenta"),
])
def test_ore_vein_colors(ore_type, expected_color):
    """Ore veins should render with correct colors based on type."""
    player = Player(name="Player", x=0, y=0, hp=20, max_hp=20, attack=5, defense=2)
    ore = OreVein(ore_type=ore_type, x=5, y=5, hardness=50, conductivity=50,
                  malleability=50, purity=50, density=50)

    segment = cell(player, ore)

    assert segment.text == '*', f"{ore_type} ore should render as '*'"
    assert expected_color in segment.style.color.name.lower(), \
        f"{ore_type} ore should be {expected_color}, got {segment.style.color}"


def test_bare_cells_render_the_terrain_from_the_snapshot():
    """Terrain comes from snapshot tiles: walls as blocks, floor as dots, off-map as blank."""
    game = Game()
    game.start_new_game(seed=3)
    state = game.state
    state.entities.clear()
    state.entities[state.player.entity_id] = state.player
    m = state.dungeon_map
    widget = MapWidget()
    snap = build_snapshot(state)
    seen = set()
    for y in range(m.height):
        for x in range(m.width):
            if (x, y) != (state.player.x, state.player.y):
                seen.add(widget._render_cell(x, y, snap).text)
    assert seen == {'█', '·'} | (seen & {'+', '<', '>'})
    assert widget._render_cell(m.width, 0, snap).text == ' '


def test_another_party_member_is_drawn_in_the_ally_colour():
    """Multiplayer: the other seats are 'player' entities in the viewer's snapshot."""
    me = create_entity_by_type(EntityType.PLAYER, x=5, y=5)
    ally = Player(name="Bob", x=6, y=5, hp=20, max_hp=20, attack=5, defense=2)
    goblin = create_entity_by_type(EntityType.MONSTER, x=7, y=5)
    assert cell(me, ally, goblin, x=6).text == ally.display_symbol
    assert str(cell(me, ally, goblin, x=6).style.color.name) == MapWidget.ALLY_COLOR
    me_cell = cell(me, ally, x=5)
    assert me_cell.text == me.display_symbol and str(me_cell.style.color.name) != MapWidget.ALLY_COLOR
