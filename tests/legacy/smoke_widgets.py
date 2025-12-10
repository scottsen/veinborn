#!/usr/bin/env python3
"""
Test that widgets can be created without errors.
This is a non-TUI test - just creates objects.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("Testing Veinborn components...")
print("="*60)

try:
    print("1. Importing core.game...")
    from core.game import Game
    print("   ✓ Imported")

    print("2. Creating Game instance...")
    game = Game()
    print("   ✓ Created")

    print("3. Starting new game...")
    game.start_new_game()
    print(f"   ✓ Game started")
    print(f"   Player: ({game.state.player.x}, {game.state.player.y})")
    print(f"   Map: {game.state.map.width}x{game.state.map.height}")
    print(f"   Rooms: {len(game.state.map.rooms)}")
    print(f"   Monsters: {len(game.state.monsters)}")

    print("4. Importing Textual widgets...")
    from ui.textual.widgets import MapWidget, StatusBar, Sidebar
    from ui.textual.widgets.message_log import MessageLog
    print("   ✓ Imported")

    print("5. Creating MapWidget...")
    map_widget = MapWidget(game_state=game.state)
    print(f"   ✓ Created (viewport: {map_widget.viewport_width}x{map_widget.viewport_height})")

    print("6. Creating StatusBar...")
    status_bar = StatusBar(game_state=game.state)
    print("   ✓ Created")

    print("7. Creating Sidebar...")
    sidebar = Sidebar(game_state=game.state)
    print("   ✓ Created")

    print("8. Creating MessageLog...")
    message_log = MessageLog(game_state=game.state)
    print("   ✓ Created")

    print("9. Testing map rendering (non-TUI)...")
    # Try to call render_line
    try:
        from rich.console import Console
        from io import StringIO
        console = Console(file=StringIO(), force_terminal=True)
        line = map_widget.render_line(0)
        print(f"   ✓ render_line() works (returned Strip with {len(line.segments)} segments)")
    except Exception as e:
        print(f"   ⚠ render_line() failed: {e}")

    print("\n" + "="*60)
    print("✓ ALL COMPONENTS CREATED SUCCESSFULLY")
    print("="*60)
    print("\nComponents are working. Issue is likely:")
    print("  - Terminal compatibility (try different terminal)")
    print("  - Textual app.run() hanging")
    print("  - Terminal size too small")
    print("  - Display rendering issue")
    print("\nNext: Run python3 run_debug.py in separate window")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
