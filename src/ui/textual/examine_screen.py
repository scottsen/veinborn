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
