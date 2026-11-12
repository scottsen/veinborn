"""
Achievements: milestones for kills, depth, crafting and survival.

State is per game and is not saved (it resets when a saved game is loaded).
"""

from dataclasses import dataclass

from ...events import GameEventType
from ...extensions import event_handler, on
from .common import player_kill


@dataclass(frozen=True)
class Achievement:
    id: str
    name: str
    description: str
    stat: str        # which tracked stat unlocks it
    threshold: int   # unlocked when the stat reaches this


ACHIEVEMENTS = (
    Achievement("centurion", "Centurion", "Kill 100 monsters", "kills", 100),
    Achievement("slayer", "Slayer", "Kill 500 monsters", "kills", 500),
    Achievement("explorer", "Explorer", "Descend 10 floors", "deepest_floor", 10),
    Achievement("deep_diver", "Deep Diver", "Descend 25 floors", "deepest_floor", 25),
    Achievement("craftsman", "Craftsman", "Craft 50 items", "items_crafted", 50),
    Achievement("master_craftsman", "Master Craftsman", "Craft 100 items", "items_crafted", 100),
    Achievement("survivor", "Survivor", "Survive 1000 turns", "turns_survived", 1000),
    Achievement("veteran", "Veteran", "Survive 5000 turns", "turns_survived", 5000),
)

# Progress message every N of a stat (not for deepest_floor/turns shown at 0)
MILESTONE_EVERY = {"kills": 50, "deepest_floor": 5, "items_crafted": 25, "turns_survived": 500}
MILESTONE_LABEL = {
    "kills": "Total kills",
    "deepest_floor": "Deepest floor",
    "items_crafted": "Items crafted",
    "turns_survived": "Turns survived",
}


@event_handler
class AchievementTracker:
    def __init__(self, context):
        self.context = context
        self.unlocked = set()
        self.stats = {"kills": 0, "deepest_floor": 1, "items_crafted": 0, "turns_survived": 0}

    def _set(self, stat: str, value: int) -> None:
        self.stats[stat] = value
        for achievement in ACHIEVEMENTS:
            if (achievement.stat == stat and value >= achievement.threshold
                    and achievement.id not in self.unlocked):
                self.unlocked.add(achievement.id)
                self.context.add_message(
                    f"Achievement Unlocked: {achievement.name} - {achievement.description}"
                )
        every = MILESTONE_EVERY[stat]
        if value > 0 and value % every == 0:
            self.context.add_message(f"{MILESTONE_LABEL[stat]}: {value}")

    @on(GameEventType.ENTITY_DIED)
    def on_entity_died(self, event):
        if player_kill(self.context, event):
            self._set("kills", self.stats["kills"] + 1)

    @on(GameEventType.FLOOR_CHANGED)
    def on_floor_changed(self, event):
        to_floor = event.data.get("to_floor", 1)
        if to_floor > self.stats["deepest_floor"]:
            self._set("deepest_floor", to_floor)

    @on(GameEventType.EQUIPMENT_CRAFTED, GameEventType.ITEM_CRAFTED)
    def on_item_crafted(self, event):
        self._set("items_crafted", self.stats["items_crafted"] + 1)

    @on(GameEventType.TURN_ENDED)
    def on_turn_ended(self, event):
        self._set("turns_survived", event.turn or event.data.get("turn", 0))
