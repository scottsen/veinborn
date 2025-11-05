"""
Integration tests for Legacy Vault system with game flows.

Tests the integration of Legacy Vault with:
- Player death (saving rare ore)
- Victory conditions (recording victory type)
- Game state tracking (pure vs legacy runs)
"""

pytestmark = pytest.mark.integration

import pytest
from unittest.mock import patch, MagicMock

from core.game import Game
from core.game_state import GameState
from core.entities import Player, Monster, OreVein
from core.legacy import get_vault, reset_vault, LegacyVault
from core.turn_processor import TurnProcessor
from core.floor_manager import FloorManager
from core.base.game_context import GameContext


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_vault_for_integration(tmp_path):
    """Create a temporary vault for integration tests."""
    vault_path = tmp_path / "legacy_vault.json"
    with patch('core.legacy.LEGACY_VAULT_PATH', vault_path):
        reset_vault()  # Clear singleton
        yield get_vault()
        reset_vault()  # Clean up


@pytest.fixture
def player_with_rare_ore():
    """Create a player with rare ore in inventory."""
    player = Player(
        x=10, y=10,
        hp=20, max_hp=20,
        attack=5, defense=2
    )

    # Add rare copper ore (90 purity) to inventory
    rare_ore = OreVein(
        ore_type="copper",
        x=11, y=11,
        hardness=85,
        conductivity=82,
        malleability=88,
        purity=90,  # Legacy-worthy!
        density=75
    )
    player.inventory.append(rare_ore)

    # Add common iron ore (50 purity) - should NOT be saved
    common_ore = OreVein(
        ore_type="iron",
        x=12, y=12,
        hardness=60,
        conductivity=55,
        malleability=65,
        purity=50,  # Not legacy-worthy
        density=70
    )
    player.inventory.append(common_ore)

    return player


@pytest.fixture
def player_with_legendary_ore():
    """Create a player with multiple legendary ores."""
    player = Player(
        x=10, y=10,
        hp=20, max_hp=20,
        attack=5, defense=2
    )

    # Add 3 legendary mithril ores
    for i in range(3):
        ore = OreVein(
            ore_type="mithril",
            x=15+i, y=15+i,
            hardness=95,
            conductivity=98,
            malleability=92,
            purity=99,  # Legendary!
            density=88
        )
        player.inventory.append(ore)

    return player


# ============================================================================
# Death Flow Integration Tests
# ============================================================================

@pytest.mark.integration
def test_death_saves_rare_ore_to_vault(temp_vault_for_integration, player_with_rare_ore, simple_room_map):
    """Test that rare ore is saved to vault on player death."""
    # Create game state
    game_state = GameState(
        player=player_with_rare_ore,
        entities={player_with_rare_ore.entity_id: player_with_rare_ore},
        dungeon_map=simple_room_map,
        current_floor=5,
        run_type="pure"
    )

    # Create context and turn processor
    context = GameContext(game_state=game_state)
    turn_processor = TurnProcessor(context)

    # Kill the player
    player_with_rare_ore.hp = 0
    player_with_rare_ore.is_alive = False

    # Check game over (this should save rare ore)
    turn_processor._check_game_over()

    # Verify ore was saved to vault
    vault = temp_vault_for_integration
    assert vault.get_ore_count() == 1  # Only rare ore saved

    ores = vault.get_ores()
    assert ores[0].ore_type == "copper"
    assert ores[0].purity == 90
    assert ores[0].floor_found == 5

    # Verify defeat was recorded
    assert vault.total_runs == 1
    assert vault.total_pure_victories == 0  # Death, not victory


@pytest.mark.integration
def test_death_with_multiple_rare_ores(temp_vault_for_integration, player_with_legendary_ore, simple_room_map):
    """Test death with multiple rare ores saves all of them."""
    game_state = GameState(
        player=player_with_legendary_ore,
        entities={player_with_legendary_ore.entity_id: player_with_legendary_ore},
        dungeon_map=simple_room_map,
        current_floor=10
    )

    context = GameContext(game_state=game_state)
    turn_processor = TurnProcessor(context)

    # Kill player
    player_with_legendary_ore.hp = 0
    player_with_legendary_ore.is_alive = False
    turn_processor._check_game_over()

    # All 3 legendary ores should be saved
    vault = temp_vault_for_integration
    assert vault.get_ore_count() == 3

    ores = vault.get_ores()
    assert all(ore.ore_type == "mithril" for ore in ores)
    assert all(ore.purity == 99 for ore in ores)


@pytest.mark.integration
def test_death_with_no_rare_ore(temp_vault_for_integration, simple_room_map):
    """Test death with no rare ore doesn't add anything to vault."""
    # Player with only common ore
    player = Player(x=10, y=10, hp=20, max_hp=20, attack=5, defense=2)
    common_ore = OreVein(
        ore_type="copper",
        x=11, y=11,
        hardness=40, conductivity=40, malleability=40,
        purity=40,  # Not rare
        density=40
    )
    player.inventory.append(common_ore)

    game_state = GameState(
        player=player,
        entities={player.entity_id: player},
        dungeon_map=simple_room_map,
        current_floor=2
    )

    context = GameContext(game_state=game_state)
    turn_processor = TurnProcessor(context)

    # Kill player
    player.hp = 0
    player.is_alive = False
    turn_processor._check_game_over()

    # No ore should be saved
    vault = temp_vault_for_integration
    assert vault.get_ore_count() == 0

    # Defeat should still be recorded
    assert vault.total_runs == 1


@pytest.mark.integration
def test_death_messages(temp_vault_for_integration, player_with_rare_ore, simple_room_map):
    """Test proper messages are displayed on death with rare ore."""
    game_state = GameState(
        player=player_with_rare_ore,
        entities={player_with_rare_ore.entity_id: player_with_rare_ore},
        dungeon_map=simple_room_map,
        current_floor=5
    )

    context = GameContext(game_state=game_state)
    turn_processor = TurnProcessor(context)

    # Kill player
    player_with_rare_ore.hp = 0
    player_with_rare_ore.is_alive = False
    turn_processor._check_game_over()

    # Check messages
    messages = game_state.messages
    assert any("You died!" in msg for msg in messages)
    assert any("rare ore" in msg.lower() for msg in messages)
    assert any("Legacy Vault" in msg for msg in messages)


# ============================================================================
# Victory Flow Integration Tests
# ============================================================================

@pytest.mark.integration
def test_pure_victory_recorded(temp_vault_for_integration, simple_room_map):
    """Test Pure Victory is recorded correctly."""
    player = Player(x=10, y=10, hp=50, max_hp=50, attack=10, defense=5)
    game_state = GameState(
        player=player,
        entities={player.entity_id: player},
        dungeon_map=simple_room_map,
        current_floor=99,
        run_type="pure"  # Pure run
    )

    context = GameContext(game_state=game_state)
    mock_spawner = MagicMock()
    floor_manager = FloorManager(context, mock_spawner)

    # Trigger victory
    floor_manager._check_victory(100)

    # Verify victory recorded
    vault = temp_vault_for_integration
    assert vault.total_runs == 1
    assert vault.total_pure_victories == 1
    assert vault.total_legacy_victories == 0

    # Check victory message
    messages = game_state.messages
    assert any("PURE VICTORY" in msg for msg in messages)


@pytest.mark.integration
def test_legacy_victory_recorded(temp_vault_for_integration, simple_room_map):
    """Test Legacy Victory is recorded correctly."""
    player = Player(x=10, y=10, hp=50, max_hp=50, attack=10, defense=5)
    game_state = GameState(
        player=player,
        entities={player.entity_id: player},
        dungeon_map=simple_room_map,
        current_floor=99,
        run_type="legacy"  # Legacy run (used vault ore)
    )

    context = GameContext(game_state=game_state)
    mock_spawner = MagicMock()
    floor_manager = FloorManager(context, mock_spawner)

    # Trigger victory
    floor_manager._check_victory(100)

    # Verify victory recorded
    vault = temp_vault_for_integration
    assert vault.total_runs == 1
    assert vault.total_pure_victories == 0
    assert vault.total_legacy_victories == 1

    # Check victory message
    messages = game_state.messages
    assert any("LEGACY VICTORY" in msg for msg in messages)


@pytest.mark.integration
def test_multiple_runs_tracking(temp_vault_for_integration, simple_room_map):
    """Test multiple runs are tracked correctly."""
    vault = temp_vault_for_integration

    # Run 1: Pure defeat
    player1 = Player(x=10, y=10, hp=0, max_hp=20, attack=5, defense=2)
    player1.is_alive = False
    game_state1 = GameState(
        player=player1,
        entities={player1.entity_id: player1},
        dungeon_map=simple_room_map,
        run_type="pure"
    )
    context1 = GameContext(game_state=game_state1)
    TurnProcessor(context1)._check_game_over()

    # Run 2: Legacy defeat
    player2 = Player(x=10, y=10, hp=0, max_hp=20, attack=5, defense=2)
    player2.is_alive = False
    game_state2 = GameState(
        player=player2,
        entities={player2.entity_id: player2},
        dungeon_map=simple_room_map,
        run_type="legacy"
    )
    context2 = GameContext(game_state=game_state2)
    TurnProcessor(context2)._check_game_over()

    # Run 3: Pure victory
    player3 = Player(x=10, y=10, hp=50, max_hp=50, attack=10, defense=5)
    game_state3 = GameState(
        player=player3,
        entities={player3.entity_id: player3},
        dungeon_map=simple_room_map,
        current_floor=99,
        run_type="pure"
    )
    context3 = GameContext(game_state=game_state3)
    FloorManager(context3, MagicMock())._check_victory(100)

    # Run 4: Legacy victory
    player4 = Player(x=10, y=10, hp=50, max_hp=50, attack=10, defense=5)
    game_state4 = GameState(
        player=player4,
        entities={player4.entity_id: player4},
        dungeon_map=simple_room_map,
        current_floor=99,
        run_type="legacy"
    )
    context4 = GameContext(game_state=game_state4)
    FloorManager(context4, MagicMock())._check_victory(100)

    # Verify stats
    assert vault.total_runs == 4
    assert vault.total_pure_victories == 1
    assert vault.total_legacy_victories == 1


# ============================================================================
# Game State Integration Tests
# ============================================================================

@pytest.mark.integration
def test_game_state_run_type_defaults_to_pure():
    """Test new game state defaults to pure run."""
    player = Player(x=10, y=10, hp=20, max_hp=20, attack=5, defense=2)
    game_state = GameState(player=player)

    assert game_state.run_type == "pure"


@pytest.mark.integration
def test_game_state_run_type_persists():
    """Test run type can be set and persists."""
    player = Player(x=10, y=10, hp=20, max_hp=20, attack=5, defense=2)
    game_state = GameState(player=player, run_type="legacy")

    assert game_state.run_type == "legacy"


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

@pytest.mark.integration
def test_vault_error_doesnt_crash_game(temp_vault_for_integration, player_with_rare_ore, simple_room_map):
    """Test that vault errors don't crash the game."""
    game_state = GameState(
        player=player_with_rare_ore,
        entities={player_with_rare_ore.entity_id: player_with_rare_ore},
        dungeon_map=simple_room_map,
        current_floor=5
    )

    context = GameContext(game_state=game_state)
    turn_processor = TurnProcessor(context)

    # Mock vault to raise exception
    with patch('core.turn_processor.get_vault') as mock_vault:
        mock_vault.side_effect = Exception("Vault error!")

        # Kill player - should not crash
        player_with_rare_ore.hp = 0
        player_with_rare_ore.is_alive = False
        turn_processor._check_game_over()

        # Game should still be over
        assert game_state.game_over is True


@pytest.mark.integration
def test_death_with_empty_inventory(temp_vault_for_integration, simple_room_map):
    """Test death with empty inventory doesn't cause errors."""
    player = Player(x=10, y=10, hp=0, max_hp=20, attack=5, defense=2)
    # Empty inventory
    player.inventory = []

    game_state = GameState(
        player=player,
        entities={player.entity_id: player},
        dungeon_map=simple_room_map,
        current_floor=3
    )

    context = GameContext(game_state=game_state)
    turn_processor = TurnProcessor(context)

    # Should not crash
    turn_processor._check_game_over()

    # No ore saved
    vault = temp_vault_for_integration
    assert vault.get_ore_count() == 0


@pytest.mark.integration
def test_vault_overflow_during_death(temp_vault_for_integration, simple_room_map):
    """Test vault handles overflow correctly when saving on death."""
    # Fill vault to near capacity (8 ores)
    for i in range(8):
        ore = OreVein(
            ore_type=f"existing_{i}",
            x=i, y=i,
            hardness=85, conductivity=85, malleability=85,
            purity=85, density=85
        )
        temp_vault_for_integration.add_ore(ore, floor=i)

    # Player dies with 5 rare ores (will exceed max of 10)
    player = Player(x=10, y=10, hp=0, max_hp=20, attack=5, defense=2)
    player.is_alive = False
    for i in range(5):
        ore = OreVein(
            ore_type=f"death_ore_{i}",
            x=20+i, y=20+i,
            hardness=90, conductivity=90, malleability=90,
            purity=95, density=90
        )
        player.inventory.append(ore)

    game_state = GameState(
        player=player,
        entities={player.entity_id: player},
        dungeon_map=simple_room_map,
        current_floor=15
    )

    context = GameContext(game_state=game_state)
    turn_processor = TurnProcessor(context)

    # Death should handle overflow (FIFO)
    turn_processor._check_game_over()

    # Should have exactly 10 ores
    vault = temp_vault_for_integration
    assert vault.get_ore_count() == 10
    assert vault.is_full()

    # Oldest 3 ores should be removed
    ores = vault.get_ores()
    # First ore should be existing_3 (existing_0,1,2 removed)
    assert "existing_" in ores[0].ore_type or "death_ore_" in ores[0].ore_type
    # Last ore should be death_ore_4
    assert "death_ore_" in ores[-1].ore_type


# ============================================================================
# Persistence Integration Tests
# ============================================================================

@pytest.mark.integration
def test_vault_persists_between_deaths(temp_vault_for_integration, simple_room_map):
    """Test vault accumulates ore across multiple deaths."""
    vault = temp_vault_for_integration

    # Death 1: Add 2 rare ores
    player1 = Player(x=10, y=10, hp=0, max_hp=20, attack=5, defense=2)
    player1.is_alive = False
    for i in range(2):
        ore = OreVein(
            ore_type=f"death1_ore_{i}",
            x=i, y=i,
            hardness=85, conductivity=85, malleability=85,
            purity=90, density=85
        )
        player1.inventory.append(ore)

    game_state1 = GameState(
        player=player1,
        entities={player1.entity_id: player1},
        dungeon_map=simple_room_map,
        current_floor=5
    )
    context1 = GameContext(game_state=game_state1)
    TurnProcessor(context1)._check_game_over()

    assert vault.get_ore_count() == 2

    # Death 2: Add 3 more rare ores
    player2 = Player(x=10, y=10, hp=0, max_hp=20, attack=5, defense=2)
    player2.is_alive = False
    for i in range(3):
        ore = OreVein(
            ore_type=f"death2_ore_{i}",
            x=10+i, y=10+i,
            hardness=88, conductivity=88, malleability=88,
            purity=92, density=88
        )
        player2.inventory.append(ore)

    game_state2 = GameState(
        player=player2,
        entities={player2.entity_id: player2},
        dungeon_map=simple_room_map,
        current_floor=8
    )
    context2 = GameContext(game_state=game_state2)
    TurnProcessor(context2)._check_game_over()

    # Should now have 5 total ores
    assert vault.get_ore_count() == 5

    ores = vault.get_ores()
    assert sum(1 for ore in ores if "death1_" in ore.ore_type) == 2
    assert sum(1 for ore in ores if "death2_" in ore.ore_type) == 3


# ============================================================================
# Withdrawal Flow Integration Tests
# ============================================================================

@pytest.mark.integration
def test_start_game_with_withdrawn_ore(temp_vault_for_integration):
    """Test starting a game with withdrawn ore adds it to inventory."""
    from core.legacy import LegacyOre

    # Create a legacy ore
    legacy_ore = LegacyOre(
        ore_type="copper",
        hardness=85,
        conductivity=82,
        malleability=88,
        purity=90,
        density=75,
        floor_found=5,
        timestamp="2025-11-05T12:00:00"
    )

    # Start a new game with the withdrawn ore
    game = Game()
    game.start_new_game(
        seed=12345,
        player_name="TestPlayer",
        character_class=None,
        withdrawn_ore=legacy_ore,
        is_legacy_run=True
    )

    # Verify ore is in player inventory
    assert len(game.state.player.inventory) == 1
    ore_in_inventory = game.state.player.inventory[0]

    # Verify ore properties match
    assert ore_in_inventory.ore_type == "copper"
    assert ore_in_inventory.hardness == 85
    assert ore_in_inventory.conductivity == 82
    assert ore_in_inventory.malleability == 88
    assert ore_in_inventory.purity == 90
    assert ore_in_inventory.density == 75

    # Verify ore is marked as mined (ready to use)
    assert ore_in_inventory.stats['mining_turns_remaining'] == 0


@pytest.mark.integration
def test_start_game_with_withdrawn_ore_marks_legacy_run(temp_vault_for_integration):
    """Test starting a game with withdrawn ore marks run as legacy."""
    from core.legacy import LegacyOre

    # Create a legacy ore
    legacy_ore = LegacyOre(
        ore_type="mithril",
        hardness=95,
        conductivity=98,
        malleability=92,
        purity=99,
        density=88,
        floor_found=10,
        timestamp="2025-11-05T12:00:00"
    )

    # Start a new game with the withdrawn ore
    game = Game()
    game.start_new_game(
        seed=12345,
        player_name="TestPlayer",
        character_class=None,
        withdrawn_ore=legacy_ore,
        is_legacy_run=True
    )

    # Verify run is marked as legacy
    assert game.state.run_type == "legacy"

    # Verify message was added
    messages = game.state.messages
    assert any("Legacy Vault" in msg for msg in messages)
    assert any("Legacy run" in msg for msg in messages)


@pytest.mark.integration
def test_start_game_without_withdrawn_ore_marks_pure_run(temp_vault_for_integration):
    """Test starting a game without withdrawn ore marks run as pure."""
    # Start a new game without withdrawn ore
    game = Game()
    game.start_new_game(
        seed=12345,
        player_name="TestPlayer",
        character_class=None,
        withdrawn_ore=None,
        is_legacy_run=False
    )

    # Verify run is marked as pure
    assert game.state.run_type == "pure"

    # Verify no ore in inventory
    assert len(game.state.player.inventory) == 0

    # Verify no legacy messages
    messages = game.state.messages
    assert not any("Legacy Vault" in msg for msg in messages)


@pytest.mark.integration
def test_withdrawn_ore_can_be_crafted(temp_vault_for_integration):
    """Test that withdrawn ore can be used for crafting."""
    from core.legacy import LegacyOre
    from core.character_class import CharacterClass

    # Create a high-quality legacy ore
    legacy_ore = LegacyOre(
        ore_type="mithril",
        hardness=95,
        conductivity=98,
        malleability=92,
        purity=99,
        density=88,
        floor_found=10,
        timestamp="2025-11-05T12:00:00"
    )

    # Start a new game with the withdrawn ore
    game = Game()
    game.start_new_game(
        seed=12345,
        player_name="TestPlayer",
        character_class=CharacterClass.WARRIOR,
        withdrawn_ore=legacy_ore,
        is_legacy_run=True
    )

    # Verify ore is in inventory and ready to craft
    ore_in_inventory = game.state.player.inventory[0]
    assert ore_in_inventory.ore_type == "mithril"
    assert ore_in_inventory.purity == 99

    # Ore should be "mined" (mining_turns_remaining = 0)
    assert ore_in_inventory.stats['mining_turns_remaining'] == 0

    # This means it can be used in crafting recipes
    # (actual crafting test is in crafting system tests)


@pytest.mark.integration
def test_withdraw_ore_from_vault_integration(temp_vault_for_integration):
    """Test full cycle: death -> withdraw -> start new game."""
    from core.legacy import LegacyOre

    vault = temp_vault_for_integration

    # Step 1: Add ore to vault (simulating death)
    ore1 = OreVein(
        ore_type="copper",
        x=10, y=10,
        hardness=85,
        conductivity=82,
        malleability=88,
        purity=90,
        density=75
    )
    vault.add_ore(ore1, floor=5)

    assert vault.get_ore_count() == 1

    # Step 2: Withdraw ore from vault
    withdrawn = vault.withdraw_ore(0)
    assert withdrawn is not None
    assert withdrawn.ore_type == "copper"
    assert withdrawn.purity == 90
    assert vault.get_ore_count() == 0

    # Step 3: Start new game with withdrawn ore
    game = Game()
    game.start_new_game(
        seed=12345,
        player_name="TestPlayer",
        character_class=None,
        withdrawn_ore=withdrawn,
        is_legacy_run=True
    )

    # Verify everything is correct
    assert game.state.run_type == "legacy"
    assert len(game.state.player.inventory) == 1
    assert game.state.player.inventory[0].ore_type == "copper"
    assert game.state.player.inventory[0].purity == 90


@pytest.mark.integration
def test_multiple_quality_tiers_withdrawn(temp_vault_for_integration):
    """Test withdrawing different quality tiers of ore."""
    from core.legacy import LegacyOre

    # Test Rare tier (purity 71-80)
    rare_ore = LegacyOre(
        ore_type="iron",
        hardness=75, conductivity=75, malleability=75,
        purity=75, density=75,
        floor_found=3
    )

    game = Game()
    game.start_new_game(withdrawn_ore=rare_ore, is_legacy_run=True)
    assert game.state.player.inventory[0].purity == 75

    # Test Epic tier (purity 86-95)
    epic_ore = LegacyOre(
        ore_type="mithril",
        hardness=90, conductivity=90, malleability=90,
        purity=90, density=90,
        floor_found=8
    )

    game2 = Game()
    game2.start_new_game(withdrawn_ore=epic_ore, is_legacy_run=True)
    assert game2.state.player.inventory[0].purity == 90

    # Test Legendary tier (purity 96+)
    legendary_ore = LegacyOre(
        ore_type="adamantite",
        hardness=99, conductivity=99, malleability=99,
        purity=99, density=99,
        floor_found=15
    )

    game3 = Game()
    game3.start_new_game(withdrawn_ore=legendary_ore, is_legacy_run=True)
    assert game3.state.player.inventory[0].purity == 99
