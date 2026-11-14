"""Pack screen (VB-109): `i` lists what you carry; Enter uses the selected item, `d` drops it.

    > Healing Potion (potion)        usable
      Long Sword (weapon, +4 attack)
      Copper Ore (ore)

`e` and `d` on the map stay the quick "best heal" and "drop the least useful" keys. Here you
choose: save the strong potion, drink the regeneration one, drop this item and not that one.
Rows are the snapshot's inventory, so it works the same on a remote run.
"""

from textual.binding import Binding

from core.crafting import ORE_LEGEND, ore_label, stats_label

from .list_screen import ListScreen


class PackScreen(ListScreen):
    BINDINGS = ListScreen.BINDINGS + [
        Binding("e,u", "activate", "Use", show=False),
        Binding("d", "drop_selected", "Drop", show=False),
        Binding("i", "close", "Close", show=False),
    ]
    heading = "PACK"
    footer = "↑/↓ select   Enter/e use   d drop   Esc close"
    empty = "Your pack is empty."

    def _player(self):
        return self.driver.snapshot().player

    def rows(self):
        return self._player().inventory

    def header(self) -> str:
        p = self._player()
        header = f"{len(p.inventory)}/{p.inventory_capacity} items"
        if any(i.ore for i in p.inventory):
            header += f"\nOre: {ORE_LEGEND}  (★ jackpot)"
        return header

    def row_text(self, item) -> str:
        kind = item.item_type
        if item.slot:
            kind = f"{item.slot}, " + (stats_label(item.stats) or f"+{item.bonus} {'attack' if item.slot == 'weapon' else 'defense'}")
        quality = f" {ore_label(item.ore)}" if item.ore else ""
        if item.part:
            quality = f" {stats_label(item.part['stats'])}"
        return f"{item.name} ({kind}){quality}{'   usable' if item.usable else ''}"

    async def activate(self, item) -> None:
        if not item.usable:
            self.feedback = f"You can't use the {item.name} that way" + (
                " (w wears gear)." if item.slot else ".")
            self.refresh_panel()
            return
        await self.run('use', item_id=item.entity_id)

    async def action_drop_selected(self) -> None:
        rows = self.rows()
        if rows:
            await self.run('drop', item_id=rows[min(self.cursor, len(rows) - 1)].entity_id)
