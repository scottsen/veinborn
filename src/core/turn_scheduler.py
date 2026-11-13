"""RoundScheduler: when does the world move?

One action per living player per round (Scott's ruling, plan D2). Monsters act once
every living player has taken a turn-consuming action. Free actions (equip, unequip)
never count. A party of one ticks after every turn-consuming action, which is
exactly what single-player always did.
"""

from typing import Iterable, List, Set


class RoundScheduler:
    """Tracks which seats still owe an action this round."""

    def __init__(self, living: Iterable[str] = ()):
        self.round_number = 0
        self.owed: Set[str] = set(living)
        self.acted: Set[str] = set()

    def can_act(self, actor_id: str) -> bool:
        """False once this actor has already taken their turn this round."""
        return actor_id not in self.acted

    def after_action(self, actor_id: str, took_turn: bool, living: Iterable[str]) -> bool:
        """Record an executed action. Returns True if the world should tick now.

        `living` are the seats still alive after the action: the dead (and anyone
        dropped) leave the owed set at once, so they can never stall a round.
        """
        living = set(living)
        if took_turn:
            self.owed.discard(actor_id)
            self.acted.add(actor_id)
        self.owed &= living
        # Also true when the last owed seat just died or left: somebody has acted and
        # nobody is left to wait for
        return bool(self.acted) and not self.owed

    def start(self, living: Iterable[str]) -> None:
        """Begin round 0 with these seats."""
        self.round_number = 0
        self.acted.clear()
        self.owed = set(living)

    def next_round(self, living: Iterable[str]) -> None:
        """Start the next round (call after the world tick)."""
        self.round_number += 1
        self.acted.clear()
        self.owed = set(living)

    def drop(self, actor_id: str) -> bool:
        """A seat left the party. Returns True if that completes the round."""
        was_owed = actor_id in self.owed
        self.owed.discard(actor_id)
        self.acted.discard(actor_id)
        return was_owed and not self.owed and bool(self.acted)

    def waiting_on(self) -> List[str]:
        """Seats the round is waiting for, in a stable order."""
        return sorted(self.owed)
