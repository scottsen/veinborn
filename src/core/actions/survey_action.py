"""
SurveyAction - survey an ore vein to see its properties.

This action:
- Takes 1 turn
- Reveals ore properties (hardness, conductivity, etc.)
- Shows mining time estimate
- Does not mine the ore
"""

import logging
from dataclasses import dataclass
from ..base.action import Action, ActionOutcome
from ..base.game_context import GameContext
from ..base.entity import EntityType

logger = logging.getLogger(__name__)


@dataclass
class SurveyAction(Action):
    """Survey an ore vein."""

    actor_id: str
    ore_vein_id: str

    def validate(self, context: GameContext) -> bool:
        """Check if survey is valid."""
        # Use base class helper for actor validation
        actor = self._get_and_validate_actor(context)
        if not actor:
            return False

        # Validate ore vein (existence, type, adjacency) - replaces 26 lines with helper
        ore_vein = self._validate_entity(
            context, self.ore_vein_id, EntityType.ORE_VEIN,
            entity_name="ore_vein", require_adjacency=True
        )
        if not ore_vein:
            return False

        self._log_validation_success(
            "validated successfully",
            actor_name=actor.name,
            ore_vein_id=self.ore_vein_id,
            ore_vein_name=ore_vein.name
        )
        return True

    def execute(self, context: GameContext) -> ActionOutcome:
        """Execute survey."""
        if not self.validate(context):
            logger.error("SurveyAction execution failed validation",
                        extra={'actor_id': self.actor_id, 'ore_vein_id': self.ore_vein_id})
            return ActionOutcome.failure("Cannot survey")

        actor = self._get_actor(context)
        ore_vein = context.get_entity(self.ore_vein_id)

        # Mark as surveyed and get properties
        ore_vein.set_stat('surveyed', True)
        props = self._get_ore_properties(ore_vein)

        logger.info("SurveyAction completed - ore properties revealed",
                   extra={
                       'actor_id': self.actor_id, 'actor_name': actor.name,
                       'ore_vein_id': self.ore_vein_id, 'ore_vein_name': ore_vein.name,
                       'properties': props,
                   })

        # Build outcome with messages and event
        outcome = ActionOutcome.success(took_turn=True)
        self._add_survey_messages(outcome, ore_vein.name, props)
        self._add_survey_event(outcome, props)

        return outcome

    def _get_ore_properties(self, ore_vein) -> dict:
        """Extract ore vein properties as a dictionary."""
        return {
            'hardness': ore_vein.get_stat('hardness'),
            'conductivity': ore_vein.get_stat('conductivity'),
            'malleability': ore_vein.get_stat('malleability'),
            'purity': ore_vein.get_stat('purity'),
            'density': ore_vein.get_stat('density'),
            'mining_turns': ore_vein.get_stat('mining_turns'),
        }

    def _add_survey_messages(self, outcome: ActionOutcome, ore_name: str, props: dict):
        """Add formatted survey messages to outcome."""
        outcome.messages.append(f"Surveyed {ore_name}:")
        outcome.messages.append(
            f"  Hardness: {props['hardness']}  "
            f"Conductivity: {props['conductivity']}"
        )
        outcome.messages.append(
            f"  Malleability: {props['malleability']}  "
            f"Purity: {props['purity']}"
        )
        outcome.messages.append(f"  Density: {props['density']}")
        outcome.messages.append(f"Mining will take {props['mining_turns']} turns")

    def _add_survey_event(self, outcome: ActionOutcome, props: dict):
        """Add survey event to outcome."""
        outcome.events.append({
            'type': 'ore_surveyed',
            'actor_id': self.actor_id,
            'ore_vein_id': self.ore_vein_id,
            'properties': props,
        })

    def to_dict(self) -> dict:
        return {
            'action_type': 'SurveyAction',
            'actor_id': self.actor_id,
            'ore_vein_id': self.ore_vein_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SurveyAction':
        return cls(
            actor_id=data['actor_id'],
            ore_vein_id=data['ore_vein_id'],
        )
