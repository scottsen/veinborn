"""Base for keyboard list screens (crafting, pack): a cursor over rows, Enter acts, Esc closes.

Subclasses give `rows()` (from the driver's snapshot, so a remote client lists what a local
one does), `row_text(row)`, `header()` / `footer`, and `activate(row)`. The screen holds no
rules: every change is an intent submitted through the driver (plan D6).
"""

from rich.text import Text
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static


class ListScreen(ModalScreen):
    BINDINGS = [
        Binding("up,k", "move(-1)", "Up", show=False),
        Binding("down,j", "move(1)", "Down", show=False),
        Binding("enter,space", "activate", "Act", show=False),
        Binding("escape,q", "close", "Close", show=False),
    ]

    DEFAULT_CSS = """
    ListScreen { align: center middle; }
    .list-panel {
        width: 76; height: auto; max-height: 90%;
        border: round $accent; background: $surface; padding: 1 2;
    }
    """

    heading = ""
    footer = "↑/↓ select   Enter act   Esc close"
    empty = "(nothing here)"

    def __init__(self, driver, on_change=None, **kwargs):
        super().__init__(**kwargs)
        self.driver = driver
        self.on_change = on_change      # called after every intent (refresh the main UI)
        self.cursor = 0
        self.feedback = ""

    # -- subclass hooks --------------------------------------------------
    def rows(self):
        raise NotImplementedError

    def row_text(self, row) -> str:
        raise NotImplementedError

    def header(self) -> str:
        return ""

    def detail(self, row) -> str:
        """One line about the selected row, shown under the list."""
        return ""

    async def activate(self, row) -> None:
        raise NotImplementedError

    # -- plumbing --------------------------------------------------------
    def compose(self):
        yield Static(self.render_panel(), classes="list-panel", id="list-panel")

    def render_panel(self) -> Text:
        rows = self.rows()
        self.cursor = max(0, min(self.cursor, len(rows) - 1))
        text = Text()
        text.append(f"=== {self.heading} ===\n", style="bold bright_green")
        header = self.header()
        if header:
            text.append(f"{header}\n", style="bright_white")
        text.append("\n")
        if not rows:
            text.append(f"   {self.empty}\n", style="dim")
        for i, row in enumerate(rows):
            selected = i == self.cursor
            text.append(f"{'▶ ' if selected else '  '}{self.row_text(row)}\n",
                        style="bold reverse" if selected else "bright_white")
        if rows:
            detail = self.detail(rows[self.cursor])
            if detail:
                text.append(f"\n{detail}\n", style="bright_yellow")
        if self.feedback:
            text.append(f"\n{self.feedback}\n", style="bright_cyan")
        text.append(f"\n{self.footer}", style="dim")
        return text

    def refresh_panel(self) -> None:
        self.query_one("#list-panel", Static).update(self.render_panel())

    def action_move(self, step: int) -> None:
        rows = self.rows()
        if rows:
            self.cursor = (self.cursor + step) % len(rows)
        self.refresh_panel()

    async def action_activate(self) -> None:
        rows = self.rows()
        if rows:
            await self.activate(rows[min(self.cursor, len(rows) - 1)])

    def action_close(self) -> None:
        self.dismiss()

    async def run(self, intent: str, **kwargs) -> None:
        self.feedback = "  ".join(await self.driver.submit(intent, **kwargs))
        if self.on_change:
            self.on_change()
        self.refresh_panel()
