"""
TurnProcessor - handles turn progression and related mechanics.

Responsibilities:
- Process game turns (monster AI, cleanup)
- Handle HP regeneration
- Check game over conditions
- Manage turn counter

This class extracts turn processing logic from the Game class,
following Single Responsibility Principle.
"""

import logging
from typing import TYPE_CHECKING, Callable, Iterable, Optional

from .base.entity import EntityType
from .run_end import record_single_player_run_end

if TYPE_CHECKING:
    from .base.game_context import GameContext
    from .game_state import GameState

logger = logging.getLogger(__name__)


def apply_hp_regeneration(players: Iterable, turn_count: int,
                          interval: int, amount: int) -> None:
    """
    Heal each living player by `amount` HP on every `interval`-th turn.

    NetHack-style natural regeneration, shared by single-player (one player)
    and multiplayer (every party member) so the rule can't drift between them.
    """
    if turn_count % interval != 0:
        return

    for player in players:
        if player.is_alive and player.hp < player.max_hp:
            healed = player.heal(amount)

            if healed > 0:
                logger.debug(
                    f"{player.name} regenerated {healed} HP (turn {turn_count})"
                )


class TurnProcessor:
    """
    Handles turn progression and related mechanics.

    Design principles:
    - Single responsibility (turn processing only)
    - Uses GameContext (safe API)
    - Testable in isolation
    - Clear separation of concerns
    """

    def __init__(self, context: 'GameContext', hp_regen_interval: int = 10, hp_regen_amount: int = 1, spawner=None,
                 on_run_end: Optional[Callable[['GameState', bool], None]] = None):
        """
        Initialize turn processor.

        Args:
            context: Game context for safe state access
            hp_regen_interval: Number of turns between HP regeneration (default: 10)
            hp_regen_amount: Amount of HP restored per regeneration tick (default: 1)
            spawner: EntitySpawner for ongoing spawns (VB-52); None disables them
            on_run_end: Called as (game_state, victory) when the run is lost; defaults
                to the single-player score/vault records
        """
        self.context = context
        self.game_state = context.game_state
        self.hp_regen_interval = hp_regen_interval
        self.hp_regen_amount = hp_regen_amount
        self.spawner = spawner
        self.on_run_end = on_run_end or record_single_player_run_end
        logger.debug(f"TurnProcessor initialized (HP regen: {hp_regen_amount} per {hp_regen_interval} turns)")

    def process_turn(self) -> None:
        """
        Process one game turn.

        Steps:
        1. Increment turn counter
        2. Apply HP regeneration
        3. Run AI systems (monsters act)
        4. Cleanup dead entities
        5. Check game over conditions
        """
        # Increment turn counter
        self.game_state.turn_count += 1

        logger.debug(
            f"Processing turn {self.game_state.turn_count}",
            extra={
                'turn': self.game_state.turn_count,
                'floor': self.game_state.current_floor,
                'players_alive': len(self.context.get_alive_players()),
                'monster_count': len([
                    e for e in self.context.get_entities_by_type(EntityType.MONSTER)
                    if e.is_alive
                ]),
            }
        )

        # Apply HP regeneration
        self._apply_hp_regeneration()

        # A new monster may wander in (VB-52)
        self._maybe_spawn_wanderer()

        # Run AI system (monsters take turns)
        self._run_ai_systems()

        # Cleanup dead entities
        self._cleanup_dead_entities()

        # Check game over conditions
        self._check_game_over()

    def _apply_hp_regeneration(self) -> None:
        """
        Apply natural HP regeneration to every living player.

        NetHack-style: 1 HP every 10 turns (configurable)
        """
        apply_hp_regeneration(
            self.context.get_all_players(),
            self.game_state.turn_count,
            self.hp_regen_interval,
            self.hp_regen_amount,
        )

    def _maybe_spawn_wanderer(self) -> None:
        """NetHack-style ongoing spawn: small per-turn chance of a new monster."""
        if self.spawner is None:
            return
        config = self.spawner.config.get_ongoing_spawn_config()
        if not config.get('enabled', False):
            return

        players = self.context.get_alive_players()
        if not players:
            return

        rng = self.context.get_rng()
        if rng.random() >= config.get('chance_per_turn', 0.0):
            return

        monsters = [
            m for m in self.context.get_entities_by_type(EntityType.MONSTER) if m.is_alive
        ]
        if len(monsters) >= config.get('max_monsters_per_floor', 12):
            return

        occupied = {
            (e.x, e.y) for e in self.game_state.entities.values() if e.x is not None
        }
        level = max(1, round(sum(p.get_stat('level', 1) for p in players) / len(players)))
        monster = self.spawner.spawn_wandering_monster(
            self.game_state.current_floor,
            level,
            self.game_state.dungeon_map,
            [(p.x, p.y) for p in players],
            occupied,
            rng,
        )
        if monster:
            self.context.add_entity(monster)
            logger.info(
                f"A {monster.name} wandered in at ({monster.x}, {monster.y})",
                extra={'turn': self.game_state.turn_count, 'floor': self.game_state.current_floor},
            )

    def _run_ai_systems(self) -> None:
        """Run all AI systems (monster turns)."""
        ai_system = self.context.get_system('ai')

        if ai_system:
            logger.debug("Running AI system for monster turns")
            ai_system.update()
        else:
            logger.warning("AI system not found, monsters will not act")

    def _cleanup_dead_entities(self) -> None:
        """Remove dead entities from the game."""
        dead_count = len([
            e for e in self.context.game_state.entities.values()
            if not e.is_alive
        ])

        if dead_count > 0:
            logger.debug(f"Cleaning up {dead_count} dead entities")
            self.game_state.cleanup_dead_entities()

    def _check_game_over(self) -> None:
        """The run is lost when no player is left alive (a party of one: the player died)."""
        if not self.context.get_alive_players():
            self.on_run_end(self.game_state, False)

            self.game_state.add_message("You died! Press 'r' to restart.")
            self.game_state.game_over = True

            logger.info(
                "Game over - every player died",
                extra={
                    'turn': self.game_state.turn_count,
                    'floor': self.game_state.current_floor,
                    'player_level': self.game_state.player.get_stat('level', 1),
                }
            )
