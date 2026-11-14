"""Main Textual application for Veinborn."""
import atexit
import logging
import signal
import sys
from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding

from core.game import Game
from core.config.user_config import ConfigManager
from ui.textual.widgets import MapWidget, StatusBar, Sidebar, InventoryWidget, ChatInput
from ui.textual.widgets.message_log import MessageLog
from core.item_listing import ground_messages, inventory_messages, items_here
from ui.textual.equipment_screen import EquipmentScreen
from ui.driver import LocalDriver, RemoteDriver

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
        Binding("up", "move_up", "Move Up", show=False),
        Binding("down", "move_down", "Move Down", show=False),
        Binding("left", "move_left", "Move Left", show=False),
        Binding("right", "move_right", "Move Right", show=False),
        # Vim keys
        Binding("k", "move_up", "Move Up", show=False),
        Binding("j", "move_down", "Move Down", show=False),
        Binding("h", "move_left", "Move Left", show=False),
        Binding("l", "move_right", "Move Right", show=False),
        # Diagonal movement
        Binding("y", "move_up_left", "Move Up-Left", show=False),
        Binding("u", "move_up_right", "Move Up-Right", show=False),
        Binding("b", "move_down_left", "Move Down-Left", show=False),
        Binding("n", "move_down_right", "Move Down-Right", show=False),
        # Mining actions
        Binding("s", "survey", "Survey Ore", show=True),
        Binding("z", "ability", "Class Ability (cast/heal)", show=True),
        # Inventory and inspection
        Binding("i", "show_inventory", "Show Inventory", show=True),
        Binding("w", "equip_item", "Equipment (wield/wear/remove)", show=True),
        Binding("g", "pickup", "Pick up Items", show=True),
        Binding("e", "use_item", "Eat/Drink (heal)", show=True),
        Binding("d", "drop_item", "Drop least useful item", show=True),
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
        Binding("R", "ready", "Ready (multiplayer lobby)", show=True),
        Binding("r", "restart", "Restart", show=True),
        Binding("q", "quit", "Quit", show=True),
        # Debug
        Binding("D", "debug_ui", "Debug UI", show=False),
    ]

    TITLE = "Veinborn: Walking in Big Brother's Footsteps"

    def __init__(self, player_name=None, character_class=None, seed=None, withdrawn_ore=None, is_legacy_run=False, multiplayer_client=None, multiplayer_setup=None, driver=None, reveal_map=False):
        """
        Initialize Veinborn app.

        Args:
            player_name: Player name (for high scores)
            character_class: CharacterClass enum (for starting stats)
            seed: Game seed (for reproducibility)
            withdrawn_ore: LegacyOre from vault (optional)
            is_legacy_run: Whether this is a legacy run (used vault ore)
            multiplayer_client: Optional MultiplayerClient for multiplayer games
            multiplayer_setup: Optional async callable(client) -> bool that connects the
                client. Run from on_mount so the websocket listener lives in Textual's
                event loop (a separate asyncio.run() cancels it when that loop ends).
            driver: The run to play (plan D6). Default: the seat behind
                `multiplayer_client` (`RemoteDriver`) if one is given, else a new local
                single-player run (`LocalDriver`) started with the options above.
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

        # The UI reads snapshots from the driver and submits intents to it; it never holds a Game
        if driver is None:
            driver = RemoteDriver(multiplayer_client) if multiplayer_client is not None else LocalDriver(Game())
        self.driver = driver
        self.driver.on_update(self.refresh_ui)

        # Player configuration for starting a local run
        self.player_name = player_name or "Anonymous"
        self.character_class = character_class
        self.seed = seed
        self.withdrawn_ore = withdrawn_ore
        self.is_legacy_run = is_legacy_run
        self.reveal_map = reveal_map

        # Multiplayer support
        self.multiplayer_client = multiplayer_client
        self._multiplayer_setup = multiplayer_setup
        self.is_multiplayer = multiplayer_client is not None

        self.map_widget = None
        self.status_bar = None
        self.sidebar = None
        self.inventory_widget = None
        self.message_log = None
        self.chat_input = None

        logger.info("VeinbornApp.__init__() complete")

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        logger.info("compose() starting")

        if isinstance(self.driver, LocalDriver) and self.driver.snapshot() is None:
            logger.info(f"  Starting new game (Player: {self.player_name}, Class: {self.character_class}, Seed: {self.seed}, Legacy: {self.is_legacy_run})...")
            self.driver.start(
                seed=self.seed,
                player_name=self.player_name,
                character_class=self.character_class,
                withdrawn_ore=self.withdrawn_ore,
                is_legacy_run=self.is_legacy_run,
                reveal_map=self.reveal_map,
            )

        snap = self.driver.snapshot()
        if snap is not None:
            logger.info(f"  Run ready: player at ({snap.player.x}, {snap.player.y}), "
                        f"map {snap.map.width}x{snap.map.height}, {len(snap.entities)} entities")

        self.status_bar = StatusBar(snapshot=snap)
        self.map_widget = MapWidget(snapshot=snap)
        self.sidebar = Sidebar(snapshot=snap, layout_name=self.layout_name)
        self.inventory_widget = InventoryWidget(snapshot=snap)
        self.message_log = MessageLog(snapshot=snap)
        self.chat_input = ChatInput()

        yield self.status_bar
        yield self.inventory_widget  # Bottom of right panel
        yield self.sidebar  # Top of right panel (stacks from bottom up)
        yield self.map_widget
        yield self.message_log
        yield self.chat_input  # Chat input overlays on top (focus disabled until shown)
        logger.info("compose() complete")

    # -- acting --------------------------------------------------------------
    def _playing(self) -> bool:
        """There is a run and it is not over."""
        snap = self.driver.snapshot()
        return snap is not None and not snap.game_over

    async def _act(self, intent: str, **args) -> None:
        """Submit an intent; the driver's update redraws the screen."""
        if self._playing():
            await self.driver.submit(intent, **args)

    def _note(self, lines) -> None:
        """Lines for this player's own log (listings), then redraw."""
        for line in lines:
            self.driver.note(line)
        self.refresh_ui()

    async def action_move(self, dx: int, dy: int) -> None:
        """Move (or bump: attack, mine) one step."""
        await self._act('move', dx=dx, dy=dy)

    # Individual movement actions (workaround for Textual negative number parsing bug)
    async def action_move_up(self) -> None:
        """Move up."""
        await self.action_move(0, -1)

    async def action_move_down(self) -> None:
        """Move down."""
        await self.action_move(0, 1)

    async def action_move_left(self) -> None:
        """Move left."""
        await self.action_move(-1, 0)

    async def action_move_right(self) -> None:
        """Move right."""
        await self.action_move(1, 0)

    async def action_move_up_left(self) -> None:
        """Move up-left (diagonal)."""
        await self.action_move(-1, -1)

    async def action_move_up_right(self) -> None:
        """Move up-right (diagonal)."""
        await self.action_move(1, -1)

    async def action_move_down_left(self) -> None:
        """Move down-left (diagonal)."""
        await self.action_move(-1, 1)

    async def action_move_down_right(self) -> None:
        """Move down-right (diagonal)."""
        await self.action_move(1, 1)

    async def action_survey(self) -> None:
        """Survey an adjacent ore vein."""
        await self._act('survey')

    async def action_ability(self) -> None:
        """Use the class ability: mage force bolt, healer heal."""
        await self._act('ability')

    async def action_descend(self) -> None:
        """Descend the stairs to the next floor."""
        await self._act('descend')

    async def action_wait(self) -> None:
        """Wait / pass the turn."""
        await self._act('wait')

    async def action_show_inventory(self) -> None:
        """List the full inventory in the message log."""
        if self._playing():
            self._note(inventory_messages(self.driver.snapshot().player))

    async def action_use_item(self) -> None:
        """Drink a healing potion or eat food: the one that best covers missing HP."""
        await self._act('use')

    async def action_drop_item(self) -> None:
        """Drop the item least worth carrying (gold, scrolls, worse gear first)."""
        await self._act('drop')

    async def action_pickup(self) -> None:
        """Pick up items from the ground."""
        await self._act('pickup')

    def check_action(self, action: str, parameters) -> bool | None:
        """While the equipment screen is open the map keys must not move or hit anything."""
        if isinstance(self.screen, EquipmentScreen):
            return action in ('quit', 'debug_ui')
        return True

    async def action_equip_item(self) -> None:
        """Open the equipment screen: wear, remove and compare gear from one list."""
        if self._playing():
            self.push_screen(EquipmentScreen(self.driver, on_change=self.refresh_ui))

    async def action_look_at_ground(self) -> None:
        """List the items on the player's tile in the message log."""
        if self._playing():
            self._note(ground_messages(items_here(self.driver.snapshot())))

    async def action_save_game(self) -> None:
        """Save the run (local runs only)."""
        if not self.driver.can_save:
            self._note(["Saving is only available in single-player."])
            return
        if not self._playing():
            return
        if self.driver.save():
            logger.info("Game saved successfully")
        else:
            logger.error("Failed to save game")
        self.refresh_ui()

    async def action_load_game(self) -> None:
        """Load the saved run (local runs only)."""
        if not self.driver.can_save:
            self._note(["Loading is only available in single-player."])
            return
        if self.driver.load():
            logger.info("Game loaded successfully")
        else:
            logger.error("Failed to load game")

    async def action_restart(self) -> None:
        """Start a new run (local runs only)."""
        if not self.driver.can_save:
            self._note(["Restarting is only available in single-player."])
            return
        self.driver.restart()

    async def action_ready(self) -> None:
        """Ready up in a multiplayer lobby (the game starts when every seat is ready)."""
        ready = getattr(self.driver, 'ready', None)
        if ready is None or self.driver.snapshot() is not None:
            return
        await ready()

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

    async def on_mount(self) -> None:
        """Called when app is mounted."""
        logger.info("on_mount() called - app is mounting")

        # Set up multiplayer client callbacks if in multiplayer mode
        if self.multiplayer_client:
            logger.info("Setting up multiplayer client callbacks")
            self.multiplayer_client.on_chat_message = self._handle_chat_message
            self.multiplayer_client.on_system_message = self._handle_system_message

            if self._multiplayer_setup:
                # Connect inside this loop so the listener task survives
                if not await self._multiplayer_setup(self.multiplayer_client):
                    logger.error("Multiplayer setup failed; exiting")
                    self.exit(message="Failed to connect to the multiplayer server")

    async def on_unmount(self) -> None:
        """Close the multiplayer connection in the loop that owns it."""
        if self.multiplayer_client:
            await self.multiplayer_client.disconnect()

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
            snap = self.inventory_widget.snapshot
            logger.info(f"  InventoryWidget has a snapshot: {snap is not None}")
            if snap is not None:
                logger.info(f"  Player inventory items: {len(snap.player.inventory)}")
        if self.map_widget:
            logger.info(f"MapWidget: visible={self.map_widget.display}, styles={self.map_widget.styles}")
        if self.message_log:
            logger.info(f"MessageLog: visible={self.message_log.display}, styles={self.message_log.styles}")

        # Try to manually render inventory content
        if self.inventory_widget:
            content = self.inventory_widget.render_content()
            logger.info(f"Manual render_content() result:\n{str(content)[:200]}")

        self._note(["UI debug info dumped to logs/veinborn.log"])

    def refresh_ui(self) -> None:
        """Draw the driver's current snapshot in every widget (one snapshot per refresh)."""
        widgets = (self.map_widget, self.status_bar, self.sidebar, self.inventory_widget, self.message_log)
        if not any(widgets):
            return
        snap = self.driver.snapshot()
        if snap is None and self.status_bar is not None and hasattr(self.driver, 'lobby'):
            self.status_bar.waiting_text = StatusBar.lobby_text(self.driver.lobby())
        for widget in widgets:
            if widget is not None:
                widget.show(snap)


def run_game(player_name=None, character_class=None, seed=None, withdrawn_ore=None, is_legacy_run=False,
             reveal_map=False):
    """
    Run the Veinborn game.

    Args:
        player_name: Player name (for high scores)
        character_class: CharacterClass enum (for starting stats)
        seed: Game seed (for reproducibility)
        withdrawn_ore: LegacyOre from vault (optional)
        is_legacy_run: Whether this is a legacy run (used vault ore)
        reveal_map: Dev switch: no fog of war (VB-105)
    """
    logger.info(f"run_game() called (player={player_name}, class={character_class}, seed={seed}, legacy={is_legacy_run})")
    app = VeinbornApp(player_name=player_name, character_class=character_class, seed=seed,
                    withdrawn_ore=withdrawn_ore, is_legacy_run=is_legacy_run, reveal_map=reveal_map)
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
