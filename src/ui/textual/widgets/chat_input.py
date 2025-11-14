"""Chat input widget for multiplayer chat."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Input, Static
from textual.binding import Binding


class ChatInput(Container):
    """Modal chat input widget that overlays the game screen."""

    DEFAULT_CSS = """
    ChatInput {
        display: none;
        align: center middle;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
    }

    ChatInput.visible {
        display: block;
    }

    ChatInput > .chat-container {
        width: 80%;
        max-width: 100;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }

    ChatInput > .chat-container > .chat-label {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    ChatInput > .chat-container > Input {
        width: 100%;
        border: solid $accent;
    }

    ChatInput > .chat-container > .chat-help {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
        text-style: italic;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._input = None
        self._on_submit_callback = None

    def compose(self) -> ComposeResult:
        """Compose the chat input UI."""
        with Container(classes="chat-container"):
            yield Static("Chat Message", classes="chat-label")
            self._input = Input(placeholder="Type your message...")
            yield self._input
            yield Static("Press Enter to send, Esc to cancel", classes="chat-help")

    def on_mount(self) -> None:
        """When mounted, hide by default."""
        self.remove_class("visible")

    def show(self, on_submit=None):
        """Show the chat input and focus it.

        Args:
            on_submit: Callback function to call when message is submitted
        """
        self._on_submit_callback = on_submit
        self.add_class("visible")
        if self._input:
            self._input.value = ""
            self._input.focus()

    def hide(self):
        """Hide the chat input."""
        self.remove_class("visible")
        if self._input:
            self._input.value = ""
            self._input.blur()

    def action_cancel(self):
        """Cancel chat input (Escape key)."""
        self.hide()

    async def on_input_submitted(self, event: Input.Submitted):
        """Handle input submission (Enter key).

        Args:
            event: Input submitted event
        """
        message = event.value.strip()

        # Hide the input
        self.hide()

        # Call the callback if message is not empty
        if message and self._on_submit_callback:
            self._on_submit_callback(message)
