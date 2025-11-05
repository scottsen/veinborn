"""Unit tests for stairs placement and descent mechanics.

Tests for:
- Stairs placement (up and down)
- Stairs finding methods
- DescendAction validation and execution
- Floor transitions
- Difficulty scaling

Following MVP_TESTING_GUIDE.md patterns.
"""
import pytest
from core.world import Map, TileType
from core.actions.descend_action import DescendAction
from core.base.action import ActionResult
from core.game import Game
from core.entities import Player, Monster, EntityType


# ============================================================================
# Stairs Placement Tests
# ============================================================================

pytestmark = pytest.mark.unit

class TestStairsPlacement:
    """Tests for placing stairs in the dungeon."""

    @pytest.mark.unit
    def test_place_stairs_down_in_last_room(self):
        """Stairs down should be placed in the last room's center."""
        game_map = Map(width=80, height=24)

        # Verify stairs were placed
        stairs_pos = game_map.find_stairs_down()
        assert stairs_pos is not None, "Stairs down should be placed"

        # Verify it's in the last room
        last_room = game_map.rooms[-1]
        expected_x, expected_y = last_room.center
        assert stairs_pos == (expected_x, expected_y)

    @pytest.mark.unit
    def test_place_stairs_up_in_first_room(self):
        """Stairs up should be placed in the first room's center."""
        game_map = Map(width=80, height=24)

        # Place stairs up (not done by default generation)
        stairs_pos = game_map.place_stairs_up()
        assert stairs_pos is not None

        # Verify it's in the first room
        first_room = game_map.rooms[0]
        expected_x, expected_y = first_room.center
        assert stairs_pos == (expected_x, expected_y)

    @pytest.mark.unit
    def test_stairs_down_tile_is_walkable(self):
        """Stairs down tiles should be walkable."""
        game_map = Map(width=80, height=24)
        stairs_pos = game_map.find_stairs_down()

        assert stairs_pos is not None
        x, y = stairs_pos
        tile = game_map.tiles[x][y]

        assert tile.tile_type == TileType.STAIRS_DOWN
        assert tile.walkable is True
        assert tile.transparent is True

    @pytest.mark.unit
    def test_stairs_up_tile_is_walkable(self):
        """Stairs up tiles should be walkable."""
        game_map = Map(width=80, height=24)
        game_map.place_stairs_up()
        stairs_pos = game_map.find_stairs_up()

        assert stairs_pos is not None
        x, y = stairs_pos
        tile = game_map.tiles[x][y]

        assert tile.tile_type == TileType.STAIRS_UP
        assert tile.walkable is True
        assert tile.transparent is True

    @pytest.mark.unit
    def test_both_stairs_can_coexist(self):
        """Both stairs up and down can exist on the same map."""
        game_map = Map(width=80, height=24)
        game_map.place_stairs_up()

        stairs_down = game_map.find_stairs_down()
        stairs_up = game_map.find_stairs_up()

        assert stairs_down is not None
        assert stairs_up is not None
        assert stairs_down != stairs_up, "Stairs should be in different locations"


# ============================================================================
# Stairs Finding Tests
# ============================================================================

class TestStairsFinding:
    """Tests for finding stairs positions."""

    @pytest.mark.unit
    def test_find_stairs_down_when_present(self):
        """Should find stairs down when they exist."""
        game_map = Map(width=80, height=24)
        stairs_pos = game_map.find_stairs_down()

        assert stairs_pos is not None
        x, y = stairs_pos
        assert 0 <= x < game_map.width
        assert 0 <= y < game_map.height

    @pytest.mark.unit
    def test_find_stairs_up_when_present(self):
        """Should find stairs up when they exist."""
        game_map = Map(width=80, height=24)
        game_map.place_stairs_up()
        stairs_pos = game_map.find_stairs_up()

        assert stairs_pos is not None
        x, y = stairs_pos
        assert 0 <= x < game_map.width
        assert 0 <= y < game_map.height

    @pytest.mark.unit
    def test_find_stairs_down_returns_correct_position(self):
        """find_stairs_down should return the exact position."""
        game_map = Map(width=80, height=24)

        # Get expected position from last room
        last_room = game_map.rooms[-1]
        expected_pos = last_room.center

        # Should match what find returns
        found_pos = game_map.find_stairs_down()
        assert found_pos == expected_pos

    @pytest.mark.unit
    def test_find_stairs_up_returns_correct_position(self):
        """find_stairs_up should return the exact position."""
        game_map = Map(width=80, height=24)
        game_map.place_stairs_up()

        # Get expected position from first room
        first_room = game_map.rooms[0]
        expected_pos = first_room.center

        # Should match what find returns
        found_pos = game_map.find_stairs_up()
        assert found_pos == expected_pos


# ============================================================================
# DescendAction Validation Tests
# ============================================================================

class TestDescendActionValidation:
    """Tests for DescendAction validation logic."""

    @pytest.mark.unit
    def test_descend_requires_stairs(self, new_game):
        """Can't descend unless standing on stairs."""
        game = new_game
        player = game.state.player

        # Move player away from any stairs
        player.x = 1
        player.y = 1

        action = DescendAction(actor_id=player.entity_id)
        from core.base.game_context import GameContext
        context = GameContext(game_state=game.state)

        # Should fail validation
        assert action.validate(context) is False

    @pytest.mark.unit
    def test_descend_succeeds_on_stairs(self, new_game):
        """Can descend when standing on stairs."""
        game = new_game
        player = game.state.player

        # Find and move player to stairs
        stairs_pos = game.state.dungeon_map.find_stairs_down()
        assert stairs_pos is not None
        player.x, player.y = stairs_pos

        action = DescendAction(actor_id=player.entity_id)
        from core.base.game_context import GameContext
        context = GameContext(game_state=game.state)

        # Should pass validation
        assert action.validate(context) is True

    @pytest.mark.unit
    def test_dead_player_cannot_descend(self, new_game):
        """Dead players can't descend."""
        game = new_game
        player = game.state.player

        # Move to stairs
        stairs_pos = game.state.dungeon_map.find_stairs_down()
        player.x, player.y = stairs_pos

        # Kill player (take damage to 0 HP)
        player.take_damage(player.hp)
        assert not player.is_alive

        action = DescendAction(actor_id=player.entity_id)
        from core.base.game_context import GameContext
        context = GameContext(game_state=game.state)

        # Should fail validation
        assert action.validate(context) is False


# ============================================================================
# DescendAction Execution Tests
# ============================================================================

class TestDescendActionExecution:
    """Tests for DescendAction execution."""

    @pytest.mark.unit
    def test_descend_creates_floor_event(self, new_game):
        """Descending creates a floor transition event."""
        game = new_game
        player = game.state.player

        # Move to stairs
        stairs_pos = game.state.dungeon_map.find_stairs_down()
        player.x, player.y = stairs_pos

        action = DescendAction(actor_id=player.entity_id)
        from core.base.game_context import GameContext
        context = GameContext(game_state=game.state)

        outcome = action.execute(context)

        # Should succeed
        assert outcome.result == ActionResult.SUCCESS
        assert outcome.took_turn is True

        # Should have descent event
        assert len(outcome.events) > 0
        descent_event = outcome.events[0]
        assert descent_event['type'] == 'descend_floor'
        assert descent_event['actor_id'] == player.entity_id
        assert descent_event['from_floor'] == 1

    @pytest.mark.unit
    def test_descend_has_message(self, new_game):
        """Descending displays a message."""
        game = new_game
        player = game.state.player

        # Move to stairs
        stairs_pos = game.state.dungeon_map.find_stairs_down()
        player.x, player.y = stairs_pos

        action = DescendAction(actor_id=player.entity_id)
        from core.base.game_context import GameContext
        context = GameContext(game_state=game.state)

        outcome = action.execute(context)

        # Should have message
        assert len(outcome.messages) > 0
        message = outcome.messages[0]
        assert "descend" in message.lower()
        assert "floor" in message.lower()

    @pytest.mark.unit
    def test_descend_fails_without_validation(self, new_game):
        """Descending fails if not on stairs."""
        game = new_game
        player = game.state.player

        # Move player away from stairs
        player.x = 1
        player.y = 1

        action = DescendAction(actor_id=player.entity_id)
        from core.base.game_context import GameContext
        context = GameContext(game_state=game.state)

        outcome = action.execute(context)

        # Should fail
        assert outcome.result == ActionResult.FAILURE
        assert len(outcome.messages) > 0
        assert "stairs" in outcome.messages[0].lower()


# ============================================================================
# Floor Transition Tests
# ============================================================================

class TestFloorTransitions:
    """Tests for multi-floor transitions."""

    @pytest.mark.integration
    def test_descend_floor_increments_floor_number(self, new_game):
        """Floor number increases when descending."""
        game = new_game

        assert game.state.current_floor == 1

        # Descend
        game.descend_floor()

        assert game.state.current_floor == 2

    @pytest.mark.integration
    def test_descend_generates_new_map(self, new_game):
        """Descending generates a new map."""
        game = new_game
        old_map = game.state.dungeon_map

        # Descend
        game.descend_floor()
        new_map = game.state.dungeon_map

        # Should be a different map object
        assert new_map is not old_map
        assert new_map.width == old_map.width
        assert new_map.height == old_map.height

    @pytest.mark.integration
    def test_player_starts_on_stairs_up_after_descent(self, new_game):
        """Player should be placed on stairs up on new floor."""
        game = new_game

        # Descend
        game.descend_floor()

        player = game.state.player
        stairs_up = game.state.dungeon_map.find_stairs_up()

        assert stairs_up is not None
        assert (player.x, player.y) == stairs_up

    @pytest.mark.integration
    def test_new_floor_has_stairs_down(self, new_game):
        """New floors should have stairs down."""
        game = new_game

        # Descend
        game.descend_floor()

        stairs_down = game.state.dungeon_map.find_stairs_down()
        assert stairs_down is not None

    @pytest.mark.integration
    def test_multiple_floor_descents(self, new_game):
        """Can descend multiple floors in sequence."""
        game = new_game

        for expected_floor in range(2, 6):
            game.descend_floor()
            assert game.state.current_floor == expected_floor

            # Each floor should have stairs
            assert game.state.dungeon_map.find_stairs_down() is not None
            assert game.state.dungeon_map.find_stairs_up() is not None


# ============================================================================
# Difficulty Scaling Tests
# ============================================================================

class TestDifficultyScaling:
    """Tests for difficulty scaling across floors."""

    @pytest.mark.integration
    def test_monster_count_increases_with_floor(self, new_game):
        """Monster count should meet minimum for each floor depth.

        Each floor has a base count plus random special rooms that may add more.
        We test that the base formula is respected, not floor-to-floor comparison
        (since special rooms are random).
        """
        game = new_game

        # Floor 1: Base formula is 3 + (1 // 2) = 3 monsters minimum
        floor1_monsters = [e for e in game.state.entities.values()
                          if e.entity_type == EntityType.MONSTER]
        floor1_count = len(floor1_monsters)
        assert floor1_count >= 3, f"Floor 1 should have at least 3 monsters, got {floor1_count}"

        # Floor 2: Base formula is 3 + (2 // 2) = 4 monsters minimum
        game.descend_floor()
        floor2_monsters = [e for e in game.state.entities.values()
                          if e.entity_type == EntityType.MONSTER]
        floor2_count = len(floor2_monsters)
        assert floor2_count >= 4, f"Floor 2 should have at least 4 monsters, got {floor2_count}"

        # Floor 3: Base formula is 3 + (3 // 2) = 4 monsters minimum
        game.descend_floor()
        floor3_monsters = [e for e in game.state.entities.values()
                          if e.entity_type == EntityType.MONSTER]
        floor3_count = len(floor3_monsters)
        assert floor3_count >= 4, f"Floor 3 should have at least 4 monsters, got {floor3_count}"

        # Floor 5: Base formula is 3 + (5 // 2) = 5 monsters minimum
        game.descend_floor()
        game.descend_floor()
        floor5_monsters = [e for e in game.state.entities.values()
                          if e.entity_type == EntityType.MONSTER]
        floor5_count = len(floor5_monsters)
        assert floor5_count >= 5, f"Floor 5 should have at least 5 monsters, got {floor5_count}"

    @pytest.mark.integration
    def test_ore_count_increases_with_floor(self, new_game):
        """Ore vein count should meet minimum for each floor depth.

        Each floor has a base count plus random special rooms that may add bonus ore.
        We test that the base formula is respected, not floor-to-floor comparison
        (since special rooms are random).
        """
        game = new_game

        # Floor 1: Base formula is 8 ore veins minimum
        floor1_ore = [e for e in game.state.entities.values()
                     if e.entity_type == EntityType.ORE_VEIN]
        floor1_count = len(floor1_ore)
        assert floor1_count >= 8, f"Floor 1 should have at least 8 ore veins, got {floor1_count}"

        # Floor 2: Base formula is 8 + (2-1) = 9 ore veins minimum
        game.descend_floor()
        floor2_ore = [e for e in game.state.entities.values()
                     if e.entity_type == EntityType.ORE_VEIN]
        floor2_count = len(floor2_ore)
        assert floor2_count >= 9, f"Floor 2 should have at least 9 ore veins, got {floor2_count}"

        # Floor 3: Base formula is 8 + (3-1) = 10 ore veins minimum
        game.descend_floor()
        floor3_ore = [e for e in game.state.entities.values()
                     if e.entity_type == EntityType.ORE_VEIN]
        floor3_count = len(floor3_ore)
        assert floor3_count >= 10, f"Floor 3 should have at least 10 ore veins, got {floor3_count}"

    @pytest.mark.integration
    def test_difficulty_formula_floor_5(self, new_game):
        """Verify difficulty scaling formula at floor 5."""
        game = new_game

        # Descend to floor 5
        for _ in range(4):
            game.descend_floor()

        assert game.state.current_floor == 5

        # Floor 5: Base formula monsters = 3 + (5 // 2) = 3 + 2 = 5
        # Special rooms may add more, so test for minimum
        monsters = [e for e in game.state.entities.values()
                   if e.entity_type == EntityType.MONSTER]
        assert len(monsters) >= 5, f"Floor 5 should have at least 5 monsters, got {len(monsters)}"

        # Floor 5: Base formula ore = 8 + (5-1) = 12
        # Special rooms may add bonus ore, so test for minimum
        ore_veins = [e for e in game.state.entities.values()
                    if e.entity_type == EntityType.ORE_VEIN]
        assert len(ore_veins) >= 12, f"Floor 5 should have at least 12 ore veins, got {len(ore_veins)}"


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    @pytest.mark.unit
    def test_descend_action_player_fallback(self, new_game):
        """DescendAction should work with player entity."""
        game = new_game
        player = game.state.player

        # Move to stairs
        stairs_pos = game.state.dungeon_map.find_stairs_down()
        player.x, player.y = stairs_pos

        # Use player's entity_id
        action = DescendAction(actor_id=player.entity_id)
        from core.base.game_context import GameContext
        context = GameContext(game_state=game.state)

        outcome = action.execute(context)

        # Should work even though player isn't in entities dict
        assert outcome.result == ActionResult.SUCCESS

    @pytest.mark.integration
    def test_entities_cleared_on_floor_transition(self, new_game):
        """Old floor entities should be cleared on descent."""

        game = new_game

        # Get entity IDs from floor 1
        floor1_entity_ids = set(game.state.entities.keys())

        # Descend
        game.descend_floor()

        # Get entity IDs from floor 2
        floor2_entity_ids = set(game.state.entities.keys())

        # Should be completely different entities
        # (except possibly the player if they're in entities dict)
        overlapping = floor1_entity_ids & floor2_entity_ids
        # Allow player entity ID to overlap
        assert len(overlapping) <= 1, "Old entities should be cleared"

    @pytest.mark.integration
    def test_player_survives_floor_transition(self, new_game):
        """Player entity should persist across floors."""
        game = new_game
        player = game.state.player

        # Remember player stats
        old_hp = player.hp
        old_max_hp = player.max_hp
        old_id = player.entity_id

        # Descend
        game.descend_floor()

        # Player should be same object with same stats
        assert game.state.player.entity_id == old_id
        assert game.state.player.hp == old_hp
        assert game.state.player.max_hp == old_max_hp
        assert game.state.player.is_alive
