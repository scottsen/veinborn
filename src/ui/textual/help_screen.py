"""Keys screen (VB-109): `?` lists every key the app binds, read from its BINDINGS so the
list cannot drift from the real keys."""

from rich.text import Text
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static

_MOVE = {"move_up", "move_down", "move_left", "move_right",
         "move_up_left", "move_up_right", "move_down_left", "move_down_right"}


def key_rows(bindings):
    """[(keys, description)] with the eight move bindings folded into one row, hidden ones kept
    only when they carry a description worth listing (not debug)."""
    rows, by_action = [], {}
    for b in bindings:
        by_action.setdefault(b.action, []).append(b)
    moves = [b.key for a in _MOVE for b in by_action.get(a, [])]
    if moves:
        rows.append((" ".join(moves), "Move / attack / mine (bump)"))
    for action, group in by_action.items():
        if action in _MOVE or action == "debug_ui":
            continue
        rows.append((" ".join(b.key for b in group), group[0].description))
    return rows


class HelpScreen(ModalScreen):
    BINDINGS = [Binding("escape,q,question_mark,enter", "close", "Close", show=False)]
    DEFAULT_CSS = """
    HelpScreen { align: center middle; }
    #help-panel { width: 76; height: auto; max-height: 92%;
                  border: round $accent; background: $surface; padding: 1 2; }
    """

    def __init__(self, bindings, **kwargs):
        super().__init__(**kwargs)
        self._bindings_list = bindings

    def render_panel(self) -> Text:
        text = Text()
        text.append("=== KEYS ===\n\n", style="bold bright_green")
        for keys, description in key_rows(self._bindings_list):
            text.append(f"{keys:<16}", style="bold bright_yellow")
            text.append(f"{description}\n", style="bright_white")
        text.append("\nCrafting: stand next to a forge and press f.   Esc closes.", style="dim")
        return text

    def compose(self):
        yield Static(self.render_panel(), id="help-panel")

    def action_close(self) -> None:
        self.dismiss()
