# Brogue Microservice Architecture

**Date:** 2025-10-21
**Session:** icy-temple-1021
**Design Philosophy:** Authoritative server, dumb clients (thin client architecture)

---

## 🎯 Core Principle

**Server is the single source of truth. Clients are rendering engines.**

```
SERVER (Authoritative)          CLIENTS (Dumb)
━━━━━━━━━━━━━━━━━━━━━━━━        ━━━━━━━━━━━━━━━━━━━━━
✓ Owns dungeon state            ✓ Render what server says
✓ Owns player state             ✓ Capture player input
✓ Owns monster state            ✓ Send actions to server
✓ Validates all actions         ✓ Play sounds/animations
✓ Processes combat              ✓ Show chat messages
✓ Generates loot
✓ Runs monster AI               ✗ NO game logic
✓ Enforces game rules           ✗ NO state storage
                                ✗ NO validation
```

**Benefits:**
- 🔒 Impossible to cheat (server validates everything)
- 👁️ Easy spectator mode (just another client)
- 📹 Easy replay system (record server state)
- 🌐 Multiple client types (terminal, web, mobile)
- 🧪 Easy testing (deterministic server state)

---

## 🏗️ Microservice Components

### 1. Game State Service (Core)

**Responsibility:** Maintains authoritative game state

```
GameStateService
├── Dungeon Management
│   ├── Map generation (BSP algorithm)
│   ├── Tile states (floor, wall, ore)
│   ├── Ore properties (hardness, conductivity, etc.)
│   └── Floor progression
├── Entity Management
│   ├── Player positions, HP, inventory
│   ├── Monster positions, AI state
│   ├── Loot on ground
│   └── Legacy Vault (persistent)
├── Combat System
│   ├── Damage calculation
│   ├── Hit validation
│   ├── Death handling
│   └── Loot drops
└── Mining System
    ├── Mining progress (turns remaining)
    ├── Ore extraction
    └── Inventory management
```

**API:**
```python
class GameStateService:
    def create_dungeon(self, party_id: str) -> DungeonState
    def get_state(self, party_id: str) -> GameState
    def process_action(self, party_id: str, action: Action) -> Result
    def tick(self, party_id: str) -> StateUpdate
    def save_state(self, party_id: str) -> bool
    def load_state(self, party_id: str) -> GameState
```

### 2. Connection Service (WebSocket Gateway)

**Responsibility:** Manages client connections and message routing

```
ConnectionService
├── WebSocket Management
│   ├── Accept connections
│   ├── Authenticate players
│   ├── Assign to parties
│   └── Handle disconnects
├── Message Routing
│   ├── Client → Server (actions)
│   ├── Server → Clients (state updates)
│   └── Broadcast to party
└── Chat Relay
    ├── Party chat
    ├── Global chat
    └── Whispers
```

**API:**
```python
class ConnectionService:
    async def on_connect(self, websocket, player_id: str)
    async def on_action(self, websocket, action: Action)
    async def broadcast_state(self, party_id: str, state: GameState)
    async def send_chat(self, party_id: str, message: ChatMessage)
    async def on_disconnect(self, websocket)
```

### 3. Persistence Service (Database)

**Responsibility:** Save/load game state and player data

```
PersistenceService
├── Player Data
│   ├── Accounts (username, password hash)
│   ├── Legacy Vault (per player)
│   ├── Stats (victories, deaths, ore collected)
│   └── Achievements/badges
├── Dungeon State
│   ├── Active dungeons (in-progress)
│   ├── Map tiles
│   ├── Entity positions
│   └── Loot on ground
└── Leaderboards
    ├── Pure victories
    ├── Deepest floor
    └── Fastest runs
```

**API:**
```python
class PersistenceService:
    def save_player(self, player: Player) -> bool
    def load_player(self, player_id: str) -> Player
    def save_dungeon(self, party_id: str, state: GameState) -> bool
    def load_dungeon(self, party_id: str) -> GameState
    def update_legacy_vault(self, player_id: str, ore: LegacyOre)
    def get_leaderboard(self, category: str) -> List[Entry]
```

### 4. Chat Service (Optional - can be in Connection Service)

**Responsibility:** Handle chat, party finder, social features

```
ChatService
├── Message Routing
│   ├── Party chat
│   ├── Global chat
│   ├── Guild chat
│   └── Whispers
├── Party Finder
│   ├── LFG listings
│   ├── Party invites
│   └── Party formation
└── Social
    ├── Friend lists
    ├── Block lists
    └── Guild management
```

---

## 📡 Client-Server Communication Protocol

### Client → Server (Actions)

**Client sends only player intent, no game logic:**

```json
// Movement
{
  "type": "move",
  "player_id": "warrior_alice",
  "direction": "north"
}

// Attack
{
  "type": "attack",
  "player_id": "warrior_alice",
  "target_id": "goblin_1"
}

// Mine ore
{
  "type": "mine",
  "player_id": "warrior_alice",
  "target_pos": [10, 5]
}

// Use ability
{
  "type": "ability",
  "player_id": "healer_dave",
  "ability": "heal",
  "target_id": "warrior_alice"
}

// Chat
{
  "type": "chat",
  "player_id": "warrior_alice",
  "message": "Pull back, low HP!"
}

// Survey ore
{
  "type": "survey",
  "player_id": "rogue_carol",
  "target_pos": [10, 5]
}
```

### Server → Client (State Updates)

**Server sends complete state snapshot (or delta):**

```json
{
  "type": "state_update",
  "tick": 1523,
  "party_id": "dragon_slayers",

  "map": {
    "width": 80,
    "height": 24,
    "tiles": "..compressed or diff.."
  },

  "players": [
    {
      "id": "warrior_alice",
      "class": "warrior",
      "pos": [6, 10],
      "hp": 18,
      "max_hp": 20,
      "mana": 0,
      "status_effects": ["blessed"],
      "inventory": [...]
    },
    {
      "id": "healer_dave",
      "class": "healer",
      "pos": [4, 10],
      "hp": 12,
      "max_hp": 12,
      "mana": 15,
      "status_effects": []
    }
  ],

  "monsters": [
    {
      "id": "goblin_1",
      "type": "goblin",
      "pos": [10, 10],
      "hp": 4,
      "max_hp": 6
    }
  ],

  "loot": [
    {
      "id": "ore_1",
      "type": "iron_ore",
      "pos": [12, 15],
      "properties": {
        "hardness": 78,
        "conductivity": 23,
        "purity": 82
      }
    }
  ],

  "messages": [
    "Warrior hits Goblin for 6 damage!",
    "Healer casts Heal on Warrior (+8 HP)"
  ]
}
```

### Optimization: Delta Updates

**Instead of full state every tick, send only changes:**

```json
{
  "type": "delta_update",
  "tick": 1524,
  "base_tick": 1523,

  "changed_players": [
    {
      "id": "warrior_alice",
      "hp": 18  // Only HP changed
    }
  ],

  "moved_entities": [
    {"id": "goblin_1", "pos": [11, 10]}
  ],

  "removed_entities": ["goblin_2"],  // Died

  "new_messages": [
    "Goblin dies!"
  ]
}
```

**Client rebuilds state:**
```python
# Client maintains shadow state
client_state.apply_delta(delta_update)
client_state.render()
```

---

## 🔄 Data Flow Example

### Example: Warrior Attacks Goblin

```
1. CLIENT (Terminal)
   ├─> Player presses 'h' (move left into goblin)
   └─> Send to server:
       {
         "type": "move",
         "player_id": "warrior_alice",
         "direction": "west"
       }

2. CONNECTION SERVICE
   ├─> Receive WebSocket message
   ├─> Parse action
   └─> Route to GameStateService

3. GAME STATE SERVICE
   ├─> Validate action
   │   ├─> Is player alive? ✓
   │   ├─> Is it player's turn? ✓
   │   ├─> Is west tile valid? (Monster there!)
   │   └─> Trigger combat instead of move
   │
   ├─> Process combat
   │   ├─> Calculate damage: 8 (player ATK) - 1 (goblin DEF) = 7
   │   ├─> Apply damage: goblin.hp -= 7
   │   ├─> Check death: goblin.hp <= 0 → true
   │   ├─> Remove goblin
   │   ├─> Generate loot
   │   └─> Add message: "Warrior kills Goblin!"
   │
   └─> Create state update

4. CONNECTION SERVICE
   ├─> Receive state update
   └─> Broadcast to all party members:
       {
         "type": "state_update",
         "monsters": [],  // Goblin removed
         "players": [
           {"id": "warrior_alice", "pos": [5, 10]}  // Didn't move
         ],
         "messages": ["Warrior kills Goblin!"]
       }

5. ALL CLIENTS
   ├─> Receive state update
   ├─> Update local shadow state
   ├─> Re-render map
   │   ├─> Goblin disappears
   │   └─> Message appears in log
   └─> Play attack sound (optional)
```

**Key Points:**
- Client sent intent ("move west"), not result
- Server decided it triggered combat
- Server calculated damage, death, loot
- All clients get same state update (synchronized)
- Client can't cheat (server validates everything)

---

## 🎮 Client Architecture (Dumb Terminal)

### Client Responsibilities

```python
class BrogueClient:
    def __init__(self):
        self.ws = None  # WebSocket connection
        self.state = None  # Shadow copy of game state
        self.ui = TextualUI()  # Rendering engine

    async def connect(self, server_url: str, player_id: str):
        """Connect to game server"""
        self.ws = await websockets.connect(server_url)
        await self.ws.send(json.dumps({
            "type": "auth",
            "player_id": player_id
        }))

    async def handle_input(self, key: str):
        """Send player action to server"""
        action = self.parse_key(key)  # 'h' → {"type": "move", "dir": "west"}
        await self.ws.send(json.dumps(action))

    async def receive_updates(self):
        """Receive state updates from server"""
        async for message in self.ws:
            update = json.loads(message)

            if update["type"] == "state_update":
                self.state = update
                self.ui.render(self.state)

            elif update["type"] == "chat":
                self.ui.show_chat(update["message"])

    def parse_key(self, key: str) -> dict:
        """Convert keypress to action (NO GAME LOGIC)"""
        if key in ['h', 'j', 'k', 'l']:  # Movement
            return {"type": "move", "direction": KEY_TO_DIR[key]}
        elif key == 'm':  # Mine
            return {"type": "mine"}
        elif key == 'x':  # Survey
            return {"type": "survey"}
        # etc.
```

**What Client Does NOT Do:**
- ❌ Validate movement (server checks if tile walkable)
- ❌ Calculate damage (server does combat math)
- ❌ Check inventory space (server validates)
- ❌ Generate random numbers (server RNG only)
- ❌ Store persistent data (server/DB only)

**What Client DOES Do:**
- ✅ Render game state (draw map, entities, UI)
- ✅ Capture input (keypresses)
- ✅ Send actions to server
- ✅ Play sounds/animations (cosmetic)
- ✅ Maintain shadow state (for smooth rendering)

---

## 🏛️ Microservice Deployment

### Development (Local)

```
┌─────────────────────────────────────┐
│   All services on localhost         │
│                                     │
│   GameStateService   :8001          │
│   ConnectionService  :8002          │
│   PersistenceService :8003          │
│   PostgreSQL         :5432          │
└─────────────────────────────────────┘

Clients connect to: ws://localhost:8002
```

### Production (Docker Compose)

```yaml
version: '3.8'

services:
  game-state:
    build: ./services/game-state
    ports:
      - "8001:8001"
    environment:
      - PERSISTENCE_URL=http://persistence:8003
    depends_on:
      - persistence

  connection:
    build: ./services/connection
    ports:
      - "8002:8002"
    environment:
      - GAME_STATE_URL=http://game-state:8001

  persistence:
    build: ./services/persistence
    ports:
      - "8003:8003"
    environment:
      - DB_URL=postgresql://postgres:5432/brogue
    depends_on:
      - db

  db:
    image: postgres:14
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=brogue
      - POSTGRES_DB=brogue

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs

volumes:
  pgdata:
```

### Cloud (Kubernetes - Future)

```
┌──────────────────────────────────────┐
│         Load Balancer                │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│    Connection Service (3 pods)       │
│    - WebSocket termination           │
│    - Session affinity                │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│    Game State Service (5 pods)       │
│    - Stateless (state in Redis/DB)   │
│    - Horizontal scaling              │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│    Persistence Service (2 pods)      │
│    - DB connection pooling           │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│    PostgreSQL (RDS/managed)          │
│    - Backups, replication            │
└──────────────────────────────────────┘
```

---

## 🔒 Security & Validation

### Server-Side Validation (Critical!)

**Every action must be validated:**

```python
class GameStateService:
    def process_action(self, action: Action) -> Result:
        # 1. Validate player exists
        player = self.get_player(action.player_id)
        if not player:
            return Error("Invalid player")

        # 2. Validate player is alive
        if player.hp <= 0:
            return Error("Player is dead")

        # 3. Validate action is legal
        if action.type == "move":
            target_tile = self.map.get_tile(action.target_pos)

            # Can't move through walls
            if not target_tile.walkable:
                return Error("Tile not walkable")

            # Can't move too far
            if distance(player.pos, action.target_pos) > 1:
                return Error("Too far to move")

            # Check for monster (trigger combat instead)
            monster = self.get_monster_at(action.target_pos)
            if monster:
                return self.process_combat(player, monster)

        # 4. Process valid action
        return self.execute_action(action)
```

**Rate Limiting:**
```python
# Prevent action spam
MAX_ACTIONS_PER_SECOND = 10

if player.action_count_this_second > MAX_ACTIONS_PER_SECOND:
    return Error("Too many actions, slow down!")
```

**Anti-Cheat:**
- All RNG on server (can't manipulate rolls)
- All calculations on server (can't fake damage)
- All validation on server (can't walk through walls)
- Client input sanitized (prevent injection attacks)

---

## 📊 State Synchronization Strategies

### Option 1: Full State Snapshots

**Every tick, send complete game state:**

**Pros:**
- Simple to implement
- No sync issues (always current)
- Easy debugging (see exact state)

**Cons:**
- High bandwidth (80x24 map + entities = ~50KB)
- Wasteful (most state doesn't change)

**Good for:** Early development, small player counts

### Option 2: Delta Updates (Recommended)

**Send only changes since last tick:**

**Pros:**
- Low bandwidth (~1-5KB per tick)
- Efficient for large maps
- Scales better

**Cons:**
- More complex (need diffing)
- Client must maintain shadow state
- Risk of desync (needs recovery)

**Implementation:**
```python
def create_delta(old_state: GameState, new_state: GameState) -> Delta:
    delta = Delta()

    # Check player changes
    for player in new_state.players:
        old_player = old_state.get_player(player.id)
        if player != old_player:
            delta.changed_players.append(player)

    # Check monster changes
    # ... similar for monsters, loot, etc.

    return delta
```

**Desync Recovery:**
```python
# Client detects desync (checksum mismatch)
if client_state.checksum != server_checksum:
    # Request full state resync
    client.request_full_state()
```

### Option 3: Hybrid (Best of Both)

**Send deltas most of the time, full state occasionally:**

```python
# Every 10 ticks, send full state (resync)
if tick % 10 == 0:
    send_full_state()
else:
    send_delta()
```

**Pros:**
- Efficient (deltas)
- Self-correcting (full state resync)
- Best of both worlds

---

## 🎯 API Design

### REST API (Management)

**For lobby, party management, accounts:**

```
POST   /api/auth/register
POST   /api/auth/login
GET    /api/players/{player_id}
GET    /api/legacy-vault/{player_id}
POST   /api/party/create
POST   /api/party/join/{party_id}
GET    /api/servers/list
GET    /api/leaderboard/{category}
```

### WebSocket API (Real-time Game)

**For gameplay, state updates:**

```
// Client → Server
ws://game.brogue.io/play

{connect, auth, move, attack, mine, survey, chat, ...}

// Server → Client
{state_update, delta_update, chat, error, ...}
```

### gRPC (Inter-Service - Optional)

**For service-to-service communication:**

```protobuf
service GameState {
  rpc CreateDungeon(PartyID) returns (DungeonState);
  rpc ProcessAction(Action) returns (Result);
  rpc GetState(PartyID) returns (GameState);
  rpc Tick(PartyID) returns (StateUpdate);
}

service Persistence {
  rpc SavePlayer(Player) returns (Success);
  rpc LoadPlayer(PlayerID) returns (Player);
  rpc UpdateLegacyVault(LegacyOreUpdate) returns (Success);
}
```

---

## 🧪 Testing Strategy

### Unit Tests (Each Service)

```python
def test_combat_damage_calculation():
    player = Player(attack=8)
    monster = Monster(defense=1)

    damage = calculate_damage(player, monster)

    assert damage == 7  # 8 - 1

def test_movement_validation():
    game_state = GameState()
    player = game_state.players[0]

    # Try to move through wall
    result = game_state.process_action(MoveAction(
        player_id=player.id,
        direction="north"  # Wall is north
    ))

    assert result.error == "Tile not walkable"
```

### Integration Tests (Service Communication)

```python
async def test_client_server_flow():
    # Start server
    server = await start_server()

    # Connect client
    client = BrogueClient()
    await client.connect(server.url, "test_player")

    # Send action
    await client.send_action(MoveAction(direction="north"))

    # Receive state update
    update = await client.receive_update()

    assert update.players[0].pos == [5, 9]  # Moved north

    await server.stop()
```

### Load Tests (Performance)

```python
async def test_100_concurrent_players():
    server = await start_server()

    # Connect 100 clients
    clients = [BrogueClient() for _ in range(100)]
    await asyncio.gather(*[c.connect(server.url) for c in clients])

    # All clients move simultaneously
    start = time.time()
    await asyncio.gather(*[c.move("north") for c in clients])
    duration = time.time() - start

    assert duration < 1.0  # Should handle 100 actions in <1 second
```

---

## 📈 Performance Considerations

### Tick Rate

**How often does server update?**

```
Option 1: Fixed tick (10 Hz / 100ms)
  - Predictable
  - Easy to reason about
  - Good for real-time feel

Option 2: Event-driven (only when action happens)
  - More efficient
  - No wasted ticks
  - Good for turn-based feel

Recommendation: Hybrid
  - Real-time ticks when monsters active
  - Event-driven when just exploring
```

### State Size Optimization

**Compress map data:**

```python
# Instead of sending full 80x24 map:
map = [[Tile(...) for _ in range(24)] for _ in range(80)]

# Send run-length encoded:
map_rle = "###50...20###10"  # 50 walls, 20 floors, 10 walls

# Or delta from known base:
map_diff = {
  (10, 5): Tile.FLOOR,  # Only changed tiles
  (11, 5): Tile.ORE
}
```

### Bandwidth Estimation

**Per tick (60 ticks/min):**
- Full state: 50 KB × 60 = 3 MB/min
- Delta: 2 KB × 60 = 120 KB/min
- **Savings: 96%**

**Per player per hour:**
- Full state: 180 MB/hour
- Delta: 7.2 MB/hour

**100 players:**
- Full state: 18 GB/hour = 432 GB/day 💸
- Delta: 720 MB/hour = 17.3 GB/day ✅

**Conclusion: Delta updates essential for scaling!**

---

## 🚀 Implementation Roadmap

### Phase 1: Single Service MVP (Week 1-2)

```
Goal: Prove the architecture works

✓ Monolithic server (all services in one)
✓ WebSocket connection
✓ 2 players, shared state
✓ Server validates movement
✓ Clients render server state
✓ Basic chat

Success = "Clients are truly dumb, server owns state"
```

### Phase 2: Split Services (Week 3-4)

```
Goal: Microservice separation

✓ GameStateService (separate process)
✓ ConnectionService (separate process)
✓ Inter-service communication (HTTP or gRPC)
✓ Docker Compose deployment

Success = "Can scale services independently"
```

### Phase 3: Persistence (Week 5-6)

```
Goal: Save/load state

✓ PersistenceService
✓ PostgreSQL integration
✓ Player accounts
✓ Legacy Vault storage
✓ Dungeon state save/load

Success = "Players can log in/out, state persists"
```

### Phase 4: Optimization (Week 7-8)

```
Goal: Performance and scale

✓ Delta updates
✓ State compression
✓ Database indexing
✓ Connection pooling
✓ Load testing

Success = "Can handle 50+ concurrent players"
```

---

## 🎯 Key Takeaways

### Why This Architecture?

**1. Cheat-Proof**
- All logic on server
- Client can't manipulate state
- Fair gameplay guaranteed

**2. Multiple Client Types**
- Terminal client (Textual)
- Web client (HTML5 canvas)
- Mobile client (touch)
- All use same server API

**3. Spectator/Replay**
- Spectators just receive state updates
- Replays = recorded state updates
- Streaming-friendly

**4. Easier Development**
- Client is simple (just render)
- All complexity in server (testable)
- Can iterate on client without affecting server

**5. Future-Proof**
- Can add features server-side
- Clients auto-update (just render what server sends)
- Can swap out services (microservices!)

---

## 📋 Next Steps

**To Prototype:**
1. Create simple GameStateService (Flask/FastAPI)
2. Create simple ConnectionService (WebSocket server)
3. Create dumb client (Textual + WebSocket)
4. Test 2-player movement and chat
5. Validate clients are truly stateless

**To Validate:**
- Can client disconnect and reconnect seamlessly?
- Is lag <100ms with delta updates?
- Can we add a 3rd client type (web) easily?
- Does server prevent cheating?

---

**This is the right architecture for a serious multiplayer game!**

Thin clients + authoritative server = scalable, secure, future-proof. 🏗️
