"""The client's one way to play a run: read a Snapshot, submit intents (plan D6).

`VeinbornApp` and its screens talk only to a `GameDriver`, so the same UI plays
a local single-player game (`LocalDriver`) or a seat in a server's game
(`RemoteDriver`, plan phase 4c). Rules never run in the UI: an intent goes to
the engine (locally, or over the wire) and the next snapshot shows the result.
"""

import logging
from dataclasses import replace
from typing import Callable, Dict, List, Optional, Protocol

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


class RemoteDriver:
    """A seat in a server's game, over a connected `ui.multiplayer_client.MultiplayerClient`.

    The snapshot is the newest one the server sent this seat. Its message log is
    kept here: the server's lines (new ones told apart by `message_count`) merged
    with this player's own notes, in arrival order. Before the game starts there
    is no snapshot, only the lobby.
    """

    can_save = False
    LOG_LIMIT = 100

    def __init__(self, client):
        self.client = client
        self._callbacks: List[Callable[[], None]] = []
        self._log: List[str] = []
        self._seen_count = 0
        self._snapshot = None
        client.on_snapshot = self._on_snapshot
        client.on_lobby = lambda lobby: self._updated()
        if client.snapshot is not None:
            self._on_snapshot(client.snapshot)

    # -- reading -----------------------------------------------------------
    def snapshot(self):
        if self._snapshot is None:
            return None
        return replace(self._snapshot, messages=self._log[-20:])

    def lobby(self) -> Dict:
        """The game before it starts ({} once it runs): game_id, game_name, players (name, class, is_ready)."""
        return self.client.lobby

    # -- acting ------------------------------------------------------------
    async def submit(self, intent: str, **args) -> List[str]:
        accepted, lines = await self.client.act(intent, **args)
        return lines

    async def ready(self) -> None:
        """Mark this seat ready in the lobby; the game starts when every seat is."""
        await self.client.send_ready()

    def note(self, line: str) -> None:
        self._append([line])
        self._updated()

    def on_update(self, callback: Callable[[], None]) -> None:
        self._callbacks.append(callback)

    # -- internals ---------------------------------------------------------
    def _on_snapshot(self, snapshot) -> None:
        # The snapshot carries the server's recent lines; message_count says how many are new
        new = snapshot.message_count - self._seen_count
        if self._seen_count == 0 or new >= len(snapshot.messages):
            fresh = snapshot.messages            # first snapshot, or more new lines than it carries
        else:
            fresh = snapshot.messages[-new:] if new > 0 else []
        self._append(fresh)
        self._seen_count = max(self._seen_count, snapshot.message_count)
        self._snapshot = snapshot
        self._updated()

    def _append(self, lines) -> None:
        self._log.extend(lines)
        if len(self._log) > self.LOG_LIMIT:
            del self._log[:-self.LOG_LIMIT]

    def _updated(self) -> None:
        for callback in self._callbacks:
            try:
                callback()
            except Exception:
                logger.exception("update callback failed")
