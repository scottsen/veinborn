"""
Shared post-action handling for single-player (Game) and multiplayer (GameSession).

Both modes must do the same things with an ActionOutcome: log failures, publish
its events, react to floor-descent events, and record its messages. Keeping that
in one place stops new post-action rules from having to be built twice (VB-24).

What legitimately differs stays with the caller: how a descent is carried out
(FloorManager vs MultiplayerGameState) and what happens after a turn is
consumed (TurnProcessor vs the round/quota logic).
"""

import logging
from typing import Callable, Optional

from .base.action import ActionOutcome
from .events import EventBus

logger = logging.getLogger(__name__)


def process_action_outcome(
    outcome: ActionOutcome,
    action_type: str,
    *,
    add_message: Callable[[str], None],
    on_descend_floor: Callable[[], None],
    event_bus: Optional[EventBus] = None,
) -> bool:
    """Apply an action's outcome to the game and report whether it took a turn.

    Args:
        outcome: The ActionOutcome from action execution
        action_type: The action type, used only for logging
        add_message: Records a player-visible message in the game log
        on_descend_floor: Invoked once per 'descend_floor' event
        event_bus: Receives the outcome's events, if any subscribers matter

    Returns:
        True if the action consumed a turn.
    """
    if not outcome.is_success:
        logger.info(
            f"Action failed: {action_type}",
            extra={
                'action_class': outcome.__class__.__name__,
                'failure_message': outcome.messages[0] if outcome.messages else 'No message',
            }
        )

    if event_bus is not None and outcome.events:
        event_bus.publish_all(outcome.events)
        logger.debug(f"Published {len(outcome.events)} events to EventBus")

    for event in outcome.events:
        if event.get('type') == 'descend_floor':
            on_descend_floor()

    for msg in outcome.messages:
        add_message(msg)

    return outcome.took_turn
