"""
Crafting system - turn mined ore into equipment.

This is Brogue's core unique hook: SWG-style ore properties → equipment stats

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

        # Ensure minimum stat value of 1 (even terrible ore makes usable gear)
        for stat_name in ['attack_bonus', 'defense_bonus', 'durability']:
            if stat_name in stats and stats[stat_name] < 1 and stat_name in self.stat_formulas:
                stats[stat_name] = 1

        logger.debug(
            f"Calculated stats for {self.recipe_id}",
            extra={'recipe_id': self.recipe_id, 'ore_properties': ore_properties, 'stats': stats}
        )

        return stats

    def get_required_ore_type(self) -> str:
        """Get the ore type required by this recipe."""
        return self.requirements.get('ore_type', 'copper')

    def get_required_ore_count(self) -> int:
        """Get the ore count required by this recipe."""
        return self.requirements.get('ore_count', 1)

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

    def _load_recipes(self):
        """Load all recipes from YAML file."""
        try:
            with open(self.recipes_path, 'r') as f:
                data = yaml.safe_load(f)

            # Load weapons
            weapons = data.get('weapons', {})
            for recipe_id, recipe_data in weapons.items():
                self.recipes[recipe_id] = self._create_recipe(recipe_id, recipe_data)

            # Load armor
            armor = data.get('armor', {})
            for recipe_id, recipe_data in armor.items():
                self.recipes[recipe_id] = self._create_recipe(recipe_id, recipe_data)

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
            if recipe.get_required_ore_type() == ore_type
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
        # Count ore by type in inventory
        ore_counts = {}
        for item in player_inventory:
            ore_type = item.get_stat('ore_type')
            if ore_type:
                ore_counts[ore_type] = ore_counts.get(ore_type, 0) + 1

        # Filter recipes by requirements
        craftable = []
        for recipe in self.recipes.values():
            # Check floor requirement
            if current_floor < recipe.get_min_floor():
                continue

            # Check ore requirement
            required_type = recipe.get_required_ore_type()
            required_count = recipe.get_required_ore_count()
            if ore_counts.get(required_type, 0) >= required_count:
                craftable.append(recipe)

        return craftable

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
        craftable = self.get_craftable_recipes(player_inventory, current_floor)
        if not craftable:
            return None

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
                type_priority = 1 if is_weapon else 0
            elif preference == 'defense':
                # Prefer armor
                type_priority = 1 if is_armor else 0
            else:  # balanced
                # Alternate: slightly prefer weapons
                type_priority = 1 if is_weapon else 0

            # Return tuple: (tier, type_priority, ore_count)
            # Negated for reverse sorting (higher = better)
            return (-tier, -type_priority, recipe.get_required_ore_count())

        # Sort and return best recipe
        sorted_recipes = sorted(craftable, key=recipe_priority)
        return sorted_recipes[0].recipe_id

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

        # Count ore in inventory
        ore_counts = {}
        for item in player_inventory:
            ore_type = item.get_stat('ore_type')
            if ore_type:
                ore_counts[ore_type] = ore_counts.get(ore_type, 0) + 1

        # Check ore requirement
        required_type = recipe.get_required_ore_type()
        required_count = recipe.get_required_ore_count()
        available = ore_counts.get(required_type, 0)

        if available < required_count:
            return False, f"Requires {required_count}x {required_type} ore (have {available})"

        return True, None

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
        equipment.set_stat('ore_type', recipe.get_required_ore_type())

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
        """
        Calculate average properties from multiple ore items.

        Args:
            ore_items: List of ore Entity objects

        Returns:
            Dict with average hardness, conductivity, malleability, purity, density
        """
        if not ore_items:
            return {
                'hardness': 50,
                'conductivity': 50,
                'malleability': 50,
                'purity': 50,
                'density': 50,
            }

        properties = {
            'hardness': [],
            'conductivity': [],
            'malleability': [],
            'purity': [],
            'density': [],
        }

        for ore in ore_items:
            for prop_name in properties.keys():
                value = ore.get_stat(prop_name, 50)
                properties[prop_name].append(value)

        # Calculate averages
        avg_properties = {}
        for prop_name, values in properties.items():
            avg_properties[prop_name] = round(sum(values) / len(values))

        return avg_properties
