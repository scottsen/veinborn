"""
MoveAction - move entity by offset.

Handles:
- Movement validation (bounds, walkable)
- Collision detection
- Auto-attack if bumping into enemy
"""

import logging
from dataclasses import dataclass
from ..base.action import Action, ActionOutcome
from ..base.game_context import GameContext
from ..base.entity import EntityType

logger = logging.getLogger(__name__)


@dataclass
class MoveAction(Action):
    """Move entity by offset."""

    actor_id: str
    dx: int
    dy: int

    def validate(self, context: GameContext) -> bool:
        """Check if move is valid."""
        actor = self._get_and_validate_actor(context)
        if not actor:
            return False

        new_x = actor.x + self.dx
        new_y = actor.y + self.dy

        # Validate bounds and walkability
        if not self._validate_bounds(context, actor, new_x, new_y):
            return False

        if not self._validate_walkable(context, actor, new_x, new_y):
            return False

        self._log_validation_success(
            f"validated successfully: {actor.name} can move to ({new_x},{new_y})",
            actor_name=actor.name,
            from_pos=(actor.x, actor.y),
            to_pos=(new_x, new_y)
        )
        return True

    def _validate_bounds(self, context: GameContext, actor, new_x: int, new_y: int) -> bool:
        """Validate target position is within map bounds."""
        if not context.in_bounds(new_x, new_y):
            self._log_validation_failure(
                f"out of bounds - {actor.name} tried to move to ({new_x},{new_y})",
                actor_name=actor.name,
                from_pos=(actor.x, actor.y),
                to_pos=(new_x, new_y),
                dx=self.dx,
                dy=self.dy
            )
            return False
        return True

    def _validate_walkable(self, context: GameContext, actor, new_x: int, new_y: int) -> bool:
        """Validate target position is walkable (allow entities for bump-attack)."""
        if not context.is_walkable(new_x, new_y):
            target = context.get_entity_at(new_x, new_y)
            if not target:  # Wall or obstacle (entities are OK for bump-attack)
                tile = context.game_state.dungeon_map.tiles[new_x][new_y]
                self._log_validation_failure(
                    f"tile not walkable - {actor.name} tried to move to ({new_x},{new_y}) [{tile.tile_type.name}]",
                    actor_name=actor.name,
                    from_pos=(actor.x, actor.y),
                    to_pos=(new_x, new_y),
                    tile_type=tile.tile_type.name,
                    dx=self.dx,
                    dy=self.dy
                )
                return False
        return True

    def execute(self, context: GameContext) -> ActionOutcome:
        """Execute move or attack."""
        actor = self._get_actor(context)
        if not actor:
            logger.error("MoveAction execution failed: actor not found",
                        extra={'actor_id': self.actor_id})
            return ActionOutcome.failure("Actor not found")

        new_x = actor.x + self.dx
        new_y = actor.y + self.dy

        # Handle collision with another entity
        collision_result = self._handle_collision(context, actor, new_x, new_y)
        if collision_result:
            return collision_result

        # Validate and perform move
        if not self.validate(context):
            logger.error("MoveAction execution failed validation",
                        extra={'actor_id': self.actor_id, 'actor_name': actor.name,
                               'from_pos': (actor.x, actor.y), 'to_pos': (new_x, new_y)})
            return ActionOutcome.failure("Cannot move there")

        return self._perform_move(actor, new_x, new_y)

    def _handle_collision(self, context, actor, new_x, new_y):
        """Handle collision with entity at target position.

        Returns:
            ActionOutcome if collision blocks movement, None to continue moving
        """
        target = context.get_entity_at(new_x, new_y)
        if not target or not target.is_alive:
            return None

        # Attackable entity - bump to attack
        if target.attackable:
            logger.info("MoveAction redirecting to attack (bump combat)",
                       extra={'actor_id': self.actor_id, 'actor_name': actor.name,
                              'target_id': target.entity_id, 'target_name': target.name,
                              'position': (new_x, new_y)})
            from .attack_action import AttackAction
            attack = AttackAction(self.actor_id, target.entity_id)
            return attack.execute(context)

        # Ore vein - bump to mine
        if target.entity_type == EntityType.ORE_VEIN:
            logger.info("MoveAction redirecting to mine (bump mining)",
                       extra={'actor_id': self.actor_id, 'actor_name': actor.name,
                              'ore_vein_id': target.entity_id, 'ore_vein_name': target.name,
                              'position': (new_x, new_y)})
            from .mine_action import MineAction
            mine = MineAction(self.actor_id, target.entity_id)
            return mine.execute(context)

        # Blocking entity - cannot pass
        if target.blocks_movement:
            logger.warning("MoveAction blocked by immovable entity",
                          extra={'actor_id': self.actor_id, 'actor_name': actor.name,
                                 'blocker_id': target.entity_id, 'blocker_name': target.name,
                                 'blocker_type': target.entity_type.value,
                                 'position': (new_x, new_y)})
            return ActionOutcome.failure(f"Cannot move - {target.name} is in the way")

        # Non-blocking entity - walk over it
        logger.debug("MoveAction walking over non-blocking entity",
                    extra={'actor_id': self.actor_id, 'actor_name': actor.name,
                           'over_entity': target.name, 'over_type': target.entity_type.value,
                           'position': (new_x, new_y)})
        return None

    def _perform_move(self, actor, new_x, new_y):
        """Perform the actual move and create success outcome."""
        old_x, old_y = actor.x, actor.y
        actor.move_to(new_x, new_y)

        logger.info(f"MoveAction executed: {actor.name} moved from ({old_x},{old_y}) to ({new_x},{new_y})",
                   extra={'actor_id': self.actor_id, 'actor_name': actor.name,
                          'from_pos': (old_x, old_y), 'to_pos': (new_x, new_y)})

        outcome = ActionOutcome.success(took_turn=True)
        outcome.events.append({
            'type': 'entity_moved',
            'entity_id': self.actor_id,
            'from': (old_x, old_y),
            'to': (new_x, new_y),
        })
        return outcome

    def to_dict(self) -> dict:
        return {
            'action_type': 'MoveAction',
            'actor_id': self.actor_id,
            'dx': self.dx,
            'dy': self.dy,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MoveAction':
        return cls(
            actor_id=data['actor_id'],
            dx=data['dx'],
            dy=data['dy'],
        )
