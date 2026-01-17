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

        return self._perform_move(context, actor, new_x, new_y)

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

        # Ore vein - bump to mine (players only)
        if target.entity_type == EntityType.ORE_VEIN:
            # Only players can mine ore veins via bump-to-mine
            # Monsters treat ore veins as blocking obstacles
            from ..entities import Player
            if isinstance(actor, Player):
                logger.info("MoveAction redirecting to mine (bump mining)",
                           extra={'actor_id': self.actor_id, 'actor_name': actor.name,
                                  'ore_vein_id': target.entity_id, 'ore_vein_name': target.name,
                                  'position': (new_x, new_y)})
                from .mine_action import MineAction

                # Check if resuming existing mining action for same ore vein
                mining_data = actor.get_stat('mining_action')
                if mining_data and mining_data.get('ore_vein_id') == target.entity_id:
                    logger.debug("Resuming multi-turn mining action via bump-to-mine")
                    mine = MineAction.from_dict(mining_data)
                else:
                    # Start new mining action (or switched to different ore vein)
                    if mining_data:
                        logger.debug("Starting new mining action (switched ore veins)")
                    mine = MineAction(self.actor_id, target.entity_id)

                return mine.execute(context)
            else:
                # Monsters cannot mine - ore vein blocks them
                logger.debug("Monster blocked by ore vein (cannot mine)",
                           extra={'actor_id': self.actor_id, 'actor_name': actor.name,
                                  'ore_vein': target.name, 'position': (new_x, new_y)})
                return ActionOutcome.failure(f"Cannot move - {target.name} is in the way")

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

    def _perform_move(self, context, actor, new_x, new_y):
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

        # Autopickup items at new position (player only)
        self._handle_autopickup(context, actor, new_x, new_y, outcome)

        return outcome

    def _handle_autopickup(self, context, actor, x, y, outcome):
        """Handle automatic item pickup when walking over items."""
        # Only players autopickup
        from ..entities import Player
        if not isinstance(actor, Player):
            return

        # Check if autopickup is enabled
        from ..config.user_config import ConfigManager
        config = ConfigManager.get_instance()
        if not config.get_bool('game.autopickup', True):
            return

        # Get autopickup types
        autopickup_types_str = config.get('game.autopickup_types', 'ore,food,weapon')
        autopickup_types = [t.strip().lower() for t in autopickup_types_str.split(',')]

        # Find items at current position
        items_at_position = [
            e for e in context.game_state.entities.values()
            if e.entity_type == EntityType.ITEM and e.x == x and e.y == y and e.is_alive
        ]

        # Pickup matching items
        for item in items_at_position:
            item_type = item.get_stat('item_type', 'unknown').lower()

            # Check if item type matches autopickup types
            if item_type not in autopickup_types:
                logger.debug(f"Skipping item {item.name} (type {item_type} not in autopickup types)")
                continue

            # Try to add to inventory
            if actor.add_to_inventory(item):
                outcome.messages.append(f"Picked up {item.name}")
                outcome.events.append({
                    'type': 'item_picked_up',
                    'actor_id': self.actor_id,
                    'item_id': item.entity_id,
                    'item_name': item.name,
                    'position': (x, y),
                })
                logger.info(f"Autopickup: {actor.name} picked up {item.name}")
            else:
                outcome.messages.append(f"Inventory full! Could not pick up {item.name}")
                logger.debug(f"Autopickup failed: inventory full for {item.name}")

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
