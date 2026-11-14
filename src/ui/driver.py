"""The client's one way to play a run: read a Snapshot, submit intents (plan D6).

`VeinbornApp` and its screens talk only to a `GameDriver`, so the same UI plays
a local single-player game (`LocalDriver`) or a seat in a server's game
(`RemoteDriver`, plan phase 4c). Rules never run in the UI: an intent goes to
the engine (locally, or over the wire) and the next snapshot shows the result.
"""

import logging
from typing import Callable, List, Optional, Protocol

from core.snapshot import Snapshot, build_snapshot

logger = logging.getLogger(__name__)


class GameDriver(Protocol):
    """What the UI may do with a run."""

    #: save/load/restart exist (a local run); a server's run has none of them
    can_save: bool

    def snapshot(self) -> Optional[Snapshot]:
        """The run as this player sees it now, or None before there is one."""

    async def submit(self, intent: str, **args) -> List[str]:
        """Act. Returns the lines this action produced for the actor (what happened,
        or why it was refused); shared log lines also appear in the next snapshot."""

    def note(self, line: str) -> None:
        """A line for this player's own log (an inventory listing, a look at the ground)."""

    def on_update(self, callback: Callable[[], None]) -> None:
        """Call `callback` whenever there is a new snapshot to draw."""


class LocalDriver:
    """A single-player run in this process: a `core.game.Game`, one player."""

    can_save = True

    def __init__(self, game):
        self.game = game
        self._callbacks: List[Callable[[], None]] = []

    # -- the run -----------------------------------------------------------
    def start(self, **options) -> None:
        """Start a new run (`Game.start_new_game` options: seed, player_name, character_class, ...)."""
        self.game.start_new_game(**options)
        self._updated()

    def snapshot(self) -> Optional[Snapshot]:
        state = getattr(self.game, 'state', None)
        return build_snapshot(state) if state is not None else None

    async def submit(self, intent: str, **args) -> List[str]:
        state = self.game.state
        if state.game_over:
            return []
        before = state.message_count
        self.game.handle_player_action(intent, **args)
        self._updated()
        new = min(state.message_count - before, len(state.messages))
        return state.messages[-new:] if new > 0 else []

    def note(self, line: str) -> None:
        self.game.state.add_message(line)

    def on_update(self, callback: Callable[[], None]) -> None:
        self._callbacks.append(callback)

    # -- local only (can_save) ---------------------------------------------
    def save(self) -> bool:
        return self.game.save_game()

    def load(self) -> bool:
        loaded = self.game.load_game()
        self._updated()
        return loaded

    def restart(self) -> None:
        self.game.restart_game()
        self._updated()

    def _updated(self) -> None:
        for callback in self._callbacks:
            try:
                callback()
            except Exception:
                logger.exception("update callback failed")
