"""
Tests for perception system - line-of-sight and visibility.

Coverage goals:
- get_visible_entities() with radius checks
- get_visible_entities() with line-of-sight
- get_visible_monsters(), get_visible_items(), get_nearby_ore()
- get_entities_at_distance() with ranges
- find_nearest() for different entity types
- _has_line_of_sight() Bresenham algorithm
- get_perception_info() comprehensive data
"""

import pytest
from src.core.perception import PerceptionSystem
from src.core.entities import Player, Monster, OreVein
from src.core.world import Map
from src.core.game_state import GameState
from src.core.base.entity import EntityType


class TestGetVisibleEntities:
    """Test get_visible_entities() with radius-based visibility."""

    def test_sees_entities_within_radius(self, new_game):
        """Entities within radius are visible."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        # Place monster within radius (5 tiles away)
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=player.x + 5,
            y=player.y,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )
        game.context.add_entity(monster)

        # Check visibility with radius=10
        visible = perception.get_visible_entities(game, player, radius=10.0)

        assert monster in visible

    def test_does_not_see_entities_outside_radius(self, new_game):
        """Entities outside radius are not visible."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        # Place monster far away (15 tiles)
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=player.x + 15,
            y=player.y,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )
        game.context.add_entity(monster)

        # Check visibility with radius=10
        visible = perception.get_visible_entities(game, player, radius=10.0)

        assert monster not in visible

    def test_does_not_see_self(self, new_game):
        """Observer does not see themselves in results."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        visible = perception.get_visible_entities(game, player, radius=10.0)

        assert player not in visible

    def test_does_not_see_entities_in_inventory(self, new_game):
        """Entities without position (in inventory) are not visible."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        # Create item in inventory (no position)
        from src.core.base.entity import Entity
        item = Entity(
            entity_id='item1',
            entity_type=EntityType.ITEM,
            name='Sword',
            x=None,  # No position - in inventory
            y=None
        )
        game.state.entities[item.entity_id] = item

        visible = perception.get_visible_entities(game, player, radius=10.0)

        assert item not in visible

    def test_visibility_with_multiple_entities(self, new_game):
        """Multiple entities at various distances."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        # Replace entities dict for test isolation
        game.state.entities = {}
        game.state.entities[player.entity_id] = player

        # Close monster (3 tiles)
        close = Monster(
            entity_id='m1',
            name='Close Goblin',
            x=player.x + 3,
            y=player.y,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )

        # Mid-range monster (7 tiles)
        mid = Monster(
            entity_id='m2',
            name='Mid Orc',
            x=player.x + 7,
            y=player.y,
            hp=20,
            max_hp=20,
            attack=5,
            defense=2
        )

        # Far monster (15 tiles - out of range)
        far = Monster(
            entity_id='m3',
            name='Far Troll',
            x=player.x + 15,
            y=player.y,
            hp=30,
            max_hp=30,
            attack=8,
            defense=3
        )

        game.state.entities[close.entity_id] = close
        game.state.entities[mid.entity_id] = mid
        game.state.entities[far.entity_id] = far

        visible = perception.get_visible_entities(game, player, radius=10.0)

        assert close in visible, "Close monster (3 tiles) should be visible"
        assert mid in visible, "Mid-range monster (7 tiles) should be visible"
        assert far not in visible, "Far monster (15 tiles) should not be visible with radius 10"


class TestLineOfSight:
    """Test line-of-sight with Bresenham algorithm."""

    def test_line_of_sight_clear_path(self):
        """Clear line of sight when no walls block."""
        # Create simple map with open space
        from src.core.world import TileType, Tile
        dungeon_map = Map(width=20, height=20)

        # Set all tiles to floor
        for x in range(dungeon_map.width):
            for y in range(dungeon_map.height):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        # Create game state
        player = Player(entity_id='player', x=5, y=5, hp=10, max_hp=10, attack=5, defense=2)
        state = GameState(player=player, dungeon_map=dungeon_map)

        # Create simple game object
        class SimpleGame:
            def __init__(self, state):
                self.state = state

        game = SimpleGame(state)

        # Create monster in clear line of sight
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=10,
            y=10,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )

        perception = PerceptionSystem()
        has_los = perception._has_line_of_sight(game, player, monster)

        assert has_los is True

    def test_line_of_sight_blocked_by_wall(self):
        """Line of sight blocked by wall."""
        # Create map with wall blocking line of sight
        from src.core.world import TileType, Tile
        dungeon_map = Map(width=20, height=20)

        # Set all tiles to floor first
        for x in range(dungeon_map.width):
            for y in range(dungeon_map.height):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        # Place wall between player and monster
        for y in range(20):
            dungeon_map.tiles[7][y] = Tile(TileType.WALL)

        # Create game state
        player = Player(entity_id='player', x=5, y=10, hp=10, max_hp=10, attack=5, defense=2)
        state = GameState(player=player, dungeon_map=dungeon_map)

        class SimpleGame:
            def __init__(self, state):
                self.state = state

        game = SimpleGame(state)

        # Monster on other side of wall
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=10,
            y=10,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )

        perception = PerceptionSystem()
        has_los = perception._has_line_of_sight(game, player, monster)

        assert has_los is False

    def test_line_of_sight_diagonal_clear(self):
        """Diagonal line of sight when clear."""
        from src.core.world import TileType, Tile
        dungeon_map = Map(width=20, height=20)

        # Set all tiles to floor
        for x in range(dungeon_map.width):
            for y in range(dungeon_map.height):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        player = Player(entity_id='player', x=5, y=5, hp=10, max_hp=10, attack=5, defense=2)
        state = GameState(player=player, dungeon_map=dungeon_map)

        class SimpleGame:
            def __init__(self, state):
                self.state = state

        game = SimpleGame(state)

        # Diagonal position
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=10,
            y=10,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )

        perception = PerceptionSystem()
        has_los = perception._has_line_of_sight(game, player, monster)

        assert has_los is True

    def test_line_of_sight_same_position(self):
        """Line of sight to same position (edge case)."""
        from src.core.world import TileType, Tile
        dungeon_map = Map(width=20, height=20)

        # Set all tiles to floor
        for x in range(dungeon_map.width):
            for y in range(dungeon_map.height):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        player = Player(entity_id='player', x=5, y=5, hp=10, max_hp=10, attack=5, defense=2)
        state = GameState(player=player, dungeon_map=dungeon_map)

        class SimpleGame:
            def __init__(self, state):
                self.state = state

        game = SimpleGame(state)

        # Entity at same position
        other = Player(entity_id='other', x=5, y=5, hp=10, max_hp=10, attack=5, defense=2)

        perception = PerceptionSystem()
        has_los = perception._has_line_of_sight(game, player, other)

        assert has_los is True

    def test_get_visible_entities_with_line_of_sight(self):
        """get_visible_entities respects line-of-sight parameter."""
        # Create map with wall
        from src.core.world import TileType, Tile
        dungeon_map = Map(width=20, height=20)

        # Set all tiles to floor first
        for x in range(dungeon_map.width):
            for y in range(dungeon_map.height):
                dungeon_map.tiles[x][y] = Tile(TileType.FLOOR)

        # Vertical wall
        for y in range(20):
            dungeon_map.tiles[10][y] = Tile(TileType.WALL)

        player = Player(entity_id='player', x=5, y=10, hp=10, max_hp=10, attack=5, defense=2)
        state = GameState(player=player, dungeon_map=dungeon_map)

        # Monster on same side (visible)
        m1 = Monster(entity_id='m1', name='Nearby', x=7, y=10, hp=10, max_hp=10, attack=3, defense=1)

        # Monster behind wall (not visible with LOS)
        m2 = Monster(entity_id='m2', name='Behind Wall', x=12, y=10, hp=10, max_hp=10, attack=3, defense=1)

        state.entities[m1.entity_id] = m1
        state.entities[m2.entity_id] = m2

        class SimpleGame:
            def __init__(self, state):
                self.state = state

        game = SimpleGame(state)

        perception = PerceptionSystem()

        # Without line-of-sight (radius only)
        visible_no_los = perception.get_visible_entities(game, player, radius=15.0, line_of_sight=False)
        assert m1 in visible_no_los
        assert m2 in visible_no_los

        # With line-of-sight
        visible_with_los = perception.get_visible_entities(game, player, radius=15.0, line_of_sight=True)
        assert m1 in visible_with_los
        assert m2 not in visible_with_los  # Blocked by wall


class TestGetVisibleMonsters:
    """Test get_visible_monsters() filtering."""

    def test_returns_only_living_monsters(self, new_game):
        """Only returns living monsters, not dead or other entities."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        # Living monster
        alive = Monster(
            entity_id='m1',
            name='Alive Goblin',
            x=player.x + 3,
            y=player.y,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )

        # Dead monster (must call take_damage to set is_alive=False)
        dead = Monster(
            entity_id='m2',
            name='Dead Goblin',
            x=player.x + 5,
            y=player.y,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )
        dead.take_damage(10)  # Kill it properly

        # Ore vein (not a monster)
        ore = OreVein(
            entity_id='ore1',
            ore_type='iron',
            x=player.x + 4,
            y=player.y,
            hardness=50,
            conductivity=50,
            malleability=50,
            purity=50,
            density=50
        )

        game.context.add_entity(alive)
        game.context.add_entity(dead)
        game.context.add_entity(ore)

        monsters = perception.get_visible_monsters(game, player, radius=10.0)

        assert alive in monsters
        assert dead not in monsters  # Dead monsters excluded
        assert ore not in monsters  # Not a monster

    def test_empty_when_no_monsters(self, new_game):
        """Returns empty list when no monsters visible."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        monsters = perception.get_visible_monsters(game, player, radius=10.0)

        assert monsters == []


class TestGetVisibleItems:
    """Test get_visible_items() filtering."""

    def test_returns_only_items(self, new_game):
        """Returns only items, not monsters or ore."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        # Create item
        from src.core.base.entity import Entity
        item = Entity(
            entity_id='item1',
            entity_type=EntityType.ITEM,
            name='Sword',
            x=player.x + 3,
            y=player.y
        )

        # Monster (not an item)
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=player.x + 4,
            y=player.y,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )

        game.state.entities[item.entity_id] = item
        game.context.add_entity(monster)

        items = perception.get_visible_items(game, player, radius=10.0)

        assert item in items
        assert monster not in items


class TestGetNearbyOre:
    """Test get_nearby_ore() filtering."""

    def test_returns_only_ore_veins(self, new_game):
        """Returns only ore veins."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        # Ore vein
        ore = OreVein(
            entity_id='ore1',
            ore_type='iron',
            x=player.x + 3,
            y=player.y,
            hardness=50,
            conductivity=50,
            malleability=50,
            purity=50,
            density=50
        )

        # Monster (not ore)
        monster = Monster(
            entity_id='m1',
            name='Goblin',
            x=player.x + 4,
            y=player.y,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )

        game.context.add_entity(ore)
        game.context.add_entity(monster)

        ore_veins = perception.get_nearby_ore(game, player, radius=10.0)

        assert ore in ore_veins
        assert monster not in ore_veins


class TestGetEntitiesAtDistance:
    """Test get_entities_at_distance() range queries."""

    def test_returns_entities_in_range(self, new_game):
        """Returns entities within min-max distance range."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        # Close (distance ~2)
        close = Monster(entity_id='m1', name='Close', x=player.x + 2, y=player.y, hp=10, max_hp=10, attack=3, defense=1)

        # Mid-range (distance ~5)
        mid = Monster(entity_id='m2', name='Mid', x=player.x + 5, y=player.y, hp=10, max_hp=10, attack=3, defense=1)

        # Far (distance ~10)
        far = Monster(entity_id='m3', name='Far', x=player.x + 10, y=player.y, hp=10, max_hp=10, attack=3, defense=1)

        game.context.add_entity(close)
        game.context.add_entity(mid)
        game.context.add_entity(far)

        # Query range 3-7 (should get mid-range only)
        in_range = perception.get_entities_at_distance(game, player, min_distance=3.0, max_distance=7.0)

        assert close not in in_range  # Too close
        assert mid in in_range
        assert far not in in_range  # Too far

    def test_inclusive_boundaries(self, new_game):
        """Distance boundaries are inclusive."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        # Exactly at min distance (5)
        at_min = Monster(entity_id='m1', name='AtMin', x=player.x + 5, y=player.y, hp=10, max_hp=10, attack=3, defense=1)

        # Exactly at max distance (10)
        at_max = Monster(entity_id='m2', name='AtMax', x=player.x + 10, y=player.y, hp=10, max_hp=10, attack=3, defense=1)

        game.context.add_entity(at_min)
        game.context.add_entity(at_max)

        in_range = perception.get_entities_at_distance(game, player, min_distance=5.0, max_distance=10.0)

        assert at_min in in_range
        assert at_max in in_range


class TestFindNearest:
    """Test find_nearest() for finding closest entity of type."""

    def test_finds_nearest_monster(self, new_game):
        """Finds closest monster."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        # Close monster (3 tiles)
        close = Monster(entity_id='m1', name='Close', x=player.x + 3, y=player.y, hp=10, max_hp=10, attack=3, defense=1)

        # Far monster (10 tiles)
        far = Monster(entity_id='m2', name='Far', x=player.x + 10, y=player.y, hp=10, max_hp=10, attack=3, defense=1)

        game.context.add_entity(close)
        game.context.add_entity(far)

        nearest = perception.find_nearest(game, player, Monster)

        assert nearest == close

    def test_finds_nearest_ore(self, new_game):
        """Finds closest ore vein."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        # Close ore (4 tiles)
        close_ore = OreVein(
            entity_id='ore1',
            ore_type='copper',
            x=player.x + 4,
            y=player.y,
            hardness=30,
            conductivity=70,
            malleability=60,
            purity=50,
            density=40
        )

        # Far ore (12 tiles)
        far_ore = OreVein(
            entity_id='ore2',
            ore_type='iron',
            x=player.x + 12,
            y=player.y,
            hardness=50,
            conductivity=50,
            malleability=50,
            purity=50,
            density=50
        )

        game.context.add_entity(close_ore)
        game.context.add_entity(far_ore)

        nearest = perception.find_nearest(game, player, OreVein)

        assert nearest == close_ore

    def test_returns_none_when_no_entities_of_type(self, new_game):
        """Returns None when no entities of type exist."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        # No monsters in game
        nearest = perception.find_nearest(game, player, Monster)

        assert nearest is None

    def test_ignores_entities_without_position(self, new_game):
        """Ignores entities in inventory (no position)."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        # Monster in inventory (no position)
        from src.core.base.entity import Entity
        in_inventory = Entity(
            entity_id='item1',
            entity_type=EntityType.ITEM,
            name='Sword',
            x=None,
            y=None
        )
        game.state.entities[in_inventory.entity_id] = in_inventory

        # Should not crash
        nearest = perception.find_nearest(game, player, type(in_inventory))

        assert nearest is None


class TestGetPerceptionInfo:
    """Test get_perception_info() comprehensive data."""

    def test_returns_correct_counts(self, new_game):
        """Returns correct entity counts."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        # Save player position for test entities
        player_x, player_y = player.x, player.y

        # Replace entities dict with fresh one for deterministic test
        # (avoids issues with randomly spawned monsters/ore causing flakiness)
        game.state.entities = {}
        game.state.entities[player.entity_id] = player

        # Add known test entities adjacent to player (guaranteed line-of-sight)
        # Place them in cardinal directions to avoid wall issues
        monster = Monster(
            entity_id='test_m1',
            name='Test Goblin',
            x=player_x + 1,
            y=player_y,
            hp=10,
            max_hp=10,
            attack=3,
            defense=1
        )

        ore = OreVein(
            entity_id='test_ore1',
            ore_type='iron',
            x=player_x,
            y=player_y + 1,
            hardness=50,
            conductivity=50,
            malleability=50,
            purity=50,
            density=50
        )

        from src.core.base.entity import Entity
        item = Entity(
            entity_id='test_item1',
            entity_type=EntityType.ITEM,
            name='Test Potion',
            x=player_x - 1,
            y=player_y
        )

        game.state.entities[monster.entity_id] = monster
        game.state.entities[ore.entity_id] = ore
        game.state.entities[item.entity_id] = item

        info = perception.get_perception_info(game, player)

        # Check exact counts (deterministic now)
        # Add debugging to help diagnose flakiness
        all_entities = list(game.state.entities.values())
        visible_entities = perception.get_visible_entities(game, player, radius=10.0)

        assert info['total_visible'] == 3, (
            f"Expected 3 visible entities (monster, ore, item), got {info['total_visible']}. "
            f"All entities: {[e.name for e in all_entities]}, "
            f"Visible: {[e.name for e in visible_entities]}"
        )
        assert info['monsters_visible'] == 1, f"Expected 1 monster, got {info['monsters_visible']}"
        assert info['items_visible'] == 1, f"Expected 1 item, got {info['items_visible']}"
        assert info['ore_visible'] == 1, f"Expected 1 ore vein, got {info['ore_visible']}"
        assert info['visibility_radius'] == 10.0

    def test_identifies_nearest_threat(self, new_game):
        """Identifies nearest living monster."""
        game = new_game
        perception = PerceptionSystem()
        player = game.state.player

        close = Monster(entity_id='m1', name='Close', x=player.x + 2, y=player.y, hp=10, max_hp=10, attack=3, defense=1)
        far = Monster(entity_id='m2', name='Far', x=player.x + 8, y=player.y, hp=10, max_hp=10, attack=3, defense=1)

        game.context.add_entity(close)
        game.context.add_entity(far)

        info = perception.get_perception_info(game, player)

        assert info['nearest_threat'] == close

    def test_handles_empty_world(self):
        """Handles world with no other entities."""
        # Create minimal game without fixture spawning
        from src.core.world import Map
        from src.core.game_state import GameState

        dungeon_map = Map(width=20, height=20)
        player = Player(entity_id='player', x=10, y=10, hp=10, max_hp=10, attack=5, defense=2)
        state = GameState(player=player, dungeon_map=dungeon_map)

        # Clear all entities except player
        state.entities = {}

        class SimpleGame:
            def __init__(self, state):
                self.state = state

        game = SimpleGame(state)
        perception = PerceptionSystem()

        info = perception.get_perception_info(game, player)

        assert info['total_visible'] == 0
        assert info['monsters_visible'] == 0
        assert info['nearest_threat'] is None
        assert info['nearest_item'] is None
