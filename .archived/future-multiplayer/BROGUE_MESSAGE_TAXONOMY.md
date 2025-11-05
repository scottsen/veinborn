# Brogue: Message Taxonomy & Abstractions

**Date:** 2025-10-22
**Session:** iridescent-shade-1022
**Focus:** Classify all Brogue messages, define clean abstractions

---

## 🎯 Philosophy

**Messages are the lifeblood of a distributed system.**

Good message design means:
- ✅ Clear categories (know what type of message you're dealing with)
- ✅ Consistent patterns (predictable behavior)
- ✅ Type safety (Pydantic models, not raw dicts)
- ✅ Versioning (messages evolve, clients don't break)
- ✅ Observability (can trace message flow)

**Bad message design means:**
- ❌ "Magic strings" (`msg["type"] == "player_moved"`)
- ❌ Unclear delivery semantics (was it received?)
- ❌ Mixed concerns (game logic + chat in same message)
- ❌ No validation (malformed messages crash services)

---

## 📊 Message Classification Framework

### Axis 1: Reliability

| Type | Delivery | Example | Transport |
|------|----------|---------|-----------|
| **Ephemeral** | Fire-and-forget, OK to lose | Player position update | NATS Core |
| **Reliable** | At-least-once delivery | Legacy Ore pickup | NATS JetStream |
| **Transactional** | Exactly-once, ACID | Ore trade between players | Database transaction |

### Axis 2: Direction

| Type | Flow | Example |
|------|------|---------|
| **Command** | Client → Server | "Move north" |
| **Event** | Server → Client(s) | "Player moved to (10,5)" |
| **Query** | Request → Response | "Get player inventory" |

### Axis 3: Audience

| Type | Recipients | Example | NATS Pattern |
|------|-----------|---------|--------------|
| **Unicast** | 1 specific client | Whisper message | Direct subject |
| **Multicast** | Party members | Party chat | Party subject |
| **Broadcast** | All connected clients | Global announcement | Global subject |

---

## 🗂️ Brogue Message Categories

### Category 1: Player Actions (Commands)

**Definition:** Player intent sent to game instance

**Characteristics:**
- **Direction:** Client → Server
- **Reliability:** Best-effort (if lost, player presses key again)
- **Validation:** Server MUST validate
- **Response:** Server sends state update (async)

**NATS Subject:** `game.instance.{instance_id}.actions`

**Examples:**

```python
from pydantic import BaseModel
from enum import Enum

class ActionType(str, Enum):
    MOVE = "move"
    ATTACK = "attack"
    MINE = "mine"
    SURVEY = "survey"
    USE_ABILITY = "use_ability"
    PICKUP = "pickup"
    DROP = "drop"
    CRAFT = "craft"

class Direction(str, Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"

class MoveAction(BaseModel):
    type: ActionType = ActionType.MOVE
    player_id: str
    direction: Direction

class AttackAction(BaseModel):
    type: ActionType = ActionType.ATTACK
    player_id: str
    target_id: str  # Monster or player ID

class MineAction(BaseModel):
    type: ActionType = ActionType.MINE
    player_id: str
    target_pos: tuple[int, int]
    turns_remaining: int = 5  # Mining takes multiple turns

class UseAbilityAction(BaseModel):
    type: ActionType = ActionType.USE_ABILITY
    player_id: str
    ability_name: str  # "heal", "taunt", "stealth"
    target_id: str | None = None
```

**Publishing (client):**
```python
action = MoveAction(player_id="alice", direction=Direction.NORTH)
await nc.publish(
    f"game.instance.{instance_id}.actions",
    action.model_dump_json().encode()
)
```

**Consuming (server):**
```python
async def handle_action(msg):
    # Parse and validate
    data = json.loads(msg.data)
    action_type = data["type"]

    if action_type == ActionType.MOVE:
        action = MoveAction(**data)
    elif action_type == ActionType.ATTACK:
        action = AttackAction(**data)
    # ... etc

    # Validate
    if not game_state.is_valid_action(action):
        return  # Ignore invalid action

    # Process
    game_state.process(action)
```

---

### Category 2: State Updates (Events)

**Definition:** Server tells clients what happened

**Characteristics:**
- **Direction:** Server → Clients
- **Reliability:** Best-effort (next update in 100ms anyway)
- **Frequency:** 10-60 per second
- **Size:** Can be large (full state) or small (delta)

**NATS Subject:** `game.party.{party_id}.updates`

**Message types:**

```python
class StateUpdateType(str, Enum):
    FULL_STATE = "full_state"      # Complete snapshot
    DELTA = "delta"                # Only changes
    CRITICAL_EVENT = "critical"    # Player death, boss spawn

class Position(BaseModel):
    x: int
    y: int

class PlayerState(BaseModel):
    id: str
    class_name: str  # warrior, mage, ranger, healer
    pos: Position
    hp: int
    max_hp: int
    mana: int
    max_mana: int
    status_effects: list[str] = []
    inventory: list[dict] = []

class MonsterState(BaseModel):
    id: str
    type: str  # goblin, dragon, etc
    pos: Position
    hp: int
    max_hp: int

class OreState(BaseModel):
    id: str
    pos: Position
    ore_type: str  # iron, mithril, etc
    properties: dict  # {hardness: 78, conductivity: 23, ...}

class FullStateUpdate(BaseModel):
    type: StateUpdateType = StateUpdateType.FULL_STATE
    tick: int
    floor: int
    dungeon_seed: int

    map_tiles: list[list[str]]  # 80x24 grid
    players: list[PlayerState]
    monsters: list[MonsterState]
    ore_deposits: list[OreState]

    messages: list[str] = []  # Combat log

class DeltaUpdate(BaseModel):
    type: StateUpdateType = StateUpdateType.DELTA
    tick: int
    base_tick: int  # Delta from this tick

    # Only include changed entities
    changed_players: list[PlayerState] = []
    changed_monsters: list[MonsterState] = []
    moved_entities: dict[str, Position] = {}  # {entity_id: new_pos}
    removed_entities: list[str] = []  # Died or picked up
    new_entities: list[PlayerState | MonsterState | OreState] = []

    new_messages: list[str] = []
```

**Publishing (server):**
```python
# Full state every 10 ticks
if tick % 10 == 0:
    update = FullStateUpdate(
        tick=tick,
        floor=5,
        dungeon_seed=12345,
        map_tiles=dungeon.get_tiles(),
        players=game_state.get_players(),
        monsters=game_state.get_monsters(),
        ore_deposits=game_state.get_ore()
    )
else:
    # Delta update
    update = DeltaUpdate(
        tick=tick,
        base_tick=tick - 1,
        changed_players=game_state.get_changed_players()
    )

await nc.publish(
    f"game.party.{party_id}.updates",
    update.model_dump_json().encode()
)
```

**Consuming (client):**
```python
async def handle_update(msg):
    data = json.loads(msg.data)

    if data["type"] == StateUpdateType.FULL_STATE:
        update = FullStateUpdate(**data)
        # Replace entire shadow state
        client_state.replace(update)
    elif data["type"] == StateUpdateType.DELTA:
        update = DeltaUpdate(**data)
        # Apply delta to shadow state
        client_state.apply_delta(update)

    # Re-render UI
    ui.render(client_state)
```

---

### Category 3: Chat Messages

**Definition:** Player communication

**Characteristics:**
- **Direction:** Bidirectional (client → server → clients)
- **Reliability:** Best-effort (if lost, player types again)
- **Validation:** Server filters profanity, spam

**NATS Subjects:**
- `chat.party.{party_id}` - Party chat
- `chat.global` - Global chat
- `chat.whisper.{from_id}.{to_id}` - Private messages

**Message types:**

```python
class ChatScope(str, Enum):
    PARTY = "party"
    GLOBAL = "global"
    WHISPER = "whisper"

class ChatMessage(BaseModel):
    scope: ChatScope
    from_player: str
    to_player: str | None = None  # For whispers
    message: str
    timestamp: float

class PartyChatMessage(ChatMessage):
    scope: ChatScope = ChatScope.PARTY
    party_id: str

class GlobalChatMessage(ChatMessage):
    scope: ChatScope = ChatScope.GLOBAL

class WhisperMessage(ChatMessage):
    scope: ChatScope = ChatScope.WHISPER
    to_player: str
```

**Publishing:**
```python
# Client sends chat
msg = PartyChatMessage(
    party_id="dragon_slayers",
    from_player="alice",
    message="Pull back, low HP!"
)

await nc.publish(
    f"chat.party.{msg.party_id}",
    msg.model_dump_json().encode()
)
```

---

### Category 4: Critical Events (Reliable)

**Definition:** Events that MUST be processed (no loss allowed)

**Characteristics:**
- **Direction:** Server → Services
- **Reliability:** At-least-once (JetStream)
- **Persistence:** Stored until acknowledged
- **Consumers:** Multiple services can consume

**NATS Subject:** `events.critical.{event_type}`

**Examples:**

```python
class CriticalEventType(str, Enum):
    LEGACY_ORE_COLLECTED = "legacy_ore_collected"
    PLAYER_DIED = "player_died"
    BOSS_DEFEATED = "boss_defeated"
    FLOOR_CLEARED = "floor_cleared"
    PURE_VICTORY = "pure_victory"
    TRADE_COMPLETED = "trade_completed"

class LegacyOreCollected(BaseModel):
    type: CriticalEventType = CriticalEventType.LEGACY_ORE_COLLECTED
    player_id: str
    ore: dict  # Full ore properties
    dungeon_floor: int
    timestamp: float

class PlayerDied(BaseModel):
    type: CriticalEventType = CriticalEventType.PLAYER_DIED
    player_id: str
    killed_by: str  # Monster ID or "fall_damage"
    dungeon_floor: int
    carried_ore: list[dict]  # Lost on death
    timestamp: float

class BossDefeated(BaseModel):
    type: CriticalEventType = CriticalEventType.BOSS_DEFEATED
    boss_name: str
    party_id: str
    participants: list[str]  # Player IDs
    dungeon_floor: int
    timestamp: float
```

**Publishing (JetStream):**
```python
# Server publishes critical event
event = LegacyOreCollected(
    player_id="alice",
    ore={"type": "mithril", "hardness": 98, "conductivity": 45},
    dungeon_floor=10
)

ack = await js.publish(
    "events.critical.legacy_ore_collected",
    event.model_dump_json().encode()
)

print(f"Event persisted at sequence {ack.seq}")
```

**Consuming (durable):**
```python
# Persistence service consumes and saves to DB
consumer = await js.subscribe(
    "events.critical.>",  # All critical events
    durable="critical_persister"
)

async for msg in consumer.messages:
    event_data = json.loads(msg.data)
    event_type = event_data["type"]

    if event_type == CriticalEventType.LEGACY_ORE_COLLECTED:
        event = LegacyOreCollected(**event_data)
        await db.add_to_legacy_vault(event.player_id, event.ore)

    elif event_type == CriticalEventType.PLAYER_DIED:
        event = PlayerDied(**event_data)
        await db.record_death(event)

    # Acknowledge (removes from queue)
    await msg.ack()
```

---

### Category 5: Service Queries (RPC)

**Definition:** Request/response between services

**Characteristics:**
- **Direction:** Service → Service (bidirectional)
- **Reliability:** Timeout-based
- **Response:** Synchronous-style (await response)

**NATS Subjects:** `service.{service_name}.{method}`

**Examples:**

```python
class QueryType(str, Enum):
    GET_PLAYER_STATE = "get_player_state"
    GET_LEGACY_VAULT = "get_legacy_vault"
    GET_PARTY_INFO = "get_party_info"

class GetPlayerStateQuery(BaseModel):
    type: QueryType = QueryType.GET_PLAYER_STATE
    player_id: str

class PlayerStateResponse(BaseModel):
    player_id: str
    class_name: str
    level: int
    stats: dict
    legacy_vault_count: int

class GetLegacyVaultQuery(BaseModel):
    type: QueryType = QueryType.GET_LEGACY_VAULT
    player_id: str

class LegacyVaultResponse(BaseModel):
    player_id: str
    ore_count: int
    ore_items: list[dict]
```

**Request (client):**
```python
query = GetPlayerStateQuery(player_id="alice")

response = await nc.request(
    "service.player.get_state",
    query.model_dump_json().encode(),
    timeout=2.0
)

player_state = PlayerStateResponse(**json.loads(response.data))
```

**Respond (server):**
```python
async def handle_get_player_state(msg):
    query = GetPlayerStateQuery(**json.loads(msg.data))

    # Fetch from database
    player = await db.get_player(query.player_id)

    response = PlayerStateResponse(
        player_id=player.id,
        class_name=player.class_name,
        level=player.level,
        stats=player.stats,
        legacy_vault_count=len(player.legacy_vault)
    )

    await msg.respond(response.model_dump_json().encode())

await nc.subscribe("service.player.get_state", cb=handle_get_player_state)
```

---

### Category 6: Work Queue Jobs

**Definition:** Async tasks (no immediate response needed)

**Characteristics:**
- **Direction:** Producer → Worker(s)
- **Reliability:** At-least-once (queue groups)
- **Load balancing:** Multiple workers consume
- **Idempotent:** Jobs can be retried

**NATS Subjects:** `jobs.{job_type}`

**Examples:**

```python
class JobType(str, Enum):
    SAVE_DUNGEON = "save_dungeon"
    GENERATE_MAP = "generate_map"
    COMPUTE_STATS = "compute_stats"
    SEND_EMAIL = "send_email"

class SaveDungeonJob(BaseModel):
    type: JobType = JobType.SAVE_DUNGEON
    dungeon_id: str
    party_id: str
    state: dict  # Full dungeon state
    priority: int = 0

class GenerateMapJob(BaseModel):
    type: JobType = JobType.GENERATE_MAP
    dungeon_id: str
    floor: int
    seed: int
    width: int = 80
    height: int = 24
```

**Publish job:**
```python
job = SaveDungeonJob(
    dungeon_id="dungeon_42",
    party_id="dragon_slayers",
    state=game_state.serialize(),
    priority=1  # High priority
)

await nc.publish("jobs.save_dungeon", job.model_dump_json().encode())
```

**Workers consume (queue group):**
```python
# Worker 1
async def worker_1_save_dungeon(msg):
    job = SaveDungeonJob(**json.loads(msg.data))
    await db.save_dungeon(job.dungeon_id, job.state)
    print(f"Worker 1 saved dungeon {job.dungeon_id}")

await nc.subscribe("jobs.save_dungeon", queue="save_workers", cb=worker_1_save_dungeon)

# Worker 2
async def worker_2_save_dungeon(msg):
    job = SaveDungeonJob(**json.loads(msg.data))
    await db.save_dungeon(job.dungeon_id, job.state)
    print(f"Worker 2 saved dungeon {job.dungeon_id}")

await nc.subscribe("jobs.save_dungeon", queue="save_workers", cb=worker_2_save_dungeon)

# NATS distributes jobs across both workers
```

---

## 🏗️ Message Abstractions (Code Design)

### Base Message Class

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import ClassVar
import uuid

class BrogueMessage(BaseModel):
    """Base class for all Brogue messages"""

    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=lambda: datetime.utcnow().timestamp())
    version: str = "1.0"

    # Override in subclasses
    MESSAGE_TYPE: ClassVar[str] = "base"

    class Config:
        use_enum_values = True

    def to_nats(self) -> bytes:
        """Serialize for NATS"""
        return self.model_dump_json().encode()

    @classmethod
    def from_nats(cls, data: bytes):
        """Deserialize from NATS"""
        return cls(**json.loads(data))
```

### Message Registry (Type Safety)

```python
class MessageRegistry:
    """Registry for message types"""

    _registry: dict[str, type[BrogueMessage]] = {}

    @classmethod
    def register(cls, message_class: type[BrogueMessage]):
        """Register a message type"""
        cls._registry[message_class.MESSAGE_TYPE] = message_class
        return message_class

    @classmethod
    def parse(cls, data: bytes) -> BrogueMessage:
        """Parse message based on type field"""
        raw = json.loads(data)
        msg_type = raw.get("type")

        if msg_type not in cls._registry:
            raise ValueError(f"Unknown message type: {msg_type}")

        message_class = cls._registry[msg_type]
        return message_class(**raw)

# Usage
@MessageRegistry.register
class MoveAction(BrogueMessage):
    MESSAGE_TYPE = "move"
    player_id: str
    direction: Direction

@MessageRegistry.register
class AttackAction(BrogueMessage):
    MESSAGE_TYPE = "attack"
    player_id: str
    target_id: str

# Parse any message
msg = MessageRegistry.parse(nats_data)
# Returns correct subclass based on "type" field
```

---

### Message Bus Abstraction

```python
class MessageBus:
    """High-level abstraction over NATS"""

    def __init__(self, nats_client):
        self.nc = nats_client
        self.js = nats_client.jetstream()

    async def publish_action(self, instance_id: str, action: BrogueMessage):
        """Publish player action to game instance"""
        subject = f"game.instance.{instance_id}.actions"
        await self.nc.publish(subject, action.to_nats())

    async def publish_state(self, party_id: str, state: BrogueMessage):
        """Publish state update to party"""
        subject = f"game.party.{party_id}.updates"
        await self.nc.publish(subject, state.to_nats())

    async def publish_critical(self, event: BrogueMessage):
        """Publish critical event (JetStream)"""
        subject = f"events.critical.{event.MESSAGE_TYPE}"
        await self.js.publish(subject, event.to_nats())

    async def request_service(self, service: str, method: str, query: BrogueMessage, timeout: float = 2.0):
        """RPC-style service query"""
        subject = f"service.{service}.{method}"
        response = await self.nc.request(subject, query.to_nats(), timeout=timeout)
        return json.loads(response.data)

    async def subscribe_actions(self, instance_id: str, handler):
        """Subscribe to player actions"""
        subject = f"game.instance.{instance_id}.actions"
        await self.nc.subscribe(subject, cb=handler)

    async def subscribe_critical(self, handler, durable_name: str):
        """Subscribe to critical events (durable)"""
        consumer = await self.js.subscribe(
            "events.critical.>",
            durable=durable_name
        )
        # Return consumer for manual iteration
        return consumer

# Usage
bus = MessageBus(nats_client)

# Publish
await bus.publish_action(instance_id="42", action=MoveAction(...))

# Subscribe
async def on_action(msg):
    action = MessageRegistry.parse(msg.data)
    # Handle action

await bus.subscribe_actions(instance_id="42", handler=on_action)
```

---

## 📋 Subject Naming Convention

### Pattern

```
{domain}.{entity_type}.{entity_id}.{action}
```

**Examples:**
```
game.instance.42.actions           # Commands to instance 42
game.instance.42.get_state         # Query instance 42 state
game.party.dragon_slayers.updates  # Events for party
game.party.dragon_slayers.chat     # Party chat

chat.global                        # Global chat
chat.party.dragon_slayers          # Party chat
chat.whisper.alice.bob             # Private message

events.critical.legacy_ore         # Critical loot events
events.critical.player_death       # Critical death events

jobs.save_dungeon                  # Async work queue
jobs.generate_map                  # Async work queue

service.player.get_state           # RPC to player service
service.persistence.save           # RPC to persistence service
```

### Wildcards

```
game.instance.*.actions            # All instance actions
game.party.*.updates               # All party updates
game.>                             # Everything game-related
events.critical.>                  # All critical events
```

---

## 🎯 Summary

**Brogue has 6 message categories:**

1. **Player Actions** (Commands) - Client → Server
2. **State Updates** (Events) - Server → Clients
3. **Chat Messages** - Bidirectional
4. **Critical Events** (Reliable) - Server → Services (JetStream)
5. **Service Queries** (RPC) - Service ↔ Service
6. **Work Queue Jobs** - Producer → Workers

**Key abstractions:**
- `BrogueMessage` - Base class (Pydantic)
- `MessageRegistry` - Type-safe parsing
- `MessageBus` - High-level API over NATS

**Design principles:**
- ✅ Type safety (Pydantic models)
- ✅ Clear semantics (know reliability guarantees)
- ✅ Consistent naming (subject conventions)
- ✅ Separation of concerns (different subjects for different purposes)
- ✅ Observability (message IDs, timestamps, versioning)

---

## 🚀 Next Steps

1. ✅ Understand message taxonomy (this doc)
2. 🔨 Implement base message classes
3. 🔨 Build MessageBus abstraction
4. 🔨 Define all message types in `brogue/messages/`
5. 🔨 Test pub/sub flows
6. 📝 Integrate with services

**Key insight:** Good message design is 80% of a clean distributed architecture. Get this right, and the services practically write themselves.
