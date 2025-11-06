"""
MineAction - mine an ore vein (multi-turn action).

This action:
- Takes 3-5 turns based on ore hardness
- Player is vulnerable during mining
- Can be interrupted (cancel or take damage)
- Adds ore to inventory on completion
- Removes ore vein from map
"""

import logging
from dataclasses import dataclass
from ..base.action import Action, ActionOutcome
from ..base.game_context import GameContext
from ..base.entity import EntityType
from ..events import create_ore_mined_event, GameEventType

logger = logging.getLogger(__name__)


@dataclass
class MineAction(Action):
    """Mine an ore vein (multi-turn action)."""

    actor_id: str
    ore_vein_id: str
    turns_remaining: int = 0  # 0 means "just started"

    def validate(self, context: GameContext) -> bool:
        """Check if mining is valid."""
        # Validate actor
        actor = self._get_and_validate_actor(context)
        if not actor:
            return False

        # Validate ore vein (existence, type, adjacency) - replaces 25 lines with 2
        ore_vein = self._validate_entity(
            context, self.ore_vein_id, EntityType.ORE_VEIN,
            entity_name="ore_vein", require_adjacency=True
        )
        if not ore_vein:
            return False

        self._log_validation_success("validated successfully",
                                    actor_name=actor.name,
                                    ore_vein_id=self.ore_vein_id,
                                    ore_vein_name=ore_vein.name,
                                    turns_remaining=self.turns_remaining)
        return True

    def execute(self, context: GameContext) -> ActionOutcome:
        """Execute mining turn."""
        if not self.validate(context):
            logger.error(
                f"MineAction execution failed validation",
                extra={'actor_id': self.actor_id, 'ore_vein_id': self.ore_vein_id}
            )
            return ActionOutcome.failure("Cannot mine")

        actor = self._get_actor(context)
        ore_vein = context.get_entity(self.ore_vein_id)

        # Initialize on first turn
        if self.turns_remaining == 0:
            self._initialize_mining(actor, ore_vein)

        # Process one turn of mining
        self.turns_remaining -= 1
        self._log_mining_progress(actor, ore_vein)

        # Create outcome and handle completion
        if self.turns_remaining > 0:
            return self._handle_mining_progress(actor, ore_vein)
        else:
            return self._handle_mining_completion(context, actor, ore_vein)

    def _get_actor(self, context: GameContext):
        """Get the actor performing the mining action."""
        actor = context.get_entity(self.actor_id)
        return actor if actor else context.get_player()

    def _initialize_mining(self, actor, ore_vein):
        """Initialize mining on first turn."""
        mining_turns = ore_vein.get_stat('mining_turns', 3)
        self.turns_remaining = mining_turns

        logger.info(
            f"MineAction started - multi-turn mining initiated",
            extra={
                'actor_id': self.actor_id,
                'actor_name': actor.name,
                'ore_vein_id': self.ore_vein_id,
                'ore_vein_name': ore_vein.name,
                'total_turns': mining_turns,
            }
        )

    def _log_mining_progress(self, actor, ore_vein):
        """Log current mining progress."""
        logger.debug(
            f"MineAction progress",
            extra={
                'actor_id': self.actor_id,
                'actor_name': actor.name,
                'ore_vein_id': self.ore_vein_id,
                'turns_remaining': self.turns_remaining,
            }
        )

    def _handle_mining_progress(self, actor, ore_vein) -> ActionOutcome:
        """Handle in-progress mining (not yet complete)."""
        logger.info(
            f"MineAction in progress",
            extra={
                'actor_id': self.actor_id,
                'actor_name': actor.name,
                'ore_vein_id': self.ore_vein_id,
                'ore_vein_name': ore_vein.name,
                'turns_remaining': self.turns_remaining,
            }
        )

        outcome = ActionOutcome.success(took_turn=True)
        outcome.messages.append(f"Mining... {self.turns_remaining} turn(s) remaining")

        # Store mining state for interruption handling
        actor.set_stat('mining_action', self.to_dict())

        # Add mining started event on first progress update
        outcome.events.append({
            'type': GameEventType.MINING_STARTED.value if self.turns_remaining == ore_vein.get_stat('mining_turns', 3) - 1 else 'mining_progress',
            'data': {
                'actor_id': self.actor_id,
                'ore_vein_id': self.ore_vein_id,
                'turns_remaining': self.turns_remaining,
            },
            'timestamp': __import__('time').time(),
        })

        return outcome

    def _handle_mining_completion(self, context: GameContext, actor, ore_vein) -> ActionOutcome:
        """Handle mining completion and ore extraction."""
        logger.info(
            f"MineAction completed - ore extraction successful",
            extra={
                'actor_id': self.actor_id,
                'actor_name': actor.name,
                'ore_vein_id': self.ore_vein_id,
                'ore_vein_name': ore_vein.name,
            }
        )

        outcome = ActionOutcome.success(took_turn=True)
        outcome.messages.append(f"Mined {ore_vein.name}!")

        # Extract and handle ore item
        from ..entities import OreVein
        if isinstance(ore_vein, OreVein):
            ore_item = ore_vein.get_ore_item()
            self._handle_ore_item(context, actor, ore_item, outcome)
            self._remove_ore_vein(context, ore_vein, ore_item, outcome)

        # Clear mining state
        actor.set_stat('mining_action', None)

        return outcome

    def _handle_ore_item(self, context: GameContext, actor, ore_item, outcome: ActionOutcome):
        """Add ore to inventory or drop on ground if full."""
        from ..entities import Player
        if not isinstance(actor, Player):
            return

        if actor.add_to_inventory(ore_item):
            self._log_inventory_add(ore_item)
            outcome.messages.append(f"Added {ore_item.name} to inventory")
        else:
            self._drop_ore_on_ground(context, actor, ore_item, outcome)

    def _log_inventory_add(self, ore_item):
        """Log successful ore addition to inventory."""
        logger.info(
            f"Ore item added to inventory",
            extra={
                'actor_id': self.actor_id,
                'ore_item_id': ore_item.entity_id,
                'ore_item_name': ore_item.name,
            }
        )

    def _drop_ore_on_ground(self, context: GameContext, actor, ore_item, outcome: ActionOutcome):
        """Drop ore on ground when inventory is full."""
        logger.warning(
            f"Inventory full - ore dropped on ground",
            extra={
                'actor_id': self.actor_id,
                'ore_item_id': ore_item.entity_id,
                'drop_position': (actor.x, actor.y),
            }
        )
        outcome.messages.append("Inventory full!")
        ore_item.x = actor.x
        ore_item.y = actor.y
        context.add_entity(ore_item)

    def _remove_ore_vein(self, context: GameContext, ore_vein, ore_item, outcome: ActionOutcome):
        """Remove mined ore vein from world and log event."""
        context.remove_entity(ore_vein.entity_id)

        logger.info(
            f"Ore vein removed from world",
            extra={
                'ore_vein_id': self.ore_vein_id,
                'ore_vein_name': ore_vein.name,
            }
        )

        # Use event builder helper for type-safe ore mined event
        from ..entities import OreVein
        if isinstance(ore_vein, OreVein):
            outcome.events.append(create_ore_mined_event(
                ore_id=ore_item.entity_id,
                miner_id=self.actor_id,
                ore_type=ore_vein.ore_type,
                properties={
                    'hardness': ore_vein.hardness,
                    'conductivity': ore_vein.conductivity,
                    'malleability': ore_vein.malleability,
                    'purity': ore_vein.purity,
                    'density': ore_vein.density,
                },
            ))

    def to_dict(self) -> dict:
        return {
            'action_type': 'MineAction',
            'actor_id': self.actor_id,
            'ore_vein_id': self.ore_vein_id,
            'turns_remaining': self.turns_remaining,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MineAction':
        return cls(
            actor_id=data['actor_id'],
            ore_vein_id=data['ore_vein_id'],
            turns_remaining=data['turns_remaining'],
        )
