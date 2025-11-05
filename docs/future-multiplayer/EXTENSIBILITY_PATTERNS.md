# Brogue Extensibility & Composition Patterns

**Document Type:** Architecture Patterns
**Audience:** Senior Developers, System Architects
**Status:** Active
**Last Updated:** 2025-10-23

---

## Overview

This document defines patterns for building composable, extensible game systems that can be added, removed, or modified without touching core code.

**Core Goals:**
- Add features without modifying existing code (Open/Closed Principle)
- Enable/disable systems via configuration
- Support community mods and extensions
- Make testing easier (isolated systems)

---

## 1. Event-Driven Architecture

### The Problem

**Tight Coupling:**
```python
# ❌ Bad - systems directly call each other
class CombatSystem:
    def on_monster_died(self, monster):
        # Combat knows about achievements!
        achievement_system.check_kill_achievement(player)
        # Combat knows about stats!
        stats_system.record_kill(player)
        # Combat knows about loot!
        loot_system.drop_items(monster.pos)
```

**Problems:**
- Can't add new systems without modifying CombatSystem
- Can't test CombatSystem in isolation
- Can't disable achievements without changing code

### The Solution: Event Bus

```python
# brogue/events/event_bus.py
from typing import Callable, Dict, List
from dataclasses import dataclass
from enum import Enum

class GameEventType(str, Enum):
    # Combat
    MONSTER_DIED = "monster_died"
    PLAYER_DAMAGED = "player_damaged"

    # Mining
    ORE_EXTRACTED = "ore_extracted"

    # Progression
    PLAYER_LEVELED_UP = "player_leveled_up"
    FLOOR_COMPLETED = "floor_completed"

@dataclass
class GameEvent:
    event_type: GameEventType
    data: dict
    source: str
    tick: int

class GameEventBus:
    """Internal event bus for game systems"""

    def __init__(self):
        self._handlers: Dict[GameEventType, List[Callable]] = {}

    def subscribe(self, event_type: GameEventType, handler: Callable):
        """Subscribe to event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event: GameEvent):
        """Publish event to all subscribers"""
        if event.event_type in self._handlers:
            for handler in self._handlers[event_type]:
                await handler(event)
```

**Usage:**

```python
# ✅ Good - combat system publishes event
class CombatSystem:
    def __init__(self, event_bus: GameEventBus):
        self.event_bus = event_bus

    async def on_monster_died(self, monster, killed_by):
        # Just publish event - don't know who listens
        await self.event_bus.publish(GameEvent(
            event_type=GameEventType.MONSTER_DIED,
            data={
                "monster_id": monster.id,
                "monster_type": monster.type,
                "player_id": killed_by,
                "floor": self.current_floor
            },
            source="combat_system",
            tick=self.current_tick
        ))

# Achievement system subscribes (decoupled!)
class AchievementSystem:
    def __init__(self, event_bus: GameEventBus):
        event_bus.subscribe(GameEventType.MONSTER_DIED, self.on_monster_died)
        self.kills = {}

    async def on_monster_died(self, event: GameEvent):
        player_id = event.data["player_id"]
        self.kills[player_id] = self.kills.get(player_id, 0) + 1

        if self.kills[player_id] == 100:
            await self.award_achievement(player_id, "MONSTER_SLAYER")

# Stats system also subscribes (also decoupled!)
class StatsSystem:
    def __init__(self, event_bus: GameEventBus):
        event_bus.subscribe(GameEventType.MONSTER_DIED, self.on_kill)

    async def on_kill(self, event: GameEvent):
        # Track kills by monster type
        monster_type = event.data["monster_type"]
        self.kill_counts[monster_type] += 1
```

**Benefits:**
- ✅ CombatSystem doesn't know about achievements
- ✅ Can add new subscribers without changing CombatSystem
- ✅ Can disable AchievementSystem without code changes
- ✅ Easy to test (publish fake events)

---

## 2. Plugin-Based Game Systems

### System Base Class

```python
# brogue/systems/base.py
from abc import ABC, abstractmethod
from brogue.events.event_bus import GameEventBus

class GameSystem(ABC):
    """Base class for all game systems"""

    def __init__(self, event_bus: GameEventBus):
        self.event_bus = event_bus
        self.enabled = True

    @abstractmethod
    async def initialize(self):
        """Setup - subscribe to events, load data"""
        pass

    @abstractmethod
    async def tick(self, delta_time: float):
        """Update every game tick"""
        pass

    async def shutdown(self):
        """Cleanup"""
        pass
```

### Concrete Systems

```python
# brogue/systems/mining.py
class MiningSystem(GameSystem):
    """Mining mechanics - self-contained"""

    async def initialize(self):
        # Subscribe to events
        self.event_bus.subscribe(GameEventType.MINING_STARTED, self.on_start)

        # Load content
        self.ore_types = content_loader.load("ore_types")
        self.mining_progress = {}

    async def tick(self, delta_time: float):
        """Update mining progress"""
        for player_id, progress in list(self.mining_progress.items()):
            progress["turns_remaining"] -= 1

            if progress["turns_remaining"] <= 0:
                await self.extract_ore(player_id, progress["ore_id"])
                del self.mining_progress[player_id]

    async def on_start(self, event: GameEvent):
        player_id = event.data["player_id"]
        self.mining_progress[player_id] = {
            "ore_id": event.data["ore_id"],
            "turns_remaining": 5
        }
```

### System Manager (Orchestrator)

```python
# brogue/systems/manager.py
class SystemManager:
    """Manages all game systems"""

    def __init__(self, event_bus: GameEventBus, config: dict):
        self.event_bus = event_bus
        self.systems: List[GameSystem] = []
        self.config = config

    def register(self, system: GameSystem):
        """Register a system"""
        self.systems.append(system)

    async def initialize_all(self):
        """Initialize all enabled systems"""
        for system in self.systems:
            if self._is_enabled(system):
                await system.initialize()

    async def tick_all(self, delta_time: float):
        """Tick all enabled systems"""
        for system in self.systems:
            if system.enabled:
                await system.tick(delta_time)

    def _is_enabled(self, system: GameSystem) -> bool:
        """Check if system is enabled in config"""
        system_name = system.__class__.__name__
        return self.config.get("enabled_systems", {}).get(system_name, True)
```

### Configuration (Enable/Disable)

```yaml
# config/systems.yaml
enabled_systems:
  CombatSystem: true
  MiningSystem: true
  CraftingSystem: true
  AchievementSystem: true
  QuestSystem: false     # Disabled (future feature)
  WeatherSystem: false   # Disabled (experimental)
```

### Usage

```python
# Create system manager
manager = SystemManager(event_bus, config)

# Register systems (plugins!)
manager.register(CombatSystem(event_bus))
manager.register(MiningSystem(event_bus))
manager.register(CraftingSystem(event_bus))
manager.register(AchievementSystem(event_bus))

# Initialize
await manager.initialize_all()

# Game loop
while running:
    await manager.tick_all(delta_time=0.1)
```

**Benefits:**
- ✅ Add new systems without touching core
- ✅ Enable/disable via config
- ✅ Test systems in isolation
- ✅ Community can write system plugins

---

## 3. Data-Driven Content

See `CONTENT_SYSTEM.md` for full details.

**Quick Example:**

```yaml
# data/monsters/goblin.yaml
id: goblin
stats:
  hp: 6
  attack: 3
loot_table:
  - item: gold
    amount: [1, 5]
```

```python
# Load at runtime
content = ContentLoader()
content.load_all()

# Spawn monster
goblin_def = content.get_monster("goblin")
goblin = Monster.from_definition(goblin_def)
```

**Benefits:**
- ✅ Add monsters without code changes
- ✅ Designers iterate independently
- ✅ Hot-reload in development
- ✅ Community content support

---

## 4. Behavior Composition (Status Effects)

### Composable Effects

```python
# brogue/behaviors/effects.py
from abc import ABC, abstractmethod

class StatusEffect(ABC):
    """Composable status effect"""

    def __init__(self, duration: int, stacks: int = 1):
        self.duration = duration
        self.stacks = stacks

    @abstractmethod
    async def on_apply(self, entity):
        """Called when effect is applied"""
        pass

    @abstractmethod
    async def on_tick(self, entity):
        """Called every tick"""
        pass

    @abstractmethod
    async def on_expire(self, entity):
        """Called when effect expires"""
        pass

# Concrete effects
class PoisonEffect(StatusEffect):
    async def on_tick(self, entity):
        damage = 2 * self.stacks
        entity.hp -= damage
        self.duration -= 1

class BlessedEffect(StatusEffect):
    def __init__(self, duration: int, damage_bonus: float = 0.25):
        super().__init__(duration)
        self.damage_bonus = damage_bonus

    async def on_apply(self, entity):
        self.original_attack = entity.attack
        entity.attack = int(entity.attack * (1 + self.damage_bonus))

    async def on_expire(self, entity):
        entity.attack = self.original_attack
```

### Entity with Effects

```python
class Entity:
    def __init__(self):
        self.effects: List[StatusEffect] = []

    def add_effect(self, effect: StatusEffect):
        """Add status effect (with stacking logic)"""
        existing = next((e for e in self.effects if type(e) == type(effect)), None)
        if existing:
            existing.stacks += effect.stacks
            existing.duration = max(existing.duration, effect.duration)
        else:
            self.effects.append(effect)
            await effect.on_apply(self)

    async def tick_effects(self):
        """Update all effects"""
        for effect in self.effects[:]:
            await effect.on_tick(self)
            if effect.duration <= 0:
                await effect.on_expire(self)
                self.effects.remove(effect)
```

**Benefits:**
- ✅ Effects are composable (stack multiple)
- ✅ Easy to add new effects
- ✅ Can be data-driven (load from YAML)

---

## 5. Dependency Injection (Testability)

### Simple Container

```python
# brogue/container.py
class ServiceContainer:
    """Simple DI container"""

    def __init__(self, config):
        self.config = config
        self._nats = None
        self._db = None

    async def nats(self):
        if not self._nats:
            self._nats = await NATS().connect(self.config.nats_url)
        return self._nats

    async def message_bus(self):
        nats = await self.nats()
        return MessageBus(nats)

    async def game_instance(self, instance_id):
        bus = await self.message_bus()
        return GameInstanceService(bus, instance_id)
```

### Testing with Mocks

```python
# tests/test_game_logic.py
@pytest.fixture
def mock_container():
    """Mock container for testing"""
    container = ServiceContainer(test_config)
    container._nats = MockNATS()  # Mock NATS
    return container

@pytest.mark.asyncio
async def test_combat(mock_container):
    """Test combat in isolation"""
    game = await mock_container.game_instance("test")

    # No real NATS needed!
    result = await game.attack(player, monster)
    assert monster.hp == 0
```

---

## 6. Configuration-Driven Features

### Feature Flags

```yaml
# config/features.yaml
features:
  mining: true
  crafting: true
  achievements: true
  quests: false         # Coming soon
  weather: false        # Experimental
  trading: false        # Future
```

```python
class FeatureFlags:
    def __init__(self, config: dict):
        self.features = config.get("features", {})

    def is_enabled(self, feature: str) -> bool:
        return self.features.get(feature, False)

# Usage
if feature_flags.is_enabled("mining"):
    manager.register(MiningSystem(event_bus))
```

---

## 7. Hot-Reload (Development)

### Content Hot-Reload

```python
# brogue/dev/hot_reload.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ContentHotReloader:
    """Watch YAML files and reload on change"""

    def __init__(self, content_loader):
        self.content_loader = content_loader
        self.observer = Observer()

    async def start(self):
        class ChangeHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if event.src_path.endswith('.yaml'):
                    print(f"🔄 Reloading {event.src_path}")
                    self.content_loader.load_all()
                    print("✅ Reload complete")

        self.observer.schedule(ChangeHandler(), path="data", recursive=True)
        self.observer.start()
        print("🔥 Hot-reload enabled!")

# Development mode only
if config.environment == "development":
    hot_reloader = ContentHotReloader(content_loader)
    await hot_reloader.start()
```

**Benefits:**
- Edit YAML file
- Save
- See changes immediately in game
- No restart needed!

---

## 8. Modding Support (Future)

### Plugin Directory Structure

```
~/.brogue/mods/
├── awesome_mod/
│   ├── mod.yaml           # Mod metadata
│   ├── systems/
│   │   └── custom_system.py
│   ├── content/
│   │   └── monsters/
│   │       └── new_monster.yaml
│   └── README.md
```

### Mod Loading

```python
class ModLoader:
    """Load community mods"""

    def load_mod(self, mod_path: Path):
        """Load and validate mod"""
        # Read metadata
        with open(mod_path / "mod.yaml") as f:
            metadata = yaml.safe_load(f)

        # Load content
        for content_file in (mod_path / "content").rglob("*.yaml"):
            content_loader.load_file(content_file)

        # Load systems (sandboxed!)
        for system_file in (mod_path / "systems").glob("*.py"):
            system = self.load_system_safely(system_file)
            system_manager.register(system)
```

---

## Summary: Extensibility Benefits

| Pattern | Benefit | Example |
|---------|---------|---------|
| **Event Bus** | Decouple systems | AchievementSystem subscribes to kills |
| **Plugin Systems** | Add features without core changes | New QuestSystem as plugin |
| **Data-Driven** | Designers iterate independently | Add monsters via YAML |
| **Composition** | Mix and match behaviors | Poison + Slow effects |
| **Hot-Reload** | Instant feedback | Edit monster, see changes now |
| **Feature Flags** | A/B testing, gradual rollout | Enable mining for 50% of players |
| **Mod Support** | Community extensions | Custom monsters, systems |

---

## References

- [Event-Driven Architecture](https://martinfowler.com/articles/201701-event-driven.html)
- [Plugin Architecture](https://en.wikipedia.org/wiki/Plug-in_(computing))
- [Open/Closed Principle](https://en.wikipedia.org/wiki/Open%E2%80%93closed_principle)

---

**Next Steps:**
1. Implement GameEventBus (`brogue/events/event_bus.py`)
2. Create GameSystem base class (`brogue/systems/base.py`)
3. Implement SystemManager (`brogue/systems/manager.py`)
4. Port existing systems to plugin architecture
5. Add configuration-driven feature flags
