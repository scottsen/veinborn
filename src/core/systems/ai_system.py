"""
AISystem - handles monster AI behavior.

Responsibilities:
- Run AI for all monsters each turn
- Multiple AI behavior types (aggressive, defensive, passive, coward, guard)
- Data-driven configuration via YAML
- Extensible: behaviors are registered by name (see core.extensions)
"""

import logging
from typing import Optional, Dict, Any
from ..base.system import System
from ..base.entity import EntityType
from ..actions.move_action import MoveAction
from ..actions.attack_action import AttackAction
from ..pathfinding import get_direction
from ..config.config_loader import ConfigLoader
from .ai_behavior_registry import AIBehaviorRegistry

logger = logging.getLogger(__name__)


class AISystem(System):
    """
    AI system with multiple behavior types.

    Behaviors:
    - aggressive: Chase and attack player
    - defensive: Attack when close, flee when low HP
    - passive: Wander unless attacked
    - coward: Always flee from player
    - guard: Defend spawn area
    """

    def __init__(self, context):
        """
        Initialize AI system with config and behavior registry.

        Args:
            context: GameContext instance
        """
        super().__init__(context)
        self.config = ConfigLoader.get_config()
        self.registry = AIBehaviorRegistry()
        self._register_builtin_behaviors()

    def _register_builtin_behaviors(self) -> None:
        """Register Python AI behaviors in registry."""
        self.registry.register_python_behavior("aggressive", self._behavior_aggressive)
        self.registry.register_python_behavior("defensive", self._behavior_defensive)
        self.registry.register_python_behavior("passive", self._behavior_passive)
        self.registry.register_python_behavior("coward", self._behavior_coward)
        self.registry.register_python_behavior("guard", self._behavior_guard)
        logger.debug("Registered 5 built-in AI behaviors")

    def update(self, delta_time: float = 0) -> None:
        """Run AI for all monsters."""
        monsters = self.context.get_entities_by_type(EntityType.MONSTER)

        for monster in monsters:
            if not monster.is_alive:
                continue

            # Remember where the monster started (guards leash to this point)
            if 'spawn_x' not in monster.stats:
                monster.set_stat('spawn_x', monster.x)
                monster.set_stat('spawn_y', monster.y)

            # Get AI type (from monster or default)
            ai_type = monster.get_stat('ai_type', 'aggressive')

            # Get behavior config
            behavior_config = self.config.get_ai_behavior_config(ai_type)

            # Execute behavior
            self._execute_behavior(monster, ai_type, behavior_config)

    def _get_nearest_player(self, monster) -> Optional['Entity']:
        """
        Get the nearest alive player to a monster (for multiplayer support).

        Args:
            monster: Monster entity

        Returns:
            Nearest alive player entity, or None if no players alive
        """
        alive_players = self.context.get_alive_players()

        if not alive_players:
            return None

        # Find nearest player by Manhattan distance
        nearest_player = None
        nearest_distance = float('inf')

        for player in alive_players:
            distance = abs(monster.x - player.x) + abs(monster.y - player.y)
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_player = player

        return nearest_player

    def _execute_behavior(
        self,
        monster,
        ai_type: str,
        behavior_config: Dict[str, Any]
    ) -> None:
        """
        Execute AI behavior based on type.

        Behaviors come from the registry and act on the world directly.
        """
        # Get behavior from registry
        behavior_fn = self.registry.get_behavior(ai_type)

        if not behavior_fn:
            logger.warning(f"Unknown AI type: {ai_type}, using aggressive")
            behavior_fn = self.registry.get_behavior("aggressive")

        behavior_fn(monster, behavior_config)

    def _behavior_aggressive(
        self,
        monster,
        config: Dict[str, Any]
    ) -> None:
        """Aggressive: Chase and attack nearest player."""
        player = self._get_nearest_player(monster)

        if not player:
            self._wander(monster)
            return

        distance = abs(monster.x - player.x) + abs(monster.y - player.y)
        chase_range = config.get('chase_range', 10)

        # Attack if adjacent
        if monster.is_adjacent(player):
            self._attack_target(monster, player)
            return

        # Chase if in range
        if distance <= chase_range:
            self._move_towards(monster, player)
            return

        # Wander if out of range
        self._wander(monster)

    def _behavior_defensive(
        self,
        monster,
        config: Dict[str, Any]
    ) -> None:
        """Defensive: Attack when close, flee when low HP, otherwise patrol."""
        player = self._get_nearest_player(monster)

        if not player:
            self._wander(monster)
            return

        distance = abs(monster.x - player.x) + abs(monster.y - player.y)

        # Check if should flee
        hp_ratio = monster.hp / monster.max_hp
        flee_threshold = config.get('flee_threshold', 0.3)

        if hp_ratio < flee_threshold:
            self._flee_from(monster, player)
            return

        # Attack if adjacent
        if monster.is_adjacent(player):
            self._attack_target(monster, player)
            return

        # Chase if in range
        chase_range = config.get('chase_range', 5)
        if distance <= chase_range:
            self._move_towards(monster, player)
            return

        # Patrol/wander
        self._wander(monster)

    def _behavior_passive(
        self,
        monster,
        config: Dict[str, Any]
    ) -> None:
        """Passive: Wander peacefully, flee if attacked."""
        player = self._get_nearest_player(monster)

        if not player:
            self._wander(monster)
            return

        # Check if recently attacked (monster would track this)
        was_attacked = monster.get_stat('was_attacked_last_turn', False)

        if was_attacked:
            # Flee when attacked - flee from nearest player
            hp_ratio = monster.hp / monster.max_hp
            flee_threshold = config.get('flee_threshold', 0.5)

            if hp_ratio < flee_threshold:
                self._flee_from(monster, player)
                # Clear the flag after fleeing
                monster.set_stat('was_attacked_last_turn', False)
                return

        # Otherwise just wander
        self._wander(monster)

    def _behavior_coward(
        self,
        monster,
        config: Dict[str, Any]
    ) -> None:
        """Coward: Always flee from nearest player."""
        player = self._get_nearest_player(monster)

        if not player:
            self._wander(monster)
            return

        distance = abs(monster.x - player.x) + abs(monster.y - player.y)
        flee_range = config.get('flee_range', 8)

        if distance <= flee_range:
            self._flee_from(monster, player)
        else:
            self._wander(monster)

    def _behavior_guard(
        self,
        monster,
        config: Dict[str, Any]
    ) -> None:
        """Guard: Defend spawn area, attack nearest player within radius."""
        player = self._get_nearest_player(monster)

        # Get spawn position (stored when monster created)
        spawn_x = monster.get_stat('spawn_x', monster.x)
        spawn_y = monster.get_stat('spawn_y', monster.y)
        guard_radius = config.get('guard_radius', 4)

        # Check if too far from spawn
        distance_from_spawn = abs(monster.x - spawn_x) + abs(monster.y - spawn_y)
        if distance_from_spawn > guard_radius:
            # Return to spawn - create a temporary target entity
            class SpawnPoint:
                def __init__(self, x, y):
                    self.x = x
                    self.y = y

            spawn_point = SpawnPoint(spawn_x, spawn_y)
            self._move_towards(monster, spawn_point)
            return

        if not player:
            self._wander(monster)
            return

        # Normal aggressive behavior within guard radius
        distance_to_player = abs(monster.x - player.x) + abs(monster.y - player.y)

        if monster.is_adjacent(player):
            self._attack_target(monster, player)
            return

        chase_range = config.get('chase_range', 6)
        if distance_to_player <= chase_range and distance_from_spawn <= guard_radius:
            # Hold the line rather than step out of the leash (no border flip-flop)
            self._move_towards(monster, player, leash=(spawn_x, spawn_y, guard_radius))
            return

        self._wander(monster)

    def _attack_target(self, monster, target) -> None:
        """Attack a target."""
        action = AttackAction(monster.entity_id, target.entity_id)
        outcome = action.execute(self.context)

        # Add messages to game log
        for msg in outcome.messages:
            self.context.add_message(msg)

        logger.debug(
            f"Monster {monster.name} attacked {target.name}",
            extra={'damage': outcome.events}
        )

    def _flee_from(self, monster, target) -> None:
        """
        Move to the neighbouring tile that is farthest from target.

        Only steps that increase the distance are taken. A cornered monster
        (no such step) fights back if the target is adjacent, else holds still.
        """
        game_map = self.context.get_map()

        def dist2(x, y):
            return (x - target.x) ** 2 + (y - target.y) ** 2

        best, best_d = None, dist2(monster.x, monster.y)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = monster.x + dx, monster.y + dy
                if not game_map.is_walkable(nx, ny) or self.context.get_entity_at(nx, ny):
                    continue
                d = dist2(nx, ny)
                if d > best_d:
                    action = MoveAction(monster.entity_id, dx, dy)
                    if action.validate(self.context):
                        best, best_d = action, d

        if best:
            best.execute(self.context)
        elif monster.is_adjacent(target):
            self._attack_target(monster, target)  # cornered: bite back

    def _obstacle_tiles(self):
        """Tiles blocked by ore veins and forges (walkable terrain, solid entity)."""
        return {
            (e.x, e.y)
            for entity_type in (EntityType.ORE_VEIN, EntityType.FORGE)
            for e in self.context.get_entities_by_type(entity_type)
        }

    def _move_towards(self, monster, target, leash=None) -> None:
        """
        Move toward target using pathfinding, routing around ore veins and forges.

        Args:
            leash: Optional (x, y, radius). The monster will not step to a tile
                farther than `radius` (Manhattan) from (x, y).
        """
        game_map = self.context.get_map()
        direction = get_direction(
            game_map,
            start=(monster.x, monster.y),
            goal=(target.x, target.y),
            allow_diagonals=True,
            blocked=self._obstacle_tiles(),
        )

        if direction:
            dx, dy = direction

            if leash is not None:
                lx, ly, radius = leash
                if abs(monster.x + dx - lx) + abs(monster.y + dy - ly) > radius:
                    return  # Next step leaves the leash: hold position

            action = MoveAction(monster.entity_id, dx, dy)

            if action.validate(self.context):
                outcome = action.execute(self.context)

                # Only log if movement failed (unexpected)
                if outcome.result.value != 'success':
                    logger.debug(
                        f"Monster {monster.name} failed to move",
                        extra={'reason': outcome.messages}
                    )

    def _wander(self, monster) -> None:
        """Random movement."""
        rng = self.context.get_rng()

        # 50% chance to stand still (monsters don't always move)
        if rng.random() < 0.5:
            return

        # Pick random direction
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        rng.shuffle(directions)

        game_map = self.context.get_map()
        for dx, dy in directions:
            new_x = monster.x + dx
            new_y = monster.y + dy

            if game_map.is_walkable(new_x, new_y):
                action = MoveAction(monster.entity_id, dx, dy)
                if action.validate(self.context):
                    action.execute(self.context)
                    return
