"""
Kill streaks: kills within a few turns of each other build a streak.

Announces the streak; it grants nothing mechanical (a hook for bonus drops
later). Per game, not saved.
"""

from ...events import GameEventType
from ...extensions import event_handler, on
from .common import player_kill

STREAK_TIMEOUT = 3      # turns without a kill before the streak ends
ANNOUNCE_AT = 3         # first streak size that is announced
MEGA_STREAK = 10


@event_handler
class KillStreaks:
    def __init__(self, context):
        self.context = context
        self.streak = 0
        self.last_kill_turn = 0
        self.best = 0

    def _active(self, turn: int) -> bool:
        return turn - self.last_kill_turn <= STREAK_TIMEOUT

    @on(GameEventType.ENTITY_DIED)
    def on_entity_died(self, event):
        if not player_kill(self.context, event):
            return
        turn = self.context.get_turn_count()
        self.streak = self.streak + 1 if self.streak and self._active(turn) else 1
        self.last_kill_turn = turn
        self.best = max(self.best, self.streak)
        if self.streak >= ANNOUNCE_AT:
            self.context.add_message(f"Kill Streak x{self.streak}!")
        if self.streak == MEGA_STREAK:
            self.context.add_message("MEGA STREAK!")

    @on(GameEventType.FLOOR_CHANGED)
    def on_floor_changed(self, event):
        self.streak = 0

    @on(GameEventType.TURN_ENDED)
    def on_turn_ended(self, event):
        if self.streak and not self._active(event.turn or 0):
            if self.streak >= ANNOUNCE_AT:
                self.context.add_message("Kill streak ended.")
            self.streak = 0
