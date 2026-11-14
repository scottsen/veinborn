"""Sidebar widget for player and game information."""
from textual.widgets import Static
from rich.text import Text


class Sidebar(Static):
    """Right sidebar showing player stats and monster info."""

    # DEFAULT_CSS removed - use external layout files instead

    def __init__(self, snapshot=None, layout_name='default', **kwargs):
        super().__init__(**kwargs)
        self.snapshot = snapshot
        self.layout_name = layout_name

    def show(self, snapshot) -> None:
        """Draw this snapshot."""
        self.snapshot = snapshot
        self.update_content()

    def compose(self):
        """Compose the sidebar content."""
        yield Static(self.render_content(), id="sidebar-content")

    def render_content(self) -> Text:
        """Render the sidebar content."""
        snap = self.snapshot
        if snap is None:
            return Text("Loading...")

        text = Text()
        player = snap.player
        if snap.reveal_map:
            text.append("[MAP REVEALED: no fog]\n", style="bold bright_magenta")

        # Player info
        text.append("=== PLAYER ===\n", style="bold bright_green")
        text.append(f"Health: {player.hp}/{player.max_hp}\n")
        # Totals include equipped gear (starting kit, crafted or found)
        text.append(f"Attack: {player.attack}\n")
        text.append(f"Defense: {player.defense}\n")
        xp_line = f"{player.xp}/{player.xp_next}" if player.xp_next else f"{player.xp}"
        text.append(f"XP: {xp_line}\n")
        text.append(f"Level: {player.level}\n")
        for effect in player.effects:
            text.append(f"{effect.label} +{effect.magnitude}/turn ({effect.turns_left}t)\n", style="bright_green")
        text.append(f"Weapon: {player.weapon.name if player.weapon else '-'}\n")
        text.append(f"Armor: {player.armor.name if player.armor else '-'}\n")
        text.append(f"Shield: {player.shield.name if player.shield else '-'}\n\n")

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
        monsters = [e for e in snap.entities if e.entity_type == 'monster']
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
        ability_line = self._ability_line(player)
        if ability_line:
            text.append(ability_line + "\n")
        text.append("G: Pick up Items\n")
        text.append("I: Full Inventory\n")
        text.append(":: Look at Ground\n")
        text.append(".: Wait/Rest\n")
        text.append("Bump to attack/mine\n")
        text.append("Q: Quit | R: Restart\n")

        return text

    def _ability_line(self, player):
        """'Z: Force bolt (ready)' / '(5t)' for the player's first active ability, else None."""
        if not player.abilities:
            return None
        ability = player.abilities[0]
        status = "ready" if ability.ready else f"{ability.cooldown_remaining}t"
        return f"Z: {ability.name.replace('_', ' ').capitalize()} ({status})"

    def update_content(self):
        """Update the sidebar content."""
        sidebar_content = self.query_one("#sidebar-content", Static)
        sidebar_content.update(self.render_content())
