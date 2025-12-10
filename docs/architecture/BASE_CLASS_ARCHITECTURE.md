# Veinborn Base Class Architecture

**Session**: bamizogi-1023
**Date**: 2025-10-23
**Purpose**: Define foundational base classes for Veinborn that support MVP, Lua scripting, and multiplayer

---

## Executive Summary

**Goal**: Design base classes that:
1. ✅ Work perfectly for MVP (single-player Python)
2. ✅ Enable trivial Lua integration (Phase 3)
3. ✅ Support multiplayer refactor (Phase 2)
4. ✅ Provide clean architecture regardless

**Key Insight**: These aren't "over-engineering"—they solve TODAY's problems while enabling tomorrow's features.

---

## 🎯 Phase Guide - What to Implement When

### MVP (Phase 1) - Implement Now ✅

**Core base classes needed for MVP:**
1. **Entity** - Common base for Player/Monster/Items (§1)
2. **Action** - Serializable player actions (§3)
3. **System** - Game logic processors (§4)
4. **ContentData** - YAML-loaded definitions (§8)

**Read these sections:** §1, §3, §4, §8 + Implementation Roadmap

**Skip for now:** Component (§2), GameEvent (§5), GameContext (§6), Serializable (§7)

### Phase 2 (Multiplayer) - Future 📋

**Add when building multiplayer:**
- **GameEvent** - Event bus for decoupling (§5)
- **GameContext** - Safe API surface (§6)
- **Serializable** - Network serialization (§7)

### Phase 3 (Lua Scripting) - Future 🚀

**Add when integrating Lua:**
- **Component** - Modular entity capabilities (§2)
- Lua API bindings (referenced throughout)

**Bottom line:** For MVP, focus on Entity, Action, System, and ContentData. The other classes can wait.

---

## Current State Analysis

### What You Have Now

**entities.py**:
```python
class Player:
    hp, max_hp, attack, defense, x, y, inventory
    move(), take_damage(), heal()

class Monster:
    name, hp, max_hp, attack, defense, x, y
    move_toward(), take_damage(), attack_target()
```

**Problems**:
- ❌ Code duplication (both have hp, attack, defense, x, y, take_damage)
- ❌ Can't share systems (healing works differently for each)
- ❌ Hard to serialize for multiplayer
- ❌ Difficult to expose to Lua (two different APIs)

**game.py**:
```python
class Game:
    handle_player_move()
    handle_combat()
    handle_monster_turns()
```

**Problems**:
- ❌ Direct method calls (can't serialize for multiplayer)
- ❌ Tight coupling (Game knows about every action type)
- ❌ Hard to test (can't isolate actions)
- ❌ No Lua integration point

---

## The 8 Critical Base Classes

### Overview Table

| Base Class | Purpose | Enables | Priority |
|------------|---------|---------|----------|
| **Entity** | Common base for Player/Monster/Items | Code reuse, uniform Lua API | HIGH |
| **Component** | Modular entity capabilities | Flexible composition, Lua scripts | MEDIUM |
| **Action** | Serializable player/monster actions | Multiplayer, Lua, testing | HIGH |
| **System** | Game logic processors | Clean separation, plugins | HIGH |
| **GameEvent** | Event bus messages | Decoupling, Lua hooks | MEDIUM |
| **GameContext** | Safe game state access | Lua API surface, testing | HIGH |
| **Serializable** | Save/load/network support | Multiplayer, persistence | MEDIUM |
| **ContentData** | YAML-loaded definitions | Data-driven design, Lua | HIGH |

---

## 1. Entity Base Class ✅ MVP

**Phase:** MVP (Implement Now)
**Priority:** HIGH

### Purpose
Unified base for anything in the game world (Player, Monster, Items, OreVeins, NPCs).

### Design

```python
# src/core/base/entity.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
import uuid


class EntityType(Enum):
    """Types of entities in the game."""
    PLAYER = "player"
    MONSTER = "monster"
    ITEM = "item"
    ORE_VEIN = "ore_vein"
    NPC = "npc"
    PROJECTILE = "projectile"


@dataclass
class Entity:
    """
    Base class for all game entities.

    Design Principles:
    - Unique ID for multiplayer sync
    - Position for spatial entities (None for inventory items)
    - Stats dictionary for flexible attributes
    - Type for polymorphism
    """

    # Identity
    entity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: EntityType = EntityType.PLAYER
    name: str = "Unknown"

    # Spatial (None if not in world, e.g., inventory items)
    x: Optional[int] = None
    y: Optional[int] = None

    # Core stats (all entities have these, but many are 0)
    hp: int = 0
    max_hp: int = 0
    attack: int = 0
    defense: int = 0

    # Flexible attributes (different entities need different things)
    stats: Dict[str, Any] = field(default_factory=dict)

    # State flags
    is_alive: bool = True
    is_active: bool = True

    # Component system (Phase 2)
    components: Dict[str, 'Component'] = field(default_factory=dict)

    # Lua/Content reference
    content_id: Optional[str] = None  # e.g., "goblin_warrior"

    def take_damage(self, amount: int) -> int:
        """
        Apply damage to this entity.

        Returns actual damage taken (for combat log).
        """
        if self.hp <= 0:
            return 0

        actual_damage = max(0, amount)
        self.hp = max(0, self.hp - actual_damage)

        if self.hp == 0:
            self.is_alive = False

        return actual_damage

    def heal(self, amount: int) -> int:
        """
        Heal this entity.

        Returns actual healing done.
        """
        if not self.is_alive or self.hp >= self.max_hp:
            return 0

        actual_healing = min(amount, self.max_hp - self.hp)
        self.hp += actual_healing
        return actual_healing

    def move_to(self, x: int, y: int):
        """Move entity to absolute position."""
        self.x = x
        self.y = y

    def move_by(self, dx: int, dy: int):
        """Move entity by offset."""
        if self.x is not None and self.y is not None:
            self.x += dx
            self.y += dy

    def distance_to(self, other: 'Entity') -> float:
        """Calculate distance to another entity."""
        if self.x is None or other.x is None:
            return float('inf')

        dx = self.x - other.x
        dy = self.y - other.y
        return (dx * dx + dy * dy) ** 0.5

    def is_adjacent(self, other: 'Entity') -> bool:
        """Check if adjacent to another entity (8-directional)."""
        if self.x is None or other.x is None:
            return False

        return abs(self.x - other.x) <= 1 and abs(self.y - other.y) <= 1

    def get_stat(self, stat_name: str, default: Any = 0) -> Any:
        """Get a stat value with fallback."""
        return self.stats.get(stat_name, default)

    def set_stat(self, stat_name: str, value: Any):
        """Set a stat value."""
        self.stats[stat_name] = value

    def to_dict(self) -> dict:
        """Serialize to dictionary (for save/load, multiplayer)."""
        return {
            'entity_id': self.entity_id,
            'entity_type': self.entity_type.value,
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'attack': self.attack,
            'defense': self.defense,
            'stats': self.stats,
            'is_alive': self.is_alive,
            'is_active': self.is_active,
            'content_id': self.content_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Entity':
        """Deserialize from dictionary."""
        entity = cls(
            entity_id=data['entity_id'],
            entity_type=EntityType(data['entity_type']),
            name=data['name'],
            x=data.get('x'),
            y=data.get('y'),
            hp=data['hp'],
            max_hp=data['max_hp'],
            attack=data['attack'],
            defense=data['defense'],
            stats=data.get('stats', {}),
            is_alive=data['is_alive'],
            is_active=data['is_active'],
            content_id=data.get('content_id'),
        )
        return entity
```

### Migration from Current Code

```python
# OLD: entities.py
class Player:
    def __init__(self):
        self.hp = 10
        self.max_hp = 10
        self.attack = 2
        self.defense = 1
        self.x = 0
        self.y = 0

# NEW: Using Entity base
class Player(Entity):
    def __init__(self, x: int = 0, y: int = 0):
        super().__init__(
            entity_type=EntityType.PLAYER,
            name="Player",
            x=x,
            y=y,
            hp=10,
            max_hp=10,
            attack=2,
            defense=1,
        )
        self.inventory = Inventory()

    # Player-specific methods
    def gain_xp(self, amount: int):
        xp = self.get_stat('xp', 0)
        self.set_stat('xp', xp + amount)
```

```python
# OLD: entities.py
class Monster:
    def __init__(self, name: str, hp: int, attack: int, defense: int, x: int, y: int):
        self.name = name
        self.hp = hp
        # ... etc

# NEW: Using Entity base
class Monster(Entity):
    def __init__(self, content_id: str, x: int, y: int, monster_data: dict):
        super().__init__(
            entity_type=EntityType.MONSTER,
            name=monster_data['name'],
            content_id=content_id,
            x=x,
            y=y,
            hp=monster_data['stats']['hp'],
            max_hp=monster_data['stats']['hp'],
            attack=monster_data['stats']['attack'],
            defense=monster_data['stats']['defense'],
        )

        # Load additional stats from YAML
        self.stats = monster_data.get('stats', {}).copy()
```

### Benefits

✅ **Code Reuse**: take_damage(), heal(), distance_to() work for all entities
✅ **Uniform Lua API**: `entity:take_damage(5)` works for Player, Monster, NPC
✅ **Serialization**: Single to_dict()/from_dict() for save/load/multiplayer
✅ **Testing**: Mock entities easily
✅ **Future-Proof**: Add projectiles, traps, NPCs without refactoring

---

## 2. Component Base Class 🚀 Phase 3

**Phase:** Phase 3 (Lua Scripting) - Skip for MVP
**Priority:** MEDIUM (Future)

### Purpose
Modular capabilities that can be attached to entities (Phase 2 feature, but design now).

### Design

```python
# src/core/base/component.py
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entity import Entity
    from .game_context import GameContext


class Component(ABC):
    """
    Base class for entity components (ECS pattern).

    Components are modular capabilities:
    - InventoryComponent: Can hold items
    - AIComponent: Has behavior AI
    - CombatComponent: Can fight
    - MiningComponent: Can mine ore
    - LuaScriptComponent: Custom Lua behavior

    Phase 1 (MVP): Not used (entities use inheritance)
    Phase 2 (Multiplayer): Refactor to components
    Phase 3 (Lua): Lua scripts can add components
    """

    def __init__(self, owner: 'Entity'):
        self.owner = owner
        self.enabled = True

    @abstractmethod
    def update(self, context: 'GameContext'):
        """Called each game tick (for active components like AI)."""
        pass

    def on_attached(self):
        """Called when component is added to entity."""
        pass

    def on_detached(self):
        """Called when component is removed from entity."""
        pass

    def to_dict(self) -> dict:
        """Serialize component state."""
        return {
            'enabled': self.enabled,
        }

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict, owner: 'Entity') -> 'Component':
        """Deserialize component state."""
        pass
```

### Example Components (Future)

```python
# Example: AI Component
class AIComponent(Component):
    """AI behavior for monsters."""

    def __init__(self, owner: Entity, ai_script: Optional[str] = None):
        super().__init__(owner)
        self.ai_script = ai_script  # Path to Lua script
        self.state = {}  # AI state machine data

    def update(self, context: GameContext):
        """Run AI behavior."""
        # Try Lua script first
        if self.ai_script and context.lua_bridge:
            context.lua_bridge.call_ai(self.ai_script, self.owner, context)
        else:
            # Default Python AI
            self.simple_chase_ai(context)

    def simple_chase_ai(self, context: GameContext):
        """Default chase-player AI."""
        player = context.get_player()
        if self.owner.is_adjacent(player):
            context.combat_system.attack(self.owner, player)
        else:
            # Move toward player
            dx, dy = context.pathfinding.get_direction(self.owner, player)
            context.movement_system.move_entity(self.owner, dx, dy)


# Example: Inventory Component
class InventoryComponent(Component):
    """Inventory for players/monsters."""

    def __init__(self, owner: Entity, capacity: int = 10):
        super().__init__(owner)
        self.items: List[Entity] = []
        self.capacity = capacity

    def update(self, context: GameContext):
        """Inventory doesn't need ticking."""
        pass

    def add_item(self, item: Entity) -> bool:
        if len(self.items) < self.capacity:
            self.items.append(item)
            item.x = None  # Remove from world
            item.y = None
            return True
        return False

    def remove_item(self, item: Entity) -> bool:
        if item in self.items:
            self.items.remove(item)
            return True
        return False
```

### Why Design Now, Use Later?

**Phase 1 (MVP)**: Keep simple inheritance (Player, Monster classes)
**Phase 2 (Multiplayer)**: Optionally refactor to components
**Phase 3 (Lua)**: Lua scripts can add custom components

**Key**: Designing the interface now means future refactor is mechanical, not architectural.

---

## 3. Action Base Class (CRITICAL!) ✅ MVP

**Phase:** MVP (Implement Now)
**Priority:** HIGH

### Purpose
Serialize player/monster actions for multiplayer, testing, and Lua.

### Design

```python
# src/core/base/action.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .entity import Entity
    from .game_context import GameContext


class ActionResult(Enum):
    """Result of action execution."""
    SUCCESS = "success"
    FAILURE = "failure"
    INVALID = "invalid"
    BLOCKED = "blocked"


@dataclass
class ActionOutcome:
    """Result of an action execution."""
    result: ActionResult
    took_turn: bool  # Did this consume a game turn?
    messages: list[str]  # Messages to display
    events: list[dict]  # Events to publish

    @staticmethod
    def success(took_turn: bool = True, message: str = "") -> 'ActionOutcome':
        return ActionOutcome(
            result=ActionResult.SUCCESS,
            took_turn=took_turn,
            messages=[message] if message else [],
            events=[],
        )

    @staticmethod
    def failure(message: str = "") -> 'ActionOutcome':
        return ActionOutcome(
            result=ActionResult.FAILURE,
            took_turn=False,
            messages=[message] if message else [],
            events=[],
        )


class Action(ABC):
    """
    Base class for all game actions.

    Actions are serializable, testable, and replayable:
    - MoveAction: Move entity
    - AttackAction: Attack target
    - MineAction: Mine ore vein
    - UseItemAction: Use item from inventory
    - CastSpellAction: Cast spell (future)

    Critical for:
    - Multiplayer (actions serialize to NATS messages)
    - Testing (create actions directly, verify outcomes)
    - Lua (scripts return Action objects)
    - Replay (save action history)
    """

    def __init__(self, actor_id: str):
        """
        Args:
            actor_id: Entity ID of the actor performing this action
        """
        self.actor_id = actor_id

    @abstractmethod
    def validate(self, context: 'GameContext') -> bool:
        """
        Check if action is valid before execution.

        Returns:
            True if action can be executed, False otherwise
        """
        pass

    @abstractmethod
    def execute(self, context: 'GameContext') -> ActionOutcome:
        """
        Execute the action.

        Returns:
            ActionOutcome describing what happened
        """
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        """Serialize action (for multiplayer, save/replay)."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> 'Action':
        """Deserialize action."""
        pass

    def get_action_type(self) -> str:
        """Return action type for serialization."""
        return self.__class__.__name__
```

### Concrete Action Examples

```python
# src/core/actions/move_action.py
@dataclass
class MoveAction(Action):
    """Move entity by offset."""

    actor_id: str
    dx: int
    dy: int

    def validate(self, context: GameContext) -> bool:
        """Check if move is valid."""
        actor = context.get_entity(self.actor_id)
        if not actor or not actor.is_alive:
            return False

        new_x = actor.x + self.dx
        new_y = actor.y + self.dy

        # Check bounds
        if not context.map.in_bounds(new_x, new_y):
            return False

        # Check walkable
        if not context.map.is_walkable(new_x, new_y):
            return False

        # Check entity collision (but allow attacks)
        return True

    def execute(self, context: GameContext) -> ActionOutcome:
        """Execute move."""
        actor = context.get_entity(self.actor_id)
        if not actor:
            return ActionOutcome.failure("Actor not found")

        new_x = actor.x + self.dx
        new_y = actor.y + self.dy

        # Check for combat
        target = context.get_entity_at(new_x, new_y)
        if target and target.is_alive:
            # Redirect to attack
            attack = AttackAction(self.actor_id, target.entity_id)
            return attack.execute(context)

        # Perform move
        if not self.validate(context):
            return ActionOutcome.failure("Cannot move there")

        actor.move_to(new_x, new_y)

        outcome = ActionOutcome.success(took_turn=True)
        outcome.events.append({
            'type': 'entity_moved',
            'entity_id': self.actor_id,
            'from': (actor.x - self.dx, actor.y - self.dy),
            'to': (actor.x, actor.y),
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


# src/core/actions/attack_action.py
@dataclass
class AttackAction(Action):
    """Attack another entity."""

    actor_id: str
    target_id: str

    def validate(self, context: GameContext) -> bool:
        actor = context.get_entity(self.actor_id)
        target = context.get_entity(self.target_id)

        if not actor or not actor.is_alive:
            return False
        if not target or not target.is_alive:
            return False
        if not actor.is_adjacent(target):
            return False

        return True

    def execute(self, context: GameContext) -> ActionOutcome:
        """Execute attack."""
        if not self.validate(context):
            return ActionOutcome.failure("Cannot attack")

        actor = context.get_entity(self.actor_id)
        target = context.get_entity(self.target_id)

        # Calculate damage
        damage = max(1, actor.attack - target.defense)
        actual_damage = target.take_damage(damage)

        # Build outcome
        outcome = ActionOutcome.success(took_turn=True)
        outcome.messages.append(
            f"{actor.name} hits {target.name} for {actual_damage} damage!"
        )

        # Publish events
        outcome.events.append({
            'type': 'entity_damaged',
            'attacker_id': self.actor_id,
            'target_id': self.target_id,
            'damage': actual_damage,
        })

        if not target.is_alive:
            outcome.messages.append(f"{target.name} died!")
            outcome.events.append({
                'type': 'entity_died',
                'entity_id': self.target_id,
                'killer_id': self.actor_id,
            })

        return outcome

    def to_dict(self) -> dict:
        return {
            'action_type': 'AttackAction',
            'actor_id': self.actor_id,
            'target_id': self.target_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AttackAction':
        return cls(
            actor_id=data['actor_id'],
            target_id=data['target_id'],
        )


# Example: Mining action (multi-turn!)
@dataclass
class MineAction(Action):
    """Mine an ore vein (multi-turn action)."""

    actor_id: str
    ore_vein_id: str
    turns_remaining: int = 0  # 0 means "just started"

    def validate(self, context: GameContext) -> bool:
        actor = context.get_entity(self.actor_id)
        ore_vein = context.get_entity(self.ore_vein_id)

        if not actor or not actor.is_alive:
            return False
        if not ore_vein or ore_vein.entity_type != EntityType.ORE_VEIN:
            return False
        if not actor.is_adjacent(ore_vein):
            return False

        return True

    def execute(self, context: GameContext) -> ActionOutcome:
        """Execute mining turn."""
        if not self.validate(context):
            return ActionOutcome.failure("Cannot mine")

        actor = context.get_entity(self.actor_id)
        ore_vein = context.get_entity(self.ore_vein_id)

        # First turn? Initialize
        if self.turns_remaining == 0:
            hardness = ore_vein.get_stat('hardness', 50)
            self.turns_remaining = 3 + (hardness // 25)  # 3-5 turns

        # Mine one turn
        self.turns_remaining -= 1

        outcome = ActionOutcome.success(took_turn=True)

        if self.turns_remaining > 0:
            # Still mining
            outcome.messages.append(
                f"Mining... {self.turns_remaining} turns remaining"
            )
            # Store mining state on actor
            actor.set_stat('mining_action', self.to_dict())
        else:
            # Mining complete!
            outcome.messages.append(f"Mined {ore_vein.name}!")

            # Add ore to inventory
            ore_item = ore_vein_to_inventory_item(ore_vein)
            if actor.inventory.add(ore_item):
                # Remove ore vein from world
                context.remove_entity(ore_vein.entity_id)

                outcome.events.append({
                    'type': 'ore_mined',
                    'actor_id': self.actor_id,
                    'ore_id': ore_item.entity_id,
                    'properties': ore_vein.stats,
                })

            # Clear mining state
            actor.set_stat('mining_action', None)

        return outcome

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
```

### How Game Loop Changes

```python
# OLD: game.py (direct calls)
def handle_player_move(self, dx, dy):
    new_x = self.state.player.x + dx
    new_y = self.state.player.y + dy
    # ... inline logic

# NEW: Action-based (Phase 1)
def handle_player_input(self, key: str):
    """Convert input to Action, execute it."""
    action = self.input_handler.key_to_action(key, self.state.player.entity_id)

    if action:
        outcome = action.execute(self.context)

        # Display messages
        for msg in outcome.messages:
            self.state.add_message(msg)

        # Publish events
        for event in outcome.events:
            self.event_bus.publish(event['type'], event)

        # Process turn if action consumed time
        if outcome.took_turn:
            self.process_monster_turns()
```

### Benefits

✅ **Multiplayer Ready**: Actions serialize to JSON → NATS messages
✅ **Testable**: Create actions directly, verify outcomes
✅ **Lua Integration**: Lua scripts return Action objects
✅ **Replay**: Save action history, replay games
✅ **Debugging**: Log all actions, reproduce bugs
✅ **Validation**: Separate validate() from execute() (server can validate client actions)

---

## 4. System Base Class ✅ MVP

**Phase:** MVP (Implement Now)
**Priority:** HIGH

### Purpose
Game logic processors that operate on entities (replaces scattered methods).

### Design

```python
# src/core/base/system.py
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game_context import GameContext


class System(ABC):
    """
    Base class for game systems.

    Systems are logic processors:
    - CombatSystem: Handles damage, death
    - MovementSystem: Handles movement, collision
    - MiningSystem: Handles ore mining
    - CraftingSystem: Handles item crafting
    - AISystem: Runs monster AI
    - EventSystem: Event bus

    Benefits:
    - Clean separation of concerns
    - Easy to test (mock dependencies)
    - Can enable/disable systems
    - Lua can call system methods
    """

    def __init__(self, context: 'GameContext'):
        self.context = context
        self.enabled = True

    def initialize(self):
        """Called when system is first created."""
        pass

    def shutdown(self):
        """Called when system is destroyed."""
        pass

    @abstractmethod
    def update(self, delta_time: float = 0):
        """
        Called each game tick (for systems that need ticking).

        Args:
            delta_time: Time since last update (0 for turn-based)
        """
        pass
```

### Example Systems

```python
# src/core/systems/combat_system.py
class CombatSystem(System):
    """Handles combat calculations."""

    def update(self, delta_time: float = 0):
        """Combat doesn't tick, it's action-driven."""
        pass

    def calculate_damage(self, attacker: Entity, defender: Entity) -> int:
        """Calculate damage before defense."""
        base_damage = attacker.attack

        # Lua hook: modify damage
        if self.context.lua_bridge:
            base_damage = self.context.lua_bridge.call_hook(
                attacker, "on_calculate_damage", base_damage, defender
            )

        return max(1, base_damage - defender.defense)

    def apply_damage(self, target: Entity, damage: int, source: Entity) -> int:
        """Apply damage to target, return actual damage."""
        # Lua hook: modify incoming damage
        if self.context.lua_bridge:
            damage = self.context.lua_bridge.call_hook(
                target, "on_before_damage", damage, source
            )

        actual = target.take_damage(damage)

        # Lua hook: react to damage
        if self.context.lua_bridge:
            self.context.lua_bridge.call_hook(
                target, "on_damaged", actual, source
            )

        # Publish event
        self.context.events.publish('entity_damaged', {
            'target_id': target.entity_id,
            'source_id': source.entity_id if source else None,
            'damage': actual,
        })

        if not target.is_alive:
            self.handle_death(target, source)

        return actual

    def handle_death(self, entity: Entity, killer: Optional[Entity]):
        """Handle entity death."""
        entity.is_alive = False

        # Lua hook: on death
        if self.context.lua_bridge:
            self.context.lua_bridge.call_hook(entity, "on_death", killer)

        # Publish event
        self.context.events.publish('entity_died', {
            'entity_id': entity.entity_id,
            'killer_id': killer.entity_id if killer else None,
        })

        # Drop loot (future)
        # self.loot_system.drop_loot(entity)


# src/core/systems/ai_system.py
class AISystem(System):
    """Runs monster AI."""

    def update(self, delta_time: float = 0):
        """Run AI for all monsters."""
        for entity in self.context.get_entities_by_type(EntityType.MONSTER):
            if not entity.is_alive:
                continue

            # Get AI component
            ai = entity.components.get('ai')
            if ai:
                ai.update(self.context)
            else:
                # Default AI
                self.simple_chase_ai(entity)

    def simple_chase_ai(self, monster: Entity):
        """Default chase behavior."""
        player = self.context.get_player()

        if monster.is_adjacent(player):
            # Attack
            action = AttackAction(monster.entity_id, player.entity_id)
            action.execute(self.context)
        else:
            # Move toward
            dx = 1 if player.x > monster.x else -1 if player.x < monster.x else 0
            dy = 1 if player.y > monster.y else -1 if player.y < monster.y else 0

            action = MoveAction(monster.entity_id, dx, dy)
            if action.validate(self.context):
                action.execute(self.context)


# src/core/systems/mining_system.py
class MiningSystem(System):
    """Handles ore mining logic."""

    def update(self, delta_time: float = 0):
        """Check for interrupted mining."""
        pass

    def start_mining(self, actor: Entity, ore_vein: Entity) -> ActionOutcome:
        """Start mining an ore vein."""
        if not actor.is_adjacent(ore_vein):
            return ActionOutcome.failure("Not adjacent to ore")

        action = MineAction(actor.entity_id, ore_vein.entity_id)
        return action.execute(self.context)

    def survey_ore(self, actor: Entity, ore_vein: Entity) -> dict:
        """Survey ore to see properties."""
        if not actor.is_adjacent(ore_vein):
            return {}

        properties = ore_vein.stats.copy()

        # Calculate mining time
        hardness = properties.get('hardness', 50)
        mining_turns = 3 + (hardness // 25)
        properties['mining_turns'] = mining_turns

        return properties
```

### System Manager

```python
# src/core/base/system_manager.py
class SystemManager:
    """Manages all game systems."""

    def __init__(self, context: GameContext):
        self.context = context
        self.systems: Dict[str, System] = {}

    def register(self, name: str, system: System):
        """Register a system."""
        self.systems[name] = system
        system.initialize()

    def get(self, name: str) -> Optional[System]:
        """Get a system by name."""
        return self.systems.get(name)

    def update_all(self, delta_time: float = 0):
        """Update all systems."""
        for system in self.systems.values():
            if system.enabled:
                system.update(delta_time)

    def shutdown_all(self):
        """Shutdown all systems."""
        for system in self.systems.values():
            system.shutdown()
```

### Benefits

✅ **Separation of Concerns**: Each system has one job
✅ **Testable**: Mock GameContext, test system in isolation
✅ **Pluggable**: Enable/disable systems via config
✅ **Lua API Surface**: Systems become Lua-callable methods
✅ **Multiplayer**: Systems work on authoritative server state

---

## 5. GameEvent Base Class 📋 Phase 2

**Phase:** Phase 2 (Multiplayer) - Skip for MVP
**Priority:** MEDIUM (Future)

### Purpose
Type-safe event bus messages for decoupled communication.

### Design

```python
# src/core/base/game_event.py
from dataclasses import dataclass
from typing import Any, Dict, Callable
from enum import Enum


class GameEventType(Enum):
    """All event types in the game."""
    # Entity events
    ENTITY_MOVED = "entity_moved"
    ENTITY_DAMAGED = "entity_damaged"
    ENTITY_HEALED = "entity_healed"
    ENTITY_DIED = "entity_died"
    ENTITY_SPAWNED = "entity_spawned"

    # Combat events
    ATTACK_HIT = "attack_hit"
    ATTACK_MISS = "attack_miss"
    CRITICAL_HIT = "critical_hit"

    # Mining events
    ORE_SURVEYED = "ore_surveyed"
    ORE_MINED = "ore_mined"
    MINING_INTERRUPTED = "mining_interrupted"

    # Crafting events
    ITEM_CRAFTED = "item_crafted"
    RECIPE_DISCOVERED = "recipe_discovered"

    # Inventory events
    ITEM_PICKED_UP = "item_picked_up"
    ITEM_DROPPED = "item_dropped"
    ITEM_USED = "item_used"
    ITEM_EQUIPPED = "item_equipped"

    # Game state events
    TURN_STARTED = "turn_started"
    TURN_ENDED = "turn_ended"
    FLOOR_CHANGED = "floor_changed"
    GAME_OVER = "game_over"


@dataclass
class GameEvent:
    """Base class for all game events."""
    event_type: GameEventType
    data: Dict[str, Any]

    def get(self, key: str, default: Any = None) -> Any:
        """Get event data field."""
        return self.data.get(key, default)


class EventBus:
    """
    Simple event bus for decoupled communication.

    Systems/Lua scripts subscribe to events, publishers don't know who's listening.
    """

    def __init__(self):
        self.subscribers: Dict[GameEventType, list[Callable]] = {}
        self.lua_subscribers: Dict[GameEventType, list[str]] = {}  # Lua script paths

    def subscribe(self, event_type: GameEventType, callback: Callable):
        """Subscribe to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def subscribe_lua(self, event_type: GameEventType, script_path: str):
        """Subscribe Lua script to event (Phase 3)."""
        if event_type not in self.lua_subscribers:
            self.lua_subscribers[event_type] = []
        self.lua_subscribers[event_type].append(script_path)

    def publish(self, event_type: GameEventType, data: Dict[str, Any]):
        """Publish an event to all subscribers."""
        event = GameEvent(event_type, data)

        # Python subscribers
        for callback in self.subscribers.get(event_type, []):
            try:
                callback(event)
            except Exception as e:
                # Log error but don't crash
                print(f"Error in event handler: {e}")

        # Lua subscribers (Phase 3)
        # for script_path in self.lua_subscribers.get(event_type, []):
        #     self.lua_bridge.call_event_handler(script_path, event)

    def unsubscribe(self, event_type: GameEventType, callback: Callable):
        """Unsubscribe from an event."""
        if event_type in self.subscribers:
            self.subscribers[event_type] = [
                cb for cb in self.subscribers[event_type] if cb != callback
            ]
```

### Example Usage

```python
# Publish events
event_bus.publish(GameEventType.ENTITY_DIED, {
    'entity_id': monster.entity_id,
    'killer_id': player.entity_id,
    'floor': 5,
})

# Subscribe (Python)
def on_monster_died(event: GameEvent):
    killer_id = event.get('killer_id')
    if killer_id == player.entity_id:
        player_stats.monsters_killed += 1
        print(f"Total kills: {player_stats.monsters_killed}")

event_bus.subscribe(GameEventType.ENTITY_DIED, on_monster_died)

# Subscribe (Lua - Phase 3)
# events/on_monster_died.lua
function on_event(event)
    -- Achievement tracking
    if event.killer_id == player.entity_id then
        player_data.kills = player_data.kills + 1

        if player_data.kills == 100 then
            unlock_achievement("centurion")
        end
    end
end

# Register Lua handler
event_bus.subscribe_lua(GameEventType.ENTITY_DIED, "events/on_monster_died.lua")
```

### Benefits

✅ **Decoupling**: Publishers don't know about subscribers
✅ **Extensibility**: Add achievement/quest systems without touching core
✅ **Lua Integration**: Lua scripts subscribe to events naturally
✅ **Debugging**: Log all events, understand game flow
✅ **Multiplayer**: Events broadcast to all clients

---

## 6. GameContext Class 📋 Phase 2

**Phase:** Phase 2 (Multiplayer) - Skip for MVP
**Priority:** MEDIUM (Future)

### Purpose
Safe, controlled access to game state for systems/Lua.

### Design

```python
# src/core/base/game_context.py
from typing import Optional, List, Dict
from .entity import Entity, EntityType
from .system import System
from .game_event import EventBus


class GameContext:
    """
    Facade for game state access.

    Provides controlled API surface:
    - Systems use this instead of accessing GameState directly
    - Lua scripts get this as their API
    - Easy to mock for testing
    - Can add permission checks (multiplayer)
    """

    def __init__(self, game_state: 'GameState'):
        self.game_state = game_state
        self.events = EventBus()
        self.systems: Dict[str, System] = {}
        self.lua_bridge = None  # Set in Phase 3

    # Entity queries
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self.game_state.entities.get(entity_id)

    def get_player(self) -> Entity:
        """Get the player entity."""
        return self.game_state.player

    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Get all entities of a type."""
        return [e for e in self.game_state.entities.values()
                if e.entity_type == entity_type]

    def get_entity_at(self, x: int, y: int) -> Optional[Entity]:
        """Get entity at position."""
        for entity in self.game_state.entities.values():
            if entity.x == x and entity.y == y:
                return entity
        return None

    def get_entities_in_range(self, x: int, y: int, radius: int) -> List[Entity]:
        """Get entities within radius of position."""
        entities = []
        for entity in self.game_state.entities.values():
            if entity.x is None:
                continue
            dx = entity.x - x
            dy = entity.y - y
            if (dx * dx + dy * dy) ** 0.5 <= radius:
                entities.append(entity)
        return entities

    # Entity manipulation
    def add_entity(self, entity: Entity):
        """Add entity to game."""
        self.game_state.entities[entity.entity_id] = entity
        self.events.publish(GameEventType.ENTITY_SPAWNED, {
            'entity_id': entity.entity_id,
        })

    def remove_entity(self, entity_id: str):
        """Remove entity from game."""
        if entity_id in self.game_state.entities:
            del self.game_state.entities[entity_id]

    # Map queries
    def is_walkable(self, x: int, y: int) -> bool:
        """Check if position is walkable."""
        return self.game_state.map.is_walkable(x, y)

    def in_bounds(self, x: int, y: int) -> bool:
        """Check if position is in map bounds."""
        return (0 <= x < self.game_state.map.width and
                0 <= y < self.game_state.map.height)

    # System access
    def get_system(self, name: str) -> Optional[System]:
        """Get a system by name."""
        return self.systems.get(name)

    # Message log
    def add_message(self, message: str):
        """Add message to game log."""
        self.game_state.messages.add(message)

    # Game state
    def get_turn_count(self) -> int:
        """Get current turn number."""
        return self.game_state.turn_count

    def get_floor(self) -> int:
        """Get current floor number."""
        return self.game_state.current_floor
```

### How It's Used

```python
# Systems receive context
class CombatSystem(System):
    def __init__(self, context: GameContext):
        super().__init__(context)

    def attack(self, attacker_id: str, target_id: str):
        attacker = self.context.get_entity(attacker_id)
        target = self.context.get_entity(target_id)
        # ... combat logic

# Actions receive context
class MoveAction(Action):
    def execute(self, context: GameContext) -> ActionOutcome:
        actor = context.get_entity(self.actor_id)
        if not context.is_walkable(actor.x + self.dx, actor.y + self.dy):
            return ActionOutcome.failure("Blocked")
        # ... movement logic

# Lua scripts get context
# monsters/goblin.lua
function take_turn(monster_id, context)
    local monster = context:get_entity(monster_id)
    local player = context:get_player()

    local distance = monster:distance_to(player)
    if distance <= 1 then
        -- Attack
        context:get_system("combat"):attack(monster_id, player.entity_id)
    else
        -- Move toward player
        local dx, dy = get_direction(monster, player)
        context:get_system("movement"):move(monster_id, dx, dy)
    end
end
```

### Benefits

✅ **Safe API**: Controlled access, no direct state manipulation
✅ **Testable**: Mock GameContext for unit tests
✅ **Lua Surface**: Context becomes Lua API automatically
✅ **Permissions**: Can add checks (multiplayer: "can this player do this?")
✅ **Refactor-Friendly**: Change internals, keep API stable

---

## 7. Serializable Mixin (Optional) 📋 Phase 2

**Phase:** Phase 2 (Multiplayer) - Skip for MVP
**Priority:** LOW (Optional)

### Purpose
Reusable serialization for save/load, multiplayer, Lua data.

### Design

```python
# src/core/base/serializable.py
from abc import ABC, abstractmethod
from typing import Any, Dict
import json


class Serializable(ABC):
    """
    Mixin for classes that need serialization.

    Used for:
    - Save/load game state
    - Multiplayer state sync
    - Lua data passing
    """

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Serializable':
        """Deserialize from dictionary."""
        pass

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'Serializable':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
```

### Usage

```python
# Entity already implements Serializable
class Entity(Serializable):
    def to_dict(self) -> dict:
        return {...}

    @classmethod
    def from_dict(cls, data: dict) -> Entity:
        return Entity(...)

# Save game
game_data = {
    'player': game.player.to_dict(),
    'monsters': [m.to_dict() for m in game.monsters],
    'map': game.map.to_dict(),
    'turn': game.turn_count,
}

with open('save.json', 'w') as f:
    json.dump(game_data, f)

# Load game
with open('save.json', 'r') as f:
    data = json.load(f)

player = Entity.from_dict(data['player'])
monsters = [Entity.from_dict(m) for m in data['monsters']]
```

---

## 8. ContentData Base Class ✅ MVP

**Phase:** MVP (Implement Now)
**Priority:** HIGH

### Purpose
Base for YAML-loaded content definitions.

### Design

```python
# src/core/base/content_data.py
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ContentData:
    """
    Base class for YAML-loaded content.

    All content has:
    - Unique ID
    - Display name
    - Version (for schema evolution)
    - Optional Lua script
    """

    id: str
    name: str
    version: str = "1.0"
    lua_script: Optional[str] = None

    @classmethod
    def from_yaml(cls, data: dict) -> 'ContentData':
        """Load from YAML data."""
        return cls(**data)


# Concrete content types
@dataclass
class MonsterData(ContentData):
    """Monster definition from YAML."""
    stats: Dict[str, int]
    loot_table: list
    ai_script: Optional[str] = None

    def spawn(self, x: int, y: int) -> Entity:
        """Create entity from this data."""
        return Monster(
            content_id=self.id,
            x=x,
            y=y,
            monster_data=self,
        )


@dataclass
class ItemData(ContentData):
    """Item definition from YAML."""
    item_type: str
    stats: Dict[str, Any]
    behavior_script: Optional[str] = None

    def create_item(self) -> Entity:
        """Create entity from this data."""
        return Entity(
            entity_type=EntityType.ITEM,
            content_id=self.id,
            name=self.name,
            stats=self.stats.copy(),
        )


@dataclass
class RecipeData(ContentData):
    """Recipe definition from YAML."""
    required_ore: int
    ore_types: list[str]
    base_stats: Dict[str, int]
    crafting_formula: Optional[str] = None  # Python expression or Lua script
```

### Content Loading

```python
# src/core/content/content_loader.py
import yaml
from pathlib import Path


class ContentLoader:
    """Loads content from YAML files."""

    def __init__(self, content_dir: Path):
        self.content_dir = content_dir
        self.monsters: Dict[str, MonsterData] = {}
        self.items: Dict[str, ItemData] = {}
        self.recipes: Dict[str, RecipeData] = {}

    def load_all(self):
        """Load all content from YAML."""
        self.load_monsters()
        self.load_items()
        self.load_recipes()

    def load_monsters(self):
        """Load monster definitions."""
        monsters_dir = self.content_dir / "monsters"
        for yaml_file in monsters_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
                monster = MonsterData.from_yaml(data)
                self.monsters[monster.id] = monster

    def get_monster(self, monster_id: str) -> Optional[MonsterData]:
        """Get monster data by ID."""
        return self.monsters.get(monster_id)

    def spawn_monster(self, monster_id: str, x: int, y: int) -> Entity:
        """Spawn a monster from content."""
        monster_data = self.get_monster(monster_id)
        if not monster_data:
            raise ValueError(f"Unknown monster: {monster_id}")
        return monster_data.spawn(x, y)
```

---

## Implementation Roadmap

### Phase 1 (MVP - Next 6 Weeks)

**Week 1-2: Entity + Action Foundation**
- ✅ Create Entity base class
- ✅ Refactor Player, Monster to inherit from Entity
- ✅ Create Action base class
- ✅ Implement MoveAction, AttackAction
- ✅ Refactor game loop to use actions

**Week 3: System Architecture**
- ✅ Create System base class
- ✅ Implement CombatSystem
- ✅ Implement AISystem
- ✅ Create SystemManager

**Week 4: Events + Context**
- ✅ Create EventBus
- ✅ Create GameContext
- ✅ Refactor systems to use context
- ✅ Add event publishing to actions

**Week 5-6: Content System**
- ✅ Create ContentData base classes
- ✅ Build ContentLoader
- ✅ Create YAML schemas for monsters, items
- ✅ Migrate hardcoded content → YAML

**Result**: Clean architecture, no Lua yet, multiplayer-ready

---

### Phase 2 (Multiplayer - Weeks 7-18)

**Week 7-8: Action Serialization**
- ✅ Test action to_dict()/from_dict()
- ✅ Actions → JSON → Actions roundtrip

**Week 9-10: NATS Integration**
- ✅ Client sends actions as NATS messages
- ✅ Server receives, validates, executes
- ✅ Server broadcasts events to clients

**Week 11-12: State Sync**
- ✅ Full state sync (initial connection)
- ✅ Delta state sync (events)
- ✅ Client reconciliation

**Result**: Multiplayer working, still no Lua

---

### Phase 3 (Lua Scripting - Weeks 19-24)

**Week 19: Lua Bridge**
- Install lupa
- Create LuaBridge class
- Expose GameContext to Lua

**Week 20: Lua Content**
- Add behavior_script fields to YAML
- Load Lua scripts
- Call Lua from Python

**Week 21: Lua Integration**
- Lua AI scripts
- Lua item effects
- Lua event handlers

**Week 22-24: Polish**
- Lua API documentation
- Example scripts
- Community content support

**Result**: Full Lua modding support

---

## File Structure

```
src/
├── core/
│   ├── base/
│   │   ├── __init__.py
│   │   ├── entity.py           # Entity base class
│   │   ├── component.py        # Component base class
│   │   ├── action.py           # Action base class
│   │   ├── system.py           # System base class
│   │   ├── game_event.py       # GameEvent, EventBus
│   │   ├── game_context.py     # GameContext
│   │   ├── serializable.py     # Serializable mixin
│   │   └── content_data.py     # ContentData base
│   │
│   ├── actions/
│   │   ├── __init__.py
│   │   ├── move_action.py
│   │   ├── attack_action.py
│   │   ├── mine_action.py
│   │   └── use_item_action.py
│   │
│   ├── systems/
│   │   ├── __init__.py
│   │   ├── combat_system.py
│   │   ├── ai_system.py
│   │   ├── mining_system.py
│   │   ├── crafting_system.py
│   │   └── movement_system.py
│   │
│   ├── content/
│   │   ├── __init__.py
│   │   ├── content_loader.py
│   │   ├── monster_data.py
│   │   ├── item_data.py
│   │   └── recipe_data.py
│   │
│   ├── entities.py      # Player, Monster (inherit Entity)
│   ├── game.py          # Game, GameState
│   └── world.py         # Map, Tile, Room
│
data/
├── monsters/
│   ├── goblin.yaml
│   └── orc.yaml
├── items/
│   ├── health_potion.yaml
│   └── sword.yaml
└── recipes/
    └── longsword.yaml
```

---

## Summary Checklist

When implementing, use this checklist:

### Entity System
- [ ] Create Entity base class with UUID, type, stats
- [ ] Refactor Player to inherit from Entity
- [ ] Refactor Monster to inherit from Entity
- [ ] Implement to_dict()/from_dict() for serialization
- [ ] Add Component placeholder (use in Phase 2)

### Action System
- [ ] Create Action base class
- [ ] Implement MoveAction with validate()/execute()
- [ ] Implement AttackAction
- [ ] Refactor game loop to use actions
- [ ] Test action serialization (to_dict/from_dict)

### System Architecture
- [ ] Create System base class
- [ ] Create SystemManager
- [ ] Implement CombatSystem
- [ ] Implement AISystem
- [ ] Move game logic into systems

### Event System
- [ ] Create GameEvent and EventBus
- [ ] Add event publishing to actions
- [ ] Create example event subscriber (statistics)
- [ ] Test event flow end-to-end

### GameContext
- [ ] Create GameContext class
- [ ] Refactor systems to use context
- [ ] Remove direct GameState access
- [ ] Document context API (future Lua surface)

### Content System
- [ ] Create ContentData base classes
- [ ] Build ContentLoader
- [ ] Define YAML schemas
- [ ] Migrate hardcoded data → YAML
- [ ] Add version field to all content

---

## Benefits Summary

| Base Class | Immediate Benefit | Lua Benefit | Multiplayer Benefit |
|------------|-------------------|-------------|---------------------|
| **Entity** | Code reuse, clean inheritance | Uniform Lua API | Easy serialization |
| **Component** | N/A (Phase 2) | Lua adds components | Flexible entity sync |
| **Action** | Testable, replayable | Lua returns actions | Direct NATS mapping |
| **System** | Separated concerns | Lua calls systems | Server-authoritative |
| **GameEvent** | Decoupled logic | Lua event hooks | Event broadcast |
| **GameContext** | Safe API | Lua API surface | Permission checks |
| **Serializable** | Save/load | Lua data passing | State sync |
| **ContentData** | Data-driven | Lua script paths | Content sync |

---

**Next Step**: Start with Entity + Action base classes during Week 1-2 (Mining System implementation)!

🏗️ **Build the foundation, then build the features.**
