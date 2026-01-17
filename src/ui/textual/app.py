"""Main Textual application for Veinborn."""
import atexit
import logging
import signal
import sys
from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding

from core.game import Game
from core.base.entity import EntityType
from core.config.user_config import ConfigManager
from ui.textual.widgets import MapWidget, StatusBar, Sidebar, InventoryWidget, ChatInput
from ui.textual.widgets.message_log import MessageLog

# Setup logging
logger = logging.getLogger('veinborn.app')


def _restore_terminal():
    """Restore terminal to normal state on exit.

    This is a safety measure to ensure the terminal is properly restored
    if the app crashes or exits abnormally.

    Sends ANSI escape sequences to:
    - Disable mouse tracking modes
    - Exit alternate screen buffer (restores scrollback)
    - Show cursor
    - Reset terminal attributes
    """
    try:
        # Disable mouse tracking
        sys.stdout.write('\033[?1000l')  # Disable normal tracking
        sys.stdout.write('\033[?1002l')  # Disable button event tracking
        sys.stdout.write('\033[?1003l')  # Disable any event tracking
        sys.stdout.write('\033[?1006l')  # Disable SGR extended mode

        # Exit alternate screen buffer (critical for scrollback restoration)
        sys.stdout.write('\033[?1049l')  # Exit alternate screen, restore cursor position

        # Show cursor (in case it was hidden)
        sys.stdout.write('\033[?25h')

        # Reset terminal attributes
        sys.stdout.write('\033[0m')

        sys.stdout.flush()
        logger.debug("Restored terminal state on exit")
    except Exception as e:
        # Don't crash on cleanup failure
        logger.warning(f"Failed to restore terminal: {e}")


# Register cleanup handler to run on normal exit
atexit.register(_restore_terminal)


def _signal_handler(signum, frame):
    """Handle interrupt signals (Ctrl+C) to clean up before exit."""
    logger.info(f"Received signal {signum}, cleaning up...")
    _restore_terminal()
    sys.exit(0)


# Register signal handlers for clean interrupt
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


def _find_layout_file(layout_name: str) -> Path:
    """
    Find layout .tcss file by name.

    Search priority:
    1. ~/.config/veinborn/{layout}.tcss (user override)
    2. <project_root>/data/ui/layouts/{layout}.tcss (built-in)

    Args:
        layout_name: Layout name (without .tcss extension)

    Returns:
        Path to layout file

    Raises:
        FileNotFoundError: If layout file not found
    """
    # User override location
    user_config_dir = Path.home() / ".config" / "veinborn"
    user_layout = user_config_dir / f"{layout_name}.tcss"
    if user_layout.exists():
        logger.info(f"Using user layout: {user_layout}")
        return user_layout

    # Built-in layouts (relative to project root)
    # Get project root: src/ui/textual/app.py -> ../../.. -> project_root
    project_root = Path(__file__).parent.parent.parent.parent
    builtin_layout = project_root / "data" / "ui" / "layouts" / f"{layout_name}.tcss"
    if builtin_layout.exists():
        logger.info(f"Using built-in layout: {builtin_layout}")
        return builtin_layout

    # Fallback to default if specified layout not found
    if layout_name != "default":
        logger.warning(f"Layout '{layout_name}' not found, falling back to default")
        default_layout = project_root / "data" / "ui" / "layouts" / "default.tcss"
        if default_layout.exists():
            return default_layout

    raise FileNotFoundError(
        f"Layout '{layout_name}' not found. "
        f"Checked: {user_layout}, {builtin_layout}"
    )


class VeinbornApp(App):
    """Textual-based Veinborn game application."""

    # CSS_PATH is set dynamically in __init__ based on config (data/ui/layouts/*.tcss)

    # Disable mouse tracking - keyboard-only roguelike
    # Prevents terminal getting stuck in mouse mode if app crashes
    ENABLE_MOUSE = False

    BINDINGS = [
        # Arrow keys
        Binding("up", "move(0,-1)", "Move Up", show=False),
        Binding("down", "move(0,1)", "Move Down", show=False),
        Binding("left", "move(-1,0)", "Move Left", show=False),
        Binding("right", "move(1,0)", "Move Right", show=False),
        # Vim keys
        Binding("k", "move(0,-1)", "Move Up", show=False),
        Binding("j", "move(0,1)", "Move Down", show=False),
        Binding("h", "move(-1,0)", "Move Left", show=False),
        Binding("l", "move(1,0)", "Move Right", show=False),
        # Diagonal movement
        Binding("y", "move(-1,-1)", "Move Up-Left", show=False),
        Binding("u", "move(1,-1)", "Move Up-Right", show=False),
        Binding("b", "move(-1,1)", "Move Down-Left", show=False),
        Binding("n", "move(1,1)", "Move Down-Right", show=False),
        # Mining actions
        Binding("s", "survey", "Survey Ore", show=True),
        # Inventory and inspection
        Binding("i", "show_inventory", "Show Inventory", show=True),
        Binding("w", "equip_item", "Wield/Wear Item", show=True),
        Binding("W", "cycle_equip", "Cycle Equipment", show=False),
        Binding("g", "pickup", "Pick up Items", show=True),
        Binding(":", "look_at_ground", "Look at Ground", show=True),
        # Wait/Pass turn
        Binding(".", "wait", "Wait/Pass Turn", show=True),
        Binding("space", "wait", "Wait/Pass Turn", show=False),
        # Stairs
        Binding(">", "descend", "Descend Stairs (>)", show=True),
        # Chat (multiplayer)
        Binding("c", "chat", "Chat", show=True),
        Binding("enter", "chat", "Chat", show=False),
        # Save/Load
        Binding("S", "save_game", "Save Game", show=True),
        Binding("L", "load_game", "Load Game", show=True),
        # Game controls
        Binding("r", "restart", "Restart", show=True),
        Binding("q", "quit", "Quit", show=True),
        # Debug
        Binding("D", "debug_ui", "Debug UI", show=False),
    ]

    TITLE = "Veinborn: Walking in Big Brother's Footsteps"

    def __init__(self, player_name=None, character_class=None, seed=None, withdrawn_ore=None, is_legacy_run=False, multiplayer_client=None):
        """
        Initialize Veinborn app.

        Args:
            player_name: Player name (for high scores)
            character_class: CharacterClass enum (for starting stats)
            seed: Game seed (for reproducibility)
            withdrawn_ore: LegacyOre from vault (optional)
            is_legacy_run: Whether this is a legacy run (used vault ore)
            multiplayer_client: Optional MultiplayerClient for multiplayer games
        """
        logger.info("VeinbornApp.__init__() starting")

        # Load layout from config before calling super().__init__()
        config = ConfigManager.get_instance()
        self.layout_name = config.get('ui.layout', 'default')
        try:
            layout_file = _find_layout_file(self.layout_name)
            self.CSS_PATH = str(layout_file)
            logger.info(f"  Loaded layout: {self.layout_name} from {layout_file}")
        except FileNotFoundError as e:
            logger.error(f"  Layout error: {e}. Using widget DEFAULT_CSS.")
            # CSS_PATH will remain unset, widgets will use DEFAULT_CSS

        super().__init__()
        logger.info("  Creating Game instance...")
        self.game = Game()
        logger.info("  Game instance created")

        # Store player configuration for game start
        self.player_name = player_name or "Anonymous"
        self.character_class = character_class
        self.seed = seed
        self.withdrawn_ore = withdrawn_ore
        self.is_legacy_run = is_legacy_run

        # Multiplayer support
        self.multiplayer_client = multiplayer_client
        self.is_multiplayer = multiplayer_client is not None

        self.map_widget = None
        self.status_bar = None
        self.sidebar = None
        self.inventory_widget = None
        self.message_log = None
        self.chat_input = None

        # Equipment cycling state
        self.equip_index = 0  # Track which item to equip when cycling

        logger.info("VeinbornApp.__init__() complete")

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        logger.info("compose() starting")

        # Initialize game with player configuration
        logger.info(f"  Starting new game (Player: {self.player_name}, Class: {self.character_class}, Seed: {self.seed}, Legacy: {self.is_legacy_run})...")
        self.game.start_new_game(
            seed=self.seed,
            player_name=self.player_name,
            character_class=self.character_class,
            withdrawn_ore=self.withdrawn_ore,
            is_legacy_run=self.is_legacy_run
        )
        logger.info(f"  Game started: player at ({self.game.state.player.x}, {self.game.state.player.y})")
        logger.info(f"  Map size: {self.game.state.dungeon_map.width}x{self.game.state.dungeon_map.height}")
        logger.info(f"  Entities: {len(self.game.state.entities)}")

        # Create widgets with game state
        logger.info("  Creating StatusBar...")
        self.status_bar = StatusBar(game_state=self.game.state)
        logger.info("  Creating MapWidget...")
        self.map_widget = MapWidget(game_state=self.game.state)
        logger.info("  Creating Sidebar...")
        self.sidebar = Sidebar(game_state=self.game.state, layout_name=self.layout_name)
        logger.info("  Creating InventoryWidget...")
        self.inventory_widget = InventoryWidget(game_state=self.game.state)
        logger.info("  Creating MessageLog...")
        self.message_log = MessageLog(game_state=self.game.state)
        logger.info("  Creating ChatInput...")
        self.chat_input = ChatInput()

        # Yield widgets
        logger.info("  Yielding widgets...")
        yield self.status_bar
        yield self.inventory_widget  # Bottom of right panel
        yield self.sidebar  # Top of right panel (stacks from bottom up)
        yield self.map_widget
        yield self.message_log
        yield self.chat_input  # Chat input overlays on top
        logger.info("compose() complete")

    async def action_move(self, dx: int, dy: int) -> None:
        """Handle player movement (async Textual handler)."""
        if self.game.state.game_over:
            return

        # Call synchronous game logic
        self.game.handle_player_action('move', dx=dx, dy=dy)

        # Update all widgets (async)
        self.refresh_ui()

    async def action_survey(self) -> None:
        """Survey adjacent ore vein (async Textual handler)."""
        if self.game.state.game_over:
            return

        # Call synchronous game logic
        self.game.handle_player_action('survey')

        # Update all widgets
        self.refresh_ui()

    async def action_descend(self) -> None:
        """Descend stairs to next floor (async Textual handler)."""
        if self.game.state.game_over:
            return

        # Call synchronous game logic
        self.game.handle_player_action('descend')

        # Update all widgets
        self.refresh_ui()

    async def action_wait(self) -> None:
        """Wait/pass turn (async Textual handler)."""
        if self.game.state.game_over:
            return

        # Call synchronous game logic (wait action processes turn)
        self.game.handle_player_action('wait')

        # Update all widgets
        self.refresh_ui()

    async def action_show_inventory(self) -> None:
        """Display full inventory list in message log."""
        if self.game.state.game_over:
            return

        player = self.game.state.player
        inventory = player.inventory

        if not inventory:
            self.game.state.add_message("Your inventory is empty.")
        else:
            self.game.state.add_message(f"=== Full Inventory ({len(inventory)}/{player.get_stat('inventory_capacity', 20)} items) ===")
            for idx, item in enumerate(inventory, 1):
                item_type = item.get_stat('item_type', 'unknown')
                self.game.state.add_message(f"  {idx}. {item.name} ({item_type})")
            self.game.state.add_message("========================================")

        self.refresh_ui()

    async def action_pickup(self) -> None:
        """Pick up items from the ground (async Textual handler)."""
        if self.game.state.game_over:
            return

        # Call synchronous game logic
        self.game.handle_player_action('pickup')

        # Update all widgets
        self.refresh_ui()

    async def action_equip_item(self) -> None:
        """Equip an item from inventory (async Textual handler)."""
        if self.game.state.game_over:
            return

        player = self.game.state.player

        # Find equippable items (weapons and armor)
        equippable = []
        for item in player.inventory:
            # Check equipment_slot first, fallback to item_type
            slot = item.get_stat('equipment_slot') or item.get_stat('item_type')
            if slot in ['weapon', 'armor']:
                equippable.append((item, slot))

        if not equippable:
            self.game.state.add_message("You have no weapons or armor to equip!")
            self.refresh_ui()
            return

        # Reset equip index when starting fresh
        self.equip_index = 0

        # Show all equippable items
        self.game.state.add_message("=== Equippable Items ===")
        for idx, (item, slot) in enumerate(equippable, 1):
            bonus_stat = 'attack_bonus' if slot == 'weapon' else 'defense_bonus'
            bonus_val = item.get_stat(bonus_stat, 0)
            stat_name = 'attack' if slot == 'weapon' else 'defense'
            marker = "→" if idx == 1 else " "
            self.game.state.add_message(f"{marker} {idx}. {item.name} ({slot}, +{bonus_val} {stat_name})")
        self.game.state.add_message("===================")

        # Equip the current item
        item, slot = equippable[self.equip_index]
        self.game.state.add_message(f"Equipping {item.name}... (Press 'W' to cycle)")

        # Call synchronous game logic
        self.game.handle_player_action('equip', item_id=item.entity_id)

        # Update all widgets
        self.refresh_ui()

    async def action_cycle_equip(self) -> None:
        """Cycle through equippable items (Shift+W)."""
        if self.game.state.game_over:
            return

        player = self.game.state.player

        # Find equippable items
        equippable = []
        for item in player.inventory:
            # Check equipment_slot first, fallback to item_type
            slot = item.get_stat('equipment_slot') or item.get_stat('item_type')
            if slot in ['weapon', 'armor']:
                equippable.append((item, slot))

        if not equippable:
            self.game.state.add_message("You have no weapons or armor to equip!")
            self.refresh_ui()
            return

        # Cycle to next item
        self.equip_index = (self.equip_index + 1) % len(equippable)

        # Show all equippable items with arrow on current
        self.game.state.add_message("=== Equippable Items ===")
        for idx, (item, slot) in enumerate(equippable):
            bonus_stat = 'attack_bonus' if slot == 'weapon' else 'defense_bonus'
            bonus_val = item.get_stat(bonus_stat, 0)
            stat_name = 'attack' if slot == 'weapon' else 'defense'
            marker = "→" if idx == self.equip_index else " "
            self.game.state.add_message(f"{marker} {idx+1}. {item.name} ({slot}, +{bonus_val} {stat_name})")
        self.game.state.add_message("===================")

        # Equip the selected item
        item, slot = equippable[self.equip_index]
        self.game.state.add_message(f"Equipping {item.name}...")

        # Call synchronous game logic
        self.game.handle_player_action('equip', item_id=item.entity_id)

        # Update all widgets
        self.refresh_ui()

    async def action_look_at_ground(self) -> None:
        """Look at items on the ground at player's position."""
        if self.game.state.game_over:
            return

        player = self.game.state.player

        # Find items at player's position
        items_here = [
            e for e in self.game.state.entities.values()
            if e.entity_type == EntityType.ITEM and e.x == player.x and e.y == player.y and e.is_alive
        ]

        if not items_here:
            self.game.state.add_message("There are no items on the ground here.")
        else:
            self.game.state.add_message(f"=== Items on the ground ({len(items_here)}) ===")
            for item in items_here:
                item_type = item.get_stat('item_type', 'unknown')
                self.game.state.add_message(f"  - {item.name} ({item_type})")
            self.game.state.add_message("==============================")

        self.refresh_ui()

    async def action_save_game(self) -> None:
        """Save the game (async Textual handler)."""
        if self.game.state.game_over:
            return

        success = self.game.save_game()
        if success:
            logger.info("Game saved successfully")
        else:
            logger.error("Failed to save game")

        self.refresh_ui()

    async def action_load_game(self) -> None:
        """Load the game (async Textual handler)."""
        success = self.game.load_game()
        if success:
            logger.info("Game loaded successfully")
            # Update widgets to use new game state
            if self.map_widget:
                self.map_widget.game_state = self.game.state
            if self.status_bar:
                self.status_bar.game_state = self.game.state
            if self.sidebar:
                self.sidebar.game_state = self.game.state
            if self.message_log:
                self.message_log.game_state = self.game.state
        else:
            logger.error("Failed to load game")

        self.refresh_ui()

    async def action_restart(self) -> None:
        """Restart the game (async Textual handler)."""
        self.game.restart_game()
        self.refresh_ui()

    async def action_chat(self) -> None:
        """Open chat input (async Textual handler)."""
        if self.chat_input:
            # Show chat input with callback for when message is submitted
            self.chat_input.show(on_submit=self._send_chat_message)

    def _send_chat_message(self, message: str):
        """Send a chat message (callback from ChatInput).

        Args:
            message: Chat message text
        """
        if self.is_multiplayer and self.multiplayer_client:
            # In multiplayer mode, send to server
            import asyncio
            asyncio.create_task(self.multiplayer_client.send_chat(message))
            logger.info(f"Sent chat message: {message}")
        else:
            # In single-player mode, just show it locally (for testing)
            if self.message_log:
                self.message_log.add_chat_message(self.player_name, message)
            logger.info(f"Chat (single-player): {message}")

    def _handle_chat_message(self, chat_msg):
        """Handle incoming chat message from multiplayer client.

        Args:
            chat_msg: ChatMessage object from multiplayer client
        """
        if self.message_log:
            self.message_log.add_chat_message(chat_msg.player_name, chat_msg.message)
        logger.debug(f"Received chat from {chat_msg.player_name}: {chat_msg.message}")

    def _handle_system_message(self, message: str):
        """Handle system message from multiplayer client.

        Args:
            message: System message text
        """
        if self.message_log:
            self.message_log.add_system_message(message)
        logger.info(f"System message: {message}")

    def on_mount(self) -> None:
        """Called when app is mounted."""
        logger.info("on_mount() called - app is mounting")

        # Set up multiplayer client callbacks if in multiplayer mode
        if self.multiplayer_client:
            logger.info("Setting up multiplayer client callbacks")
            self.multiplayer_client.on_chat_message = self._handle_chat_message
            self.multiplayer_client.on_system_message = self._handle_system_message

    def on_ready(self) -> None:
        """Called when app is ready."""
        logger.info("on_ready() called - app is ready and running")

    def on_shutdown(self) -> None:
        """Called when app is shutting down."""
        logger.info("on_shutdown() called - restoring terminal")
        _restore_terminal()

    async def action_debug_ui(self) -> None:
        """Debug UI - dump widget and CSS info to logs."""
        logger.info("=== UI DEBUG DUMP ===")
        logger.info(f"CSS_PATH: {getattr(self, 'CSS_PATH', 'NOT SET')}")

        if self.sidebar:
            logger.info(f"Sidebar: visible={self.sidebar.display}, styles={self.sidebar.styles}")
        if self.inventory_widget:
            logger.info(f"InventoryWidget: visible={self.inventory_widget.display}, styles={self.inventory_widget.styles}")
            logger.info(f"  InventoryWidget has game_state: {self.inventory_widget.game_state is not None}")
            if self.inventory_widget.game_state:
                logger.info(f"  Player inventory items: {len(self.inventory_widget.game_state.player.inventory)}")
        if self.map_widget:
            logger.info(f"MapWidget: visible={self.map_widget.display}, styles={self.map_widget.styles}")
        if self.message_log:
            logger.info(f"MessageLog: visible={self.message_log.display}, styles={self.message_log.styles}")

        # Try to manually render inventory content
        if self.inventory_widget:
            content = self.inventory_widget.render_content()
            logger.info(f"Manual render_content() result:\n{str(content)[:200]}")

        self.game.state.add_message("UI debug info dumped to logs/veinborn.log")
        self.refresh_ui()

    def refresh_ui(self) -> None:
        """Refresh all UI components."""
        logger.debug("refresh_ui() called")
        if self.map_widget:
            self.map_widget.refresh()
        if self.status_bar:
            self.status_bar.refresh()
        if self.sidebar:
            self.sidebar.update_content()
        if self.inventory_widget:
            self.inventory_widget.update_content()
        if self.message_log:
            self.message_log.update_messages()


def run_game(player_name=None, character_class=None, seed=None, withdrawn_ore=None, is_legacy_run=False):
    """
    Run the Veinborn game.

    Args:
        player_name: Player name (for high scores)
        character_class: CharacterClass enum (for starting stats)
        seed: Game seed (for reproducibility)
        withdrawn_ore: LegacyOre from vault (optional)
        is_legacy_run: Whether this is a legacy run (used vault ore)
    """
    logger.info(f"run_game() called (player={player_name}, class={character_class}, seed={seed}, legacy={is_legacy_run})")
    app = VeinbornApp(player_name=player_name, character_class=character_class, seed=seed,
                    withdrawn_ore=withdrawn_ore, is_legacy_run=is_legacy_run)
    logger.info("Calling app.run()...")

    # CRITICAL: Explicitly disable mouse to prevent terminal escape sequences
    # Bug: Textual can leave mouse tracking enabled even with ENABLE_MOUSE = False
    # Fix: Pass mouse=False explicitly to run() method
    app.run(mouse=False)

    logger.info("app.run() returned")


def main():
    """Entry point for pip-installed veinborn command."""
    run_game()


if __name__ == "__main__":
    run_game()
