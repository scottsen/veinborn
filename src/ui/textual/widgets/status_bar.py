"""Status bar widget for displaying game information."""
import time

from textual.widget import Widget
from rich.text import Text


class StatusBar(Widget):
    """Top status bar showing HP, turn count, etc."""

    # DEFAULT_CSS removed - use external layout files instead

    def __init__(self, snapshot=None, **kwargs):
        super().__init__(**kwargs)
        self.snapshot = snapshot
        self.waiting_text = None    # shown while there is no snapshot (connecting, the lobby)
        self._shown_at = time.monotonic()
        self._grace_seen: tuple = ()

    def on_mount(self) -> None:
        # The server sends the grace a seat has left once; the countdown is ours to run
        self.set_interval(1.0, self._tick_grace)

    def _tick_grace(self) -> None:
        snap = self.snapshot
        if snap is not None and any(m.grace_left is not None for m in snap.party):
            self.refresh()

    def _member_label(self, member) -> str:
        if member.connected:
            return member.name
        if member.grace_left is None:
            return f"{member.name} (disconnected)"
        left = max(0, member.grace_left - int(time.monotonic() - self._shown_at))
        return f"{member.name} (disconnected, {left // 60}:{left % 60:02d})"

    @staticmethod
    def lobby_text(lobby) -> str:
        """One line for a multiplayer lobby: the game, its id (to share), each seat, and the key to start."""
        if not lobby:
            return "Connected. Create or join a game to begin."
        seats = ", ".join(
            f"{p.get('player_name')} ({p.get('player_class')}{', ready' if p.get('is_ready') else ''})"
            for p in lobby.get('players', [])
        )
        return (f"Lobby '{lobby.get('game_name')}' id {lobby.get('game_id')} | {seats} | "
                f"R: ready (starts when everyone is)")

    def show(self, snapshot) -> None:
        """Draw this snapshot."""
        self.snapshot = snapshot
        # A local redraw re-shows the same grace values: only fresh ones restart the clock
        grace = tuple(m.grace_left for m in snapshot.party) if snapshot is not None else ()
        if grace != self._grace_seen:
            self._grace_seen = grace
            self._shown_at = time.monotonic()
        self.refresh()

    def render(self) -> Text:
        """Render the status bar."""
        snap = self.snapshot
        if snap is None:
            return Text(self.waiting_text or "Veinborn - Loading...", style="bold")

        player = snap.player
        parts = [
            f"HP: {player.hp}/{player.max_hp}",
            f"Turn: {snap.turn}",
            f"Pos: ({player.x}, {player.y})",
        ]

        if snap.round is not None and snap.party:
            owed = set(snap.round.waiting_on)
            waiting = [self._member_label(m)
                       for m in snap.party if m.entity_id in owed]   # in seat order
            parts.append(f"Round {snap.round.number}" + (f": waiting on {', '.join(waiting)}" if waiting else ""))
        if not player.alive:
            parts.append("DEAD (spectating)")

        if snap.game_over:
            parts.append("GAME OVER")

        status_text = Text(" | ".join(parts))
        status_text.stylize("bold bright_green")

        return status_text
