"""Crafting screen (VB-109): press `f` next to a forge, pick a recipe, Enter crafts it.

    > Copper Dagger   3x copper ore            +4 attack     <- craftable: Enter crafts
      Iron Sword      2x iron ore    Requires 2x iron ore (have 0)

Rows are the snapshot's `PlayerView.recipes` (craftable first), so the screen holds no
rules and works the same on a local run and a server's. A craft is the `craft` intent.
"""

from textual.binding import Binding

from core.actions.craft_action import CraftAction
from core.crafting import ORE_LEGEND, ore_label, stats_label

from .list_screen import ListScreen

_STAT_LABELS = {'attack_bonus': 'attack', 'defense_bonus': 'defense'}   # the others: key with spaces


def stats_text(stats) -> str:
    return "  ".join(f"+{v} {_STAT_LABELS.get(k, k.replace('_', ' '))}"
                     for k, v in stats.items() if v)


def items_by_id(player):
    return {i.entity_id: i for i in player.inventory}


class CraftScreen(ListScreen):
    BINDINGS = ListScreen.BINDINGS + [
        Binding("o", "pick_ore", "Choose ore / parts", show=False),
        Binding("f", "close", "Close", show=False),
    ]
    heading = "FORGE"
    footer = "↑/↓ select   Enter craft (best)   o choose ore / parts   Esc close"
    empty = "(no recipes)"

    def _player(self):
        return self.driver.snapshot().player

    def rows(self):
        return self._player().recipes

    def header(self) -> str:
        return "Craft parts from ore, then assemble parts into gear."

    def row_text(self, recipe) -> str:
        tail = stats_text(recipe.stats) if recipe.craftable else (recipe.reason or "")
        mark = "" if recipe.craftable else "✗ "
        return f"{mark}{recipe.name:<22} {recipe.requires:<24} {tail}"

    def detail(self, recipe) -> str:
        if not recipe.craftable:
            return recipe.reason or ""
        items = items_by_id(self._player())
        if recipe.kind == 'assembly':
            used = ", ".join(items[i].name for i in recipe.part_ids if i in items)
            return f"Uses: {used}   (o: choose parts)"
        used = ", ".join(f"{items[i].name} {ore_label(items[i].ore)}" for i in recipe.ore_ids if i in items)
        spare = len(recipe.ore_choices) - len(recipe.ore_ids)
        more = f"   ({spare} more to choose from: o)" if spare > 0 else ""
        return f"Uses: {used}{more}\n{ORE_LEGEND}"

    def action_pick_ore(self) -> None:
        rows = self.rows()
        if not rows:
            return
        recipe = rows[min(self.cursor, len(rows) - 1)]
        if not recipe.craftable:
            self.feedback = recipe.reason or "You cannot craft that yet."
            self.refresh_panel()
            return
        picker = PartPickScreen if recipe.kind == 'assembly' else OrePickScreen
        self.app.push_screen(picker(self.driver, recipe.recipe_id, on_change=self.on_change),
                             self._back_from_pick)

    def _back_from_pick(self, feedback) -> None:
        """The picker closes after a craft with the game's answer; show it here."""
        if feedback:
            self.feedback = feedback
        self.refresh_panel()

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


class OrePickScreen(ListScreen):
    """Pick exactly the ore a craft spends: Space toggles a piece, Enter crafts (VB-112).

    Starts from the default (best) picks; the preview follows the pick. The preview runs core's
    formulas on the pieces' listed properties (RecipeManager.preview_from_properties); the craft
    itself is the `craft` intent with `ore_ids`, judged by the game like any other.
    """

    BINDINGS = [                         # its own set: Enter crafts here, Space picks
        Binding("up,k", "move(-1)", "Up", show=False),
        Binding("down,j", "move(1)", "Down", show=False),
        Binding("space,x", "toggle", "Pick", show=False),
        Binding("enter", "craft", "Craft", show=False),
        Binding("escape,q,o", "close", "Back", show=False),
    ]
    heading = "CHOOSE ORE"
    footer = "↑/↓ select   Space pick / unpick   Enter craft   Esc back"
    empty = "(no ore of this type)"

    def __init__(self, driver, recipe_id, on_change=None, **kwargs):
        super().__init__(driver, on_change=on_change, **kwargs)
        self.recipe_id = recipe_id
        recipe = self.recipe()
        self.picked = list(recipe.ore_ids) if recipe else []

    def recipe(self):
        return next((r for r in self.driver.snapshot().player.recipes
                     if r.recipe_id == self.recipe_id), None)

    def rows(self):
        recipe = self.recipe()
        if recipe is None:
            return []
        items = items_by_id(self.driver.snapshot().player)
        return [items[i] for i in recipe.ore_choices if i in items]

    def header(self) -> str:
        recipe = self.recipe()
        if recipe is None:
            return "The forge is out of reach."
        need = recipe.ore_count
        line = f"{recipe.name}: pick {need} ({len(self.picked)} picked)"
        if len(self.picked) == need:
            items = items_by_id(self.driver.snapshot().player)
            stats = CraftAction.get_recipe_manager().preview_from_properties(
                self.recipe_id, [items[i].ore for i in self.picked if i in items])
            if stats:
                line += f"  ->  {stats_text(stats)}"
        return f"{line}\n{ORE_LEGEND}  (★ jackpot)"

    def row_text(self, item) -> str:
        mark = "[x]" if item.entity_id in self.picked else "[ ]"
        return f"{mark} {item.name} {ore_label(item.ore)}"

    def action_toggle(self) -> None:
        rows = self.rows()
        if not rows:
            return
        item = rows[min(self.cursor, len(rows) - 1)]
        if item.entity_id in self.picked:
            self.picked.remove(item.entity_id)
        else:
            self.picked.append(item.entity_id)
        self.feedback = ""
        self.refresh_panel()

    async def action_craft(self) -> None:
        recipe = self.recipe()
        player = self.driver.snapshot().player
        if recipe is None or player.forge_id is None:
            self.feedback = "No forge in reach."
        elif len(self.picked) != recipe.ore_count:
            self.feedback = f"Pick exactly {recipe.ore_count} (you picked {len(self.picked)})."
        else:
            await self.run('craft', forge_id=player.forge_id, recipe_id=self.recipe_id,
                           ore_ids=list(self.picked))
            self.dismiss(self.feedback)
            return
        self.refresh_panel()


class PartPickScreen(ListScreen):
    """Pick the parts an assembly spends: one per slot, Space picks, Enter assembles (VB-116).

    Starts from the default (best) parts; picking a part in a slot replaces that slot's pick, and
    a picked optional part (a gem) can be unpicked. The preview follows the pick and runs core's
    sums on the parts' listed stats (RecipeManager.preview_from_parts); the assembly itself is
    the `craft` intent with `part_ids`, judged by the game like any other.
    """

    BINDINGS = [
        Binding("up,k", "move(-1)", "Up", show=False),
        Binding("down,j", "move(1)", "Down", show=False),
        Binding("space,x", "toggle", "Pick", show=False),
        Binding("enter", "craft", "Assemble", show=False),
        Binding("escape,q,o", "close", "Back", show=False),
    ]
    heading = "CHOOSE PARTS"
    footer = "↑/↓ select   Space pick / unpick   Enter assemble   Esc back"
    empty = "(no parts of this kind)"

    def __init__(self, driver, recipe_id, on_change=None, **kwargs):
        super().__init__(driver, on_change=on_change, **kwargs)
        self.recipe_id = recipe_id
        recipe = self.recipe()
        self.picked = list(recipe.part_ids) if recipe else []

    def recipe(self):
        return next((r for r in self.driver.snapshot().player.recipes
                     if r.recipe_id == self.recipe_id), None)

    def rows(self):
        recipe = self.recipe()
        if recipe is None:
            return []
        items = items_by_id(self.driver.snapshot().player)
        slots = recipe.required_slots + recipe.optional_slots
        return [items[i] for slot in slots for i in recipe.part_choices.get(slot, []) if i in items]

    def _picked_parts(self):
        items = items_by_id(self.driver.snapshot().player)
        return [items[i].part for i in self.picked if i in items and items[i].part]

    def header(self) -> str:
        recipe = self.recipe()
        if recipe is None:
            return "The forge is out of reach."
        line = f"{recipe.name}: one part for each of {', '.join(recipe.required_slots)}"
        if recipe.optional_slots:
            line += f" (optional: {', '.join(recipe.optional_slots)})"
        stats = CraftAction.get_recipe_manager().preview_from_parts(self.recipe_id, self._picked_parts())
        return f"{line}\n->  {stats_label(stats)}" if stats else line

    def row_text(self, item) -> str:
        mark = "[x]" if item.entity_id in self.picked else "[ ]"
        part = item.part or {}
        return f"{mark} {part.get('slot', '?'):<7} {item.name:<18} {stats_label(part.get('stats'))}"

    def action_toggle(self) -> None:
        rows = self.rows()
        if not rows:
            return
        item = rows[min(self.cursor, len(rows) - 1)]
        if item.entity_id in self.picked:
            self.picked.remove(item.entity_id)
        else:
            items = items_by_id(self.driver.snapshot().player)
            slot = (item.part or {}).get('slot')
            self.picked = [i for i in self.picked
                           if i in items and (items[i].part or {}).get('slot') != slot]
            self.picked.append(item.entity_id)
        self.feedback = ""
        self.refresh_panel()

    async def action_craft(self) -> None:
        recipe = self.recipe()
        player = self.driver.snapshot().player
        if recipe is None or player.forge_id is None:
            self.feedback = "No forge in reach."
        elif CraftAction.get_recipe_manager().preview_from_parts(
                self.recipe_id, self._picked_parts()) is None:
            self.feedback = f"Pick one part for each of: {', '.join(recipe.required_slots)}."
        else:
            await self.run('craft', forge_id=player.forge_id, recipe_id=self.recipe_id,
                           part_ids=list(self.picked))
            self.dismiss(self.feedback)
            return
        self.refresh_panel()
