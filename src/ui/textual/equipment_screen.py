"""Equipment screen: one clear list of what you wear and what you carry that you could wear.

    Worn
      Weapon: Iron Sword (+4 attack)        <- Enter removes it
      Armor:  (nothing)
    In your pack
    > Mithril Sword (weapon, +7 attack, +3 vs worn)   <- Enter wields/wears it
      Chainmail (armor, +3 defense, +3 vs worn)

The rows come from `core.equipment.equipment_listing`; changes go through the
game's `equip` / `unequip` actions, so this screen holds no rules.
"""

from rich.text import Text
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static

from core.equipment import equipment_listing


class EquipmentScreen(ModalScreen):
    """Pick a row; Enter wears (pack row) or removes (worn row); Esc closes."""

    BINDINGS = [
        Binding("up,k", "move(-1)", "Up", show=False),
        Binding("down,j", "move(1)", "Down", show=False),
        Binding("enter,space", "activate", "Wear / remove", show=False),
        Binding("x", "remove_selected", "Remove worn", show=False),
        Binding("escape,w,q", "close", "Close", show=False),
    ]

    DEFAULT_CSS = """
    EquipmentScreen { align: center middle; }
    #equipment-panel {
        width: 70; height: auto; max-height: 90%;
        border: round $accent; background: $surface; padding: 1 2;
    }
    """

    def __init__(self, game, on_change=None, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.on_change = on_change      # called after every equip/remove (refresh the main UI)
        self.cursor = 0
        self.feedback = ""

    def compose(self):
        yield Static(self.render_panel(), id="equipment-panel")

    # -- rows ------------------------------------------------------------
    def rows(self):
        """Selectable rows: the worn slots (empty ones skipped), then the wearable pack items."""
        worn, carried = equipment_listing(self.game.state.player)
        return [line for line in worn if line.item is not None] + carried

    def render_panel(self) -> Text:
        player = self.game.state.player
        worn, carried = equipment_listing(player)
        rows = self.rows()
        self.cursor = max(0, min(self.cursor, len(rows) - 1))
        selected = rows[self.cursor] if rows else None

        text = Text()
        text.append("=== EQUIPMENT ===\n", style="bold bright_green")
        text.append(f"Attack {player.get_total_attack()}   Defense {player.get_total_defense()}\n\n",
                    style="bright_white")

        text.append("Worn\n", style="bold bright_yellow")
        for line in worn:
            self._append_line(text, line, selected)
        text.append("\nIn your pack\n", style="bold bright_yellow")
        if carried:
            for line in carried:
                self._append_line(text, line, selected)
        else:
            text.append("   (no weapons or armor)\n", style="dim")

        if self.feedback:
            text.append(f"\n{self.feedback}\n", style="bright_cyan")
        text.append("\n↑/↓ select   Enter wear / remove   x remove worn   Esc close", style="dim")
        return text

    @staticmethod
    def _append_line(text, line, selected):
        is_selected = (selected is not None and line.item is not None
                       and line.worn == selected.worn and line.item is selected.item)
        marker = "▶ " if is_selected else "  "
        style = "bold reverse" if is_selected else ("dim" if line.item is None else "bright_white")
        text.append(f"{marker}{line.text()}\n", style=style)

    def refresh_panel(self) -> None:
        self.query_one("#equipment-panel", Static).update(self.render_panel())

    # -- actions ---------------------------------------------------------
    def action_move(self, step: int) -> None:
        rows = self.rows()
        if rows:
            self.cursor = (self.cursor + step) % len(rows)
        self.refresh_panel()

    def action_activate(self) -> None:
        rows = self.rows()
        if not rows:
            return
        line = rows[self.cursor]
        if line.worn:
            self._run('unequip', slot=line.slot)
        else:
            self._run('equip', item_id=line.item.entity_id)

    def action_remove_selected(self) -> None:
        """Remove the worn item: the selected one if it is worn, else the weapon, then the armor."""
        rows = self.rows()
        line = rows[self.cursor] if rows else None
        if line is not None and line.worn:
            self._run('unequip', slot=line.slot)
            return
        worn = [r for r in rows if r.worn]
        if worn:
            self._run('unequip', slot=worn[0].slot)
        else:
            self.feedback = "You are wearing nothing."
            self.refresh_panel()

    def action_close(self) -> None:
        self.dismiss()

    def _run(self, action_type: str, **kwargs) -> None:
        state = self.game.state
        before = state.message_count
        self.game.handle_player_action(action_type, **kwargs)
        new = min(state.message_count - before, len(state.messages))
        self.feedback = "  ".join(state.messages[-new:]) if new else ""
        if self.on_change:
            self.on_change()
        self.refresh_panel()
