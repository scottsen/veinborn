"""
Game telemetry and statistics tracking via events.

This module demonstrates the event subscriber pattern from
EVENTS_ASYNC_OBSERVABILITY_GUIDE.md.

Design:
- MVP: Subscribe to events via direct calls
- Phase 2: Subscribe via EventBus (already implemented!)
- Phase 3: Lua scripts can also subscribe

The key insight: StatsTracker has on_*() methods that work both ways:
- Now: game.stats.on_attack_resolved(event)
- Phase 2: event_bus.subscribe(ATTACK_RESOLVED, stats.on_attack_resolved)

Zero refactoring needed!
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import logging
import time

from .events import GameEvent, GameEventType

logger = logging.getLogger('veinborn.telemetry')


@dataclass
class GameStateSnapshot:
    """
    Snapshot of game state for telemetry.

    Used for turn-by-turn tracking and debugging.
    """
    turn: int
    player_hp: int
    player_pos: tuple[int, int]
    monsters_alive: int
    floor: int
    inventory_size: int
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Serialize for logging."""
        return {
            'turn': self.turn,
            'player_hp': self.player_hp,
            'player_pos': self.player_pos,
            'monsters_alive': self.monsters_alive,
            'floor': self.floor,
            'inventory_size': self.inventory_size,
            'timestamp': self.timestamp,
        }


class StatsTracker:
    """
    Track game statistics via event subscription.

    This is the "event-ready" pattern - methods work with direct calls now,
    subscribe to EventBus later with zero changes.

    Example:
        # MVP: Direct calls
        stats = StatsTracker()
        result = combat_system.resolve_attack(...)
        stats.on_attack_resolved(result)

        # Phase 2: Event subscription (same methods!)
        event_bus.subscribe(ATTACK_RESOLVED, stats.on_attack_resolved)
    """

    def __init__(self):
        """Initialize empty statistics."""
        # Combat stats
        self.total_damage_dealt = 0
        self.total_damage_taken = 0
        self.monsters_killed = 0
        self.attacks_made = 0
        self.attacks_received = 0

        # Mining stats
        self.ore_mined = 0
        self.ore_surveyed = 0
        self.mining_time_spent = 0  # turns

        # Crafting stats
        self.items_crafted = 0
        self.crafting_failures = 0

        # Exploration stats
        self.floors_descended = 0
        self.tiles_explored = 0
        self.turns_played = 0

        # Death tracking
        self.deaths: List[dict] = []

    # ========================================================================
    # Event Handlers (work as direct calls OR event subscribers!)
    # ========================================================================

    def on_attack_resolved(self, event: GameEvent) -> None:
        """
        Track combat statistics from attack events.

        Can be called directly OR subscribed to EventBus.

        Args:
            event: ATTACK_RESOLVED event
        """
        data = event.data
        damage = data.get('damage', 0)
        killed = data.get('killed', False)
        attacker_id = data.get('attacker_id')

        self.attacks_made += 1
        self.total_damage_dealt += damage

        if killed:
            self.monsters_killed += 1
            self._check_achievement_centurion()

        logger.debug(
            "Combat stats updated",
            extra={
                'total_damage': self.total_damage_dealt,
                'kills': self.monsters_killed,
            }
        )

    def on_entity_died(self, event: GameEvent) -> None:
        """
        Track entity deaths for difficulty analysis.

        Args:
            event: ENTITY_DIED event
        """
        data = event.data
        entity_name = data.get('entity_name', 'Unknown')
        cause = data.get('cause', 'unknown')

        # Track player death specifically
        if data.get('entity_id') == 'player':
            death_record = {
                'turn': event.turn,
                'cause': cause,
                'timestamp': event.timestamp,
            }
            self.deaths.append(death_record)

            logger.info(
                "Player death recorded",
                extra=death_record
            )

    def on_ore_mined(self, event: GameEvent) -> None:
        """
        Track mining statistics.

        Args:
            event: ORE_MINED event
        """
        self.ore_mined += 1

        logger.debug(
            "Mining stats updated",
            extra={'total_ore_mined': self.ore_mined}
        )

    def on_ore_surveyed(self, event: GameEvent) -> None:
        """
        Track ore surveying.

        Args:
            event: ORE_SURVEYED event
        """
        self.ore_surveyed += 1

    def on_item_crafted(self, event: GameEvent) -> None:
        """
        Track crafting statistics.

        Args:
            event: ITEM_CRAFTED event
        """
        self.items_crafted += 1

        logger.debug(
            "Crafting stats updated",
            extra={'total_items_crafted': self.items_crafted}
        )

    def on_crafting_failed(self, event: GameEvent) -> None:
        """
        Track crafting failures.

        Args:
            event: CRAFTING_FAILED event
        """
        self.crafting_failures += 1

    def on_floor_changed(self, event: GameEvent) -> None:
        """
        Track floor progression.

        Args:
            event: FLOOR_CHANGED event
        """
        data = event.data
        from_floor = data.get('from_floor', 0)
        to_floor = data.get('to_floor', 0)

        if to_floor > from_floor:
            self.floors_descended += 1

        logger.info(
            "Floor changed",
            extra={'from': from_floor, 'to': to_floor}
        )

    def on_turn_ended(self, event: GameEvent) -> None:
        """
        Track turn count.

        Args:
            event: TURN_ENDED event
        """
        self.turns_played += 1

    # ========================================================================
    # Statistics Queries
    # ========================================================================

    def get_session_stats(self) -> dict:
        """
        Get statistics for current session.

        Returns:
            Dictionary of all tracked stats
        """
        return {
            'turns_played': self.turns_played,
            'monsters_killed': self.monsters_killed,
            'damage_dealt': self.total_damage_dealt,
            'damage_taken': self.total_damage_taken,
            'ore_mined': self.ore_mined,
            'items_crafted': self.items_crafted,
            'floors_descended': self.floors_descended,
            'deaths': len(self.deaths),
        }

    def get_combat_stats(self) -> dict:
        """Get detailed combat statistics."""
        avg_damage = (self.total_damage_dealt / self.attacks_made
                      if self.attacks_made > 0 else 0)

        return {
            'attacks_made': self.attacks_made,
            'total_damage': self.total_damage_dealt,
            'average_damage': avg_damage,
            'kills': self.monsters_killed,
        }

    # ========================================================================
    # Achievement Checking (example of event-driven features)
    # ========================================================================

    def _check_achievement_centurion(self) -> None:
        """Check for 100 kills achievement."""
        if self.monsters_killed == 100:
            logger.info("Achievement unlocked: Centurion (100 kills)")
            # In real implementation, would publish ACHIEVEMENT_UNLOCKED event


class GameTelemetry:
    """
    Game telemetry for debugging and balance analysis.

    Tracks detailed game events for:
    - Performance analysis
    - Balance tuning
    - Bug investigation
    - Session replay

    Unlike StatsTracker (aggregated stats), this tracks individual events.
    """

    def __init__(self):
        """Initialize telemetry tracking."""
        self.turn_count = 0
        self.combat_events: List[dict] = []
        self.player_deaths: List[dict] = []
        self.performance_samples: List[dict] = []

    def log_turn(self, snapshot: GameStateSnapshot) -> None:
        """
        Log game state snapshot for turn.

        Args:
            snapshot: Current game state snapshot
        """
        self.turn_count = snapshot.turn

        logger.debug(
            "Turn state",
            extra=snapshot.to_dict()
        )

    def log_combat(
        self,
        attacker_name: str,
        attacker_attack: int,
        defender_name: str,
        defender_defense: int,
        damage: int,
        killed: bool
    ) -> None:
        """
        Log detailed combat event for balance analysis.

        Args:
            attacker_name: Name of attacker
            attacker_attack: Attack stat
            defender_name: Name of defender
            defender_defense: Defense stat
            damage: Damage dealt
            killed: Whether defender was killed
        """
        event = {
            'type': 'combat',
            'turn': self.turn_count,
            'attacker': attacker_name,
            'attacker_attack': attacker_attack,
            'defender': defender_name,
            'defender_defense': defender_defense,
            'damage': damage,
            'killed': killed,
            'timestamp': time.time(),
        }
        self.combat_events.append(event)

        logger.info(
            "Combat event",
            extra=event
        )

    def log_player_death(
        self,
        floor: int,
        player_hp: int,
        player_level: int,
        cause: str,
        monsters_alive: int
    ) -> None:
        """
        Log player death for difficulty tuning.

        Args:
            floor: Floor number where death occurred
            player_hp: Player HP at death
            player_level: Player level
            cause: Cause of death
            monsters_alive: Number of monsters alive
        """
        death = {
            'turn': self.turn_count,
            'floor': floor,
            'player_hp': player_hp,
            'player_level': player_level,
            'cause': cause,
            'monsters_alive': monsters_alive,
            'timestamp': time.time(),
        }
        self.player_deaths.append(death)

        logger.info(
            "Player death",
            extra=death
        )

    def get_average_combat_damage(self) -> float:
        """Calculate average damage per combat event."""
        if not self.combat_events:
            return 0.0

        total_damage = sum(e['damage'] for e in self.combat_events)
        return total_damage / len(self.combat_events)

    def get_death_analysis(self) -> dict:
        """
        Analyze player deaths for balance tuning.

        Returns:
            Dictionary with death statistics
        """
        if not self.player_deaths:
            return {
                'total_deaths': 0,
                'avg_floor': 0,
                'avg_turn': 0,
            }

        total = len(self.player_deaths)
        avg_floor = sum(d['floor'] for d in self.player_deaths) / total
        avg_turn = sum(d['turn'] for d in self.player_deaths) / total

        # Deaths by floor
        deaths_by_floor: Dict[int, int] = {}
        for death in self.player_deaths:
            floor = death['floor']
            deaths_by_floor[floor] = deaths_by_floor.get(floor, 0) + 1

        return {
            'total_deaths': total,
            'avg_floor': avg_floor,
            'avg_turn': avg_turn,
            'deaths_by_floor': deaths_by_floor,
        }


class PerformanceTelemetry:
    """
    Track performance metrics for optimization.

    Measures operation durations to identify bottlenecks.
    """

    def __init__(self):
        """Initialize performance tracking."""
        self.operation_times: Dict[str, List[float]] = {}

    def record(self, operation: str, duration: float) -> None:
        """
        Record operation timing.

        Args:
            operation: Operation name
            duration: Duration in seconds
        """
        if operation not in self.operation_times:
            self.operation_times[operation] = []

        self.operation_times[operation].append(duration)

        # Log if slow (> 100ms threshold)
        if duration > 0.1:
            logger.warning(
                "Slow operation",
                extra={
                    'operation': operation,
                    'duration_ms': int(duration * 1000),
                }
            )

    def get_stats(self) -> dict:
        """
        Get performance statistics for all operations.

        Returns:
            Dictionary mapping operation names to stats
        """
        stats = {}
        for operation, times in self.operation_times.items():
            if not times:
                continue

            stats[operation] = {
                'count': len(times),
                'avg_ms': int(sum(times) / len(times) * 1000),
                'max_ms': int(max(times) * 1000),
                'min_ms': int(min(times) * 1000),
            }

        return stats
