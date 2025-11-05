"""Sidebar widget for player and game information."""
from textual.widget import Widget
from textual.widgets import Static
from rich.text import Text

from core.base.entity import EntityType


class Sidebar(Static):
    """Right sidebar showing player stats and monster info."""

    DEFAULT_CSS = """
    Sidebar {
        width: 25;
        dock: right;
        background: $panel;
        border-left: solid $primary;
        padding: 1;
    }
    """

    def __init__(self, game_state=None, **kwargs):
        super().__init__(**kwargs)
        self.game_state = game_state

    def compose(self):
        """Compose the sidebar content."""
        yield Static(self.render_content(), id="sidebar-content")

    def render_content(self) -> Text:
        """Render the sidebar content."""
        if not self.game_state:
            return Text("Loading...")

        text = Text()
        player = self.game_state.player

        # Player info
        text.append("=== PLAYER ===\n", style="bold bright_green")
        text.append(f"Health: {player.hp}/{player.max_hp}\n")
        text.append(f"Attack: {player.attack}\n")
        text.append(f"Defense: {player.defense}\n\n")

        # Monster info
        monsters = [e for e in self.game_state.entities.values()
                   if e.entity_type == EntityType.MONSTER]
        if monsters:
            text.append("=== MONSTERS ===\n", style="bold bright_red")
            for monster in monsters[:5]:  # Show up to 5
                text.append(f"{monster.name}: {monster.hp}/{monster.max_hp}\n")
            text.append("\n")

        # Controls
        text.append("=== CONTROLS ===\n", style="bold bright_cyan")
        text.append("Arrow/HJKL: Move\n")
        text.append("YUBN: Diagonal\n")
        text.append("S: Survey Ore\n")
        text.append("M: Mine Ore\n")
        text.append("Q: Quit\n")
        text.append("R: Restart\n")

        return text

    def update_content(self):
        """Update the sidebar content."""
        sidebar_content = self.query_one("#sidebar-content", Static)
        sidebar_content.update(self.render_content())
