"""Message log widget for game messages."""
from textual.widget import Widget
from textual.widgets import Static
from rich.text import Text


class MessageLog(Static):
    """Bottom message log for game events and chat."""

    # DEFAULT_CSS removed - use external layout files instead

    def __init__(self, game_state=None, **kwargs):
        super().__init__(**kwargs)
        self.game_state = game_state
        self.chat_messages = []  # List of (player_name, message) tuples
        self.system_messages = []  # List of system messages

    def add_chat_message(self, player_name: str, message: str):
        """Add a chat message to the log.

        Args:
            player_name: Name of the player who sent the message
            message: Chat message text
        """
        self.chat_messages.append((player_name, message))
        # Keep only last 50 chat messages
        if len(self.chat_messages) > 50:
            self.chat_messages = self.chat_messages[-50:]
        self.refresh()

    def add_system_message(self, message: str):
        """Add a system message to the log.

        Args:
            message: System message text
        """
        self.system_messages.append(message)
        # Keep only last 50 system messages
        if len(self.system_messages) > 50:
            self.system_messages = self.system_messages[-50:]
        self.refresh()

    def render(self) -> Text:
        """Render the message log."""
        text = Text()

        # Combine game messages, chat messages, and system messages
        all_messages = []

        # Add game messages (if in single-player mode)
        if self.game_state and self.game_state.messages:
            for msg in self.game_state.messages[-8:]:
                all_messages.append(("game", msg))

        # Add recent system messages (multiplayer events)
        for msg in self.system_messages[-8:]:
            all_messages.append(("system", msg))

        # Add recent chat messages
        for player_name, msg in self.chat_messages[-8:]:
            all_messages.append(("chat", (player_name, msg)))

        # If no messages at all, show welcome
        if not all_messages:
            return Text("Welcome to Veinborn!", style="italic")

        # Display the last 8 messages (mixed game/chat/system)
        displayed_messages = all_messages[-8:]

        for msg_type, msg_data in displayed_messages:
            if msg_type == "game":
                # Regular game message
                text.append(msg_data, style="white")
                text.append("\n")
            elif msg_type == "system":
                # System message (multiplayer events)
                text.append("[", style="dim")
                text.append(msg_data, style="cyan italic")
                text.append("]", style="dim")
                text.append("\n")
            elif msg_type == "chat":
                # Chat message with player name
                player_name, message = msg_data
                text.append(f"<{player_name}> ", style="bold yellow")
                text.append(message, style="white")
                text.append("\n")

        return text

    def update_messages(self):
        """Update the message display."""
        self.refresh()
