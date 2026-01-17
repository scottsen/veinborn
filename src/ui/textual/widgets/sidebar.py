"""Sidebar widget for player and game information."""
from textual.widget import Widget
from textual.widgets import Static
from rich.text import Text

from core.base.entity import EntityType


class Sidebar(Static):
    """Right sidebar showing player stats and monster info."""

    # DEFAULT_CSS removed - use external layout files instead

    def __init__(self, game_state=None, layout_name='default', **kwargs):
        super().__init__(**kwargs)
        self.game_state = game_state
        self.layout_name = layout_name

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
        text.append(f"Defense: {player.defense}\n")
        text.append(f"XP: {player.get_stat('xp', 0)}\n")
        text.append(f"Level: {player.get_stat('level', 1)}\n\n")

        # Show inventory only if InventoryWidget is hidden (for default layout)
        # Skip if using split-sidebars layout (InventoryWidget has its own panel on left)
        if self.layout_name != 'split-sidebars':
            text.append("=== INVENTORY ===\n", style="bold bright_yellow")
            inventory = player.inventory
            if inventory:
                for item in inventory[:5]:  # Show up to 5 items
                    name = item.name[:18] if len(item.name) > 18 else item.name
                    text.append(f"• {name}\n", style="bright_white")
                if len(inventory) > 5:
                    text.append(f"  (+{len(inventory) - 5} more)\n", style="dim")
            else:
                text.append("  (empty)\n", style="dim")
            text.append("\n")

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
        text.append("W: Wield/Wear\n")
        text.append("G: Pick up Items\n")
        text.append("I: Full Inventory\n")
        text.append(":: Look at Ground\n")
        text.append(".: Wait/Rest\n")
        text.append("Bump to attack/mine\n")
        text.append("Q: Quit | R: Restart\n")

        return text

    def update_content(self):
        """Update the sidebar content."""
        sidebar_content = self.query_one("#sidebar-content", Static)
        sidebar_content.update(self.render_content())
