"""
Integration tests for Fireball Lua action.

These tests verify end-to-end functionality of the Fireball spell,
including registration, validation, execution, and game state changes.
"""

import pytest
from pathlib import Path

from core.scripting.lua_runtime import LuaRuntime
from core.actions.action_factory import ActionFactory
from core.base.action import ActionResult
from core.base.entity import Entity, EntityType
from core.base.game_context import GameContext
from unittest.mock import Mock


@pytest.fixture
def game_state():
    """Create game state with player and monsters."""
    state = Mock()
    state.entities = {}
    state.messages = []
    state.turn_count = 1
    state.current_floor = 1

    # Create dungeon map mock
    state.dungeon_map = Mock()
    state.dungeon_map.is_walkable = lambda x, y: True
    state.dungeon_map.in_bounds = lambda x, y: 0 <= x < 80 and 0 <= y < 40

    # Create player
    player = Entity(
        entity_id="player_1",
        name="Hero",
        entity_type=EntityType.PLAYER,
        x=10,
        y=10,
        hp=100,
        max_hp=100,
        attack=15,
        defense=5,
        stats={"mana": 50, "max_mana": 100}
    )
    state.player = player
    state.entities["player_1"] = player

    return state


@pytest.fixture
def game_context(game_state):
    """Create GameContext."""
    return GameContext(game_state)


@pytest.fixture
def lua_runtime():
    """Create LuaRuntime with proper scripts directory."""
    # Set scripts directory to project root
    scripts_dir = Path(__file__).parent.parent.parent / "scripts"
    return LuaRuntime(scripts_dir=scripts_dir)


@pytest.fixture
def action_factory(game_context, lua_runtime):
    """Create ActionFactory with Fireball registered."""
    factory = ActionFactory(game_context)
    factory.register_lua_action(
        "fireball",
        "actions/fireball.lua",
        lua_runtime,
        "Cast a fireball spell"
    )
    return factory


class TestFireballRegistration:
    """Test Fireball action registration."""

    def test_fireball_registered(self, action_factory):
        """Test that Fireball is registered in action factory."""
        available_actions = action_factory.get_available_actions()
        assert "fireball" in available_actions
        assert "fireball" in available_actions["fireball"].lower()

    def test_create_fireball_action(self, action_factory):
        """Test creating Fireball action."""
        action = action_factory.create(
            "fireball",
            actor_id="player_1",
            x=15,
            y=15
        )

        assert action is not None
        assert action.action_type == "fireball"


class TestFireballValidation:
    """Test Fireball validation."""

    def test_validate_with_sufficient_mana(self, action_factory, game_context):
        """Test validation succeeds with sufficient mana."""
        action = action_factory.create("fireball", actor_id="player_1", x=12, y=12)
        assert action.validate(game_context) is True

    def test_validate_fails_without_mana(self, action_factory, game_context):
        """Test validation fails without sufficient mana."""
        # Drain player mana
        game_context.get_player().stats["mana"] = 5

        action = action_factory.create("fireball", actor_id="player_1", x=12, y=12)
        assert action.validate(game_context) is False

    def test_validate_fails_out_of_range(self, action_factory, game_context):
        """Test validation fails for targets out of range."""
        # Target too far (player at 10,10, target at 50,50 = ~56 tiles away)
        action = action_factory.create("fireball", actor_id="player_1", x=50, y=50)
        assert action.validate(game_context) is False

    def test_validate_fails_without_target(self, action_factory, game_context):
        """Test validation fails without target coordinates."""
        action = action_factory.create("fireball", actor_id="player_1")
        assert action.validate(game_context) is False

    def test_validate_in_range(self, action_factory, game_context):
        """Test validation succeeds for targets in range."""
        # Target at (12, 12) is sqrt(8) ~= 2.8 tiles away
        action = action_factory.create("fireball", actor_id="player_1", x=12, y=12)
        assert action.validate(game_context) is True


class TestFireballExecution:
    """Test Fireball execution."""

    def test_execute_deducts_mana(self, action_factory, game_context):
        """Test that casting Fireball deducts mana."""
        initial_mana = game_context.get_player().stats["mana"]

        # Player is at (10, 10), cast at (12, 12) which is within range 5
        action = action_factory.create("fireball", actor_id="player_1", x=12, y=12)
        outcome = action.execute(game_context)

        assert outcome.result == ActionResult.SUCCESS
        assert game_context.get_player().stats["mana"] == initial_mana - 10

    def test_execute_damages_monsters(self, action_factory, game_context, game_state):
        """Test that Fireball damages monsters in AOE."""
        # Create monsters in AOE near player (10, 10)
        monster1 = Entity(
            entity_id="m1",
            name="Goblin",
            entity_type=EntityType.MONSTER,
            x=12,
            y=12,
            hp=30,
            max_hp=30,
            is_alive=True
        )
        monster2 = Entity(
            entity_id="m2",
            name="Orc",
            entity_type=EntityType.MONSTER,
            x=13,
            y=12,
            hp=50,
            max_hp=50,
            is_alive=True
        )
        game_state.entities["m1"] = monster1
        game_state.entities["m2"] = monster2

        action = action_factory.create("fireball", actor_id="player_1", x=12, y=12)
        outcome = action.execute(game_context)

        assert outcome.result == ActionResult.SUCCESS
        assert monster1.hp == 15  # 30 - 15 damage
        assert monster2.hp == 35  # 50 - 15 damage

    def test_execute_kills_monsters(self, action_factory, game_context, game_state):
        """Test that Fireball can kill monsters."""
        # Create weak monster near player
        monster = Entity(
            entity_id="m1",
            name="Weak Goblin",
            entity_type=EntityType.MONSTER,
            x=12,
            y=12,
            hp=10,
            max_hp=20,
            is_alive=True
        )
        game_state.entities["m1"] = monster

        action = action_factory.create("fireball", actor_id="player_1", x=12, y=12)
        outcome = action.execute(game_context)

        assert outcome.result == ActionResult.SUCCESS
        assert monster.hp == 0
        assert monster.is_alive is False
        assert "incinerated" in " ".join(game_state.messages).lower()

    def test_execute_respects_aoe_radius(self, action_factory, game_context, game_state):
        """Test that Fireball only damages monsters within AOE radius."""
        # Create monsters: one in AOE, one outside (player at 10, 10)
        close_monster = Entity(
            entity_id="m1",
            name="Close Goblin",
            entity_type=EntityType.MONSTER,
            x=12,
            y=12,
            hp=30,
            max_hp=30,
            is_alive=True
        )
        far_monster = Entity(
            entity_id="m2",
            name="Far Orc",
            entity_type=EntityType.MONSTER,
            x=8,
            y=8,  # More than 2 tiles from (12, 12) but still in player range
            hp=50,
            max_hp=50,
            is_alive=True
        )
        game_state.entities["m1"] = close_monster
        game_state.entities["m2"] = far_monster

        action = action_factory.create("fireball", actor_id="player_1", x=12, y=12)
        outcome = action.execute(game_context)

        assert outcome.result == ActionResult.SUCCESS
        assert close_monster.hp == 15  # Damaged (at fireball center)
        assert far_monster.hp == 50  # Not damaged (out of AOE radius)

    def test_execute_does_not_damage_player(self, action_factory, game_context):
        """Test that Fireball doesn't damage the caster."""
        initial_hp = game_context.get_player().hp

        # Cast Fireball at player's location
        action = action_factory.create("fireball", actor_id="player_1", x=10, y=10)
        outcome = action.execute(game_context)

        assert outcome.result == ActionResult.SUCCESS
        assert game_context.get_player().hp == initial_hp  # No self-damage

    def test_execute_generates_messages(self, action_factory, game_context, game_state):
        """Test that Fireball generates appropriate messages."""
        monster = Entity(
            entity_id="m1",
            name="Goblin",
            entity_type=EntityType.MONSTER,
            x=12,
            y=12,
            hp=30,
            max_hp=30,
            is_alive=True
        )
        game_state.entities["m1"] = monster

        action = action_factory.create("fireball", actor_id="player_1", x=12, y=12)
        outcome = action.execute(game_context)

        messages = " ".join(game_state.messages).lower()
        assert "fireball" in messages
        assert "goblin" in messages
        assert "damage" in messages

    def test_execute_generates_events(self, action_factory, game_context, game_state):
        """Test that Fireball generates appropriate events."""
        monster = Entity(
            entity_id="m1",
            name="Goblin",
            entity_type=EntityType.MONSTER,
            x=12,
            y=12,
            hp=30,
            max_hp=30,
            is_alive=True
        )
        game_state.entities["m1"] = monster

        action = action_factory.create("fireball", actor_id="player_1", x=12, y=12)
        outcome = action.execute(game_context)

        assert len(outcome.events) > 0

        # Check for damage event
        damage_events = [e for e in outcome.events if e.get("type") == "damage"]
        assert len(damage_events) == 1
        assert damage_events[0]["target_id"] == "m1"
        assert damage_events[0]["amount"] == 15

        # Check for spell cast event
        spell_events = [e for e in outcome.events if e.get("type") == "spell_cast"]
        assert len(spell_events) == 1
        assert spell_events[0]["spell"] == "fireball"
        assert spell_events[0]["hit_count"] == 1

    def test_execute_with_no_targets(self, action_factory, game_context):
        """Test Fireball with no targets in AOE."""
        # Cast near player but where there are no monsters
        action = action_factory.create("fireball", actor_id="player_1", x=12, y=12)
        outcome = action.execute(game_context)

        assert outcome.result == ActionResult.SUCCESS
        assert "harmlessly" in " ".join(game_context.game_state.messages).lower()

    def test_execute_takes_turn(self, action_factory, game_context):
        """Test that casting Fireball takes a turn."""
        action = action_factory.create("fireball", actor_id="player_1", x=12, y=12)
        outcome = action.execute(game_context)

        assert outcome.took_turn is True


class TestFireballEdgeCases:
    """Test edge cases and error handling."""

    def test_multiple_monsters_in_aoe(self, action_factory, game_context, game_state):
        """Test Fireball hitting multiple monsters."""
        # Create 3 monsters in AOE near player (10, 10)
        for i in range(3):
            monster = Entity(
                entity_id=f"m{i}",
                name=f"Monster{i}",
                entity_type=EntityType.MONSTER,
                x=12 + i,
                y=12,
                hp=30,
                max_hp=30,
                is_alive=True
            )
            game_state.entities[f"m{i}"] = monster

        action = action_factory.create("fireball", actor_id="player_1", x=12, y=12)
        outcome = action.execute(game_context)

        assert outcome.result == ActionResult.SUCCESS

        # Check all monsters were damaged
        for i in range(3):
            assert game_state.entities[f"m{i}"].hp == 15

        # Check hit count in events
        spell_events = [e for e in outcome.events if e.get("type") == "spell_cast"]
        assert spell_events[0]["hit_count"] == 3

    def test_fireball_on_edge_of_map(self, action_factory, game_context, game_state):
        """Test Fireball near map boundaries."""
        # Move player near edge
        game_state.player.x = 5
        game_state.player.y = 5

        # Cast near edge (but still in bounds and in range)
        action = action_factory.create("fireball", actor_id="player_1", x=7, y=7)
        outcome = action.execute(game_context)

        assert outcome.result == ActionResult.SUCCESS

    def test_validation_fails_invalid_target(self, action_factory, game_context):
        """Test validation fails for invalid coordinates."""
        # Out of bounds
        action = action_factory.create("fireball", actor_id="player_1", x=100, y=100)
        assert action.validate(game_context) is False
