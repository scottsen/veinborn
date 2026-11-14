"""Status bar widget for displaying game information."""
from textual.widget import Widget
from rich.text import Text


class StatusBar(Widget):
    """Top status bar showing HP, turn count, etc."""

    # DEFAULT_CSS removed - use external layout files instead

    def __init__(self, snapshot=None, **kwargs):
        super().__init__(**kwargs)
        self.snapshot = snapshot
        self.waiting_text = None    # shown while there is no snapshot (connecting, the lobby)

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
            waiting = [m.name + ("" if m.connected else " (disconnected)")
                       for m in snap.party if m.entity_id in owed]   # in seat order
            parts.append(f"Round {snap.round.number}" + (f": waiting on {', '.join(waiting)}" if waiting else ""))
        if not player.alive:
            parts.append("DEAD (spectating)")

        if snap.game_over:
            parts.append("GAME OVER")

        status_text = Text(" | ".join(parts))
        status_text.stylize("bold bright_green")

        return status_text
