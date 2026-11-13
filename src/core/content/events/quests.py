"""
Quests: kill-count objectives with a small XP reward. Per game, not saved.

To add a quest, add a Quest to QUESTS. `monster` is a monsters.yaml id; a quest
with `after` stays inactive until that quest is completed.
"""

from dataclasses import dataclass
from typing import Optional

from ...events import GameEventType
from ...extensions import event_handler, on
from .common import player_kill, victim_content_id


@dataclass(frozen=True)
class Quest:
    id: str
    name: str
    monster: str
    target: int
    reward_xp: int
    reward_message: str
    after: Optional[str] = None   # id of the quest that unlocks this one

    @property
    def description(self) -> str:
        return f"Kill {self.target} {self.monster}s"


QUESTS = (
    Quest("goblin_slayer", "Goblin Slayer", "goblin", 5, 20,
          "You have proven yourself against the goblin menace!"),
    Quest("bat_hunter", "Bat Hunter", "bat", 5, 15,
          "The caves are quieter now.", after="goblin_slayer"),
)


@event_handler
class QuestTracker:
    def __init__(self, context):
        self.context = context
        self.progress = {quest.id: 0 for quest in QUESTS}
        self.completed = set()
        self.active = {quest.id for quest in QUESTS if quest.after is None}

    def _announce(self, quest: Quest) -> None:
        self.context.add_message(f"New Quest: {quest.name} ({quest.description})")

    @on(GameEventType.GAME_STARTED)
    def on_game_started(self, event):
        for quest in QUESTS:
            if quest.id in self.active:
                self._announce(quest)

    @on(GameEventType.ENTITY_DIED)
    def on_entity_died(self, event):
        killer = player_kill(self.context, event)
        if killer is None:
            return
        monster = victim_content_id(self.context, event)
        for quest in QUESTS:
            if quest.id in self.active and quest.monster == monster:
                self.progress[quest.id] += 1
                self.context.add_message(
                    f"Quest: {quest.name} [{self.progress[quest.id]}/{quest.target}]"
                )
                if self.progress[quest.id] >= quest.target:
                    self._complete(quest, killer)

    def _complete(self, quest: Quest, player) -> None:
        self.active.discard(quest.id)
        self.completed.add(quest.id)
        self.context.add_message(f"Quest Complete: {quest.name} - {quest.reward_message}")
        if quest.reward_xp:
            self.context.add_message(f"Reward: +{quest.reward_xp} XP")
            if player.gain_xp(quest.reward_xp, rng=self.context.get_rng()):
                self.context.add_message(f"Level up! Now level {player.get_stat('level')}!")
        for follow_up in QUESTS:
            if follow_up.after == quest.id:
                self.active.add(follow_up.id)
                self._announce(follow_up)
