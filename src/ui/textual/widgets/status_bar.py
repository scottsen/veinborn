"""Status bar widget for displaying game information."""
from textual.widget import Widget
from rich.text import Text

from core.snapshot import build_snapshot


class StatusBar(Widget):
    """Top status bar showing HP, turn count, etc."""

    # DEFAULT_CSS removed - use external layout files instead

    def __init__(self, game_state=None, **kwargs):
        super().__init__(**kwargs)
        self.game_state = game_state

    def render(self) -> Text:
        """Render the status bar."""
        if not self.game_state:
            return Text("Veinborn - Loading...", style="bold")

        snap = build_snapshot(self.game_state)
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
