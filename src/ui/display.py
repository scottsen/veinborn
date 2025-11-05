"""
Terminal display system using Blessed library.
"""
try:
    from blessed import Terminal
except ImportError:
    print("Blessed library not installed. Run: pip install blessed")
    raise

from ..core.world import TileType


class MessageLog:
    """Message log for game events."""
    def __init__(self, height: int = 4):
        self.messages = []
        self.height = height

    def add(self, message: str):
        """Add a message to the log."""
        self.messages.append(message)
        if len(self.messages) > self.height:
            self.messages.pop(0)

    def draw(self, term, y_position: int):
        """Draw the message log."""
        for i, message in enumerate(self.messages):
            with term.location(0, y_position + i):
                print(term.clear_eol + message)


class Display:
    """Main display manager for Brogue."""

    # Unicode characters for display
    MAP_CHARS = {
        TileType.WALL: '█',
        TileType.FLOOR: '·',
        TileType.DOOR: '+',
        TileType.STAIRS_UP: '<',
        TileType.STAIRS_DOWN: '>',
        'player': '@',
        'rat': 'r',
        'goblin': 'g',
        'orc': 'o',
        'item': '*'
    }

    def __init__(self):
        self.term = Terminal()
        self.width = self.term.width
        self.height = self.term.height
        self.map_offset_x = 0
        self.map_offset_y = 1  # Leave room for status line

        # Color scheme
        self.colors = {
            'player': self.term.bright_yellow,
            'wall': self.term.white,
            'floor': self.term.dim,
            'monster': self.term.bright_red,
            'item': self.term.bright_blue,
            'ui': self.term.bright_green,
            'warning': self.term.bright_red
        }

    def check_terminal_size(self) -> bool:
        """Check if terminal is large enough."""
        min_width, min_height = 80, 24
        if self.term.height < min_height or self.term.width < min_width:
            print(f"Terminal too small! Need at least {min_width}x{min_height}")
            return False
        return True

    def run_game(self, game):
        """Main display loop."""
        if not self.check_terminal_size():
            return

        with self.term.fullscreen(), self.term.hidden_cursor(), self.term.cbreak():
            while game.running:
                self.draw_frame(game.state)

                # Handle input
                key = self.term.inkey(timeout=0.1)
                if key:
                    action = self.handle_input(key)
                    if action == 'quit':
                        game.running = False
                    elif action == 'restart':
                        game.restart_game()
                    elif isinstance(action, tuple):  # Movement
                        dx, dy = action
                        if game.handle_player_move(dx, dy):
                            game.process_turn()

    def draw_frame(self, game_state):
        """Draw the complete game frame."""
        # Clear screen
        print(self.term.home + self.term.clear)

        # Draw UI elements
        self.draw_status_line(game_state)
        self.draw_map(game_state)
        self.draw_sidebar(game_state)
        game_state.messages.draw(self.term, self.term.height - 4)

    def draw_status_line(self, game_state):
        """Draw the top status line."""
        player = game_state.player
        status_parts = [
            f"HP: {player.hp}/{player.max_hp}",
            f"Turn: {game_state.turn_count}",
            f"Pos: ({player.x}, {player.y})"
        ]

        if game_state.game_over:
            status_parts.append("GAME OVER")

        status_text = " | ".join(status_parts)

        with self.term.location(0, 0):
            print(self.colors['ui'] + status_text + self.term.normal)

    def draw_map(self, game_state):
        """Draw the game map."""
        player = game_state.player

        # Calculate viewport (simple for now - center on player)
        map_width = min(60, game_state.map.width)
        map_height = min(20, game_state.map.height)

        start_x = max(0, min(player.x - map_width // 2,
                           game_state.map.width - map_width))
        start_y = max(0, min(player.y - map_height // 2,
                           game_state.map.height - map_height))

        for y in range(map_height):
            world_y = start_y + y
            if world_y >= game_state.map.height:
                break

            with self.term.location(self.map_offset_x, self.map_offset_y + y):
                line = ""
                for x in range(map_width):
                    world_x = start_x + x
                    if world_x >= game_state.map.width:
                        break

                    char, color = self.get_tile_display(game_state, world_x, world_y)
                    line += color + char + self.term.normal

                print(line)

    def get_tile_display(self, game_state, x, y):
        """Get the character and color for a tile."""
        # Check for player
        if x == game_state.player.x and y == game_state.player.y:
            return self.MAP_CHARS['player'], self.colors['player']

        # Check for monsters
        for monster in game_state.monsters:
            if monster.x == x and monster.y == y:
                char = self.MAP_CHARS.get(monster.name.lower(), 'm')
                return char, self.colors['monster']

        # Get terrain
        if 0 <= x < game_state.map.width and 0 <= y < game_state.map.height:
            tile = game_state.map.tiles[x][y]
            char = self.MAP_CHARS.get(tile.tile_type, '?')

            if tile.tile_type == TileType.WALL:
                color = self.colors['wall']
            else:
                color = self.colors['floor']

            return char, color

        return ' ', self.term.normal

    def draw_sidebar(self, game_state):
        """Draw the right sidebar with game info."""
        sidebar_x = 65
        player = game_state.player

        # Player info
        with self.term.location(sidebar_x, 2):
            print(self.colors['ui'] + "=== PLAYER ===" + self.term.normal)

        with self.term.location(sidebar_x, 3):
            print(f"Health: {player.hp}/{player.max_hp}")

        with self.term.location(sidebar_x, 4):
            print(f"Attack: {player.attack}")

        with self.term.location(sidebar_x, 5):
            print(f"Defense: {player.defense}")

        # Monster info
        if game_state.monsters:
            with self.term.location(sidebar_x, 7):
                print(self.colors['ui'] + "=== MONSTERS ===" + self.term.normal)

            for i, monster in enumerate(game_state.monsters[:5]):  # Show up to 5
                with self.term.location(sidebar_x, 8 + i):
                    print(f"{monster.name}: {monster.hp}/{monster.max_hp}")

        # Controls
        with self.term.location(sidebar_x, 15):
            print(self.colors['ui'] + "=== CONTROLS ===" + self.term.normal)

        controls = [
            "Arrow keys: Move",
            "q: Quit",
            "r: Restart"
        ]

        for i, control in enumerate(controls):
            with self.term.location(sidebar_x, 16 + i):
                print(control)

    # Keyboard input mapping (cleaner than if/elif chains)
    KEY_MAP = {
        # Commands
        'q': 'quit',
        'r': 'restart',
        # Arrow keys
        'KEY_UP': (0, -1),
        'KEY_DOWN': (0, 1),
        'KEY_LEFT': (-1, 0),
        'KEY_RIGHT': (1, 0),
        # Vim keys (hjkl)
        'k': (0, -1),   # up
        'j': (0, 1),    # down
        'h': (-1, 0),   # left
        'l': (1, 0),    # right
        # Diagonal movement (yubn)
        'y': (-1, -1),  # up-left
        'u': (1, -1),   # up-right
        'b': (-1, 1),   # down-left
        'n': (1, 1),    # down-right
    }

    def handle_input(self, key):
        """Handle keyboard input using dictionary mapping."""
        # Try key.name first (for special keys like KEY_UP), then key itself
        key_str = getattr(key, 'name', None) or key
        return self.KEY_MAP.get(key_str, None)