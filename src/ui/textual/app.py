"""Main Textual application for Brogue."""
import atexit
import logging
import signal
import sys
from textual.app import App, ComposeResult
from textual.binding import Binding

from core.game import Game
from ui.textual.widgets import MapWidget, StatusBar, Sidebar, ChatInput
from ui.textual.widgets.message_log import MessageLog

# Setup logging
logger = logging.getLogger('brogue.app')


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


class BrogueApp(App):
    """Textual-based Brogue game application."""

    # CSS_PATH = "styles/brogue.tcss"  # Disabled for now, using widget DEFAULT_CSS

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
        Binding("m", "mine", "Mine Ore", show=True),
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
    ]

    TITLE = "Brogue: Walking in Big Brother's Footsteps"

    def __init__(self, player_name=None, character_class=None, seed=None, withdrawn_ore=None, is_legacy_run=False, multiplayer_client=None):
        """
        Initialize Brogue app.

        Args:
            player_name: Player name (for high scores)
            character_class: CharacterClass enum (for starting stats)
            seed: Game seed (for reproducibility)
            withdrawn_ore: LegacyOre from vault (optional)
            is_legacy_run: Whether this is a legacy run (used vault ore)
            multiplayer_client: Optional MultiplayerClient for multiplayer games
        """
        logger.info("BrogueApp.__init__() starting")
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
        self.message_log = None
        self.chat_input = None
        logger.info("BrogueApp.__init__() complete")

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
        self.sidebar = Sidebar(game_state=self.game.state)
        logger.info("  Creating MessageLog...")
        self.message_log = MessageLog(game_state=self.game.state)
        logger.info("  Creating ChatInput...")
        self.chat_input = ChatInput()

        # Yield widgets
        logger.info("  Yielding widgets...")
        yield self.status_bar
        yield self.sidebar
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

    async def action_mine(self) -> None:
        """Mine adjacent ore vein (async Textual handler)."""
        if self.game.state.game_over:
            return

        # Call synchronous game logic
        self.game.handle_player_action('mine')

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

    def refresh_ui(self) -> None:
        """Refresh all UI components."""
        logger.debug("refresh_ui() called")
        if self.map_widget:
            self.map_widget.refresh()
        if self.status_bar:
            self.status_bar.refresh()
        if self.sidebar:
            self.sidebar.update_content()
        if self.message_log:
            self.message_log.update_messages()


def run_game(player_name=None, character_class=None, seed=None, withdrawn_ore=None, is_legacy_run=False):
    """
    Run the Brogue game.

    Args:
        player_name: Player name (for high scores)
        character_class: CharacterClass enum (for starting stats)
        seed: Game seed (for reproducibility)
        withdrawn_ore: LegacyOre from vault (optional)
        is_legacy_run: Whether this is a legacy run (used vault ore)
    """
    logger.info(f"run_game() called (player={player_name}, class={character_class}, seed={seed}, legacy={is_legacy_run})")
    app = BrogueApp(player_name=player_name, character_class=character_class, seed=seed,
                    withdrawn_ore=withdrawn_ore, is_legacy_run=is_legacy_run)
    logger.info("Calling app.run()...")

    # CRITICAL: Explicitly disable mouse to prevent terminal escape sequences
    # Bug: Textual can leave mouse tracking enabled even with ENABLE_MOUSE = False
    # Fix: Pass mouse=False explicitly to run() method
    app.run(mouse=False)

    logger.info("app.run() returned")


if __name__ == "__main__":
    run_game()
