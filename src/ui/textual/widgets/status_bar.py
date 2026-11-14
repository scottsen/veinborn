"""Status bar widget for displaying game information."""
from textual.widget import Widget
from rich.text import Text


class StatusBar(Widget):
    """Top status bar showing HP, turn count, etc."""

    # DEFAULT_CSS removed - use external layout files instead

    def __init__(self, snapshot=None, **kwargs):
        super().__init__(**kwargs)
        self.snapshot = snapshot

    def show(self, snapshot) -> None:
        """Draw this snapshot."""
        self.snapshot = snapshot
        self.refresh()

    def render(self) -> Text:
        """Render the status bar."""
        snap = self.snapshot
        if snap is None:
            return Text("Veinborn - Loading...", style="bold")

        player = snap.player
        parts = [
            f"HP: {player.hp}/{player.max_hp}",
            f"Turn: {snap.turn}",
            f"Pos: ({player.x}, {player.y})",
        ]

        if snap.game_over:
            parts.append("GAME OVER")

        status_text = Text(" | ".join(parts))
        status_text.stylize("bold bright_green")

        return status_text
