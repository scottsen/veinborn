"""
ActionPlanner - Plans and creates validated actions.

Responsibility: Answer "How do I do it?"
- Convert decisions into game actions
- Handle pathfinding and movement
- Validate actions before execution
- Coordinate perception and tactical decisions

Phase 2 Service Extraction - Step 3
"""

from typing import Tuple, Optional
import random


class ActionPlanner:
    """Plans and creates validated actions."""

    def __init__(
        self,
        perception,  # PerceptionService
        decisions,   # TacticalDecisionService
        verbose: bool = False
    ):
        """
        Initialize action planner.

        Args:
            perception: PerceptionService instance
            decisions: TacticalDecisionService instance
            verbose: Enable verbose logging
        """
        self.perception = perception
        self.decisions = decisions
        self.verbose = verbose

    def log(self, message: str) -> None:
        """Log message if verbose enabled."""
        if self.verbose:
            print(f"[BOT] {message}")

    # ========================================================================
    # High-Level Planning
    # ========================================================================

    def plan_next_action(self, game, mode: str = 'strategic') -> Tuple[str, dict]:
        """
        Choose next action based on mode.

        Modes:
        - 'strategic': Use smart action selection
        - 'random': Random valid actions
        - 'hybrid': 50/50 mix

        Args:
            game: Game instance
            mode: Action selection mode

        Returns:
            Tuple of (action_type, kwargs)
        """
        if mode == 'random':
            return self.get_random_action(game)
        elif mode == 'strategic':
            return self.get_smart_action(game)
        else:  # hybrid
            if random.random() < 0.5:
                return self.get_smart_action(game)
            else:
                return self.get_random_action(game)

    def get_smart_action(self, game) -> Tuple[str, dict]:
        """
        Choose action strategically to try to win.

        Enhanced Decision Tree (With Crafting/Equipment!):
        0. If actively mining → CONTINUE MINING (multi-turn action)
        1. If unequipped gear → EQUIP IT! (instant, no turn cost)
        2. If craftable ore + near forge → CRAFT EQUIPMENT!
        3. If on stairs and floor cleared → DESCEND
        4. If monster adjacent → FIGHT (forced combat)
        5. If jackpot ore nearby and safe → MINE IT!
        6. If low health and monster nearby → FLEE TO STAIRS
        7. If high-quality ore nearby (70+) and safe → MINE IT
        8. If unsurveyed ore nearby → SURVEY IT
        9. If monster in view and we can win → PURSUE
        10. If floor cleared → SEEK STAIRS
        11. Otherwise → random exploration

        Returns:
            Tuple of (action_type, kwargs)
        """
        # Priority 0: Continue active mining (multi-turn action)
        mining_state = game.state.player.get_stat('mining_action')
        if mining_state and mining_state.get('turns_remaining', 0) > 0:
            turns_left = mining_state.get('turns_remaining', 0)
            self.log(f"⛏️  Continuing mining... {turns_left} turns remaining")
            return ('mine', {})

        # Priority 1: Equip better gear (instant action!)
        better_gear = self.perception.has_unequipped_gear(game)
        if better_gear:
            self.log(f"🎽 Equipping {better_gear.name}!")
            return ('equip', {'item_id': better_gear.entity_id})

        # Priority 2: Craft equipment if possible
        if self.decisions.should_craft(game):
            craftable = self.perception.has_craftable_ore(game)
            forge = self.perception.find_nearest_forge(game)
            if forge and craftable:
                dist = game.state.player.distance_to(forge)
                if game.state.player.is_adjacent(forge):
                    # Adjacent to forge - craft!
                    self.log(f"🔨 Crafting {craftable} at forge!")
                    return ('craft', {'forge_id': forge.entity_id, 'recipe_id': craftable})
                elif dist > 2:
                    # Seek adjacent tile to forge (forge blocks movement)
                    self.log(f"🔨 Seeking forge to craft {craftable}! (distance: {dist:.1f})")
                    return self.move_towards_adjacent(game, forge)
                # If close but not adjacent (dist <= 2), explore randomly

        # Priority 3: Descend if ready
        if self.decisions.should_descend(game):
            return ('descend', {})

        # Priority 4: Forced combat (monster adjacent)
        adjacent = self.perception.is_adjacent_to_monster(game)
        if adjacent:
            threat = self.perception.assess_threat(adjacent, {})
            player = game.state.player
            self.log(f"⚔️  Fighting {adjacent.name} ({threat}) at ({adjacent.x},{adjacent.y})")
            return self.move_towards(game, adjacent)

        # Priority 5: JACKPOT ORE
        jackpot = self.perception.find_jackpot_ore(game)
        if jackpot and not self.decisions.is_low_health(game):
            dist = game.state.player.distance_to(jackpot)
            if game.state.player.is_adjacent(jackpot):
                self.log(f"💎 Mining JACKPOT ore! {jackpot.ore_type}")
                return ('mine', {})
            elif dist > 2 and dist <= 5:
                # Seek adjacent tile to ore (ore blocks movement)
                self.log(f"💎 Seeking JACKPOT ore! Distance: {dist:.1f}")
                return self.move_towards_adjacent(game, jackpot)
            # If close but not adjacent (dist <= 2), explore randomly

        # Priority 6: Flee if in danger
        if self.decisions.should_flee(game):
            # Try to descend immediately if on stairs (emergency escape)
            if self.perception.on_stairs(game):
                player = game.state.player
                self.log(f"🚨 Emergency descent! (HP: {player.hp}/{player.max_hp})")
                return ('descend', {})

            # Seek stairs to escape
            stairs_pos = self.perception.find_level_exit(game)
            if stairs_pos:
                player = game.state.player
                dist = abs(player.x - stairs_pos[0]) + abs(player.y - stairs_pos[1])
                self.log(f"💀 Low health! Fleeing to stairs! (HP: {player.hp}/{player.max_hp}, distance: {dist})")

                # Create temporary entity to use move_towards
                from core.base.entity import Entity, EntityType
                stairs_entity = Entity(
                    entity_type=EntityType.PLAYER,
                    name="Stairs",
                    x=stairs_pos[0],
                    y=stairs_pos[1],
                )
                return self.move_towards(game, stairs_entity)

            # No stairs found - flee from nearest threat
            nearby = self.perception.monster_in_view(game, distance=5.0)
            if nearby:
                self.log("💀 Low health! Fleeing from danger!")
                return self.flee_from(game, nearby)

        # Priority 7: Strategic mining
        valuable_ore = self.perception.find_valuable_ore(game)
        if valuable_ore and not self.decisions.is_low_health(game):
            dist = game.state.player.distance_to(valuable_ore)
            if game.state.player.is_adjacent(valuable_ore):
                # Adjacent to valuable ore
                if valuable_ore.get_stat('surveyed'):
                    # Already surveyed - mine if it's high quality
                    if self.decisions.should_mine_strategically(game, valuable_ore):
                        purity = valuable_ore.get_stat('purity', 0)
                        self.log(f"⛏️  Mining high-quality {valuable_ore.ore_type} ore (purity: {purity})!")
                        return ('mine', {})
                else:
                    # Not surveyed - survey it first
                    self.log(f"🔍 Surveying {valuable_ore.ore_type} ore...")
                    return ('survey', {})
            elif dist > 2 and dist <= 4 and valuable_ore.get_stat('purity', 0) >= 80:
                # Seek adjacent tile to Legacy Vault quality ore (ore blocks movement)
                self.log(f"⛏️  Seeking Legacy Vault ore! Distance: {dist:.1f}")
                return self.move_towards_adjacent(game, valuable_ore)

        # Priority 8: Survey nearby unsurveyed ore
        unsurveyed_ore = self.decisions.should_survey_ore(game)
        if unsurveyed_ore and not self.decisions.is_low_health(game):
            dist = game.state.player.distance_to(unsurveyed_ore)
            if game.state.player.is_adjacent(unsurveyed_ore):
                self.log(f"🔍 Surveying nearby {unsurveyed_ore.ore_type} ore...")
                return ('survey', {})

        # Priority 9: Pursue monsters if we can win
        if self.decisions.should_fight(game):
            nearby = self.perception.monster_in_view(game, distance=5.0)
            if nearby:
                self.log(f"⚔️  Pursuing {nearby.name}!")
                return self.move_towards(game, nearby)

        # Priority 10: Seek stairs if floor cleared
        monsters_alive = len(self.perception.find_monsters(game))
        if monsters_alive == 0:
            stairs_pos = self.perception.find_level_exit(game)
            if stairs_pos:
                self.log("🎯 Floor cleared! Seeking stairs...")
                from core.base.entity import Entity, EntityType
                stairs_entity = Entity(
                    entity_type=EntityType.PLAYER,
                    name="Stairs",
                    x=stairs_pos[0],
                    y=stairs_pos[1],
                )
                return self.move_towards(game, stairs_entity)

        # Priority 11: Random exploration
        self.log("🗺️  Exploring randomly...")
        return self.get_random_action(game)

    def get_random_action(self, game) -> Tuple[str, dict]:
        """
        Choose a random valid action.

        Only includes mine/survey if adjacent to ore (context-aware).

        Returns:
            Tuple of (action_type, kwargs)
        """
        from core.entities import EntityType

        # Base action weights (movement and waiting)
        action_weights = {
            'move': 70,      # Most common
            'wait': 30,      # Sometimes do nothing
        }

        # Only add mining/surveying if there's adjacent ore
        player = game.state.player
        adjacent_ore = None
        for entity in game.state.entities.values():
            if entity.entity_type == EntityType.ORE_VEIN and player.is_adjacent(entity):
                adjacent_ore = entity
                break

        # If adjacent to ore, allow survey/mine actions
        if adjacent_ore:
            action_weights['survey'] = 10
            action_weights['mine'] = 10

        action = random.choices(
            list(action_weights.keys()),
            weights=list(action_weights.values())
        )[0]

        if action == 'move':
            # Random 8-directional movement
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            if dx == 0 and dy == 0:  # Don't stand still
                dx = 1
            return ('move', {'dx': dx, 'dy': dy})
        elif action == 'survey':
            return ('survey', {})
        elif action == 'mine':
            return ('mine', {})
        elif action == 'wait':
            return ('wait', {})

        return ('move', {'dx': 1, 'dy': 0})  # Default: move right

    # ========================================================================
    # Movement Actions
    # ========================================================================

    def move_towards(self, game, target) -> Tuple[str, dict]:
        """
        Get move action towards target using A* pathfinding.

        Args:
            game: Game instance
            target: Entity to move towards

        Returns:
            Tuple of (action_type, kwargs)
        """
        from core.pathfinding import get_direction

        player = game.state.player
        start = (player.x, player.y)
        goal = (target.x, target.y)

        # Use A* to find optimal path
        direction = get_direction(game.state.dungeon_map, start, goal)

        if direction:
            dx, dy = direction
            new_x, new_y = player.x + dx, player.y + dy
            self.log(f"   A* pathfinding: ({player.x},{player.y}) → ({new_x},{new_y})")
            return ('move', {'dx': dx, 'dy': dy})

        # Fallback to simple direction if A* fails
        moves_to_try = []

        # Prioritize moves that get us closer to target
        if target.x > player.x:
            moves_to_try.append((1, 0))   # Right
        elif target.x < player.x:
            moves_to_try.append((-1, 0))  # Left

        if target.y > player.y:
            moves_to_try.append((0, 1))   # Down
        elif target.y < player.y:
            moves_to_try.append((0, -1))  # Up

        # Try diagonal if both x and y need adjustment
        if target.x > player.x and target.y > player.y:
            moves_to_try.insert(0, (1, 1))
        elif target.x > player.x and target.y < player.y:
            moves_to_try.insert(0, (1, -1))
        elif target.x < player.x and target.y > player.y:
            moves_to_try.insert(0, (-1, 1))
        elif target.x < player.x and target.y < player.y:
            moves_to_try.insert(0, (-1, -1))

        # Try each move in priority order
        for dx, dy in moves_to_try:
            new_x = player.x + dx
            new_y = player.y + dy
            if game.state.dungeon_map.is_walkable(new_x, new_y):
                self.log(f"   Fallback: moving ({dx:+d}, {dy:+d})")
                return ('move', {'dx': dx, 'dy': dy})

        # If we can't move towards target, try random exploration
        self.log("   Fallback failed - target unreachable, exploring randomly")
        return self.get_random_action(game)

    def move_towards_adjacent(self, game, target) -> Tuple[str, dict]:
        """
        Get move action towards a tile adjacent to target.

        Used for entities that block movement (ore veins, forges).
        Finds the closest walkable tile adjacent to the target and pathfinds there.

        Args:
            game: Game instance
            target: Entity to move adjacent to (must have x, y)

        Returns:
            Tuple of (action_type, kwargs)
        """
        player = game.state.player

        # Find all 8 adjacent positions to target
        adjacent_positions = [
            (target.x - 1, target.y - 1), (target.x, target.y - 1), (target.x + 1, target.y - 1),
            (target.x - 1, target.y),                                (target.x + 1, target.y),
            (target.x - 1, target.y + 1), (target.x, target.y + 1), (target.x + 1, target.y + 1),
        ]

        # Filter for walkable positions
        walkable_adjacent = [
            pos for pos in adjacent_positions
            if game.state.dungeon_map.is_walkable(pos[0], pos[1])
        ]

        if not walkable_adjacent:
            self.log(f"   No walkable adjacent tiles to {target.name}!")
            return self.get_random_action(game)

        # Find closest walkable adjacent position to player
        def distance(pos):
            dx = pos[0] - player.x
            dy = pos[1] - player.y
            return dx * dx + dy * dy

        closest_adjacent = min(walkable_adjacent, key=distance)

        # Create temporary entity at that position for move_towards
        from core.base.entity import Entity, EntityType
        adjacent_target = Entity(
            entity_type=EntityType.PLAYER,
            name=f"Adjacent to {target.name}",
            x=closest_adjacent[0],
            y=closest_adjacent[1],
        )

        self.log(f"   Moving to adjacent tile of {target.name} at {closest_adjacent}")
        return self.move_towards(game, adjacent_target)

    def flee_from(self, game, threat) -> Tuple[str, dict]:
        """
        Get move action away from threat.

        Strategy: Find a walkable position that maximizes distance from threat.

        Args:
            game: Game instance
            threat: Entity to flee from

        Returns:
            Tuple of (action_type, kwargs)
        """
        player = game.state.player

        # Get all possible moves
        moves = [
            (-1, -1), (0, -1), (1, -1),
            (-1,  0),          (1,  0),
            (-1,  1), (0,  1), (1,  1),
        ]

        best_move = None
        best_distance = player.distance_to(threat)

        # Find move that maximizes distance from threat
        for dx, dy in moves:
            new_x = player.x + dx
            new_y = player.y + dy

            # Check if move is valid
            if not game.state.dungeon_map.in_bounds(new_x, new_y):
                continue
            if not game.state.dungeon_map.is_walkable(new_x, new_y):
                continue

            # Calculate distance from threat at new position
            dist = abs(new_x - threat.x) + abs(new_y - threat.y)

            if dist > best_distance:
                best_distance = dist
                best_move = (dx, dy)

        if best_move:
            new_x, new_y = player.x + best_move[0], player.y + best_move[1]
            self.log(f"   Fleeing: ({player.x},{player.y}) → ({new_x},{new_y}), dist={best_distance:.1f}")
            return ('move', {'dx': best_move[0], 'dy': best_move[1]})

        # No good escape - try any walkable move
        random.shuffle(moves)
        for dx, dy in moves:
            new_x = player.x + dx
            new_y = player.y + dy
            if game.state.dungeon_map.is_walkable(new_x, new_y):
                self.log(f"   Fleeing (desperate): ({player.x},{player.y}) → ({new_x},{new_y})")
                return ('move', {'dx': dx, 'dy': dy})

        # Completely trapped - stand and fight
        self.log("   Fleeing failed - trapped!")
        return ('wait', {})

    # ========================================================================
    # Action Validation
    # ========================================================================

    def validate_action(self, game, action_type: str, kwargs: dict) -> bool:
        """
        Validate action before execution.

        Prevents common errors like:
        - Mining when not adjacent to ore
        - Moving into walls
        - Invalid action parameters

        Args:
            game: Game instance
            action_type: Type of action
            kwargs: Action parameters

        Returns:
            True if action is valid
        """
        player = game.state.player

        if action_type == 'move':
            dx = kwargs.get('dx', 0)
            dy = kwargs.get('dy', 0)
            new_x = player.x + dx
            new_y = player.y + dy

            # Check bounds and walkability
            if not game.state.dungeon_map.in_bounds(new_x, new_y):
                return False
            if not game.state.dungeon_map.is_walkable(new_x, new_y):
                return False

            return True

        elif action_type == 'mine':
            # Must be adjacent to ore
            adjacent_ore = self.perception.find_adjacent_ore(game)
            return adjacent_ore is not None

        elif action_type == 'survey':
            # Must be adjacent to unsurveyed ore
            adjacent_ore = self.perception.find_adjacent_ore(game)
            if adjacent_ore and not adjacent_ore.get_stat('surveyed'):
                return True
            return False

        elif action_type in ('wait', 'descend', 'equip', 'craft'):
            # These are always valid (game engine will reject if not)
            return True

        # Unknown action type
        return False
