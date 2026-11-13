"""
PerceptionService - Pure functions for querying game state.

Responsibility: Answer "What do I see?"
- Extract information from game state
- No logging (just return data)
- No decision-making (that's for TacticalDecisionService)
- All static/pure functions (no state)

Phase 2 Service Extraction - Step 1
"""

import logging
from typing import List, Optional, Tuple
from enum import Enum

# Configure logger for buffered I/O (5-10% performance improvement in verbose mode)
logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat classification for monsters."""
    TRIVIAL = "trivial"      # Goblins
    MANAGEABLE = "manageable"  # Orcs
    DANGEROUS = "dangerous"   # Trolls
    DEADLY = "deadly"        # Bosses
    UNKNOWN = "unknown"      # No intelligence data


class PerceptionService:
    """Pure functions for querying game state."""

    def __init__(self, verbose: bool = False):
        """
        Initialize perception service.

        Args:
            verbose: Enable verbose perception logging
        """
        self.verbose = verbose
        # Turn-based caching for performance (2-3x speedup)
        self._cache = {}
        self._cache_turn = -1

    def start_turn(self, turn: int) -> None:
        """
        Invalidate cache at start of new turn.

        Call this from bot's game loop to enable caching.

        Args:
            turn: Current turn number
        """
        if turn != self._cache_turn:
            self._cache.clear()
            self._cache_turn = turn

    # ========================================================================
    # Monster Perception
    # ========================================================================

    def find_monsters(self, game) -> List:
        """Get all living monsters in the game."""
        # Check cache first (performance optimization)
        if 'monsters' in self._cache:
            return self._cache['monsters']

        from core.entities import Monster
        monsters = [
            entity for entity in game.state.entities.values()
            if isinstance(entity, Monster) and entity.is_alive
        ]

        # Cache result for this turn
        self._cache['monsters'] = monsters

        if self.verbose and monsters:
            logger.debug(f"find_monsters: {len(monsters)} alive ({', '.join(m.name for m in monsters[:3])}{'...' if len(monsters) > 3 else ''})")

        return monsters

    def find_nearest_monster(self, game) -> Optional:
        """Find closest living monster to player."""
        monsters = self.find_monsters(game)
        if not monsters:
            return None

        player = game.state.player
        nearest = min(
            monsters,
            key=lambda m: player.distance_to(m)
        )

        if self.verbose:
            dist = player.distance_to(nearest)
            logger.debug(f"find_nearest_monster: {nearest.name} at distance {dist:.1f}")

        return nearest

    
    def monster_in_view(self, game, distance: float = 10.0) -> Optional:
        """
        Check if any monster is within viewing distance.

        Returns closest monster within range, or None.
        """
        nearest = self.find_nearest_monster(game)
        if nearest and game.state.player.distance_to(nearest) <= distance:
            return nearest
        return None

    
    def is_adjacent_to_monster(self, game) -> Optional:
        """
        Check if player is adjacent to any monster.

        Uses is_adjacent() method (not distance!) to properly handle diagonals.
        """
        nearest = self.find_nearest_monster(game)
        if nearest and game.state.player.is_adjacent(nearest):
            return nearest
        return None

    # ========================================================================
    # Ore Perception
    # ========================================================================


    def find_ore_veins(self, game) -> List:
        """Get all ore veins in the game."""
        # Check cache first (performance optimization)
        if 'ore_veins' in self._cache:
            return self._cache['ore_veins']

        from core.entities import OreVein
        ore_veins = [
            entity for entity in game.state.entities.values()
            if isinstance(entity, OreVein)
        ]

        # Cache result for this turn
        self._cache['ore_veins'] = ore_veins
        return ore_veins

    
    def find_adjacent_ore(self, game) -> Optional:
        """
        Find ore vein adjacent to player (for mining validation).

        Returns first adjacent ore, or None.
        """
        ore_veins = self.find_ore_veins(game)
        player = game.state.player

        for ore in ore_veins:
            if player.is_adjacent(ore):
                return ore

        return None

    
    def find_valuable_ore(self, game) -> Optional:
        """
        Find nearby ore veins worth mining (high purity for Legacy Vault).

        Priority:
        1. Surveyed high-purity ore (80+ for Legacy Vault)
        2. Surveyed medium-purity ore (70+)
        3. Unsurveyed ore nearby (might be valuable)

        Returns closest valuable ore, or None.
        """
        ore_veins = self.find_ore_veins(game)

        # Priority 1: Surveyed high-purity ore (80+ = Legacy Vault!)
        legacy_ore = [
            ore for ore in ore_veins
            if ore.get_stat('surveyed') and ore.get_stat('purity', 0) >= 80
        ]
        if legacy_ore:
            closest = min(legacy_ore, key=lambda o: game.state.player.distance_to(o))
            return closest

        # Priority 2: Surveyed medium-purity ore (70+)
        good_ore = [
            ore for ore in ore_veins
            if ore.get_stat('surveyed') and ore.get_stat('purity', 0) >= 70
        ]
        if good_ore:
            closest = min(good_ore, key=lambda o: game.state.player.distance_to(o))
            return closest

        # Priority 3: Unsurveyed ore nearby (might be valuable)
        unsurveyed = [
            ore for ore in ore_veins
            if not ore.get_stat('surveyed')
            and game.state.player.distance_to(ore) <= 3
        ]
        if unsurveyed:
            return min(unsurveyed, key=lambda o: game.state.player.distance_to(o))

        return None

    
    def find_jackpot_ore(self, game) -> Optional:
        """
        Find jackpot ore (all properties 80-100) - extremely valuable!

        Jackpot ore is a 5% spawn chance with exceptional quality.
        This is the holy grail of mining.
        """
        from core.entities import OreVein
        ore_veins = [
            e for e in game.state.entities.values()
            if isinstance(e, OreVein) and e.get_stat('surveyed')
        ]

        for ore in ore_veins:
            # Check if ALL properties are 80+ (jackpot!)
            if all([
                ore.get_stat('hardness', 0) >= 80,
                ore.get_stat('conductivity', 0) >= 80,
                ore.get_stat('malleability', 0) >= 80,
                ore.get_stat('purity', 0) >= 80,
                ore.get_stat('density', 0) >= 80,
            ]):
                return ore

        return None

    
    def find_unsurveyed_ore_nearby(self, game, max_distance: float = 3.0) -> Optional:
        """
        Find unsurveyed ore within distance threshold.

        Returns closest unsurveyed ore, or None.
        """
        ore_veins = self.find_ore_veins(game)
        player = game.state.player

        unsurveyed = [
            ore for ore in ore_veins
            if not ore.get_stat('surveyed')
            and player.distance_to(ore) <= max_distance
        ]

        if unsurveyed:
            return min(unsurveyed, key=lambda o: player.distance_to(o))

        return None

    # ========================================================================
    # Environment Perception
    # ========================================================================

    
    def find_materials(self, game) -> List:
        """Boss materials on the floor (items.yaml materials): legendary recipes consume them."""
        from core.base.entity import EntityType
        return [
            e for e in game.state.entities.values()
            if e.entity_type == EntityType.ITEM and e.x is not None and e.is_alive
            and e.get_stat('item_type') == 'material'
        ]

    def find_usable_items(self, game) -> List:
        """Items on the floor whose effect the game can apply (potions, food)."""
        if 'usable_items' in self._cache:
            return self._cache['usable_items']
        from core.base.entity import EntityType
        from core.actions.use_item_action import usable_effect
        items = [
            e for e in game.state.entities.values()
            if e.entity_type == EntityType.ITEM and e.x is not None and e.is_alive
            and usable_effect(e)
        ]
        self._cache['usable_items'] = items
        return items

    def find_level_exit(self, game) -> Optional[Tuple[int, int]]:
        """
        Find stairs down to next level.

        Returns:
            Position of stairs, or None if not found
        """
        return game.state.dungeon_map.find_stairs_down()

    
    def on_stairs(self, game) -> bool:
        """Check if player is standing on stairs down."""
        stairs_pos = self.find_level_exit(game)
        if not stairs_pos:
            return False

        player = game.state.player
        return (player.x, player.y) == stairs_pos

    # ========================================================================
    # Crafting & Equipment Perception
    # ========================================================================


    def find_forges(self, game) -> List:
        """Get all forges in the game."""
        # Check cache first (performance optimization)
        if 'forges' in self._cache:
            return self._cache['forges']

        from core.entities import Forge
        forges = [
            entity for entity in game.state.entities.values()
            if isinstance(entity, Forge)
        ]

        # Cache result for this turn
        self._cache['forges'] = forges
        return forges

    
    def find_nearest_forge(self, game) -> Optional:
        """Find closest forge to player."""
        forges = self.find_forges(game)
        if not forges:
            return None

        player = game.state.player
        return min(forges, key=lambda f: player.distance_to(f))

    
    def has_unequipped_gear(self, game) -> Optional:
        """
        Find best unequipped item that's an upgrade over current gear.

        Returns None if:
        - No unequipped items
        - All unequipped items are worse than equipped gear
        """
        player = game.state.player

        if not hasattr(player, 'inventory') or not player.inventory:
            return None

        # Crafted gear has equipment_slot, looted gear only item_type: core's gear_slot
        # reads both, as EquipAction does (ore may carry bonuses but isn't equippable).
        # Reading equipment_slot alone left every looted weapon and armor unworn (VB-73).
        from core.actions.drop_action import gear_slot
        for item in player.inventory:
            equipment_slot = gear_slot(item)
            is_equipped_stat = item.get_stat('equipped', False)

            if equipment_slot:
                # Skip if item has 'equipped' stat set to True
                if is_equipped_stat:
                    continue

                # FIX EQUIP SPAM: Also check if this exact item is already equipped
                # by comparing to actor.equipped_weapon or actor.equipped_armor
                # (Some items may not have 'equipped' stat but are still equipped)
                if equipment_slot == 'weapon':
                    # Skip if this item is already the equipped weapon
                    if hasattr(player, 'equipped_weapon') and player.equipped_weapon:
                        if player.equipped_weapon.entity_id == item.entity_id:
                            continue
                        # NEW: Check if this is an upgrade (only equip better weapons)
                        current_attack = player.equipped_weapon.get_stat('attack_bonus', 0)
                        new_attack = item.get_stat('attack_bonus', 0)
                        if new_attack <= current_attack:
                            continue  # Not an upgrade, skip it

                elif equipment_slot == 'armor':
                    # Skip if this item is already the equipped armor
                    if hasattr(player, 'equipped_armor') and player.equipped_armor:
                        if player.equipped_armor.entity_id == item.entity_id:
                            continue
                        # NEW: Check if this is an upgrade (only equip better armor)
                        current_defense = player.equipped_armor.get_stat('defense_bonus', 0)
                        new_defense = item.get_stat('defense_bonus', 0)
                        if new_defense <= current_defense:
                            continue  # Not an upgrade, skip it

                # This item passed all checks - it's an upgrade!
                return item

        return None

    
    def has_craftable_ore(self, game) -> Optional[str]:
        """
        The recipe whose result most improves on the gear worn in its slot, or None.

        Uses the game's own preview (RecipeManager.preview_stats: the ore CraftAction
        would consume, the recipe's formulas), so only real upgrades are crafted.
        Crafting whatever suggest_recipe ranked first made a warrior craft 53 items in
        6000 turns, most never worn, and burn the ore and turns (VB-73).
        """
        from core.actions.craft_action import CraftAction
        from core.actions.drop_action import gear_bonus
        player = game.state.player

        if not hasattr(player, 'inventory') or not player.inventory:
            return None

        # The game's shared RecipeManager: building one per call re-read recipes.yaml
        # every turn and was ~94% of a bot game's run time
        recipe_manager = CraftAction.get_recipe_manager()
        best, best_gain = None, 0
        for recipe in recipe_manager.get_craftable_recipes(player.inventory, game.context.get_floor()):
            slot = recipe.equipment_slot
            if slot not in ('weapon', 'armor'):
                continue
            stats = recipe_manager.preview_stats(recipe.recipe_id, player.inventory)
            new = (stats or {}).get('attack_bonus' if slot == 'weapon' else 'defense_bonus', 0)
            worn = player.equipped_weapon if slot == 'weapon' else player.equipped_armor
            gain = new - (gear_bonus(worn, slot) if worn is not None else 0)
            if gain > best_gain:
                best, best_gain = recipe.recipe_id, gain
        return best

    # ========================================================================
    # Threat Assessment
    # ========================================================================


    def assess_threat(self, monster, threat_rankings: dict) -> ThreatLevel:
        """
        Get threat classification: trivial, manageable, dangerous, deadly.

        Uses YAML-loaded monster stats for perfect information.

        Args:
            monster: Monster entity
            threat_rankings: Dict of monster_id -> threat_score

        Returns:
            ThreatLevel enum
        """
        if not monster.content_id:
            return ThreatLevel.UNKNOWN

        threat_score = threat_rankings.get(monster.content_id, 0)

        if threat_score < 30:
            return ThreatLevel.TRIVIAL   # Goblins (6*3/1 = 18)
        elif threat_score < 100:
            return ThreatLevel.MANAGEABLE  # Orcs (12*5/2 = 30)
        elif threat_score < 200:
            return ThreatLevel.DANGEROUS  # Trolls (20*7/3 = 46.7)
        else:
            return ThreatLevel.DEADLY     # Future boss monsters
