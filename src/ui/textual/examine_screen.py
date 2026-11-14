"""Examine screen (VB-129, VB-110): press `x` to list what is around you, nearest first.

    > Goblin 8/8                     1 away
      Iron Ore Vein (surveyed)       3 away

The selected row says more underneath: a monster's attack, defense and XP; a surveyed vein's
properties and mining time (the survey message scrolls away; this does not); an item's stats.
Rows come from core.examine over the snapshot, so a remote client sees the same.
"""

from core.examine import examine_listing

from .list_screen import ListScreen


class ExamineScreen(ListScreen):
    heading = "EXAMINE"
    footer = "↑/↓ select   Esc close"
    empty = "(nothing in sight or remembered)"

    def rows(self):
        return examine_listing(self.driver.snapshot())

    def header(self) -> str:
        return "Monsters, ore, items and forges you can see or remember."

    def row_text(self, line) -> str:
        return line.text

    def detail(self, line) -> str:
        return line.detail

    async def activate(self, line) -> None:
        pass            # looking changes nothing


class TargetScreen(ListScreen):
    """Choose what a bolt hits (VB-128): `z` opens it when two or more targets are in range.

    Nearest first, so Enter on the first row is what `z` always did. Rows are the snapshot
    ability's `targets` (the same range and sight rule the cast uses); the cast is the
    `ability` intent with `target_id`.
    """

    heading = "AIM"
    footer = "↑/↓ select   Enter cast   Esc cancel"
    empty = "(nothing in range)"

    def __init__(self, driver, ability: str, on_change=None, **kwargs):
        super().__init__(driver, on_change=on_change, **kwargs)
        self.ability = ability

    def _ability(self):
        return next((a for a in self.driver.snapshot().player.abilities if a.name == self.ability), None)

    def rows(self):
        ability = self._ability()
        if ability is None:
            return []
        me = self.driver.snapshot().player
        by_id = {e.entity_id: e for e in self.driver.snapshot().entities}
        return [by_id[t] for t in ability.targets if t in by_id]

    def header(self) -> str:
        return f"{self.ability.replace('_', ' ').capitalize()}: pick a target"

    def row_text(self, e) -> str:
        me = self.driver.snapshot().player
        dist = max(abs(me.x - e.x), abs(me.y - e.y))
        return f"{e.name:<16} {e.hp}/{e.max_hp} hp   {dist} away"

    async def activate(self, e) -> None:
        await self.run('ability', ability=self.ability, target_id=e.entity_id)
        self.dismiss()
