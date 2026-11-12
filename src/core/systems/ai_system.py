"""
AISystem - handles monster AI behavior.

Responsibilities:
- Run AI for all monsters each turn
- Look up each monster's behaviour by name (monsters.yaml `ai: type:`)
- Provide the toolkit behaviours are written against

Behaviours are not defined here: they live in core/content/ai/ and register
with @ai_behavior (see core.extensions, docs/EXTENDING.md). The public methods
below (nearest_player, distance, in_sight, attack, move_towards, flee_from,
wander, summon) are the toolkit a behaviour calls.
"""

import logging
from functools import partial
from typing import Optional, Dict, Any
from ..base.system import System
from ..base.entity import EntityType
from ..actions.move_action import MoveAction
from ..actions.attack_action import AttackAction
from ..pathfinding import get_direction
from ..config.config_loader import ConfigLoader
from ..extensions import ai_behaviors
from ..geometry import chebyshev, has_line_of_sight
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

    def __init__(self, context, entity_loader=None):
        """
        Initialize AI system with config and behavior registry.

        Args:
            context: GameContext instance
            entity_loader: EntityLoader used by summon(); created on first use
                if not given
        """
        super().__init__(context)
        self.config = ConfigLoader.get_config()
        self.registry = AIBehaviorRegistry()
        self._entity_loader = entity_loader
        self._register_behaviors()

    def _register_behaviors(self) -> None:
        """Register every @ai_behavior from core.content, bound to this system."""
        for name, fn in ai_behaviors.items():
            self.registry.register_python_behavior(name, partial(fn, self))
        logger.debug(f"Registered {len(self.registry.list_behaviors())} AI behaviors")

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

    @staticmethod
    def distance(a, b) -> int:
        """Range between two entities (or anything with x, y): 8-way steps (Chebyshev)."""
        return chebyshev(a.x, a.y, b.x, b.y)

    def in_sight(self, a, b) -> bool:
        """True if no wall blocks the straight line between a and b."""
        game_map = self.context.get_map()
        return has_line_of_sight(a.x, a.y, b.x, b.y, game_map.is_transparent)

    def nearest_player(self, monster) -> Optional['Entity']:
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

        # Find the nearest player (ties: first in the player list)
        nearest_player = None
        nearest_distance = float('inf')

        for player in alive_players:
            distance = self.distance(monster, player)
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

        try:
            behavior_fn(monster, behavior_config)
        except Exception:
            # Content is pluggable: one buggy behaviour must not stop the turn.
            logger.exception(
                f"AI behavior '{ai_type}' failed for {monster.name}; monster skipped this turn"
            )

    def attack(self, monster, target, ranged: bool = False) -> None:
        """Attack a target (adjacent, or from range when ranged=True)."""
        action = AttackAction(monster.entity_id, target.entity_id, ranged=ranged)
        outcome = action.execute(self.context)

        # Add messages to game log
        for msg in outcome.messages:
            self.context.add_message(msg)

        logger.debug(
            f"Monster {monster.name} attacked {target.name}",
            extra={'damage': outcome.events}
        )

    def flee_from(self, monster, target) -> None:
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
            self.attack(monster, target)  # cornered: bite back

    def _obstacle_tiles(self):
        """Tiles blocked by ore veins and forges (walkable terrain, solid entity)."""
        return {
            (e.x, e.y)
            for entity_type in (EntityType.ORE_VEIN, EntityType.FORGE)
            for e in self.context.get_entities_by_type(entity_type)
        }

    def move_towards(self, monster, target, leash=None) -> None:
        """
        Move toward target using pathfinding, routing around ore veins and forges.

        Args:
            leash: Optional (x, y, radius). The monster will not step to a tile
                farther than `radius` (Chebyshev) from (x, y).
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
                if chebyshev(monster.x + dx, monster.y + dy, lx, ly) > radius:
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

    def wander(self, monster) -> None:
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

    def summon(self, monster, monster_id: str):
        """Create `monster_id` on a free tile next to `monster`; None if there is none.

        Used by behaviours that call for help. The new monster is added to the
        world and acts from the next turn.
        """
        from ..entity_loader import EntityLoader
        from ..spawning.entity_spawner import EntitySpawner

        if self._entity_loader is None:
            self._entity_loader = EntityLoader()
        minion = self._entity_loader.create_monster(monster_id, monster.x, monster.y)
        occupied = {
            (e.x, e.y) for e in self.context.game_state.entities.values() if e.x is not None
        }
        if not EntitySpawner._claim_free_tile(
            minion, occupied, self.context.get_map(), max_radius=3
        ):
            return None
        self.context.add_entity(minion)
        return minion
