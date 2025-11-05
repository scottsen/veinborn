"""
AISystem - handles monster AI behavior.

Responsibilities:
- Run AI for all monsters each turn
- Simple chase/attack behavior for MVP
- Extensible for future AI types (flee, ranged, etc.)
"""

import logging
from ..base.system import System
from ..base.entity import EntityType
from ..actions.move_action import MoveAction
from ..actions.attack_action import AttackAction
from ..pathfinding import get_direction

logger = logging.getLogger(__name__)


class AISystem(System):
    """
    AI system for monster behavior.

    Design principles:
    - Simple aggressive AI for MVP
    - Easy to extend with different AI types
    - Uses action system (same code path as player)
    """

    def update(self, delta_time: float = 0) -> None:
        """Run AI for all monsters."""
        monsters = self.context.get_entities_by_type(EntityType.MONSTER)

        for monster in monsters:
            if not monster.is_alive:
                continue

            # Get AI type (future: different behaviors)
            ai_type = monster.get_stat('ai_type', 'aggressive')

            if ai_type == 'aggressive':
                self._aggressive_ai(monster)
            # Future: 'fleeing', 'ranged', 'guard', etc.

    def _aggressive_ai(self, monster) -> None:
        """
        Aggressive chase-and-attack AI.

        Behavior:
        - If adjacent to player: attack
        - Otherwise: move toward player
        """
        player = self.context.get_player()

        if not player.is_alive:
            return  # Player dead, nothing to do

        # Check if adjacent
        if monster.is_adjacent(player):
            # Attack player
            action = AttackAction(monster.entity_id, player.entity_id)
            outcome = action.execute(self.context)

            # Add messages to game log
            for msg in outcome.messages:
                self.context.add_message(msg)

            logger.debug(
                f"Monster {monster.name} attacked player",
                extra={'damage': outcome.events}
            )

        else:
            # Move toward player (A* pathfinding - avoids walls)
            game_map = self.context.get_map()
            direction = get_direction(
                game_map,
                start=(monster.x, monster.y),
                goal=(player.x, player.y),
                allow_diagonals=True
            )

            if direction:
                dx, dy = direction
                action = MoveAction(monster.entity_id, dx, dy)

                if action.validate(self.context):
                    outcome = action.execute(self.context)

                    # Only log if movement failed (unexpected)
                    if outcome.result.value != 'success':
                        logger.debug(
                            f"Monster {monster.name} failed to move",
                            extra={'reason': outcome.messages}
                        )
            # else: No path to player - stand still (do nothing)
