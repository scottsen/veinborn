# Brogue: Problems & Solutions Architecture

**Date:** 2025-10-22
**Session:** iridescent-shade-1022
**Philosophy:** Start with problems, not technologies

---

## 🎯 Core Philosophy

**We don't choose technologies because they're cool.**
**We choose them because they solve specific problems.**

This document inverts the typical architecture discussion:
- ❌ "Let's use NATS!" → "What for?"
- ✅ "We have this problem" → "NATS solves it"

---

## 🎮 The Brogue Game: What Are We Building?

**Brogue is:**
- Multiplayer roguelike (2-8 players co-op)
- Real-time terminal UI (not turn-based for multiplayer)
- Server-authoritative (clients are dumb renderers)
- Persistent (dungeons survive logout)
- SWG-inspired ore crafting system
- Class-based (Warrior/Mage/Ranger/Healer synergies)

**Scale target:**
- MVP: 4 players, 1 dungeon
- Phase 2: 50 concurrent players, 10 dungeons
- Future: 500+ players, MMO-lite features

---

## 🔨 Problem Category 1: RENDERING

### Problem 1.1: How do players see the game?

**Challenge:**
- Terminal-based (not web, not GUI)
- 80x24 character grid
- Real-time updates (not static refresh)
- Rich UI (HP bars, inventory, chat, map)
- Mouse + keyboard input
- Cross-platform (Linux, Mac, Windows)

**Failed approaches:**
- Raw curses → Too low-level, mouse support painful
- Rich library → Not reactive enough, no async
- Custom ncurses → Reinventing the wheel

**Solution: Textual Framework**

```python
from textual.app import App
from textual.widgets import Static

class BrogueUI(App):
    def compose(self):
        yield MapWidget()
        yield StatusBar()
        yield ChatLog()
```

**Why Textual:**
- ✅ React-like component model
- ✅ Async-first (built on asyncio)
- ✅ Mouse + keyboard events
- ✅ CSS-like styling
- ✅ Hot reload for development
- ✅ Terminal abstraction (works everywhere)
- ✅ Active development (modern, maintained)

**Status:** ✅ SOLVED (already implemented)

---

## 🔨 Problem Category 2: COMMUNICATION

### Problem 2.1: How do players communicate with the server?

**Challenge:**
- Real-time (not HTTP polling)
- Bidirectional (server pushes updates)
- Low latency (<100ms)
- Works over internet (not just LAN)
- Python-friendly

**Solution: WebSockets**

```python
# Client
async with websockets.connect("ws://server:8765") as ws:
    await ws.send(json.dumps(action))
    state = await ws.recv()

# Server
async def handler(websocket):
    async for message in websocket:
        action = json.loads(message)
        result = game.process(action)
        await websocket.send(json.dumps(result))
```

**Why WebSockets:**
- ✅ Real-time, bidirectional
- ✅ Built on TCP (reliable)
- ✅ Works through firewalls (port 80/443)
- ✅ Excellent Python support (`websockets` lib)
- ✅ Browser-compatible (future web client possible)

**Status:** ✅ SOLVED (design proven)

---

### Problem 2.2: How do services talk to each other?

**Challenge:**
- Multiple services (GameInstance, ConnectionService, Persistence, Chat)
- Services need to:
  - Broadcast events (player moved → all clients)
  - Request/reply (get player state)
  - Queue work (save dungeon state)
  - Scale independently
- No tight coupling (services don't know each other's IPs)
- Handle service failures gracefully

**Failed approaches:**
- HTTP REST → Too slow for real-time, no pub/sub
- Direct TCP → Tight coupling, no discovery
- Redis Pub/Sub → No delivery guarantees, limited routing

**Solution: NATS**

```python
# Game instance publishes state update
await nats.publish("game.party.dragon_slayers.updates", state)

# Connection service subscribes to all parties
await nats.subscribe("game.party.*.updates", broadcast_to_clients)

# Request player state
response = await nats.request("player.alice.get_state", timeout=1.0)
```

**Why NATS:**
- ✅ Pub/Sub built-in (broadcast to many)
- ✅ Request/Reply built-in (RPC pattern)
- ✅ Queue groups (load balancing)
- ✅ Subject hierarchy (clean routing)
- ✅ JetStream (persistence when needed)
- ✅ Lightweight (15MB memory)
- ✅ Clustering (high availability)

**Status:** 🔨 IN DESIGN

---

## 🔨 Problem Category 3: STATE MANAGEMENT

### Problem 3.1: Where does game state live?

**Challenge:**
- Game state is BIG (80x24 map, entities, inventory, ore properties)
- Multiple players viewing same state
- State changes rapidly (10-60 ticks/second)
- Must be authoritative (prevent cheating)
- Need to save/load dungeons

**Anti-pattern: Client-side state**
```python
# ❌ CLIENT CALCULATES DAMAGE
def attack(monster):
    damage = player.attack - monster.defense
    monster.hp -= damage  # CLIENT MODIFIES STATE!
```
**Problem:** Clients can cheat, desync between players

**Solution: Server-authoritative state**

```python
# ✅ SERVER IS SINGLE SOURCE OF TRUTH
class GameState:
    def __init__(self):
        self.dungeon = Dungeon()
        self.players = {}
        self.monsters = {}

    def process_action(self, action):
        # Server validates
        if not self.is_valid(action):
            return Error("Invalid action")

        # Server calculates
        result = self.execute(action)

        # Server broadcasts new state
        return self.get_snapshot()
```

**Client is dumb:**
```python
# Client only renders what server says
def on_state_update(state):
    ui.render_map(state.map)
    ui.render_entities(state.players + state.monsters)
```

**Why server-authoritative:**
- ✅ Impossible to cheat (server validates everything)
- ✅ All clients see same state (no desync)
- ✅ Easier testing (one codebase)
- ✅ Replay system (record server state)
- ✅ Spectator mode (just receive updates)

**Status:** ✅ SOLVED (design established)

---

### Problem 3.2: Where does persistent state live?

**Challenge:**
- Player accounts (username, password, stats)
- Legacy Vault (ore collection that survives death)
- Dungeon state (save dungeon when party logs off)
- Leaderboards (Pure Victory count, deepest floor)
- Trading history
- Guild data (future)

**Requirements:**
- ACID transactions (inventory changes must be atomic)
- Relational queries (find all ore in Legacy Vault)
- JSON support (flexible schema for ore properties)
- Proven reliability
- Good Python support

**Solution: PostgreSQL**

```sql
-- Player account
CREATE TABLE players (
    id UUID PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    created_at TIMESTAMP
);

-- Legacy Vault (ore that survives death)
CREATE TABLE legacy_vault (
    id UUID PRIMARY KEY,
    player_id UUID REFERENCES players(id),
    ore_type TEXT,
    properties JSONB,  -- {hardness: 98, conductivity: 45, ...}
    acquired_at TIMESTAMP
);

-- Dungeon state
CREATE TABLE dungeons (
    id UUID PRIMARY KEY,
    party_id UUID,
    floor INT,
    state JSONB,  -- Full dungeon snapshot
    updated_at TIMESTAMP
);
```

**Why PostgreSQL:**
- ✅ Rock-solid reliability
- ✅ ACID transactions
- ✅ JSONB for flexible schemas (ore properties)
- ✅ Excellent Python support (`asyncpg`)
- ✅ Mature ecosystem
- ✅ Can scale to millions of rows
- ✅ Free and open source

**Not MySQL because:**
- PostgreSQL has better JSON support (JSONB > JSON)
- Better concurrency (MVCC vs table locks)
- More features (CTEs, window functions, full-text search)

**Not NoSQL (MongoDB) because:**
- Need relational queries (player → vault → ore)
- Need transactions (transfer ore between players)
- Schema is mostly structured (not pure document store)

**Status:** ✅ SOLVED (PostgreSQL chosen)

---

## 🔨 Problem Category 4: CONCURRENCY

### Problem 4.1: Multiple players act simultaneously

**Challenge:**
- 4 players in dungeon, all pressing keys at once
- Server must process 40 actions/second (4 players × 10 actions/sec)
- Must stay responsive (<100ms latency)
- Python GIL limits true parallelism

**Solution: AsyncIO + Single-threaded event loop**

```python
# All actions processed on single thread (no locks!)
async def game_loop():
    while True:
        # Collect all pending actions
        actions = await action_queue.get_all()

        # Process in order
        for action in actions:
            game_state.process(action)

        # Broadcast new state
        await broadcast_state()

        # Sleep for tick rate
        await asyncio.sleep(0.1)  # 10 ticks/second
```

**Why single-threaded:**
- ✅ No locks (no race conditions)
- ✅ Deterministic (same inputs = same state)
- ✅ Easy to reason about
- ✅ Replay-friendly (record inputs, replay)
- ✅ Python-friendly (no GIL fighting)

**When to use threads/multiprocessing:**
- ❌ Game logic → Keep single-threaded
- ✅ I/O (database, NATS) → AsyncIO handles this
- ✅ Separate game instances → Run multiple processes

**Status:** ✅ SOLVED (async design)

---

### Problem 4.2: Multiple game instances

**Challenge:**
- 10 different parties playing simultaneously
- Each needs isolated game state
- Need to scale horizontally

**Solution: Process-per-instance**

```python
# Game Instance Manager
class InstanceManager:
    def __init__(self):
        self.instances = {}  # instance_id → Process

    async def create_instance(self, party_id):
        # Spawn new Python process
        process = await asyncio.create_subprocess_exec(
            "python", "game_instance.py", f"--party={party_id}"
        )

        self.instances[party_id] = process

        # Instance listens on NATS: game.instance.{party_id}.*
```

**Why processes not threads:**
- ✅ True isolation (one crash doesn't kill others)
- ✅ True parallelism (bypass GIL)
- ✅ Can run on different machines (cloud scale)
- ✅ OS-level resource limits

**Status:** 🔨 IN DESIGN

---

## 🔨 Problem Category 5: RELIABILITY

### Problem 5.1: Service crashes

**Challenge:**
- Network hiccups
- Out of memory
- Bugs causing exceptions
- Server restarts

**Solution: Supervision + NATS clustering**

```python
# Supervisor pattern (systemd, Docker, K8s)
# If service dies, restart it

# NATS clustering
# If NATS server dies, clients reconnect to another

# JetStream for critical events
# If consumer is down, messages queued until it comes back
```

**Status:** 🔨 IN DESIGN

---

### Problem 5.2: Player disconnects

**Challenge:**
- WiFi drops
- Browser closed
- Network hiccup
- Laptop sleep

**Solution: Reconnection + state recovery**

```python
# Client reconnects
await ws.connect()
await ws.send({"type": "reconnect", "player_id": "alice", "session_token": "..."})

# Server restores session
session = sessions.get(session_token)
game_instance = instances[session.party_id]

# Send full state (resync)
state = await nats.request(f"game.instance.{party_id}.get_full_state")
await ws.send(state)
```

**Status:** 🔨 IN DESIGN

---

### Problem 5.3: Data loss

**Challenge:**
- Server crash before save
- Database corruption
- Accidental deletion

**Solution: Write-ahead logging + backups**

```python
# Every critical event logged before processing
await wal.log({"action": "pickup_legacy_ore", "player": "alice", "ore": {...}})

# Then process
game_state.add_to_vault(ore)

# If crash, replay WAL on restart

# Daily backups
pg_dump brogue > backups/brogue_$(date +%Y%m%d).sql
```

**Status:** 🔨 FUTURE

---

## 🔨 Problem Category 6: DEPLOYMENT

### Problem 6.1: How do players find the game?

**Challenge:**
- Players need stable URL/IP
- Multiple game servers (dev, staging, prod)
- Load balancing
- SSL/TLS termination
- WebSocket proxying

**Solution: tia-proxy (nginx-based)**

```nginx
# /etc/tia-proxy/sites/brogue.conf

upstream brogue_websocket {
    server 127.0.0.1:8765;
    server 127.0.0.1:8766;  # Multiple instances
}

server {
    listen 443 ssl;
    server_name brogue.tia.dev;

    ssl_certificate /etc/letsencrypt/live/brogue.tia.dev/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/brogue.tia.dev/privkey.pem;

    location / {
        proxy_pass http://brogue_websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

**Players connect to:**
```python
ws = await websockets.connect("wss://brogue.tia.dev")
```

**Status:** 🔨 IN DESIGN

---

### Problem 6.2: How do we deploy changes?

**Challenge:**
- Players are connected
- Can't just restart server (they'll disconnect)
- Need zero-downtime deploys

**Solution: Rolling deploys + graceful shutdown**

```python
# 1. Start new version on different port
./brogue_server --port 8766

# 2. Add to load balancer
nginx: upstream now includes :8765 and :8766

# 3. Graceful shutdown old version
# Stop accepting new connections
# Wait for existing games to finish
# Or migrate sessions to new instance

# 4. Remove old from load balancer
```

**Status:** 🔨 FUTURE

---

## 🔨 Problem Category 7: OBSERVABILITY

### Problem 7.1: What's happening right now?

**Challenge:**
- How many players online?
- Which dungeons are active?
- Any errors happening?
- Performance (latency, throughput)?

**Solution: Metrics + structured logging**

```python
# Prometheus metrics
from prometheus_client import Counter, Gauge

players_online = Gauge('brogue_players_online', 'Current players')
actions_processed = Counter('brogue_actions_total', 'Actions processed')

# Structured logging
logger.info("player_joined", extra={
    "player_id": "alice",
    "party_id": "dragon_slayers",
    "dungeon_floor": 5
})
```

**Status:** 🔨 FUTURE

---

## 📊 Summary: Problem → Solution Mapping

| Problem | Solution | Status |
|---------|----------|--------|
| **Rendering (TUI)** | Textual framework | ✅ SOLVED |
| **Client ↔ Server** | WebSockets | ✅ SOLVED |
| **Service ↔ Service** | NATS | 🔨 IN DESIGN |
| **Game state authority** | Server-authoritative | ✅ SOLVED |
| **Persistent storage** | PostgreSQL | ✅ SOLVED |
| **Concurrency (single instance)** | AsyncIO | ✅ SOLVED |
| **Concurrency (multi instance)** | Process-per-instance | 🔨 IN DESIGN |
| **Service discovery** | NATS subjects | 🔨 IN DESIGN |
| **Reliability** | Clustering + supervision | 🔨 IN DESIGN |
| **Load balancing** | tia-proxy (nginx) | 🔨 IN DESIGN |
| **Deployment** | Docker + systemd | 🔨 FUTURE |
| **Observability** | Prometheus + logs | 🔨 FUTURE |

---

## 🎯 Technology Stack (Problem-Driven)

```
┌─────────────────────────────────────────────┐
│ PROBLEM: Players need to see the game      │
│ SOLUTION: Textual (TUI framework)          │
└─────────────────────────────────────────────┘
         ↕ (WebSocket)
┌─────────────────────────────────────────────┐
│ PROBLEM: Load balancing, SSL, routing      │
│ SOLUTION: tia-proxy (nginx)                │
└─────────────────────────────────────────────┘
         ↕ (WebSocket)
┌─────────────────────────────────────────────┐
│ PROBLEM: Client connections                │
│ SOLUTION: ConnectionService (websockets)   │
└─────────────────────────────────────────────┘
         ↕ (NATS)
┌─────────────────────────────────────────────┐
│ PROBLEM: Service communication             │
│ SOLUTION: NATS (message bus)               │
└─────────────────────────────────────────────┘
         ↕ (NATS)
┌─────────────────────────────────────────────┐
│ PROBLEM: Game logic                        │
│ SOLUTION: GameInstance (asyncio)           │
└─────────────────────────────────────────────┘
         ↕ (NATS/DB)
┌─────────────────────────────────────────────┐
│ PROBLEM: Persistence                       │
│ SOLUTION: PostgreSQL + asyncpg             │
└─────────────────────────────────────────────┘
```

---

## 🚀 Next Steps

**To complete the architecture:**
1. ✅ Understand problems (this doc)
2. 🔨 Design NATS infrastructure (next doc)
3. 🔨 Design message taxonomy (next doc)
4. 🔨 Design tia-proxy routing (next doc)
5. 📝 Implement MVP prototype

**Key insight:** Every technology choice maps to a specific problem. If we can't explain the problem, we don't need the technology.
