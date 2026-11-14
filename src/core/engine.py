"""Engine: the rules loop for one run, for any number of players.

Single-player (`Game`) and multiplayer (`GameSession`) are hosts around this class.
The engine owns what makes a run a run: building actions from intents, executing them
through the shared outcome pipeline, the world tick, floor changes, monster AI, and the
events and content handlers wired to one bus. Hosts own what differs: seats, locking and
transport for multiplayer; saves, telemetry and the personal high score for single-player.
When the world ticks is the host's decision (single-player: after every turn-consuming
action; multiplayer: when the RoundScheduler says the round is complete).
"""

import logging
from dataclasses import dataclass
from typing import Optional

from .action_pipeline import process_action_outcome
from .actions.action_factory import ActionFactory
from .base.action import Action, ActionOutcome
from .base.game_context import GameContext
from .events import EventBus, create_floor_changed_event
from .extensions import install_event_handlers, uninstall_event_handlers
from .floor_manager import FloorManager
from .snapshot import Snapshot, build_snapshot
from .spawning import EntitySpawner
from .systems.ai_system import AISystem
from .turn_processor import TurnProcessor

logger = logging.getLogger(__name__)


@dataclass
class ActResult:
    """What executing one action did."""
    outcome: ActionOutcome
    took_turn: bool


class Engine:
    """Actions, world tick, floor changes, AI, events and content handlers for one run."""

    def __init__(
        self,
        context: GameContext,
        config,
        event_bus: EventBus,
        *,
        spawner: Optional[EntitySpawner] = None,
        entity_loader=None,
        ai_entity_loader=None,
        log_failures: bool = True,
        defeat_message: Optional[str] = None,
    ):
        """
        Args:
            context: Safe state access for the run (players already in it)
            config: ConfigLoader result (regen rule, victory floor, spawning)
            event_bus: One bus for the engine, its AI and the content handlers
            spawner: Entity spawner; built from config + entity_loader if omitted
            ai_entity_loader: Passed to AISystem (per-monster parameters), if any
            log_failures: Run a failed action's messages through the shared log.
                Single-player does; multiplayer reports a failure to the sender only.
            defeat_message: Message-log line when every player is dead (default: TurnProcessor's)
        """
        self.context = context
        self.state = context.game_state
        self.config = config
        self.event_bus = event_bus
        self.log_failures = log_failures

        self.spawner = spawner or EntitySpawner(config, entity_loader)

        regen = config.game_constants['player']['health_regeneration']
        tp_kwargs = {'defeat_message': defeat_message} if defeat_message else {}
        self.turn_processor = TurnProcessor(
            context, regen['interval_turns'], regen['amount'],
            hp_regen_percent=regen.get('percent_of_max', 0.0),
            hp_rest_multiplier=regen.get('rest_multiplier', 1),
            spawner=self.spawner, event_bus=event_bus, **tp_kwargs,
        )
        self.floor_manager = FloorManager(context, self.spawner, event_bus=event_bus)
        self.action_factory = ActionFactory(context)

        # Content event handlers (core/content/events/): one instance each, per run
        self.event_handlers = install_event_handlers(context, event_bus)

        self.ai_system = AISystem(context, entity_loader=ai_entity_loader, event_bus=event_bus)
        context.register_system('ai', self.ai_system)

    # ---- actions -------------------------------------------------------------------

    def make_action(self, action_type: str, actor_id: Optional[str] = None, **kwargs) -> Optional[Action]:
        """Build the action for an intent. The actor defaults to the player (single-player)."""
        return self.action_factory.create(action_type, actor_id=actor_id, **kwargs)

    def execute(self, action: Action, action_type: Optional[str] = None) -> ActResult:
        """Execute an action and run its outcome through the shared pipeline.

        The pipeline publishes the action's events, adds its messages and descends the
        floor if asked. Returns whether the action consumed a turn; ticking the world is
        the host's call (`tick`).
        """
        outcome = action.execute(self.context)
        if not outcome.is_success and not self.log_failures:
            return ActResult(outcome, False)

        took_turn = process_action_outcome(
            outcome,
            action_type or action.get_action_type(),
            add_message=self.state.add_message,
            on_descend_floor=self.descend_floor,
            event_bus=self.event_bus,
        )
        return ActResult(outcome, took_turn)

    # ---- reading the world -----------------------------------------------------------

    def snapshot(self, viewer=None) -> Snapshot:
        """What `viewer` (an entity, or an entity id) can see. Default: the player.

        A host passes the entity object for a dead player whose entity has been
        purged from the state, so a spectator still gets a view.
        """
        if isinstance(viewer, str):
            viewer = self.context.get_entity(viewer)
        return build_snapshot(self.state, viewer)

    # ---- the world -----------------------------------------------------------------

    def tick(self) -> None:
        """Let the world move: regen, wanderers, monsters, cleanup, game over, turn_ended."""
        self.turn_processor.process_turn()

    def after_action(self) -> None:
        """Announce deaths and the end of the run caused by the action just executed."""
        self.turn_processor.announce_deaths()
        self.turn_processor.check_game_over()

    def descend_floor(self) -> None:
        """Move the whole party down (FloorManager), then announce it."""
        from_floor = self.state.current_floor
        self.floor_manager.descend_floor()
        if self.state.current_floor != from_floor:
            living = self.context.get_alive_players()
            actor = living[0].entity_id if living else self.state.player.entity_id
            self.event_bus.publish_dict(create_floor_changed_event(
                from_floor, self.state.current_floor, actor, self.state.turn_count,
            ))

    def close(self) -> None:
        """Detach from the bus (before replacing this engine, e.g. after loading a save)."""
        uninstall_event_handlers(self.event_handlers, self.event_bus)
        self.event_handlers = []
        self.ai_system.detach()
