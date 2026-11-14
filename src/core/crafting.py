"""
Crafting system - turn mined ore into equipment.

This is Veinborn's core unique hook: SWG-style ore properties → equipment stats

Architecture:
- RecipeManager: Loads recipes.yaml, manages all recipes
- CraftingRecipe: Individual recipe (requirements + stat formulas)
- StatFormulaEvaluator: Evaluates formula strings ("hardness * 0.1 + purity * 0.05")

Design Goals:
- Data-driven (recipes in YAML, not hardcoded)
- Transparent formulas (player can see how stats are calculated)
- Quality matters (purity 90 ore >> purity 30 ore)
- Simple to add new recipes
"""

import logging
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import re
from simpleeval import simple_eval

logger = logging.getLogger(__name__)


@dataclass
class CraftingRecipe:
    """
    A crafting recipe that converts ore → equipment.

    Attributes:
        recipe_id: Unique identifier (e.g., "copper_sword")
        display_name: Human-readable name
        description: Flavor text
        requirements: Dict with ore_type, ore_count, min_floor
        stat_formulas: Dict with formula strings for each stat
        item_type: "weapon" or "armor"
        equipment_slot: "weapon" or "armor"
        symbol: Display character
        color: Display color
        tags: List of tags for categorization
    """
    recipe_id: str
    display_name: str
    description: str
    requirements: Dict[str, Any]
    stat_formulas: Dict[str, Any]
    item_type: str
    equipment_slot: str
    symbol: str
    color: str
    tags: List[str]
    # Crafting v2 (VB-115). kind 'item' is a one-step ore -> equipment recipe (the old shape);
    # 'part' turns ore into a part item; 'assembly' turns carried parts into equipment.
    kind: str = 'item'
    part_slot: Optional[str] = None                  # part: which slot it fills (head, grip, ...)
    accepts: Optional[List[str]] = None              # part: ore types it takes (None: ore_type)
    assembly_parts: Optional[Dict[str, str]] = None  # assembly: required slot -> part recipe id
    optional_slots: Optional[List[str]] = None       # assembly: slots that may be left empty
    fixed_stats: Optional[Dict[str, int]] = None     # assembly: added once (a material's bonus)
    assembly_ore: Optional[List[str]] = None         # assembly: every part must be made of these ores

    def calculate_stats(self, ore_properties: Dict[str, int]) -> Dict[str, int]:
        """
        Calculate equipment stats from ore properties.

        Args:
            ore_properties: Dict with hardness, conductivity, malleability, purity, density

        Returns:
            Dict with calculated stats (attack_bonus, defense_bonus, durability, weight)
        """
        evaluator = StatFormulaEvaluator(ore_properties)
        stats = {}

        for stat_name, formula in self.stat_formulas.items():
            if isinstance(formula, (int, float)):
                # Fixed value (e.g., defense_bonus: 0)
                stats[stat_name] = int(formula)
            elif isinstance(formula, str):
                # Formula string (e.g., "hardness * 0.1 + purity * 0.05")
                stats[stat_name] = evaluator.evaluate(formula)
            else:
                logger.warning(
                    f"Unknown formula type for {stat_name}: {type(formula)}",
                    extra={'recipe_id': self.recipe_id, 'stat_name': stat_name}
                )
                stats[stat_name] = 0

        # Ensure minimum stat value of 1 (even terrible ore makes usable gear), for stats the
        # recipe computes from ore; a fixed value (a weapon's 'defense_bonus: 0') stays as written
        for stat_name in ['attack_bonus', 'defense_bonus', 'durability']:
            if (stat_name in stats and stats[stat_name] < 1
                    and isinstance(self.stat_formulas.get(stat_name), str)):
                stats[stat_name] = 1

        logger.debug(
            f"Calculated stats for {self.recipe_id}",
            extra={'recipe_id': self.recipe_id, 'ore_properties': ore_properties, 'stats': stats}
        )

        return stats

    def get_required_ore_type(self) -> str:
        """Get the ore type required by this recipe."""
        return self.requirements.get('ore_type', 'copper')

    def accepted_ore_types(self) -> List[str]:
        """Every ore type this recipe can spend (a part may take any metal)."""
        return list(self.accepts) if self.accepts else [self.get_required_ore_type()]

    def get_required_ore_count(self) -> int:
        """Get the ore count required by this recipe."""
        return self.requirements.get('ore_count', 1)

    def get_special_requirement(self) -> Optional[str]:
        """Item id (items.yaml) a craft also consumes, e.g. a boss drop; None if none."""
        return self.requirements.get('special_requirement')

    def get_min_floor(self) -> int:
        """Get the minimum floor where this recipe is available."""
        return self.requirements.get('min_floor', 1)


class StatFormulaEvaluator:
    """
    Evaluates stat formula strings using ore properties.

    Examples:
        "hardness * 0.1" → hardness value * 0.1
        "hardness * 0.1 + purity * 0.05" → combined formula
        "avg(hardness, purity)" → average of hardness and purity

    Security: Uses safe evaluation (no exec/eval), only allows basic math
    """

    def __init__(self, ore_properties: Dict[str, int]):
        """
        Initialize evaluator with ore properties.

        Args:
            ore_properties: Dict with hardness, conductivity, malleability, purity, density
        """
        self.properties = ore_properties

    def evaluate(self, formula: str) -> int:
        """
        Evaluate a formula string.

        Args:
            formula: Formula string (e.g., "hardness * 0.1 + purity * 0.05")

        Returns:
            Calculated value (rounded to nearest integer)
        """
        try:
            # Replace property names with values
            expr = formula
            for prop_name, prop_value in self.properties.items():
                # Use word boundaries to avoid partial matches
                expr = re.sub(rf'\b{prop_name}\b', str(prop_value), expr)

            # Handle special functions
            expr = self._handle_functions(expr)

            # Evaluate using simpleeval for safe expression evaluation
            # Allows only math operations - no function calls, imports, or builtins
            result = simple_eval(expr)
            return round(result)

        except Exception as e:
            logger.error(
                f"Failed to evaluate formula: {formula}",
                extra={'formula': formula, 'error': str(e), 'properties': self.properties}
            )
            return 0

    def _handle_functions(self, expr: str) -> str:
        """Handle special functions like avg()."""
        # avg(a, b, c) → (a + b + c) / 3
        avg_pattern = r'avg\(([\d\s,+\-*/().]+)\)'
        matches = re.findall(avg_pattern, expr)
        for match in matches:
            values = [v.strip() for v in match.split(',')]
            replacement = f"({' + '.join(values)}) / {len(values)}"
            expr = expr.replace(f"avg({match})", replacement)
        return expr


# The five ore properties recipes read, in the order a label shows them (most telling first)
ORE_PROPERTIES = ('purity', 'hardness', 'malleability', 'conductivity', 'density')
ORE_LEGEND = "P purity  H hardness  M malleability  C conductivity  D density"
JACKPOT_MIN = 80   # a jackpot vein rolls every property in 80-100 (ores.yaml ore_generation)


def average_properties(properties: List[Dict[str, int]]) -> Dict[str, int]:
    """Rounded average of each ore property; 50 each for no ore. Crafting stats come from this."""
    if not properties:
        return {name: 50 for name in ORE_PROPERTIES}
    return {name: round(sum(p.get(name, 50) for p in properties) / len(properties))
            for name in ORE_PROPERTIES}


def ore_properties(item) -> Optional[Dict[str, int]]:
    """The recipe-relevant properties of a raw ore item, or None for anything else (VB-111)."""
    if not is_ore_item(item):
        return None
    return {name: int(item.get_stat(name, 50)) for name in ORE_PROPERTIES}


def ore_label(props: Optional[Dict[str, int]]) -> str:
    """'P85 H70 M55 C40 D50', with a star when every property is jackpot grade; '' for None."""
    if not props:
        return ""
    label = " ".join(f"{name[0].upper()}{props[name]}" for name in ORE_PROPERTIES if name in props)
    if all(props.get(name, 0) >= JACKPOT_MIN for name in ORE_PROPERTIES):
        label += " ★"
    return label


def is_ore_item(item) -> bool:
    """True for raw ore, false for crafted equipment.

    Crafted equipment used to carry an ``ore_type`` stat (and old saves still do),
    which made a finished dagger count as copper ore: a forge would "craft" from
    it indefinitely without consuming any real ore. Equipment always has an
    ``equipment_slot``; ore never does.
    """
    return bool(item.get_stat('ore_type')) and not item.get_stat('equipment_slot')


class RecipeManager:
    """
    Manages all crafting recipes.

    Responsibilities:
    - Load recipes from recipes.yaml
    - Provide recipe lookup by ID, ore type, floor
    - Validate crafting requirements
    - Create equipment from recipes
    """

    def __init__(self, recipes_path: Optional[Path] = None):
        """
        Initialize recipe manager.

        Args:
            recipes_path: Path to recipes.yaml (defaults to data/balance/recipes.yaml)
        """
        if recipes_path is None:
            recipes_path = Path(__file__).parent.parent.parent / "data" / "balance" / "recipes.yaml"

        self.recipes_path = recipes_path
        self.recipes: Dict[str, CraftingRecipe] = {}
        self._load_recipes()

        logger.info(
            f"RecipeManager initialized with {len(self.recipes)} recipes",
            extra={'recipe_count': len(self.recipes), 'recipes_path': str(self.recipes_path)}
        )

    RECIPE_SECTIONS = ('weapons', 'armor', 'legendary')
    METALS = ('copper', 'iron', 'mithril', 'adamantite')   # what `accepts: metal` expands to

    def _load_recipes(self):
        """Load all recipes from YAML file."""
        try:
            with open(self.recipes_path, 'r') as f:
                data = yaml.safe_load(f)

            # Legendary recipes also need a boss drop (requirements.special_requirement)
            for section in self.RECIPE_SECTIONS:
                for recipe_id, recipe_data in (data.get(section) or {}).items():
                    self.recipes[recipe_id] = self._create_recipe(recipe_id, recipe_data)
            for part_id, part_data in (data.get('parts') or {}).items():
                self.recipes[part_id] = self._create_part(part_id, part_data)
            for asm_id, asm_data in (data.get('assemblies') or {}).items():
                self.recipes[asm_id] = self._create_assembly(asm_id, asm_data)
            self._validate_assemblies()

            logger.info(
                f"Loaded {len(self.recipes)} recipes from {self.recipes_path}",
                extra={'recipe_count': len(self.recipes)}
            )

        except Exception as e:
            logger.error(
                f"Failed to load recipes from {self.recipes_path}",
                extra={'error': str(e), 'recipes_path': str(self.recipes_path)}
            )
            raise

    def _create_recipe(self, recipe_id: str, recipe_data: Dict[str, Any]) -> CraftingRecipe:
        """Create a CraftingRecipe from YAML data."""
        return CraftingRecipe(
            recipe_id=recipe_id,
            display_name=recipe_data.get('display_name', recipe_id),
            description=recipe_data.get('description', ''),
            requirements=recipe_data.get('requirements', {}),
            stat_formulas=recipe_data.get('stat_formulas', {}),
            item_type=recipe_data.get('item_type', 'item'),
            equipment_slot=recipe_data.get('equipment_slot', 'none'),
            symbol=recipe_data.get('symbol', '?'),
            color=recipe_data.get('color', 'white'),
            tags=recipe_data.get('tags', []),
        )

    def _create_part(self, part_id: str, data: Dict[str, Any]) -> CraftingRecipe:
        """A part recipe: `ore_count` of any `accepts` ore -> one part item for `part` slot."""
        accepts = data.get('accepts', 'metal')
        accepts = list(self.METALS) if accepts == 'metal' else list(accepts)
        return CraftingRecipe(
            recipe_id=part_id,
            display_name=data.get('display_name', part_id.replace('_', ' ').title()),
            description=data.get('description', ''),
            requirements={'ore_type': accepts[0], 'ore_count': data.get('ore_count', 1),
                          'min_floor': data.get('min_floor', 1)},
            stat_formulas=data.get('stats', {}),
            item_type='part', equipment_slot='none',
            symbol=data.get('symbol', '%'), color=data.get('color', 'white'),
            tags=['part', data['part']],
            kind='part', part_slot=data['part'], accepts=accepts,
        )

    def _create_assembly(self, asm_id: str, data: Dict[str, Any]) -> CraftingRecipe:
        """An assembly recipe: one carried part per required slot (+ optional gem) -> equipment."""
        slot = data['slot']
        requirements = {'min_floor': data.get('min_floor', 1)}
        if data.get('material'):
            requirements['special_requirement'] = data['material']   # consumed, like a boss drop
        return CraftingRecipe(
            recipe_id=asm_id,
            display_name=data.get('display_name', asm_id.replace('_', ' ').title()),
            description=data.get('description', ''),
            requirements=requirements, stat_formulas={},
            item_type='weapon' if slot == 'weapon' else 'armor', equipment_slot=slot,
            symbol=data.get('symbol', ')' if slot == 'weapon' else '['),
            color=data.get('color', 'white'),
            tags=[slot, 'assembly'] + list(data.get('tags', [])),
            kind='assembly', assembly_parts=dict(data['parts']),
            optional_slots=list(data.get('optional', [])),
            fixed_stats=dict(data.get('bonus', {})),
            assembly_ore=list(data['ore']) if data.get('ore') else None,
        )

    def _validate_assemblies(self):
        """Every assembly slot names a real part recipe made for that slot (fail at load)."""
        for recipe in self.recipes.values():
            if recipe.kind != 'assembly':
                continue
            slots = dict(recipe.assembly_parts)
            for slot in recipe.optional_slots:
                slots.setdefault(slot, None)
            for slot, part_id in recipe.assembly_parts.items():
                part = self.recipes.get(part_id)
                if part is None or part.kind != 'part' or part.part_slot != slot:
                    raise ValueError(f"assembly {recipe.recipe_id}: slot '{slot}' needs a part "
                                     f"recipe for that slot, got '{part_id}'")

    def get_recipe(self, recipe_id: str) -> Optional[CraftingRecipe]:
        """Get a recipe by ID."""
        return self.recipes.get(recipe_id)

    def get_all_recipes(self) -> List[CraftingRecipe]:
        """Get all recipes."""
        return list(self.recipes.values())

    def get_recipes_for_ore(self, ore_type: str) -> List[CraftingRecipe]:
        """
        Get all recipes that use a specific ore type.

        Args:
            ore_type: Ore type (e.g., "copper", "iron")

        Returns:
            List of recipes that use this ore type
        """
        return [
            recipe for recipe in self.recipes.values()
            if recipe.kind != 'assembly' and ore_type in recipe.accepted_ore_types()
        ]

    def get_craftable_recipes(
        self,
        player_inventory: List[Any],
        current_floor: int
    ) -> List[CraftingRecipe]:
        """
        Get recipes that player can currently craft.

        Args:
            player_inventory: Player's inventory (list of Entity objects)
            current_floor: Current dungeon floor

        Returns:
            List of craftable recipes
        """
        return [recipe for recipe in self.recipes.values()
                if self.can_craft(recipe.recipe_id, player_inventory, current_floor)[0]]

    def suggest_recipe(
        self,
        player_inventory: List[Any],
        current_floor: int,
        preference: str = 'balanced'
    ) -> Optional[str]:
        """
        Suggest the best recipe to craft based on current situation.

        Args:
            player_inventory: Player's inventory
            current_floor: Current dungeon floor
            preference: 'offense', 'defense', or 'balanced'

        Returns:
            recipe_id of best recipe, or None if nothing craftable
        """
        # Only one-step recipes: parts and assemblies are chosen by hand (or by a bot that
        # knows them), never auto-suggested
        craftable = [r for r in self.get_craftable_recipes(player_inventory, current_floor)
                     if r.kind == 'item']
        if not craftable:
            return None

        # ADD LOGGING: Show craftable recipes for debugging
        logger.info(f"Craftable recipes: {[(r.recipe_id, r.item_type, r.get_required_ore_count()) for r in craftable[:5]]}")

        # Define tier ordering for ore types
        ore_tier_order = {
            'adamantite': 4,
            'mithril': 3,
            'iron': 2,
            'copper': 1
        }

        # Sort by priority: higher tier first, then by preference
        def recipe_priority(recipe: CraftingRecipe) -> tuple:
            ore_type = recipe.get_required_ore_type()
            tier = ore_tier_order.get(ore_type, 0)

            # Secondary sort by item type based on preference
            is_weapon = recipe.item_type == 'weapon'
            is_armor = recipe.item_type == 'armor'

            if preference == 'offense':
                # Prefer weapons
                type_priority = 2 if is_weapon else 0
            elif preference == 'defense':
                # Prefer armor
                type_priority = 2 if is_armor else 0
            else:  # balanced
                # Truly balanced: prefer armor slightly to compensate for 2-ore requirement
                # This encourages bots to mine enough ore for armor recipes
                type_priority = 2 if is_armor else 1

            # Return tuple: (tier, type_priority, ore_count)
            # Negated for reverse sorting (higher = better)
            return (-tier, -type_priority, recipe.get_required_ore_count())

        # Sort and return best recipe
        sorted_recipes = sorted(craftable, key=recipe_priority)
        selected = sorted_recipes[0]

        # ADD LOGGING: Show selected recipe for debugging
        logger.info(f"Selected recipe: {selected.recipe_id} (type: {selected.item_type}, ore: {selected.get_required_ore_count()})")

        return selected.recipe_id

    def can_craft(
        self,
        recipe_id: str,
        player_inventory: List[Any],
        current_floor: int
    ) -> tuple[bool, Optional[str]]:
        """
        Check if player can craft a specific recipe.

        Args:
            recipe_id: Recipe to check
            player_inventory: Player's inventory
            current_floor: Current dungeon floor

        Returns:
            (can_craft: bool, reason: Optional[str])
        """
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return False, f"Recipe '{recipe_id}' not found"

        # Check floor requirement
        if current_floor < recipe.get_min_floor():
            return False, f"Requires floor {recipe.get_min_floor()}+ (currently on floor {current_floor})"

        if recipe.kind == 'assembly':
            missing = self.missing_slots(recipe, player_inventory)
            if missing:
                return False, "Requires parts: " + ", ".join(missing)
        else:
            required_count = recipe.get_required_ore_count()
            available = len(self.ore_choices(recipe, player_inventory))
            if available < required_count:
                kinds = "/".join(recipe.accepted_ore_types()) if recipe.accepts else recipe.get_required_ore_type()
                return False, f"Requires {required_count}x {kinds} ore (have {available})"

        special = recipe.get_special_requirement()
        if special and self.special_item_for(recipe, player_inventory) is None:
            return False, f"Requires {special}"

        return True, None

    @staticmethod
    def special_item_for(recipe: 'CraftingRecipe', player_inventory: List[Any]) -> Optional[Any]:
        """The inventory item a craft of `recipe` consumes besides ore (a boss drop), or None."""
        special = recipe.get_special_requirement()
        if not special:
            return None
        return next((i for i in player_inventory if getattr(i, 'content_id', None) == special), None)

    def ore_choices(self, recipe: 'CraftingRecipe', player_inventory: List[Any]) -> List[Any]:
        """Every carried ore a craft of `recipe` could use (right type), in pack order."""
        accepted = recipe.accepted_ore_types()
        return [i for i in player_inventory
                if is_ore_item(i) and i.get_stat('ore_type') in accepted]

    @staticmethod
    def main_stat(recipe: 'CraftingRecipe') -> str:
        """The stat a recipe is for: attack for weapons, defense for the rest; a part's own
        first formula (a blade's attack, a hilt's accuracy)."""
        if recipe.kind == 'part' and recipe.stat_formulas:
            return next(iter(recipe.stat_formulas))
        return 'attack_bonus' if recipe.equipment_slot == 'weapon' else 'defense_bonus'

    def ore_for(self, recipe: 'CraftingRecipe', player_inventory: List[Any],
                ore_ids: Optional[List[Any]] = None) -> List[Any]:
        """The ore a craft of `recipe` consumes (VB-112).

        With `ore_ids`, exactly those items, or [] when the pick is wrong (an id not carried,
        not this recipe's ore, a repeat, or the wrong count). Without, the best ore for the
        recipe's main stat (each piece scored alone; the formulas are linear in the averaged
        properties, so the top N scores give the best average), then by purity, then pack order.
        CraftAction and preview_stats both use this, so a preview is what the craft makes.
        """
        choices = self.ore_choices(recipe, player_inventory)
        count = recipe.get_required_ore_count()
        if ore_ids is not None:
            by_id = {i.entity_id: i for i in choices}
            if len(ore_ids) != count or len(set(ore_ids)) != count or any(o not in by_id for o in ore_ids):
                return []
            return [by_id[o] for o in ore_ids]
        stat = self.main_stat(recipe)

        def score(item):
            alone = recipe.calculate_stats(self._average_ore_properties([item]))
            return (alone.get(stat, 0), item.get_stat('purity', 0))

        ranked = sorted(choices, key=score, reverse=True)   # stable: ties keep pack order
        return ranked[:count]

    # -- assemblies (VB-115) ------------------------------------------------------------

    @staticmethod
    def parts_in(player_inventory: List[Any], part_id: str,
                 ores: Optional[List[str]] = None) -> List[Any]:
        """Carried part items made by part recipe `part_id`, in pack order; with `ores`, only
        parts made of those ores (a legendary wants adamantite parts, not copper ones)."""
        return [i for i in player_inventory if i.get_stat('part_id') == part_id
                and (ores is None or i.get_stat('part_ore_type') in ores)]

    def missing_slots(self, recipe: 'CraftingRecipe', player_inventory: List[Any]) -> List[str]:
        """Required slots of an assembly with no carried part for them (empty: can assemble)."""
        return [slot for slot, part_id in recipe.assembly_parts.items()
                if not self.parts_in(player_inventory, part_id, recipe.assembly_ore)]

    def parts_for(self, recipe: 'CraftingRecipe', player_inventory: List[Any],
                  part_ids: Optional[List[Any]] = None) -> List[Any]:
        """The parts an assembly consumes: one per required slot, plus any optional-slot part
        named in `part_ids`. With `part_ids`, exactly those (each must be carried, fit a slot
        of this assembly, and no slot twice; every required slot filled) or [] when wrong.
        Without, the best carried part per required slot (by its main stat), never a gem."""
        slot_of = {pid: slot for slot, pid in recipe.assembly_parts.items()}
        for slot in recipe.optional_slots:
            for r in self.recipes.values():
                if r.kind == 'part' and r.part_slot == slot:
                    slot_of[r.recipe_id] = slot
        if part_ids is not None:
            by_id = {i.entity_id: i for i in player_inventory if i.get_stat('part_id') in slot_of
                     and (recipe.assembly_ore is None
                          or i.get_stat('part_ore_type') in recipe.assembly_ore)}
            if len(set(part_ids)) != len(part_ids) or any(p not in by_id for p in part_ids):
                return []
            chosen = [by_id[p] for p in part_ids]
            slots = [slot_of[i.get_stat('part_id')] for i in chosen]
            if len(set(slots)) != len(slots) or not set(recipe.assembly_parts) <= set(slots):
                return []
            return chosen
        chosen = []
        for slot, part_id in recipe.assembly_parts.items():
            part_recipe = self.recipes[part_id]
            stat = self.main_stat(part_recipe)
            carried = self.parts_in(player_inventory, part_id, recipe.assembly_ore)
            chosen.append(max(carried, key=lambda i: (i.get_stat('part_stats') or {}).get(stat, 0))
                          if carried else None)
        return [] if None in chosen else chosen

    def assembly_stats(self, recipe: 'CraftingRecipe', parts: List[Any]) -> Dict[str, int]:
        """Sum of the parts' stats plus the assembly's fixed bonus (a material's)."""
        totals: Dict[str, int] = {}
        for part in parts:
            for stat, value in (part.get_stat('part_stats') or {}).items():
                totals[stat] = totals.get(stat, 0) + int(value)
        for stat, value in (recipe.fixed_stats or {}).items():
            totals[stat] = totals.get(stat, 0) + int(value)
        return totals

    def create_part(self, recipe_id: str, ore_items: List[Any]) -> Optional[Any]:
        """A part item from ore: stats from the averaged ore, remembers its ore for naming."""
        recipe = self.get_recipe(recipe_id)
        if not recipe or recipe.kind != 'part':
            logger.error(f"Part recipe not found: {recipe_id}")
            return None
        from .base.entity import Entity, EntityType
        props = self._average_ore_properties(ore_items)
        stats = recipe.calculate_stats(props)
        ore_type = ore_items[0].get_stat('ore_type') if ore_items else recipe.accepted_ore_types()[0]
        part = Entity(name=f"{ore_type.title()} {recipe.display_name}",
                      entity_type=EntityType.ITEM, x=None, y=None)
        part.set_stat('item_type', 'part')
        part.set_stat('part_slot', recipe.part_slot)
        part.set_stat('part_id', recipe_id)
        part.set_stat('recipe_id', recipe_id)       # like any crafted item: the recipe that made it
        part.set_stat('part_ore_type', ore_type)
        part.set_stat('part_stats', stats)
        part.set_stat('crafted_from_ore', props)
        return part

    def create_assembly(self, recipe_id: str, parts: List[Any]) -> Optional[Any]:
        """Wearable equipment from parts: stats are the parts' sum, named from the head's ore
        ('Mithril Sword'; 'Adamantite-Iron Sword' when the other parts' ore differs)."""
        recipe = self.get_recipe(recipe_id)
        if not recipe or recipe.kind != 'assembly' or not parts:
            logger.error(f"Assembly recipe not found or no parts: {recipe_id}")
            return None
        from .base.entity import Entity, EntityType
        stats = self.assembly_stats(recipe, parts)
        head_ore = parts[0].get_stat('part_ore_type')
        others = {p.get_stat('part_ore_type') for p in parts[1:]} - {head_ore}
        prefix = "-".join([head_ore.title()] + sorted(o.title() for o in others))
        equipment = Entity(name=f"{prefix} {recipe.display_name}",
                           entity_type=EntityType.ITEM, x=None, y=None)
        equipment.set_stat('item_type', recipe.item_type)
        equipment.set_stat('equipment_slot', recipe.equipment_slot)
        equipment.set_stat('recipe_id', recipe_id)
        for stat_name, value in stats.items():
            equipment.set_stat(stat_name, value)
        equipment.set_stat('crafted_from_ore', average_properties(
            [p.get_stat('crafted_from_ore') or {} for p in parts]))
        equipment.set_stat('crafted_ore_type', head_ore)
        equipment.set_stat('assembled_from', [p.get_stat('part_id') for p in parts])
        return equipment

    def preview_stats(self, recipe_id: str, player_inventory: List[Any],
                      ore_ids: Optional[List[Any]] = None) -> Optional[Dict[str, int]]:
        """Stats crafting `recipe_id` now would give (with `ore_ids`, from that ore), or None
        without enough (or a wrong pick of) ore."""
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            return None
        if recipe.kind == 'assembly':
            parts = self.parts_for(recipe, player_inventory, ore_ids)   # ore_ids: the part ids
            return self.assembly_stats(recipe, parts) if parts else None
        ore = self.ore_for(recipe, player_inventory, ore_ids)
        if len(ore) < recipe.get_required_ore_count():
            return None
        return recipe.calculate_stats(self._average_ore_properties(ore))

    def preview_from_properties(self, recipe_id: str,
                                properties: List[Dict[str, int]]) -> Optional[Dict[str, int]]:
        """Stats from ore described only by its properties (a client's ItemView.ore), so a
        forge screen previews a hand-picked set without the items themselves."""
        recipe = self.get_recipe(recipe_id)
        if not recipe or len(properties) != recipe.get_required_ore_count():
            return None
        return recipe.calculate_stats(average_properties(properties))

    def create_equipment(
        self,
        recipe_id: str,
        ore_items: List[Any]
    ) -> Optional[Any]:
        """
        Create equipment from recipe and ore.

        Args:
            recipe_id: Recipe to use
            ore_items: List of ore Entity objects to consume

        Returns:
            Equipment Entity, or None if failed
        """
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            logger.error(f"Recipe not found: {recipe_id}")
            return None
        if recipe.kind == 'part':
            return self.create_part(recipe_id, ore_items)

        # Calculate average ore properties
        ore_properties = self._average_ore_properties(ore_items)

        # Calculate equipment stats
        equipment_stats = recipe.calculate_stats(ore_properties)

        # Create equipment entity
        from .base.entity import Entity, EntityType

        equipment = Entity(
            name=recipe.display_name,
            entity_type=EntityType.ITEM,
            x=None,  # Not in world (in inventory)
            y=None,
        )

        # Set equipment properties
        equipment.set_stat('item_type', recipe.item_type)
        equipment.set_stat('equipment_slot', recipe.equipment_slot)
        equipment.set_stat('recipe_id', recipe_id)

        # Set calculated stats
        for stat_name, stat_value in equipment_stats.items():
            equipment.set_stat(stat_name, stat_value)

        # Set ore properties (for info display)
        equipment.set_stat('crafted_from_ore', ore_properties)
        # Not 'ore_type': that tag marks raw ore (see is_ore_item).
        equipment.set_stat('crafted_ore_type', recipe.get_required_ore_type())

        logger.info(
            f"Created equipment: {recipe.display_name}",
            extra={
                'recipe_id': recipe_id,
                'equipment_id': equipment.entity_id,
                'stats': equipment_stats,
                'ore_properties': ore_properties,
            }
        )

        return equipment

    def _average_ore_properties(self, ore_items: List[Any]) -> Dict[str, int]:
        """Average properties of ore items (each missing property counts as 50)."""
        return average_properties(
            [{name: ore.get_stat(name, 50) for name in ORE_PROPERTIES} for ore in ore_items])
