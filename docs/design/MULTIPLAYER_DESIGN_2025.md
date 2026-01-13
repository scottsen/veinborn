# Veinborn Multiplayer Design (2025)

**Date:** 2025-11-11
**Status:** Active Design
**Version:** 2.0
**Based on:** Previous designs from icy-temple-1021 and iridescent-shade-1022

---

## 📋 Executive Summary

This document presents a comprehensive multiplayer design for Veinborn, building on the solid single-player foundation and previous design work. The design emphasizes:

- **Multiple game modes**: Co-op, competitive, and hybrid modes
- **Flexible player counts**: 2-8 players with dynamic scaling
- **Modern architecture**: WebSocket-based real-time communication with server authority
- **Incremental implementation**: Phased rollout from 2-player prototype to full MMO-lite
- **Existing foundation**: Leverages action serialization, events, and entity IDs already in place

### Core Vision

**"Four colored @ symbols, coordinating in real-time, hunting perfect ore together"**

But also: racing each other, competing for loot, forming alliances, and creating emergent stories through multiplayer roguelike gameplay.

---

## 🎯 Game Modes

### Mode 1: Co-op Dungeon (Primary Focus)

**Players:** 2-4 (optimal), up to 8 possible
**Goal:** Survive together, reach floor 26, share victory
**Loot:** Personal loot (everyone gets their own rolls)
**Death:** Individual permadeath, party can continue or resurrect

**Features:**
- Class synergies (Warrior, Mage, Rogue, Healer)
- Shared Legacy Vault for persistent progression
- Boss fights require coordination
- In-game chat and quick commands
- Spectator mode for dead players

**Ideal for:** Friends playing together, streamers, community events

---

### Mode 2: Race Mode (Competitive)

**Players:** 2-8
**Goal:** First to floor 26 wins (or highest floor when first player dies)
**Loot:** Shared ore veins (first to mine gets it)
**Death:** Eliminates player, others continue

**Features:**
- Same dungeon generation (seeded)
- See other players' positions (fog of war applies)
- Can't attack other players directly
- Leaderboards and speedrun timers
- Optional "zones" (you can't enter certain areas until others clear)

**Ideal for:** Competitive players, tournaments, streaming events

---

### Mode 3: PvP Arena (Future)

**Players:** 2-4
**Goal:** Last @ standing wins
**Loot:** Crafted before match or found in arena
**Death:** Elimination tournament style

**Features:**
- Balanced starting gear or draft system
- Smaller, arena-style maps
- Power-ups spawn at set intervals
- Best of 3 or 5 rounds
- ELO ranking system

**Ideal for:** Competitive community, esports potential

---

### Mode 4: Async Guild Mode (Ambitious)

**Players:** Unlimited (per guild)
**Goal:** Guild collectively explores deeper floors over time
**Loot:** Guild vault, members can withdraw gear
**Death:** Individual, but guild progress persists

**Features:**
- Players take turns exploring the same dungeon
- Each death advances "corruption level"
- Guild collectively tries to push as deep as possible
- Leaderboard by guild depth
- Async play (like chess by mail)

**Ideal for:** Large communities, casual players

---

## 🏗️ Core Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENTS (Players)                     │
│        Python Textual UI + WebSocket Client              │
│                                                          │
│  Features:                                               │
│  - Render game state                                    │
│  - Send player actions                                  │
│  - Client-side prediction                               │
│  - Local audio/visual effects                           │
└─────────────────────────────────────────────────────────┘
                          ↕ WebSocket (JSON messages)
┌─────────────────────────────────────────────────────────┐
│              GATEWAY LAYER (Load Balancer)               │
│                nginx + SSL termination                   │
│                                                          │
│  Features:                                               │
│  - SSL/TLS encryption                                   │
│  - Load balancing across connection services            │
│  - DDoS protection                                      │
│  - Health checks                                        │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│           CONNECTION SERVICE (Python + asyncio)          │
│                                                          │
│  Responsibilities:                                       │
│  - WebSocket connection management                      │
│  - Authentication / session management                  │
│  - Message routing (player → game instance)             │
│  - Heartbeat / latency monitoring                       │
│  - Reconnection handling                                │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│             MESSAGE BUS (Redis Pub/Sub or NATS)          │
│                                                          │
│  Channels:                                               │
│  - game.instance.{id}.actions    (player input)         │
│  - game.instance.{id}.state      (state broadcasts)     │
│  - game.party.{id}.chat          (chat messages)        │
│  - system.events                  (global events)        │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│           GAME INSTANCE SERVICE (Python)                 │
│                                                          │
│  Responsibilities:                                       │
│  - Authoritative game state                             │
│  - Action validation & execution                        │
│  - Turn processing                                       │
│  - Monster AI                                            │
│  - Event generation                                      │
│  - State synchronization (broadcast to clients)         │
│                                                          │
│  Each instance handles 1-8 players (one dungeon run)    │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│              PERSISTENCE LAYER (PostgreSQL)              │
│                                                          │
│  Tables:                                                 │
│  - users (authentication, profiles)                     │
│  - parties (party metadata, members)                    │
│  - legacy_vaults (persistent ore storage)               │
│  - highscores (leaderboards)                            │
│  - game_sessions (active/historical runs)               │
│  - replays (action logs for replay system)              │
└─────────────────────────────────────────────────────────┘
```

---

### Design Principles

1. **Server Authority**: All game logic runs on server, clients are "dumb" renderers
2. **Stateless Connections**: Connection service can be restarted without losing game state
3. **Horizontal Scaling**: Add more connection services and game instances as needed
4. **Failure Isolation**: One game instance crash doesn't affect others
5. **Observable**: Extensive logging, metrics, and replay capability
6. **Secure**: Authentication, input validation, anti-cheat measures

---

## 🌐 Networking Layer

### WebSocket Protocol

**Why WebSocket:**
- ✅ Full-duplex: Server can push updates without client polling
- ✅ Low latency: Near real-time communication
- ✅ Efficient: Binary or JSON over persistent connection
- ✅ Widely supported: Works in browsers and Python clients
- ✅ Firewall friendly: Works over port 443 (HTTPS)

**Message Format (JSON):**

```json
{
  "type": "action|state|chat|system",
  "timestamp": 1699728000000,
  "data": {
    // Type-specific payload
  }
}
```

---

### Client → Server Messages

**1. Player Action**
```json
{
  "type": "action",
  "timestamp": 1699728000123,
  "data": {
    "action_type": "move",
    "actor_id": "player_alice_uuid",
    "dx": 1,
    "dy": 0
  }
}
```

**2. Chat Message**
```json
{
  "type": "chat",
  "timestamp": 1699728000123,
  "data": {
    "channel": "party",
    "message": "Heal me!"
  }
}
```

**3. Quick Command**
```json
{
  "type": "quick_command",
  "timestamp": 1699728000123,
  "data": {
    "command": "ready" // Predefined: ready, wait, help, pull, retreat
  }
}
```

**4. Pause Request**
```json
{
  "type": "pause",
  "timestamp": 1699728000123,
  "data": {
    "paused": true
  }
}
```

---

### Server → Client Messages

**1. Full State Update** (on connect or large change)
```json
{
  "type": "state",
  "timestamp": 1699728000123,
  "data": {
    "turn_count": 142,
    "floor": 3,
    "players": [
      {
        "id": "player_alice_uuid",
        "name": "Alice",
        "class": "warrior",
        "hp": 18,
        "max_hp": 20,
        "position": [10, 5],
        "color": "red"
      }
    ],
    "monsters": [
      {
        "id": "goblin_1_uuid",
        "type": "goblin",
        "hp": 4,
        "max_hp": 6,
        "position": [15, 8]
      }
    ],
    "ore_veins": [
      {
        "id": "ore_vein_1_uuid",
        "type": "iron",
        "position": [12, 10],
        "purity": 78,
        "hardness": 65
      }
    ],
    "map": {
      "width": 80,
      "height": 24,
      "tiles": "..." // Compressed representation
    }
  }
}
```

**2. Delta Update** (after action)
```json
{
  "type": "delta",
  "timestamp": 1699728000456,
  "data": {
    "changes": [
      {
        "type": "entity_moved",
        "entity_id": "player_alice_uuid",
        "from": [10, 5],
        "to": [11, 5]
      },
      {
        "type": "entity_damaged",
        "entity_id": "goblin_1_uuid",
        "damage": 6,
        "new_hp": 0,
        "source": "player_alice_uuid"
      },
      {
        "type": "entity_died",
        "entity_id": "goblin_1_uuid"
      }
    ],
    "messages": [
      "Alice attacks Goblin for 6 damage!",
      "Goblin dies!"
    ]
  }
}
```

**3. Chat Message**
```json
{
  "type": "chat",
  "timestamp": 1699728000123,
  "data": {
    "sender": "Bob",
    "sender_color": "blue",
    "channel": "party",
    "message": "I'll heal you next turn"
  }
}
```

**4. System Event**
```json
{
  "type": "system",
  "timestamp": 1699728000123,
  "data": {
    "event": "player_joined",
    "player_name": "Carol",
    "player_class": "rogue"
  }
}
```

---

### Latency Optimization

**1. Client-Side Prediction**
```python
# Client predicts movement immediately (optimistic)
def handle_move_key(dx, dy):
    # 1. Update local state immediately
    player.position = (player.x + dx, player.y + dy)
    render_game()

    # 2. Send action to server
    await send_action({"action_type": "move", "dx": dx, "dy": dy})

    # 3. Server confirms or corrects
    # If server says "invalid", rollback local prediction
```

**2. Delta Compression**
- Only send what changed, not full state
- Use protobuf or msgpack for binary encoding (future optimization)

**3. Adaptive Update Rate**
- Fast exploration: 10 updates/sec
- Combat: 30 updates/sec
- Tactical pause: 1 update/sec

---

### Reconnection Handling

**Scenario: Player disconnects mid-game**

1. **Connection Service**: Detects disconnect, marks player as "disconnected"
2. **Game Instance**: Player entity becomes AI-controlled (defensive behavior)
3. **Message Bus**: Broadcasts `player_disconnected` event to party
4. **Reconnect Window**: Player has 2 minutes to reconnect
5. **On Reconnect**:
   - Authenticate with same session token
   - Receive full state update
   - Resume control of character
6. **If Timeout**: Player is removed from game, loot redistributed

---

## 🎮 Turn System Design

### Hybrid Turn Model (Recommended)

**Core Principle:** "4 actions per round, anyone can take them"

**Rules:**
1. Any player can submit an action at any time
2. Server processes actions immediately (FIFO)
3. After 4 actions total → Monsters act (all of them)
4. Action counter resets, repeat

**Example:**
```
Round 1:
  t=0.0s: Alice (Warrior) moves north        [1/4 actions]
  t=0.2s: Bob (Mage) casts fireball          [2/4 actions]
  t=0.3s: Alice moves north again (fast!)    [3/4 actions]
  t=0.5s: Carol (Rogue) backstabs goblin     [4/4 actions]

  → MONSTER TURN: All 5 monsters act
  → Action counter resets to 0/4

Round 2:
  t=0.6s: Dave (Healer) heals Alice          [1/4 actions]
  t=0.8s: Alice attacks                      [2/4 actions]
  ...
```

**Strategic Depth:**
- **Fast players** can dominate actions (risk vs reward)
- **Slow players** can be deliberate (fewer mistakes)
- **Team coordination** emerges organically
  - "Everyone hold, let healer take 3 heals"
  - "Go go go, burn them down fast!"
- **Specialist rounds** happen naturally
  - Rogue takes 4 scouting actions
  - Healer takes 3 healing actions + party moves once

**Why This Works:**
- ✅ Simple to understand
- ✅ Complex emergent strategy
- ✅ Fast-paced but allows tactics
- ✅ Rewards both speed and deliberation
- ✅ No boring waiting for your turn

---

### Boss Fight Mode (Optional Tactical)

**Trigger:** Entering boss room, or any player presses 'T' (toggle tactical)

**Rules:**
1. **Planning Phase** (5 seconds or until all ready)
   - Players queue their actions
   - Can see what allies are planning
   - Can change action before ready
2. **Execution Phase** (instant)
   - All actions resolve in priority order:
     1. Buffs/debuffs
     2. Movement
     3. Attacks
     4. Heals
   - Boss reacts
3. **Repeat**

**UI:**
```
┌─ TACTICAL MODE ────────────────────────────┐
│ Queued Actions:                             │
│  [Red]    Warrior:  ↑ (Move to boss)        │
│  [Blue]   Mage:     🔥 Boss (Fireball)      │
│  [Green]  Rogue:    ⚔️ Boss (Backstab)       │
│  [Yellow] Healer:   ✓ READY                 │
│                                             │
│  Waiting for players... (3/4 ready)         │
│  Press ENTER when ready, ESC to change      │
└─────────────────────────────────────────────┘
```

**Why Optional:**
- Some teams prefer pure chaos (mash fast)
- Others want coordination (tactical)
- Let players choose their playstyle

---

### Pause System

**Any player can pause:**
- Press SPACE → Game pauses
- All players see pause state
- Chat still works
- Unpause when ready (host or vote)

**Cooldown:** 5 seconds between pauses (prevent spam)

**Use cases:**
- "Wait, let me check ore stats"
- "BRB, phone"
- "Let's plan this boss fight"
- "I'm lagging, hold on"

---

## 📊 State Synchronization

### Authority Model

**Server is 100% authoritative:**
- Server validates all actions
- Server resolves all combat
- Server determines all loot
- Clients cannot cheat

**Client is display only:**
- Renders game state
- Sends input to server
- Predicts movement (optional)
- Displays feedback

---

### Synchronization Strategy

**1. Full State on Connect**
```python
async def on_player_connect(player_id: str, websocket):
    # Send complete game state
    full_state = game_instance.serialize_full_state()
    await websocket.send(json.dumps({
        "type": "state",
        "data": full_state
    }))
```

**2. Delta Updates on Actions**
```python
async def on_player_action(player_id: str, action: dict):
    # 1. Validate action
    if not game_instance.validate_action(player_id, action):
        return {"error": "Invalid action"}

    # 2. Execute action
    outcome = game_instance.execute_action(player_id, action)

    # 3. Generate delta
    delta = {
        "changes": outcome.changes,
        "messages": outcome.messages
    }

    # 4. Broadcast to all party members
    await broadcast_to_party(party_id, {
        "type": "delta",
        "data": delta
    })
```

**3. Periodic Full Sync** (heartbeat)
```python
# Every 10 seconds, send full state
# Corrects any client drift
asyncio.create_task(periodic_full_sync(party_id))
```

---

### Conflict Resolution

**Scenario:** Two players try to move to same tile simultaneously

```python
def resolve_movement_conflict(player_a, player_b, target_tile):
    # FIFO: First action received wins
    if player_a.action_timestamp < player_b.action_timestamp:
        # Player A gets tile
        player_a.position = target_tile
        # Player B bumps (or pushes A, configurable)
        player_b.blocked = True
        return "Player A wins (arrived first)"
    else:
        # Player B gets tile
        player_b.position = target_tile
        player_a.blocked = True
        return "Player B wins (arrived first)"
```

**Alternative: Push mechanic**
- First player moves to tile
- Second player "pushes" first player 1 tile
- Creates interesting tactical situations

---

## 🎨 UI/UX Enhancements

### Multiplayer HUD

```
┌─────────────────────── VEINBORN DUNGEON ────────────────────┐
│                                                            │
│   @ (Red)      @ (Blue)         OOO (Monsters)            │
│                                                            │
│        @ (Green)                                           │
│                  @ (Yellow)                                │
│                                                            │
│                    ⛏ (Ore Vein - Iron)                     │
└────────────────────────────────────────────────────────────┘
┌─────────────────────── PARTY STATUS ──────────────────────┐
│ [Red]    Warrior Alice:  18/20 HP  ████████░░  [L3]       │
│ [Blue]   Mage Bob:        8/8  HP  ████████    [L3]       │
│ [Green]  Rogue Carol:    10/12 HP  ████████░   [L3]       │
│ [Yellow] Healer Dave:    12/12 HP  ██████████  [L3]       │
│                                                            │
│ Floor: 3  |  Turn: 142  |  Actions: 2/4  |  Party: OK     │
└────────────────────────────────────────────────────────────┘
┌─────────────────────── CHAT & LOG ────────────────────────┐
│ [Yellow] Dave: Healing Alice now                          │
│ [Red] Alice: Thanks!                                       │
│ [System] Round 36 complete, monsters acting...            │
│ [Blue] Bob: Fireball ready for next group                 │
│                                                            │
│ Type /say <message> or press TAB to chat                  │
└────────────────────────────────────────────────────────────┘
```

### Color Coding

**Player @ Symbols:**
- Warrior: Bold Red
- Mage: Bright Blue
- Rogue: Green
- Healer: Yellow
- Spectator: Dim Gray (dead/watching)

**Damage Numbers** (floating text):
- Physical damage: Red
- Magic damage: Blue
- Critical hits: Gold (with flash)
- Healing: Green

**Status Indicators:**
- Glowing border: Buffed
- Pulsing: Taking action this turn
- Dim: Stealthed
- Skull icon: Dead (spectating)

---

### Chat System

**Channels:**
- `/party <message>` - Party only (default)
- `/say <message>` - Same as party
- `/all <message>` - All players in instance (if race mode)
- `/w <player> <message>` - Whisper

**Quick Commands:**
- `/ready` → "[Alice] Ready!"
- `/wait` → "[Alice] Wait up!"
- `/help` → "[Alice] Need help!"
- `/pull` → "[Alice] Pulling enemies!"
- `/heal` → "[Alice] Need healing!"
- `/oom` → "[Alice] Out of mana!"

**Chat UI:**
- Tab to open chat input
- ESC to close
- Up arrow to recall last message
- Auto-complete player names

---

## 🎓 Class System

### Four Base Classes

**1. Warrior (Tank/DPS)**
```yaml
starting_hp: 20
starting_stats:
  attack: 5
  defense: 3
  speed: 1.0

abilities:
  - name: Cleave
    description: Hit all adjacent enemies
    cooldown: 5 turns
    cost: 0

  - name: Taunt
    description: Force enemies to attack you for 5 turns
    cooldown: 10 turns
    cost: 0

  - name: Shield Block
    description: +5 defense for 3 turns
    cooldown: 8 turns
    cost: 0

ore_bonuses:
  hardness: +50% attack damage
  density: +30% armor
  malleability: +20% durability
```

**2. Mage (Ranged DPS/AOE)**
```yaml
starting_hp: 8
starting_stats:
  attack: 3
  defense: 1
  speed: 1.0
  mana: 50

abilities:
  - name: Fireball
    description: 10 damage in 3x3 area
    range: 8
    cooldown: 0
    cost: 10 mana

  - name: Ice Bolt
    description: 8 damage + slow enemy
    range: 10
    cooldown: 0
    cost: 8 mana

  - name: Mana Shield
    description: Convert mana to HP (1:1) for 5 turns
    cooldown: 15 turns
    cost: 0

ore_bonuses:
  conductivity: +50% spell damage
  purity: -20% mana cost
  density_low: +10% cast speed if density < 50
```

**3. Rogue (Mobility/Crit)**
```yaml
starting_hp: 12
starting_stats:
  attack: 4
  defense: 2
  speed: 1.2

abilities:
  - name: Backstab
    description: 3x damage from behind or stealthed
    cooldown: 0
    cost: 0

  - name: Stealth
    description: Invisible for 5 turns or until attack
    cooldown: 10 turns
    cost: 0

  - name: Dash
    description: Move 3 tiles instantly
    cooldown: 6 turns
    cost: 0

ore_bonuses:
  hardness: +40% backstab damage
  malleability: +30% durability
  density_low: +15% speed if density < 40
```

**4. Healer (Support/Sustain)**
```yaml
starting_hp: 12
starting_stats:
  attack: 2
  defense: 2
  speed: 1.0
  mana: 60

abilities:
  - name: Heal
    description: Restore 8 HP to target
    range: 5
    cooldown: 0
    cost: 10 mana

  - name: Group Heal
    description: Restore 5 HP to all allies in 5 tile radius
    cooldown: 5 turns
    cost: 20 mana

  - name: Resurrect
    description: Revive dead ally at 50% HP
    range: 1
    cooldown: Once per floor
    cost: 30 mana

  - name: Blessing
    description: +2 defense to target for 10 turns
    range: 5
    cooldown: 8 turns
    cost: 15 mana

ore_bonuses:
  conductivity: +40% healing amount
  purity: +50% buff duration
  malleability: +25% staff durability
```

---

### Class Balance Philosophy

**Design Goals:**
- Each class feels essential in co-op
- No class is useless in solo (AI companions fill gaps)
- Classes have clear strengths and weaknesses
- Synergies reward good teamwork

**Balance Levers:**
- HP pools (Warrior > Rogue/Healer > Mage)
- Damage output (Mage burst > Warrior sustained > Rogue crit > Healer chip)
- Utility (Healer essential > Rogue mobility > Warrior tank > Mage AOE)
- Skill floor (Warrior easy > Healer medium > Rogue hard > Mage expert)

---

## 🏆 Loot & Progression

### Loot Distribution: Personal Loot (Recommended)

**How it works:**
- Each player gets their own roll on ore veins
- Everyone can mine the same vein
- Ore properties are randomized per player
- No competition, no drama

**Example:**
```
Party mines Iron Ore Vein:
  Alice (Warrior): Iron Ore (H:78, C:23, P:65)  ← High hardness, great for warrior!
  Bob (Mage):      Iron Ore (H:34, C:82, P:71)  ← High conductivity, great for mage!
  Carol (Rogue):   Iron Ore (H:45, C:45, P:88)  ← Balanced, good for rogue
  Dave (Healer):   Iron Ore (H:21, C:76, P:91)  ← High purity, great for healer!

Everyone gets ore they can use!
```

**Pros:**
- ✅ No loot drama
- ✅ Everyone gets appropriate gear
- ✅ Scales to any party size
- ✅ Encourages mining together

**Cons:**
- ❌ Less competition/excitement
- ❌ No "I got the drop!" moments

---

### Loot Distribution: Shared Loot (Alternative)

**How it works:**
- Ore vein properties are same for everyone
- First to mine gets it
- Or use Need/Greed system

**Need/Greed System:**
```
Iron Ore (H:78, C:23, P:82) drops!

[Warrior]  NEED     (High hardness, I can use this!)
[Mage]     PASS     (Low conductivity, not for me)
[Rogue]    GREED    (Might be useful later)
[Healer]   PASS     (Not my stat priority)

→ Warrior wins (NEED > GREED > PASS)
```

**Pros:**
- ✅ Exciting competition
- ✅ Memorable "got the drop!" moments
- ✅ Strategic decisions (need vs greed)

**Cons:**
- ❌ Can cause loot drama
- ❌ Some players may never get upgrades
- ❌ Requires etiquette

---

### Shared Legacy Vault

**Concept:** Party shares persistent ore storage

**Rules:**
- Ore with purity 80+ goes to vault on death
- Any party member can withdraw ore for new run
- Vault has 50 ore capacity
- Tracks who found what

**Victory Types:**
- **Pure Victory** (No vault ore used) → Maximum prestige
- **Legacy Victory** (Vault ore used) → Still counts, less prestige
- **Party Pure Victory** (No one uses vault) → Ultimate achievement

**UI:**
```
┌─── PARTY LEGACY VAULT ───────────────────────┐
│ Party: "The Dragon Slayers"                  │
│ Members: Alice, Bob, Carol, Dave             │
│                                              │
│ Rare Ore Stored: 12/50                       │
│                                              │
│ [1] Starforged Iron (P:99, H:92, C:45)       │
│     Found by: Alice on Floor 8               │
│                                              │
│ [2] Moonsilver (P:95, H:34, C:88)            │
│     Found by: Bob on Floor 12                │
│                                              │
│ [3] Void Crystal (P:98, H:67, C:91)          │
│     Found by: Carol on Floor 15              │
│                                              │
│ Press 1-9 to withdraw ore for this run       │
│ ESC to close                                 │
└──────────────────────────────────────────────┘
```

---

## 🔐 Security & Anti-Cheat

### Authentication

**Option 1: Simple Token Auth (Development)**
```python
# Client sends on connect
{
  "type": "auth",
  "username": "alice",
  "password_hash": "sha256_hash_here"
}

# Server validates against database
# Returns session token
{
  "type": "auth_success",
  "session_token": "uuid_token_here"
}
```

**Option 2: OAuth2 (Production)**
- Use existing OAuth providers (GitHub, Discord, Google)
- No password storage
- Easy for users

**Option 3: JWT (Recommended)**
```python
# Server issues JWT on login
import jwt

token = jwt.encode({
    "user_id": "alice_uuid",
    "username": "alice",
    "exp": datetime.utcnow() + timedelta(hours=24)
}, SECRET_KEY, algorithm="HS256")

# Client includes token in WebSocket handshake
# Server validates token on every message
```

---

### Input Validation

**Server validates everything:**
```python
def validate_move_action(player_id: str, action: dict) -> bool:
    player = game_state.get_player(player_id)
    dx, dy = action["dx"], action["dy"]

    # 1. Is player alive?
    if player.hp <= 0:
        return False

    # 2. Is move within bounds?
    new_x, new_y = player.x + dx, player.y + dy
    if not game_state.is_in_bounds(new_x, new_y):
        return False

    # 3. Is tile walkable?
    if not game_state.is_walkable(new_x, new_y):
        return False

    # 4. Is player not stunned/frozen?
    if player.has_status("stunned"):
        return False

    # 5. Is move within allowed distance (anti-speedhack)?
    if abs(dx) > 1 or abs(dy) > 1:
        return False

    return True
```

**Never trust client:**
- Client says "I have 1000 HP" → Ignore, use server value
- Client says "I moved 10 tiles" → Reject, max 1 tile per action
- Client says "I one-shot boss" → Reject, validate damage formula

---

### Rate Limiting

**Prevent spam/DoS:**
```python
# Max 30 actions per second per player
rate_limiter = RateLimiter(max_actions=30, window_seconds=1)

async def handle_action(player_id: str, action: dict):
    if not rate_limiter.allow(player_id):
        # Throttle player
        await send_error(player_id, "Too many actions, slow down")
        return

    # Process action
    await process_action(player_id, action)
```

---

### Cheat Detection

**1. Impossible Actions**
```python
# Flag player if they do something impossible
if action_type == "attack" and distance(player, target) > weapon_range:
    log_cheat_attempt(player_id, "attacked beyond weapon range")
    ban_player(player_id)
```

**2. Statistical Anomalies**
```python
# Track player stats, flag anomalies
if player.actions_per_minute > 120:  # Humanly impossible
    flag_for_review(player_id, "superhuman APM")

if player.crit_rate > 0.9:  # Statistically impossible
    flag_for_review(player_id, "impossible crit rate")
```

**3. Client Fingerprinting**
```python
# Detect modified clients
expected_client_version = "1.0.0"
if client_version != expected_client_version:
    log_warning(player_id, f"outdated client: {client_version}")
    # Could be legit (slow updater) or modded client
```

---

## 🧪 Testing Strategy

### Unit Tests

```python
# Test action validation
def test_move_validation():
    game = GameInstance()
    player = game.add_player("alice", "warrior")

    # Valid move
    assert game.validate_action(player.id, {"action_type": "move", "dx": 1, "dy": 0})

    # Invalid move (off map)
    assert not game.validate_action(player.id, {"action_type": "move", "dx": 100, "dy": 0})

    # Invalid move (through wall)
    game.place_wall(player.x + 1, player.y)
    assert not game.validate_action(player.id, {"action_type": "move", "dx": 1, "dy": 0})
```

---

### Integration Tests

```python
# Test full client-server flow
async def test_multiplayer_combat():
    # Start server
    server = await start_test_server()

    # Connect two clients
    client_a = await connect_client("alice")
    client_b = await connect_client("bob")

    # Create party
    await client_a.send({"type": "create_party", "party_name": "Test"})
    await client_b.send({"type": "join_party", "party_name": "Test"})

    # Start game
    await client_a.send({"type": "start_game"})

    # Alice attacks goblin
    await client_a.send({"action_type": "attack", "target_id": "goblin_1"})

    # Both clients receive update
    update_a = await client_a.receive()
    update_b = await client_b.receive()

    assert update_a["type"] == "delta"
    assert "entity_damaged" in update_a["data"]["changes"]
    assert update_a == update_b  # Both see same state
```

---

### Load Testing

```python
# Simulate 100 concurrent players
import asyncio
import websockets

async def simulate_player(player_id: int):
    ws = await websockets.connect("ws://localhost:8765")

    # Authenticate
    await ws.send(json.dumps({"type": "auth", "username": f"bot_{player_id}"}))

    # Spam actions for 60 seconds
    for _ in range(60):
        await ws.send(json.dumps({"action_type": "move", "dx": 1, "dy": 0}))
        await asyncio.sleep(1)

    await ws.close()

# Run 100 in parallel
async def load_test():
    tasks = [simulate_player(i) for i in range(100)]
    await asyncio.gather(*tasks)

asyncio.run(load_test())
```

**Metrics to watch:**
- Server CPU usage
- Memory usage
- Message latency (p50, p95, p99)
- Dropped connections
- Error rate

---

### Bot Testing (Fuzz Testing)

```python
# Bot that plays randomly
class RandomBot:
    def __init__(self, game):
        self.game = game
        self.player_id = self.game.add_player("bot", "warrior").id

    def play_turn(self):
        # Choose random valid action
        actions = ["move_north", "move_south", "move_east", "move_west",
                   "attack", "wait", "mine", "craft"]

        action = random.choice(actions)

        try:
            self.game.handle_action(self.player_id, action)
        except Exception as e:
            print(f"Bot found crash: {e}")
            raise

# Run bot for 10,000 turns
bot = RandomBot(game)
for _ in range(10000):
    bot.play_turn()
```

**Goal:** Find crashes, infinite loops, edge cases

---

## 📦 Implementation Roadmap

### Phase 1: Foundation (2 weeks)

**Goal:** 2 players can move around together

**Tasks:**
- [ ] Set up WebSocket server (connection service)
- [ ] Implement authentication (simple token)
- [ ] Modify GameState to support multiple players
- [ ] Implement action routing (player → server → game instance)
- [ ] Implement state broadcasting (game instance → all players)
- [ ] Basic multiplayer UI (show other player's @)

**Deliverable:** 2 players can see each other move in real-time

---

### Phase 2: Combat & Chat (2 weeks)

**Goal:** Players can fight together and communicate

**Tasks:**
- [ ] Implement multiplayer combat (shared monster targeting)
- [ ] Implement chat system (party channel)
- [ ] Implement quick commands (/ready, /wait, etc.)
- [ ] Add party status panel (show all players' HP)
- [ ] Implement monster scaling (2x HP for 2 players)
- [ ] Add damage numbers and visual feedback

**Deliverable:** 2 players can fight monsters together and chat

---

### Phase 3: Loot & Classes (2 weeks)

**Goal:** Classes feel different, loot works

**Tasks:**
- [ ] Implement 4 class system (Warrior, Mage, Rogue, Healer)
- [ ] Implement class abilities (skills + cooldowns)
- [ ] Implement personal loot system
- [ ] Implement mining in multiplayer
- [ ] Add class-specific ore bonuses
- [ ] Balance testing

**Deliverable:** 4-player party with distinct classes hunting ore

---

### Phase 4: Turn System & Boss Fights (2 weeks)

**Goal:** Turn system feels good, bosses are challenging

**Tasks:**
- [ ] Implement "4 actions per round" turn system
- [ ] Implement tactical mode for boss fights
- [ ] Implement pause system
- [ ] Add boss encounters (every 3 floors)
- [ ] Boss AI with multi-phase fights
- [ ] Add floor transitions for parties

**Deliverable:** Party can coordinate to defeat bosses

---

### Phase 5: Persistence & Progression (2 weeks)

**Goal:** Parties persist, Legacy Vault works

**Tasks:**
- [ ] Implement party creation/joining
- [ ] Implement shared Legacy Vault
- [ ] Implement party high scores
- [ ] Add victory types (Pure vs Legacy)
- [ ] Implement save/load for parties
- [ ] Add party statistics

**Deliverable:** Parties can have persistent progression

---

### Phase 6: Polish & Balance (2 weeks)

**Goal:** Game feels great, ready for alpha

**Tasks:**
- [ ] Extensive playtesting
- [ ] Balance classes, monsters, loot
- [ ] Optimize network performance
- [ ] Add reconnection handling
- [ ] Add spectator mode (dead players)
- [ ] Tutorial for multiplayer
- [ ] Bug fixes

**Deliverable:** Alpha-quality multiplayer experience

---

### Phase 7: Competitive Modes (Future)

**Goal:** Race mode and PvP work

**Tasks:**
- [ ] Implement race mode
- [ ] Leaderboards
- [ ] Implement PvP arena (optional)
- [ ] Tournament system
- [ ] Replays and spectating

**Deliverable:** Competitive multiplayer modes

---

## 🛠️ Technology Stack

### Server

```python
# Core
Python 3.10+              # Language
asyncio                   # Async runtime
websockets                # WebSocket server
pydantic                  # Message validation

# Data
PostgreSQL 15             # Persistence
Redis 7                   # Message bus (alternative to NATS)
# OR
NATS 2.10                 # Message bus (from previous design)

# Deployment
Docker                    # Containerization
docker-compose            # Local dev orchestration
systemd                   # Production service management
nginx                     # Load balancing, SSL termination

# Monitoring
prometheus                # Metrics
grafana                   # Dashboards
structlog                 # Structured logging
```

### Client

```python
# Core
Python 3.10+              # Language
Textual 0.45+             # Terminal UI
websockets                # WebSocket client

# Future (Optional)
pygame                    # Graphical client
web browser + JS          # Web client
```

### Infrastructure

```bash
# Cloud Provider (Choose one)
- DigitalOcean Droplets   # Simple, cheap
- AWS EC2 + RDS           # Scalable
- Fly.io                  # Edge deployment
- Self-hosted             # Full control

# DNS + CDN
Cloudflare                # Free tier is generous

# SSL
Let's Encrypt             # Free SSL certificates

# Monitoring
Datadog / New Relic       # APM
OR
Self-hosted Prometheus    # Free
```

---

## 💰 Cost Estimates

### Small Scale (10-50 concurrent players)

```
Server:
  - 1x DigitalOcean Droplet (4GB RAM, 2 CPU) = $24/month
  - PostgreSQL (managed) = $15/month
  - Redis (managed) = $10/month
  - Domain + SSL = $12/year

Total: ~$50/month
```

### Medium Scale (100-500 concurrent players)

```
Servers:
  - 2x Connection Services (load balanced) = $48/month
  - 3x Game Instance Services = $72/month
  - PostgreSQL (2GB) = $60/month
  - Redis (1GB) = $20/month
  - Load balancer = $10/month

Total: ~$210/month
```

### Large Scale (1000+ concurrent players)

```
Servers:
  - 5x Connection Services (auto-scaling) = $200/month
  - 10x Game Instance Services = $400/month
  - PostgreSQL (10GB, replicated) = $200/month
  - Redis Cluster = $100/month
  - CDN + DDoS protection = $50/month

Total: ~$950/month
```

**Note:** These are rough estimates. Actual costs depend on traffic, storage, and cloud provider.

---

## 📈 Scalability

### Horizontal Scaling

**Connection Services:**
- Stateless, can add as many as needed
- Load balance with nginx (least_conn)
- Each handles ~500 concurrent WebSocket connections

**Game Instances:**
- Each handles 1 dungeon run (1-8 players)
- Spawn dynamically as parties form
- Kill when party completes or all disconnect

**Database:**
- Use read replicas for high scores, leaderboards
- Write to primary for critical data (vault, parties)
- Consider sharding by region (future)

**Message Bus:**
- NATS/Redis handles 100k+ messages/sec easily
- Cluster for high availability
- Add nodes as needed

---

### Geographic Distribution (Future)

```
┌─── US-EAST ───┐    ┌─── US-WEST ───┐    ┌─── EU ───┐
│ Connection    │    │ Connection    │    │Connection│
│ Game Instance │    │ Game Instance │    │Game Inst │
│ Redis         │    │ Redis         │    │Redis     │
└───────────────┘    └───────────────┘    └──────────┘
        ↓                    ↓                    ↓
            ┌────────────────────────────┐
            │   PostgreSQL (Global)      │
            │   Replicated               │
            └────────────────────────────┘
```

**Benefits:**
- Lower latency (players connect to nearest region)
- Better availability (region failure doesn't kill everything)
- Scales to global playerbase

---

## 🎯 Success Metrics

### Technical Metrics

```
Performance:
  - Latency (p95): < 100ms (excellent), < 200ms (acceptable)
  - Actions per second: > 1000 (per instance)
  - Uptime: > 99.5%
  - Crash rate: < 0.1% of games

Engagement:
  - Avg session length: > 30 minutes
  - Party completion rate: > 50%
  - Return rate (7 days): > 30%
  - Multiplayer adoption: > 60% of players try it

Community:
  - Active parties: > 100
  - Discord members: > 500
  - Twitch viewers: > 50 concurrent
  - GitHub stars: > 1000
```

---

## 🚀 Launch Strategy

### Alpha (Invite-only)

**Duration:** 4 weeks
**Players:** 50-100 selected testers
**Focus:** Find bugs, balance, get feedback

**Goals:**
- [ ] No critical bugs
- [ ] Classes feel balanced
- [ ] Network performance acceptable
- [ ] Players want to keep playing

---

### Beta (Public)

**Duration:** 8 weeks
**Players:** Unlimited
**Focus:** Scale testing, community building

**Marketing:**
- Reddit (/r/roguelikes, /r/incremental_games)
- HackerNews (Show HN: Multiplayer roguelike in the terminal)
- Twitter (gaming dev influencers)
- Twitch streamers (roguelike community)

**Goals:**
- [ ] 500+ registered users
- [ ] 50+ concurrent players at peak
- [ ] Active Discord community
- [ ] Positive reviews

---

### Launch (v1.0)

**Event:** Public announcement
**Features:** All core features complete

**Monetization (Optional):**
- Free to play (core game)
- Cosmetics (colored @ symbols, death messages)
- Supporter tier ($5/month) - Name in credits, special discord role
- Self-hosted license ($50 one-time) - Run private servers

**No pay-to-win, ever.**

---

## 🎉 Conclusion

This design provides a comprehensive roadmap for bringing multiplayer to Veinborn. Key strengths:

1. **Builds on existing work** - Action serialization, events, and entity IDs already exist
2. **Phased approach** - Start small (2 players), scale up
3. **Multiple modes** - Co-op, competitive, PvP options
4. **Modern tech** - WebSocket, server authority, horizontal scaling
5. **Clear roadmap** - 12 weeks to alpha-quality multiplayer

The vision is clear: **Four colored @ symbols, coordinating in real-time, hunting perfect ore, defeating bosses, and building shared stories in the depths of Veinborn's dungeon.**

Let's build it. 🎮⚔️

---

## 📚 References

- Previous design: `~/Archive/veinborn/docs-archive-2026-01-13/future-multiplayer/VEINBORN_MULTIPLAYER_DESIGN.md`
- Turn system: `~/Archive/veinborn/docs-archive-2026-01-13/future-multiplayer/VEINBORN_TURN_SYSTEM.md`
- NATS infra: `~/Archive/veinborn/docs-archive-2026-01-13/future-multiplayer/VEINBORN_NATS_INFRASTRUCTURE.md`
- Current codebase: `/home/user/veinborn/src/core/`

---

**Next Steps:**
1. Review this design with team/community
2. Set up development environment
3. Start Phase 1: Foundation
4. Iterate based on feedback

🚀 **Ready to build!**
