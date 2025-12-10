# Events, Async/Await, and Observability: Pre-Coding Guide

**Document Type:** Technical Guidelines (MVP + Phase 2 Considerations)
**Audience:** Developers starting MVP implementation
**Status:** Active
**Last Updated:** 2025-10-24

---

## Overview

This guide covers **critical topics NOT well addressed** in other docs:
1. **Event-driven patterns** for MVP that scale to Phase 2
2. **Async/await with Textual** - critical integration patterns
3. **Game state observability** - beyond infrastructure logging

**Why this matters:** These decisions affect your code structure from day 1. Getting them right now prevents major refactoring later.

---

## Table of Contents

1. [Event-Driven Architecture for MVP](#1-event-driven-architecture-for-mvp)
2. [Async/Await Patterns with Textual](#2-asyncawait-patterns-with-textual)
3. [Game State Observability](#3-game-state-observability)
4. [Instrumentation Strategy](#4-instrumentation-strategy)
5. [Common Pitfalls](#5-common-pitfalls)

---

## 1. Event-Driven Architecture for MVP

### The Tension

**BASE_CLASS_ARCHITECTURE.md** describes a full event-driven system (EventBus, GameEvent) but marks it "Phase 2 - skip for MVP."

**The problem:** If you write pure imperative code now, refactoring to event-driven later is painful.

**The solution:** Write "event-ready" code without implementing EventBus yet.

### Event-Ready Pattern (Use Now)

```python
# ✅ GOOD - Event-ready without EventBus
class CombatSystem:
    def resolve_attack(self, attacker: Entity, defender: Entity) -> AttackResult:
        """Resolve attack and return structured result."""
        # Calculate damage
        damage = self._calculate_damage(attacker, defender)
        actual_damage = defender.take_damage(damage)

        # Create result object (this IS an event, just not published yet)
        result = AttackResult(
            attacker_id=attacker.entity_id,
            defender_id=defender.entity_id,
            damage=actual_damage,
            killed=not defender.is_alive,
            timestamp=time.time(),
        )

        # MVP: Direct notification
        self.game.message_log.add(f"{attacker.name} hits {defender.name} for {actual_damage}!")

        # Phase 2: Just add one line here
        # self.event_bus.publish(GameEventType.ATTACK_RESOLVED, result.to_dict())

        return result


# ✅ Result objects are proto-events
@dataclass
class AttackResult:
    """Attack result - MVP uses this, Phase 2 publishes it."""
    attacker_id: str
    defender_id: str
    damage: int
    killed: bool
    timestamp: float

    def to_dict(self) -> dict:
        """Convert to event payload (Phase 2)."""
        return {
            'attacker_id': self.attacker_id,
            'defender_id': self.defender_id,
            'damage': self.damage,
            'killed': self.killed,
            'timestamp': self.timestamp,
        }
```

### Action Pattern Returns Events

**Already in BASE_CLASS_ARCHITECTURE.md** - ActionOutcome has `events` field:

```python
@dataclass
class ActionOutcome:
    """Result of action execution."""
    result: ActionResult
    took_turn: bool
    messages: list[str]
    events: list[dict]  # ⭐ These become EventBus events in Phase 2


# MVP usage
outcome = action.execute(context)

# Display messages (MVP)
for message in outcome.messages:
    self.message_log.add(message)

# Phase 2: Publish events
# for event_data in outcome.events:
#     self.event_bus.publish(event_data['type'], event_data)
```

### Statistics/Achievements Pattern

**Problem:** You want to track statistics (kills, damage dealt) but don't want to pollute game logic.

**Event-ready solution:**

```python
# src/core/stats_tracker.py
class StatsTracker:
    """Track game statistics (MVP: direct calls, Phase 2: event subscriber)."""

    def __init__(self):
        self.total_damage_dealt = 0
        self.monsters_killed = 0
        self.ore_mined = 0

    # MVP: Call directly after combat
    def on_attack_resolved(self, result: AttackResult):
        """Track combat stats."""
        self.total_damage_dealt += result.damage
        if result.killed:
            self.monsters_killed += 1
            self._check_achievement_centurion()

    # MVP: Call directly after mining
    def on_ore_mined(self, ore: Entity):
        """Track mining stats."""
        self.ore_mined += 1

    def _check_achievement_centurion(self):
        """Check for 100 kills achievement."""
        if self.monsters_killed >= 100:
            print("🏆 Achievement: Centurion (100 kills)")


# MVP: Game.py calls tracker directly
class Game:
    def __init__(self):
        self.stats = StatsTracker()

    def process_combat(self, attacker, defender):
        result = self.combat_system.resolve_attack(attacker, defender)
        self.stats.on_attack_resolved(result)  # Direct call


# Phase 2: StatsTracker becomes event subscriber
# event_bus.subscribe(GameEventType.ATTACK_RESOLVED, stats.on_attack_resolved)
# No more direct calls needed!
```

### Event-Ready Checklist

**✅ Do this in MVP:**
- [ ] Return structured result objects (AttackResult, MiningResult, etc.)
- [ ] Result objects have `to_dict()` method
- [ ] ActionOutcome has `events` field (even if unused)
- [ ] Statistics tracked in separate class with `on_*` methods
- [ ] Methods accept result objects, not individual parameters

**❌ Don't do this in MVP:**
- [ ] ~~Implement EventBus~~
- [ ] ~~Create event subscription system~~
- [ ] ~~Event-driven game loop~~

**Refactoring effort Phase 1 → Phase 2:** < 1 day if you follow event-ready pattern.

---

## 2. Async/Await Patterns with Textual

### The Critical Gap

**UI_FRAMEWORK.md says:** "Use async/await for all Textual code"

**Current code (app.py):** 100% synchronous

**The problem:** Textual is async-native. Mixing sync game logic with async UI requires careful patterns.

### Textual Async Architecture

```python
from textual.app import App
from textual.reactive import reactive

class VeinbornApp(App):
    """Textual app - async required."""

    # Reactive state (updates UI automatically)
    player_hp: reactive[int] = reactive(10)

    def compose(self) -> ComposeResult:
        """Build UI - SYNCHRONOUS."""
        yield MapWidget()
        yield StatusBar()
        yield MessageLog()

    async def on_mount(self) -> None:
        """Called when app mounted - ASYNC."""
        # Initialize game state
        self.game = Game()  # Sync object
        self.refresh_ui()

    # Action handlers can be async
    async def action_move(self, dx: int, dy: int) -> None:
        """Handle movement action - ASYNC."""
        # Call sync game logic
        outcome = self.game.process_move(dx, dy)

        # Update UI (async)
        await self.update_ui(outcome)

    async def update_ui(self, outcome: ActionOutcome) -> None:
        """Update UI from game outcome - ASYNC."""
        # Add messages
        for message in outcome.messages:
            self.query_one(MessageLog).add_message(message)

        # Update reactive properties (triggers re-render)
        self.player_hp = self.game.player.hp

        # Refresh widgets
        self.query_one(MapWidget).refresh()
```

### Sync vs Async Decision Tree

**When to use `async def`:**
- ✅ Textual event handlers (`on_mount`, `on_key`, action methods)
- ✅ Any method that calls other async methods
- ✅ Any method that does I/O (file, network - Phase 2)
- ✅ Methods that need `await self.query_one(...)` or UI updates

**When to use regular `def`:**
- ✅ Pure game logic (combat, pathfinding, map generation)
- ✅ Data classes and entities
- ✅ Utility functions (math, validation)
- ✅ Anything that doesn't touch UI or I/O

### Pattern: Sync Game Logic, Async UI Glue

```python
# ✅ GOOD - Clear separation

# Game logic - SYNCHRONOUS
class CombatSystem:
    def resolve_attack(self, attacker: Entity, defender: Entity) -> AttackResult:
        """Pure game logic - no I/O, no UI."""
        damage = self._calculate_damage(attacker, defender)
        actual_damage = defender.take_damage(damage)
        return AttackResult(damage=actual_damage, killed=not defender.is_alive)


# UI layer - ASYNCHRONOUS
class VeinbornApp(App):
    async def action_attack(self, target_id: str) -> None:
        """UI action handler - async."""
        # Call sync game logic
        target = self.game.get_entity(target_id)
        result = self.game.combat_system.resolve_attack(self.game.player, target)

        # Update UI (async)
        await self.show_combat_animation(result)
        await self.refresh_display()
```

### Pattern: Async I/O with Sync Game State

```python
# Future: Save/load with async I/O
class GamePersistence:
    async def save_game(self, game: Game, path: Path) -> None:
        """Save game asynchronously."""
        # Get sync game state
        game_data = game.to_dict()  # Synchronous

        # Write async (doesn't block UI)
        async with aiofiles.open(path, 'w') as f:
            await f.write(json.dumps(game_data))

    async def load_game(self, path: Path) -> Game:
        """Load game asynchronously."""
        # Read async
        async with aiofiles.open(path, 'r') as f:
            game_data = json.loads(await f.read())

        # Restore sync game state
        return Game.from_dict(game_data)  # Synchronous


# Usage in app
class VeinbornApp(App):
    async def action_save(self) -> None:
        """Save game action."""
        await self.persistence.save_game(self.game, Path("save.json"))
        self.notify("Game saved!")
```

### Common Pitfall: Blocking the Event Loop

```python
# ❌ BAD - Blocks UI for 2 seconds!
class VeinbornApp(App):
    async def action_generate_dungeon(self) -> None:
        """Generate new dungeon."""
        # This blocks the event loop!
        self.game.generate_dungeon()  # Takes 2 seconds
        await self.refresh_display()


# ✅ GOOD - Run in thread pool
import asyncio
from concurrent.futures import ThreadPoolExecutor

class VeinbornApp(App):
    def __init__(self):
        super().__init__()
        self.executor = ThreadPoolExecutor(max_workers=1)

    async def action_generate_dungeon(self) -> None:
        """Generate new dungeon without blocking UI."""
        # Show loading message
        self.notify("Generating dungeon...")

        # Run in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self.game.generate_dungeon  # Sync function runs in thread
        )

        # Update UI
        await self.refresh_display()
        self.notify("Dungeon generated!")
```

### Textual Reactive Properties

**Use these for automatic UI updates:**

```python
from textual.reactive import reactive

class VeinbornApp(App):
    # Reactive properties trigger re-render when changed
    player_hp: reactive[int] = reactive(10)
    player_max_hp: reactive[int] = reactive(10)
    floor_number: reactive[int] = reactive(1)

    async def action_move(self, dx: int, dy: int) -> None:
        """Move player."""
        outcome = self.game.process_move(dx, dy)

        # Update reactive properties (automatic UI refresh!)
        self.player_hp = self.game.player.hp

    def watch_player_hp(self, old_hp: int, new_hp: int) -> None:
        """Called automatically when player_hp changes."""
        if new_hp < old_hp:
            # Player took damage - show red flash
            self.add_class("damage-flash")


# In status bar widget
class StatusBar(Static):
    def render(self) -> str:
        """Render status bar."""
        app = self.app
        return f"HP: {app.player_hp}/{app.player_max_hp}  Floor: {app.floor_number}"
```

### Async/Await Checklist

**✅ For MVP:**
- [ ] Textual event handlers are `async def`
- [ ] Game logic classes are regular `def`
- [ ] Long operations (dungeon gen) run in thread pool
- [ ] Use reactive properties for UI state
- [ ] Test that UI stays responsive during generation

**⚠️ Don't worry about:**
- [ ] ~~Async database calls~~ (Phase 2)
- [ ] ~~Async network calls~~ (Phase 2)
- [ ] ~~Async message bus~~ (Phase 2)

---

## 3. Game State Observability

### Beyond Infrastructure Logging

**OPERATIONAL_EXCELLENCE_GUIDELINES.md** covers logging (INFO/DEBUG/ERROR).

**Missing:** What game state to log for debugging gameplay issues.

### Game State Telemetry

```python
# src/core/telemetry.py
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Any

logger = logging.getLogger('veinborn.telemetry')


@dataclass
class GameStateSnapshot:
    """Snapshot of game state for telemetry."""
    turn: int
    player_hp: int
    player_pos: tuple[int, int]
    monsters_alive: int
    floor: int
    inventory_size: int
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GameTelemetry:
    """Track game state for debugging and analytics."""

    def __init__(self):
        self.turn_count = 0
        self.combat_events = []
        self.player_deaths = []

    def log_turn(self, game: 'Game'):
        """Log game state each turn (DEBUG level)."""
        self.turn_count += 1

        snapshot = GameStateSnapshot(
            turn=self.turn_count,
            player_hp=game.player.hp,
            player_pos=(game.player.x, game.player.y),
            monsters_alive=len([m for m in game.monsters if m.is_alive]),
            floor=game.current_floor,
            inventory_size=len(game.player.inventory),
            timestamp=time.time(),
        )

        logger.debug(
            "Turn state",
            extra=snapshot.to_dict()  # Structured logging
        )

    def log_combat(self, attacker: Entity, defender: Entity, damage: int):
        """Log combat event for balance analysis."""
        event = {
            'type': 'combat',
            'turn': self.turn_count,
            'attacker': attacker.name,
            'attacker_attack': attacker.attack,
            'defender': defender.name,
            'defender_defense': defender.defense,
            'damage': damage,
            'killed': defender.hp <= 0,
        }
        self.combat_events.append(event)

        logger.info(
            "Combat event",
            extra=event
        )

    def log_player_death(self, game: 'Game', cause: str):
        """Log player death for difficulty tuning."""
        death = {
            'turn': self.turn_count,
            'floor': game.current_floor,
            'player_hp': game.player.hp,
            'player_level': game.player.get_stat('level', 1),
            'cause': cause,
            'monsters_alive': len([m for m in game.monsters if m.is_alive]),
            'timestamp': time.time(),
        }
        self.player_deaths.append(death)

        logger.info(
            "Player death",
            extra=death
        )

    def get_session_stats(self) -> dict:
        """Get statistics for this session."""
        return {
            'turns_played': self.turn_count,
            'combat_events': len(self.combat_events),
            'deaths': len(self.player_deaths),
            'average_combat_damage': self._average_damage(),
        }

    def _average_damage(self) -> float:
        """Calculate average damage per combat event."""
        if not self.combat_events:
            return 0.0
        total_damage = sum(e['damage'] for e in self.combat_events)
        return total_damage / len(self.combat_events)
```

### Balance Telemetry

```python
class BalanceTelemetry:
    """Track game balance metrics."""

    def __init__(self):
        self.ore_quality_samples = []
        self.monster_difficulty = []

    def log_ore_spawn(self, ore: OreVein, floor: int):
        """Track ore quality distribution."""
        sample = {
            'floor': floor,
            'hardness': ore.hardness,
            'purity': ore.purity,
            'avg_quality': ore.average_quality,
        }
        self.ore_quality_samples.append(sample)

        # Log every 10 spawns
        if len(self.ore_quality_samples) % 10 == 0:
            avg_quality = sum(s['avg_quality'] for s in self.ore_quality_samples[-10:]) / 10
            logger.info(
                "Ore quality stats",
                floor=floor,
                avg_quality_last_10=avg_quality,
            )

    def log_monster_spawn(self, monster: Monster, floor: int):
        """Track monster difficulty distribution."""
        difficulty = monster.hp * monster.attack / max(1, monster.defense)
        sample = {
            'floor': floor,
            'monster_type': monster.name,
            'hp': monster.hp,
            'attack': monster.attack,
            'defense': monster.defense,
            'difficulty': difficulty,
        }
        self.monster_difficulty.append(sample)
```

### Performance Telemetry

```python
import time
from contextlib import contextmanager

class PerformanceTelemetry:
    """Track performance metrics."""

    def __init__(self):
        self.operation_times = {}

    @contextmanager
    def measure(self, operation: str):
        """Measure operation duration."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self._record(operation, duration)

    def _record(self, operation: str, duration: float):
        """Record operation timing."""
        if operation not in self.operation_times:
            self.operation_times[operation] = []

        self.operation_times[operation].append(duration)

        # Log if slow
        if duration > 0.1:  # 100ms threshold
            logger.warning(
                "Slow operation",
                operation=operation,
                duration_ms=int(duration * 1000),
            )

    def get_stats(self) -> dict:
        """Get performance statistics."""
        stats = {}
        for operation, times in self.operation_times.items():
            stats[operation] = {
                'count': len(times),
                'avg_ms': int(sum(times) / len(times) * 1000),
                'max_ms': int(max(times) * 1000),
                'min_ms': int(min(times) * 1000),
            }
        return stats


# Usage
class Game:
    def __init__(self):
        self.perf = PerformanceTelemetry()

    def generate_dungeon(self):
        """Generate dungeon with performance tracking."""
        with self.perf.measure('dungeon_generation'):
            # Generate dungeon
            self._generate_bsp_tree()
            self._place_corridors()
            self._spawn_monsters()
```

---

## 4. Instrumentation Strategy

### What to Instrument in MVP

**High value (do now):**
- ✅ Player death (floor, HP, cause)
- ✅ Combat events (attacker, defender, damage)
- ✅ Slow operations (> 100ms)
- ✅ Dungeon generation time
- ✅ Turn-by-turn state snapshots (DEBUG)

**Medium value (Phase 2):**
- ⚠️ Ore quality distribution
- ⚠️ Monster spawn distribution
- ⚠️ Player progression rate

**Low value (Phase 3):**
- ❌ Every entity position
- ❌ Every HP change
- ❌ UI render times

### Instrumentation Pattern

```python
class Game:
    def __init__(self):
        # Always create telemetry objects
        self.telemetry = GameTelemetry()
        self.balance_telemetry = BalanceTelemetry()
        self.perf_telemetry = PerformanceTelemetry()

    def process_turn(self):
        """Process one game turn."""
        # Log state snapshot (DEBUG level - disabled in prod)
        self.telemetry.log_turn(self)

        # Process player action
        action = self._get_player_action()
        outcome = action.execute(self.context)

        # Log if combat occurred
        if outcome.events:
            for event in outcome.events:
                if event['type'] == 'attack_resolved':
                    self.telemetry.log_combat(
                        self.get_entity(event['attacker_id']),
                        self.get_entity(event['defender_id']),
                        event['damage'],
                    )

        # Process monsters
        with self.perf_telemetry.measure('monster_ai'):
            self._process_monster_turns()

        # Check for player death
        if not self.player.is_alive:
            self.telemetry.log_player_death(self, cause="combat")
```

### Log Analysis Workflow

```python
# analyze_logs.py
import json
from pathlib import Path

def analyze_player_deaths(log_file: Path):
    """Analyze player deaths for difficulty tuning."""
    deaths = []

    with open(log_file) as f:
        for line in f:
            if 'Player death' in line:
                # Parse JSON log line
                log_data = json.loads(line)
                deaths.append(log_data)

    # Analyze
    avg_floor = sum(d['floor'] for d in deaths) / len(deaths)
    avg_turn = sum(d['turn'] for d in deaths) / len(deaths)

    print(f"Average death floor: {avg_floor:.1f}")
    print(f"Average death turn: {avg_turn:.0f}")

    # Deaths by floor
    by_floor = {}
    for d in deaths:
        floor = d['floor']
        by_floor[floor] = by_floor.get(floor, 0) + 1

    print("\nDeaths by floor:")
    for floor in sorted(by_floor.keys()):
        print(f"  Floor {floor}: {by_floor[floor]}")


# Run analysis
analyze_player_deaths(Path("veinborn.log"))
```

---

## 5. Common Pitfalls

### Pitfall 1: Over-Engineering Events

```python
# ❌ BAD - Implementing full EventBus in MVP
class EventBus:
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type, callback):
        # 100 lines of event bus code...

# ✅ GOOD - Just return result objects
def resolve_attack(...) -> AttackResult:
    return AttackResult(damage=5, killed=True)
```

### Pitfall 2: Async Everywhere

```python
# ❌ BAD - Making pure game logic async
class Entity:
    async def take_damage(self, amount: int):  # Why async???
        self.hp -= amount

# ✅ GOOD - Only UI layer is async
class Entity:
    def take_damage(self, amount: int):  # Sync!
        self.hp -= amount
```

### Pitfall 3: Logging Everything

```python
# ❌ BAD - Logging every tiny detail
def move_player(dx, dy):
    logger.debug(f"move_player called with dx={dx}, dy={dy}")
    logger.debug(f"Current position: {self.x}, {self.y}")
    new_x = self.x + dx
    logger.debug(f"Calculating new_x: {new_x}")
    new_y = self.y + dy
    logger.debug(f"Calculating new_y: {new_y}")
    # ... 20 more debug lines

# ✅ GOOD - Log meaningful state changes
def move_player(dx, dy):
    old_pos = (self.x, self.y)
    self.x += dx
    self.y += dy
    logger.debug("Player moved", from_pos=old_pos, to_pos=(self.x, self.y))
```

### Pitfall 4: Blocking UI Thread

```python
# ❌ BAD - Long operation blocks UI
async def action_generate() -> None:
    self.game.generate_dungeon()  # Blocks for 2 seconds!

# ✅ GOOD - Run in executor
async def action_generate() -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, self.game.generate_dungeon)
```

---

## Summary Checklist

### Events (MVP)
- [ ] Return structured result objects (AttackResult, etc.)
- [ ] Result objects have `to_dict()` method
- [ ] ActionOutcome has `events` field
- [ ] Statistics/achievements in separate class with `on_*` methods
- [ ] Don't implement EventBus yet

### Async/Await (MVP)
- [ ] Textual event handlers are `async def`
- [ ] Game logic is regular `def`
- [ ] Long operations use `run_in_executor`
- [ ] Use reactive properties for UI state
- [ ] Test UI responsiveness

### Observability (MVP)
- [ ] Log player deaths with context
- [ ] Log combat events
- [ ] Track slow operations (> 100ms)
- [ ] Log turn state at DEBUG level
- [ ] Create telemetry classes

### Performance (MVP)
- [ ] Measure dungeon generation time
- [ ] Measure AI processing time
- [ ] Measure turn processing time
- [ ] Log warnings for slow operations

---

## Quick Reference

**Event-ready code:**
```python
# Return result objects, not void
def resolve_attack(...) -> AttackResult:
    return AttackResult(damage=5)
```

**Async/sync boundary:**
```python
# Textual handler (async) → Game logic (sync)
async def action_move(self):
    result = self.game.move_player()  # Sync call
    await self.refresh_ui()  # Async UI update
```

**Game telemetry:**
```python
# Log meaningful events
logger.info("Player death", floor=5, turn=234, cause="goblin")
```

**Performance:**
```python
# Measure long operations
with perf.measure('dungeon_gen'):
    generate_dungeon()
```

---

**Next Steps:**
1. Read this guide before starting MVP coding
2. Set up telemetry classes
3. Make all Textual event handlers async
4. Keep game logic synchronous
5. Return result objects from all systems

**Reference Docs:**
- `BASE_CLASS_ARCHITECTURE.md` - Action/System patterns
- `OPERATIONAL_EXCELLENCE_GUIDELINES.md` - Logging standards
- `UI_FRAMEWORK.md` - Textual overview

---

**You're now prepared for events, async, and observability!** 🚀
