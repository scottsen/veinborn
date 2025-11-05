"""Message log widget for game messages."""
from textual.widget import Widget
from textual.widgets import Static
from rich.text import Text


class MessageLog(Static):
    """Bottom message log for game events."""

    DEFAULT_CSS = """
    MessageLog {
        height: 5;
        dock: bottom;
        background: $surface;
        border-top: solid $primary;
        padding: 0 1;
    }
    """

    def __init__(self, game_state=None, **kwargs):
        super().__init__(**kwargs)
        self.game_state = game_state

    def render(self) -> Text:
        """Render the message log."""
        if not self.game_state or not self.game_state.messages:
            return Text("Welcome to Brogue!", style="italic")

        text = Text()
        for msg in self.game_state.messages[-4:]:  # Show last 4 messages
            text.append(msg + "\n")

        return text

    def update_messages(self):
        """Update the message display."""
        self.refresh()
