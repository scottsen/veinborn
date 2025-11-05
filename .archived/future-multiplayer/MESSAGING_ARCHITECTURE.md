# Brogue Messaging Architecture

**Document Type:** Technical Specification
**Audience:** Backend Developers, System Architects
**Status:** Active
**Last Updated:** 2025-10-23

---

## Overview

This document defines Brogue's messaging infrastructure - the nervous system connecting all services.

**Core Principles:**
1. **Type-safe messages** - Pydantic models, not raw dicts
2. **Consistent subjects** - Naming convention enforced
3. **Message registry** - Auto-parsing, no manual if/elif chains
4. **MessageBus abstraction** - Hide NATS complexity

---

## Message Architecture Layers

```
┌─────────────────────────────────────────────┐
│  Application Layer (Game Logic)             │
│  - GameInstance, CombatSystem, etc.         │
└─────────────────────────────────────────────┘
              ↓ (uses)
┌─────────────────────────────────────────────┐
│  MessageBus Abstraction                     │
│  - publish_action(), subscribe_actions()    │
│  - High-level API, typed methods            │
└─────────────────────────────────────────────┘
              ↓ (wraps)
┌─────────────────────────────────────────────┐
│  Message Models (Pydantic)                  │
│  - MoveAction, FullStateUpdate, etc.        │
│  - to_nats(), from_nats() serialization     │
└─────────────────────────────────────────────┘
              ↓ (serializes to)
┌─────────────────────────────────────────────┐
│  NATS Transport                             │
│  - Pub/Sub, JetStream, Request/Reply        │
│  - Network, clustering, persistence         │
└─────────────────────────────────────────────┘
```

---

## 1. Message Types (Pydantic Models)

### Base Message Class

All messages inherit from `BrogueMessage`:

```python
# brogue/messages/base.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import ClassVar
import uuid

class BrogueMessage(BaseModel):
    """Base class for all Brogue messages"""

    # Auto-generated fields
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=lambda: datetime.utcnow().timestamp())
    version: str = "1.0"

    # Subclasses MUST override
    MESSAGE_TYPE: ClassVar[str] = "base"

    class Config:
        use_enum_values = True  # Serialize enums as strings
        extra = "ignore"        # Forward compatibility

    def to_nats(self) -> bytes:
        """Serialize to NATS message"""
        return self.model_dump_json().encode()

    @classmethod
    def from_nats(cls, data: bytes):
        """Deserialize from NATS message"""
        import json
        return cls(**json.loads(data))
```

### Message Categories

#### Category 1: Player Actions (Commands)

Client → Server, ephemeral (fire-and-forget)

```python
# brogue/messages/actions.py
from enum import Enum
from .base import BrogueMessage

class Direction(str, Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"

class MoveAction(BrogueMessage):
    MESSAGE_TYPE: ClassVar[str] = "move"

    player_id: str
    direction: Direction

class AttackAction(BrogueMessage):
    MESSAGE_TYPE: ClassVar[str] = "attack"

    player_id: str
    target_id: str

class MineAction(BrogueMessage):
    MESSAGE_TYPE: ClassVar[str] = "mine"

    player_id: str
    target_pos: tuple[int, int]
    turns_remaining: int = 5
```

**NATS Subject:** `game.instance.{instance_id}.actions`

#### Category 2: State Updates (Events)

Server → Clients, ephemeral (sent frequently)

```python
# brogue/messages/events.py
from typing import List, Dict, Any
from .base import BrogueMessage

class Position(BaseModel):
    x: int
    y: int

class PlayerState(BaseModel):
    id: str
    class_name: str
    pos: Position
    hp: int
    max_hp: int
    mana: int = 0
    inventory: List[Dict[str, Any]] = []

class FullStateUpdate(BrogueMessage):
    """Complete game state snapshot"""
    MESSAGE_TYPE: ClassVar[str] = "full_state"

    tick: int
    floor: int
    map_tiles: List[List[str]]
    players: List[PlayerState]
    monsters: List[MonsterState]
    messages: List[str] = []

class DeltaUpdate(BrogueMessage):
    """Only changes since last tick"""
    MESSAGE_TYPE: ClassVar[str] = "delta"

    tick: int
    base_tick: int
    changed_players: List[PlayerState] = []
    moved_entities: Dict[str, Position] = {}
    removed_entities: List[str] = []
```

**NATS Subject:** `game.party.{party_id}.updates`

**Optimization Strategy:**
- Full state every 10 ticks (resync)
- Delta updates between (efficiency)
- Bandwidth savings: ~96% (3MB/min → 120KB/min)

#### Category 3: Critical Events (Reliable)

Server → Services, persisted (JetStream)

```python
# brogue/messages/critical.py
from .base import BrogueMessage

class LegacyOreCollected(BrogueMessage):
    """MUST NOT LOSE - player's rare ore!"""
    MESSAGE_TYPE: ClassVar[str] = "legacy_ore_collected"

    player_id: str
    ore: Dict[str, Any]
    dungeon_floor: int

class PlayerDied(BrogueMessage):
    MESSAGE_TYPE: ClassVar[str] = "player_died"

    player_id: str
    killed_by: str
    carried_ore: List[Dict] = []
```

**NATS Subject:** `events.critical.{event_type}`
**Delivery:** At-least-once (JetStream)

---

## 2. NATS Subject Naming Convention

### Pattern

```
{domain}.{entity_type}.{entity_id}.{action}
```

### Subject Definitions

**All subjects as constants - NO MAGIC STRINGS:**

```python
# brogue/messaging/subjects.py
class Subjects:
    """Type-safe subject builder"""

    # Player Actions
    @staticmethod
    def game_instance_actions(instance_id: str) -> str:
        return f"game.instance.{instance_id}.actions"

    # State Updates
    @staticmethod
    def game_party_updates(party_id: str) -> str:
        return f"game.party.{party_id}.updates"

    # Chat
    @staticmethod
    def chat_party(party_id: str) -> str:
        return f"chat.party.{party_id}"

    CHAT_GLOBAL = "chat.global"

    # Critical Events
    @staticmethod
    def critical_event(event_type: str) -> str:
        return f"events.critical.{event_type}"

    CRITICAL_ALL = "events.critical.>"  # Wildcard subscription

    # Service RPC
    @staticmethod
    def service_query(service: str, method: str) -> str:
        return f"service.{service}.{method}"

    # Work Queues
    JOBS_SAVE_DUNGEON = "jobs.save_dungeon"
    JOBS_GENERATE_MAP = "jobs.generate_map"
```

### Subject Examples

```
game.instance.42.actions              # Actions to instance 42
game.party.dragon_slayers.updates     # State updates for party
chat.global                           # Global chat
chat.party.dragon_slayers             # Party chat
events.critical.legacy_ore_collected  # Critical event (JetStream)
jobs.save_dungeon                     # Background job queue
service.player.get_state              # RPC query
```

### Wildcard Subscriptions

```python
# Subscribe to all party updates
await nc.subscribe("game.party.*.updates", cb=handler)

# Subscribe to all critical events
await nc.subscribe("events.critical.>", cb=handler)

# Subscribe to all game-related messages
await nc.subscribe("game.>", cb=handler)
```

---

## 3. Message Registry (Type-Safe Parsing)

**Problem:** How to parse incoming NATS messages into typed objects?

**Solution:** Registry pattern + auto-registration

```python
# brogue/messaging/registry.py
import json
from typing import Type, Dict
from brogue.messages.base import BrogueMessage

class MessageRegistry:
    """Auto-parse messages based on MESSAGE_TYPE field"""

    _registry: Dict[str, Type[BrogueMessage]] = {}

    @classmethod
    def register(cls, message_class: Type[BrogueMessage]):
        """Decorator: auto-register message class"""
        msg_type = message_class.MESSAGE_TYPE

        if msg_type in cls._registry:
            raise ValueError(f"Duplicate message type: {msg_type}")

        cls._registry[msg_type] = message_class
        return message_class

    @classmethod
    def parse(cls, data: bytes) -> BrogueMessage:
        """
        Parse NATS message → typed BrogueMessage instance.

        Raises:
            ValueError: Unknown message type
            ValidationError: Invalid data (Pydantic)
        """
        raw = json.loads(data)
        msg_type = raw.get("type")

        if msg_type not in cls._registry:
            raise ValueError(f"Unknown message type: {msg_type}")

        message_class = cls._registry[msg_type]
        return message_class(**raw)
```

### Registration

```python
# Auto-register all message types
from brogue.messages.actions import MoveAction, AttackAction, MineAction
from brogue.messages.events import FullStateUpdate, DeltaUpdate
from brogue.messages.critical import LegacyOreCollected, PlayerDied

MessageRegistry.register(MoveAction)
MessageRegistry.register(AttackAction)
MessageRegistry.register(MineAction)
MessageRegistry.register(FullStateUpdate)
MessageRegistry.register(DeltaUpdate)
MessageRegistry.register(LegacyOreCollected)
MessageRegistry.register(PlayerDied)
```

### Usage

```python
# Incoming NATS message
data = b'{"type": "move", "player_id": "alice", "direction": "north"}'

# Auto-parse to correct type!
message = MessageRegistry.parse(data)
# → Returns MoveAction instance (typed!)

# Type-safe handling
if isinstance(message, MoveAction):
    # IDE knows: message.player_id, message.direction
    process_move(message)
elif isinstance(message, AttackAction):
    process_attack(message)
```

---

## 4. MessageBus Abstraction

**Goal:** Hide NATS complexity, provide clean API

```python
# brogue/messaging/bus.py
import json
from typing import Callable, Any
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext

from .subjects import Subjects
from .registry import MessageRegistry
from ..messages.base import BrogueMessage

class MessageBus:
    """High-level messaging abstraction over NATS"""

    def __init__(self, nats_client: NATS):
        self.nc = nats_client
        self.js: JetStreamContext = nats_client.jetstream()

    # ===== Publishing =====

    async def publish_action(self, instance_id: str, action: BrogueMessage):
        """Publish player action to game instance"""
        subject = Subjects.game_instance_actions(instance_id)
        await self.nc.publish(subject, action.to_nats())

    async def publish_state(self, party_id: str, state: BrogueMessage):
        """Publish state update to party members"""
        subject = Subjects.game_party_updates(party_id)
        await self.nc.publish(subject, state.to_nats())

    async def publish_critical(self, event: BrogueMessage):
        """Publish critical event (JetStream - reliable)"""
        subject = Subjects.critical_event(event.MESSAGE_TYPE)
        ack = await self.js.publish(subject, event.to_nats())
        return ack  # Proof of persistence (sequence number)

    # ===== Subscribing =====

    async def subscribe_actions(
        self,
        instance_id: str,
        handler: Callable[[BrogueMessage], Any]
    ):
        """Subscribe to player actions - auto-parsed!"""
        subject = Subjects.game_instance_actions(instance_id)

        async def wrapper(msg):
            try:
                # Auto-parse using registry
                action = MessageRegistry.parse(msg.data)
                await handler(action)
            except Exception as e:
                logger.error("Failed to handle action", error=str(e))

        await self.nc.subscribe(subject, cb=wrapper)

    async def subscribe_party_updates(
        self,
        party_id: str,
        handler: Callable[[BrogueMessage], Any]
    ):
        """Subscribe to game state updates"""
        subject = Subjects.game_party_updates(party_id)

        async def wrapper(msg):
            state = MessageRegistry.parse(msg.data)
            await handler(state)

        await self.nc.subscribe(subject, cb=wrapper)

    async def subscribe_critical_events(
        self,
        handler: Callable[[BrogueMessage], Any],
        durable_name: str = "critical_persister"
    ):
        """Subscribe to critical events (durable - survives restarts)"""
        consumer = await self.js.subscribe(
            Subjects.CRITICAL_ALL,
            durable=durable_name
        )
        return consumer  # Async iterator

    # ===== Request/Reply (RPC) =====

    async def request(
        self,
        service: str,
        method: str,
        query: BrogueMessage,
        timeout: float = 2.0
    ) -> Dict:
        """RPC-style service query"""
        subject = Subjects.service_query(service, method)
        response = await self.nc.request(subject, query.to_nats(), timeout=timeout)
        return json.loads(response.data)

    # ===== Lifecycle =====

    async def drain(self):
        """Graceful shutdown"""
        await self.nc.drain()
```

---

## 5. Usage Examples

### Game Instance (Server)

```python
from brogue.messaging.bus import MessageBus
from brogue.messages.actions import MoveAction, AttackAction
from brogue.messages.events import FullStateUpdate

class GameInstanceService:
    def __init__(self, bus: MessageBus, instance_id: str):
        self.bus = bus
        self.instance_id = instance_id

    async def start(self):
        """Subscribe to player actions"""
        await self.bus.subscribe_actions(
            self.instance_id,
            self.handle_action
        )

    async def handle_action(self, action: BrogueMessage):
        """Type-safe action handler"""
        if isinstance(action, MoveAction):
            await self.handle_move(action)
        elif isinstance(action, AttackAction):
            await self.handle_attack(action)

    async def handle_move(self, action: MoveAction):
        """Process move - validate and update"""
        if not self.is_valid_move(action.player_id, action.direction):
            return  # Invalid, ignore

        self.move_player(action.player_id, action.direction)
        await self.broadcast_state()

    async def broadcast_state(self):
        """Send state update to clients"""
        update = FullStateUpdate(
            tick=self.tick,
            floor=self.floor,
            map_tiles=self.map.tiles,
            players=self.get_players(),
            monsters=self.get_monsters()
        )

        await self.bus.publish_state(self.party_id, update)
```

### Game Client

```python
from brogue.messaging.bus import MessageBus
from brogue.messages.actions import MoveAction
from brogue.messages.events import FullStateUpdate, DeltaUpdate

class GameClient:
    def __init__(self, bus: MessageBus, party_id: str, player_id: str):
        self.bus = bus
        self.party_id = party_id
        self.player_id = player_id
        self.state = None

    async def start(self):
        """Subscribe to state updates"""
        await self.bus.subscribe_party_updates(
            self.party_id,
            self.handle_state_update
        )

    async def handle_state_update(self, update: BrogueMessage):
        """Receive and render state"""
        if isinstance(update, FullStateUpdate):
            self.state = update
        elif isinstance(update, DeltaUpdate):
            self.apply_delta(update)

        self.ui.render(self.state)

    async def send_move(self, direction: Direction):
        """Send move action"""
        action = MoveAction(
            player_id=self.player_id,
            direction=direction
        )
        await self.bus.publish_action(self.instance_id, action)
```

---

## 6. Performance Characteristics

### State Update Bandwidth

**Full State:**
- Size: ~50 KB (80x24 map + entities)
- Frequency: Every 10 ticks (1 Hz)
- Bandwidth: 50 KB/s = 3 MB/min per player

**Delta Updates:**
- Size: ~2 KB (only changes)
- Frequency: 9/10 ticks (9 Hz)
- Bandwidth: 18 KB/s = 1.08 MB/min per player

**Combined (Hybrid):**
- Bandwidth: ~1.2 MB/min per player
- **Savings: 60% vs full-state-only**

### Message Latency (Target)

| Message Type | Target Latency | Acceptable Max |
|--------------|---------------|----------------|
| Player Action → Server | <10ms | 50ms |
| Server → Client Update | <10ms | 50ms |
| Critical Event → DB | <100ms | 500ms |
| Service RPC | <5ms | 20ms |

---

## 7. Error Handling

### Invalid Messages

```python
# MessageRegistry validates structure
try:
    message = MessageRegistry.parse(data)
except ValueError as e:
    logger.error("Unknown message type", error=str(e))
    return  # Ignore unknown messages
except ValidationError as e:
    logger.error("Invalid message data", error=str(e))
    return  # Ignore malformed messages
```

### NATS Connection Loss

```python
# NATS auto-reconnects
async def disconnected_cb():
    logger.warning("NATS disconnected - will retry")

async def reconnected_cb():
    logger.info("NATS reconnected")

nc = await NATS().connect(
    servers=["nats://server1:4222", "nats://server2:4222"],
    max_reconnect_attempts=10,
    disconnected_cb=disconnected_cb,
    reconnected_cb=reconnected_cb
)
```

### Message Processing Errors

```python
# Don't let one bad message crash the service
async def safe_handler(msg):
    try:
        action = MessageRegistry.parse(msg.data)
        await process(action)
    except Exception as e:
        logger.error(
            "Message processing failed",
            subject=msg.subject,
            error=str(e),
            exc_info=True
        )
        # Continue processing other messages
```

---

## 8. Testing

### Unit Tests

```python
import pytest
from brogue.messages.actions import MoveAction, Direction
from brogue.messaging.registry import MessageRegistry

def test_message_serialization():
    """Test Pydantic model serialization"""
    action = MoveAction(player_id="alice", direction=Direction.NORTH)

    # Serialize
    data = action.to_nats()
    assert isinstance(data, bytes)

    # Deserialize
    parsed = MoveAction.from_nats(data)
    assert parsed.player_id == "alice"
    assert parsed.direction == Direction.NORTH

def test_message_registry():
    """Test auto-parsing"""
    MessageRegistry.register(MoveAction)

    data = b'{"type": "move", "player_id": "alice", "direction": "north"}'
    message = MessageRegistry.parse(data)

    assert isinstance(message, MoveAction)
    assert message.player_id == "alice"
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_message_bus_publish_subscribe(nats_server):
    """Test pub/sub flow"""
    nc = await NATS().connect(nats_server.url)
    bus = MessageBus(nc)

    received = []

    async def handler(action):
        received.append(action)

    # Subscribe
    await bus.subscribe_actions("test_instance", handler)

    # Publish
    action = MoveAction(player_id="alice", direction=Direction.NORTH)
    await bus.publish_action("test_instance", action)

    # Wait for delivery
    await asyncio.sleep(0.1)

    # Assert
    assert len(received) == 1
    assert received[0].player_id == "alice"
```

---

## 9. Migration Path

### Phase 1: Core Messages (MVP)
- Player actions (move, attack, mine)
- State updates (full + delta)
- Chat messages

### Phase 2: Advanced Messages
- Critical events (JetStream)
- Service RPC
- Work queues

### Phase 3: Optimization
- Compression (zstd)
- Batching (multiple messages in one packet)
- Protocol buffers (if JSON overhead too high)

---

## References

- [NATS Documentation](https://docs.nats.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- `BROGUE_MESSAGE_TAXONOMY.md` - Complete message reference
- `BROGUE_NATS_INFRASTRUCTURE.md` - NATS setup guide
- `DEVELOPMENT_GUIDELINES.md` - Coding standards

---

**Next Steps:**
1. Implement base message classes (`brogue/messages/base.py`)
2. Define all message types (`brogue/messages/{actions,events,critical}.py`)
3. Implement MessageRegistry (`brogue/messaging/registry.py`)
4. Implement MessageBus (`brogue/messaging/bus.py`)
5. Write tests (`tests/test_messaging.py`)
