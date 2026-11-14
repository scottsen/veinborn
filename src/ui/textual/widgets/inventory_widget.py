"""Inventory widget for displaying player inventory."""
import logging
from textual.widgets import Static
from rich.text import Text

logger = logging.getLogger(__name__)


class InventoryWidget(Static):
    """Widget displaying player inventory."""

    # DEFAULT_CSS removed - use external layout files instead

    def __init__(self, snapshot=None, **kwargs):
        super().__init__(**kwargs)
        self.snapshot = snapshot

    def show(self, snapshot) -> None:
        """Draw this snapshot."""
        self.snapshot = snapshot
        self.update_content()

    def compose(self):
        """Compose the inventory content."""
        logger.info("InventoryWidget.compose() called")
        content = self.render_content()
        logger.info(f"  Rendered content length: {len(str(content))}")
        yield Static(content, id="inventory-content")

    def render_content(self) -> Text:
        """Render the inventory content."""
        logger.debug("InventoryWidget.render_content() called")

        if self.snapshot is None:
            return Text("Loading...")

        text = Text()
        player = self.snapshot.player
        logger.debug(f"  Player inventory: {len(player.inventory)} items")

        # Inventory header
        text.append("=== INVENTORY ===\n", style="bold bright_yellow")

        inventory = player.inventory
        max_display = 10  # Show up to 10 items in dedicated window

        if inventory:
            capacity = player.inventory_capacity
            text.append(f"({len(inventory)}/{capacity} items)\n\n", style="dim")

            for idx, item in enumerate(inventory[:max_display], 1):
                item_type = item.item_type
                # Truncate long names
                name = item.name[:18] if len(item.name) > 18 else item.name
                text.append(f"{idx:2}. {name}\n", style="bright_white")
                text.append(f"    ({item_type})\n", style="dim")

            if len(inventory) > max_display:
                text.append(f"\n  (+{len(inventory) - max_display} more)\n", style="dim italic")
                text.append("  Press 'i' for full list\n", style="dim")
        else:
            text.append("(empty)\n\n", style="dim")
            text.append("Pick up items by\nwalking over them\n", style="dim")

        return text

    def update_content(self):
        """Update the inventory content."""
        logger.debug("InventoryWidget.update_content() called")
        try:
            inventory_content = self.query_one("#inventory-content", Static)
            new_content = self.render_content()
            logger.debug(f"  Updating with content length: {len(str(new_content))}")
            inventory_content.update(new_content)
        except Exception as e:
            logger.error(f"  Error updating inventory content: {e}")
