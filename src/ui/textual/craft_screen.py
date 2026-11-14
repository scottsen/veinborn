"""Crafting screen (VB-109): press `f` next to a forge, pick a recipe, Enter crafts it.

    > Copper Dagger   3x copper ore            +4 attack     <- craftable: Enter crafts
      Iron Sword      2x iron ore    Requires 2x iron ore (have 0)

Rows are the snapshot's `PlayerView.recipes` (craftable first), so the screen holds no
rules and works the same on a local run and a server's. A craft is the `craft` intent.
"""

from .list_screen import ListScreen

_STAT_LABELS = {'attack_bonus': 'attack', 'defense_bonus': 'defense'}   # the others: key with spaces


def stats_text(stats) -> str:
    return "  ".join(f"+{v} {_STAT_LABELS.get(k, k.replace('_', ' '))}"
                     for k, v in stats.items() if v)


class CraftScreen(ListScreen):
    heading = "FORGE"
    footer = "↑/↓ select   Enter craft   Esc close"
    empty = "(no recipes)"

    def _player(self):
        return self.driver.snapshot().player

    def rows(self):
        return self._player().recipes

    def header(self) -> str:
        return "Craft from the ore in your pack."

    def row_text(self, recipe) -> str:
        tail = stats_text(recipe.stats) if recipe.craftable else (recipe.reason or "")
        mark = "" if recipe.craftable else "✗ "
        return f"{mark}{recipe.name:<22} {recipe.requires:<24} {tail}"

    def detail(self, recipe) -> str:
        return "" if recipe.craftable else (recipe.reason or "")

    async def activate(self, recipe) -> None:
        player = self._player()
        if player.forge_id is None:
            self.feedback = "No forge in reach."
            self.refresh_panel()
        elif not recipe.craftable:
            self.feedback = recipe.reason or "You cannot craft that yet."
            self.refresh_panel()
        else:
            await self.run('craft', forge_id=player.forge_id, recipe_id=recipe.recipe_id)
