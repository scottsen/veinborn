"""Yes/no prompt (VB-109): quit and restart end a run, so they ask first."""

from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static


class ConfirmScreen(ModalScreen):
    BINDINGS = [
        Binding("y", "answer(True)", "Yes", show=False),
        Binding("n,escape", "answer(False)", "No", show=False),
    ]
    DEFAULT_CSS = """
    ConfirmScreen { align: center middle; }
    #confirm-panel { width: 50; height: auto; border: round $warning;
                     background: $surface; padding: 1 2; }
    """

    def __init__(self, question: str, **kwargs):
        super().__init__(**kwargs)
        self.question = question

    def compose(self):
        yield Static(f"{self.question}\n\n[b]y[/b] yes   [b]n[/b] no", id="confirm-panel")

    def action_answer(self, yes: bool) -> None:
        self.dismiss(yes)
