"""
Test stairs pathfinding - debug why bot can't reach stairs.
"""

from core.game import Game
from core.pathfinding import find_path, get_direction

def test_bot_can_reach_stairs():
    """Test that bot can path from any position to stairs."""
    # Create a new game
    game = Game()
    game.start_new_game()

    # Get player position
    player_pos = (game.state.player.x, game.state.player.y)

    # Find stairs
    stairs_pos = game.state.dungeon_map.find_stairs_down()

    print(f"\nPlayer at: {player_pos}")
    print(f"Stairs at: {stairs_pos}")

    assert stairs_pos is not None, "Stairs not found on map!"

    # Check if stairs are walkable
    is_walkable = game.state.dungeon_map.is_walkable(*stairs_pos)
    print(f"Stairs walkable: {is_walkable}")
    assert is_walkable, "Stairs should be walkable!"

    # Try to find path
    path = find_path(game.state.dungeon_map, player_pos, stairs_pos)

    if path:
        print(f"Path found! Length: {len(path)}")
        print(f"First 5 steps: {path[:5]}")
    else:
        print("NO PATH FOUND!")
        # Debug: check if player position is walkable
        player_walkable = game.state.dungeon_map.is_walkable(*player_pos)
        print(f"Player position walkable: {player_walkable}")

        # Debug: try simple test
        test_path = find_path(game.state.dungeon_map, player_pos, (player_pos[0]+1, player_pos[1]))
        print(f"Can move one step right: {test_path is not None}")

    assert path is not None, f"Should find path from {player_pos} to {stairs_pos}"
    assert path[0] == player_pos
    assert path[-1] == stairs_pos

    # Test get_direction
    direction = get_direction(game.state.dungeon_map, player_pos, stairs_pos)
    print(f"Direction to stairs: {direction}")
    assert direction is not None


def test_pathfinding_to_stairs_after_clear():
    """Test pathfinding after clearing all monsters (bot's exact scenario)."""
    game = Game()
    game.start_new_game()

    # Kill all monsters
    monsters = list(game.state.entities.values())
    for monster in monsters:
        if monster.entity_id in game.state.entities:
            game.state.entities.pop(monster.entity_id)

    print(f"\nAll monsters cleared. Remaining entities: {len(game.state.entities)}")

    # Get positions
    player_pos = (game.state.player.x, game.state.player.y)
    stairs_pos = game.state.dungeon_map.find_stairs_down()

    print(f"Player at: {player_pos}")
    print(f"Stairs at: {stairs_pos}")

    # Try pathfinding
    path = find_path(game.state.dungeon_map, player_pos, stairs_pos)

    if not path:
        print("ERROR: No path to stairs after clearing floor!")
        # Detailed debugging
        print(f"Player pos in bounds: {game.state.dungeon_map.in_bounds(*player_pos)}")
        print(f"Player pos walkable: {game.state.dungeon_map.is_walkable(*player_pos)}")
        print(f"Stairs pos in bounds: {game.state.dungeon_map.in_bounds(*stairs_pos)}")
        print(f"Stairs pos walkable: {game.state.dungeon_map.is_walkable(*stairs_pos)}")

        # Check tile types
        player_tile = game.state.dungeon_map.tiles[player_pos[0]][player_pos[1]]
        stairs_tile = game.state.dungeon_map.tiles[stairs_pos[0]][stairs_pos[1]]
        print(f"Player tile: {player_tile.tile_type}")
        print(f"Stairs tile: {stairs_tile.tile_type}")

    assert path is not None
    print(f"Success! Path length: {len(path)}")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing stairs pathfinding")
    print("=" * 60)

    print("\n### Test 1: Basic pathfinding to stairs ###")
    test_bot_can_reach_stairs()

    print("\n### Test 2: Pathfinding after clearing floor ###")
    test_pathfinding_to_stairs_after_clear()

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
