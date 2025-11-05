# Brogue Server Architecture Options

**Date:** 2025-10-21
**Session:** icy-temple-1021
**Question:** Host-owned vs Dedicated Server vs Persistent MMO?

---

## 🏗️ Three Architecture Paths

### Option 1: Host-Owned (Peer-to-Peer Style)

**How it works:**
```
Alice starts game → Becomes host → Server runs on her machine
Bob, Carol, Dave connect to Alice's IP
Alice quits → Server dies → Game ends
```

**Pros:**
- ✅ No infrastructure costs
- ✅ Simple to implement
- ✅ Private games with friends
- ✅ No hosting/maintenance needed
- ✅ Host controls everything (mods, rules)

**Cons:**
- ❌ Host disconnect = game over for everyone
- ❌ No persistence (dungeon dies when host quits)
- ❌ Host must port-forward (technical barrier)
- ❌ Host's internet = everyone's experience
- ❌ Can't play without host online

**Use Cases:**
- "Hey friends, let's run a dungeon tonight at 8pm"
- Private sessions, known players
- LAN parties
- Testing/development

---

### Option 2: Dedicated Server (Always-On)

**How it works:**
```
VPS/Cloud server runs 24/7
Players connect anytime
Dungeon persists between sessions
Multiple parties can play simultaneously
```

**Pros:**
- ✅ Always available
- ✅ Professional experience
- ✅ Persistence (save/load dungeon state)
- ✅ Multiple parties simultaneously
- ✅ No host disconnect issues
- ✅ Better performance (dedicated resources)
- ✅ Community can form around server

**Cons:**
- ❌ Costs money ($5-20/month VPS)
- ❌ Requires hosting knowledge
- ❌ Need maintenance (updates, backups)
- ❌ Security concerns (public-facing)
- ❌ Moderation needed (if public)

**Use Cases:**
- Public community servers
- Persistent world gameplay
- Larger player base
- Serious/competitive play

**Cost Estimate:**
- Small VPS (4 players): $5/month (DigitalOcean, Linode)
- Medium VPS (20 players): $10/month
- Large VPS (100 players): $20-40/month

---

### Option 3: Persistent Text MMO (The Big Vision!)

**How it works:**
```
Central server runs persistent world
Hundreds/thousands of players
Dungeons persist and evolve
Asynchronous gameplay (log in/out anytime)
Shared economy, trading, guilds
```

**Architecture:**
```
┌─────────────────────────────────────┐
│     Central Game Server             │
│  - Persistent world state           │
│  - Multiple dungeons                │
│  - Player database                  │
│  - Economy/trading                  │
│  - Chat/guilds                      │
└─────────────────────────────────────┘
         ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑
         │ │ │ │ │ │ │ │ │ │
    [100+ players connected]

         ┌──────────────┐
         │  Database    │
         │  PostgreSQL  │
         │  - Accounts  │
         │  - Dungeons  │
         │  - Items     │
         └──────────────┘
```

**Features:**

**Persistent Dungeons:**
```
Dungeon #42 (Floor 5)
  - Party "Dragon Slayers" logged off here yesterday
  - Their campfire still burning
  - Message carved in wall: "Boss room cleared, loot taken"
  - Monsters respawned (6 hours later)
  - New party can explore same dungeon
```

**Shared World:**
- Multiple parties in different dungeons
- Town/hub area (safe zone, forge, trading)
- Global chat channels
- Guilds/clans
- Leaderboards (Pure Victory count, deepest floor)

**Asynchronous Gameplay:**
```
Session 1 (Monday):
  Party plays 2 hours, reaches Floor 7
  → Logs off at safe room
  → Dungeon state saved

Session 2 (Wednesday):
  Party logs back in
  → Resume from Floor 7
  → Monsters may have respawned
  → Continue deeper
```

**Economy & Trading:**
```
[Red] Alice: "Selling 99 conductivity Mithril!"
[Blue] Bob: "I'll trade you high hardness Iron?"
[Green] Carol: "I'll buy for 500 gold"

Town square trading post:
  - List items for sale
  - Set prices
  - Auction house?
```

**Social Features:**
- Global chat
- Party chat
- Guild chat
- Whispers (private messages)
- Friend lists
- Party finder ("LFG: Need healer for Floor 10+")

**Pros:**
- ✅ Massive community potential
- ✅ Always something happening
- ✅ Trading/economy adds depth
- ✅ Asynchronous play (log in anytime)
- ✅ Guilds create retention
- ✅ Persistent world feels alive
- ✅ Content creates itself (player interactions)

**Cons:**
- ❌ MUCH more complex to build
- ❌ Database required (PostgreSQL, etc.)
- ❌ Moderation needed (trolls, cheaters)
- ❌ Balance harder (economy, exploits)
- ❌ Infrastructure costs (higher)
- ❌ 24/7 uptime critical
- ❌ Longer development time (6+ months)

**Use Cases:**
- Full-fledged online game
- Community-driven content
- Streamer-friendly (audiences can watch/join)
- Long-term engagement

---

## 🎯 Hybrid Approach (Recommended!)

**Best of all worlds: Support BOTH host-owned AND dedicated servers**

```
┌─ BROGUE MULTIPLAYER ───────────────┐
│ Choose Game Mode:                  │
│                                    │
│ [H] Host Private Game              │
│     → You run server on your PC    │
│     → Friends join via IP          │
│     → No persistence               │
│                                    │
│ [J] Join Server                    │
│     → Connect to dedicated server  │
│     → Public or private servers    │
│     → Persistent dungeons          │
│                                    │
│ [B] Browse Servers                 │
│     → See active servers           │
│     → Filter by rules/mods         │
│     → Join community               │
└────────────────────────────────────┘
```

**Implementation:**
```python
# Same server code works for both!

# Host-owned mode:
python brogue_server.py --host --port 5000
# → Server runs locally, LAN/internet via port forward

# Dedicated mode:
python brogue_server.py --dedicated --port 5000 --persist
# → Server runs on VPS, saves state to DB

# Players connect the same way regardless:
python brogue_client.py --connect alice.example.com:5000
```

**Why Hybrid:**
1. **Start simple:** Friends can host private games immediately
2. **Grow naturally:** Community can set up dedicated servers later
3. **Flexibility:** Choose what fits your needs
4. **Testing:** Develop using host mode, deploy to dedicated

---

## 🌍 Persistent MMO Features (If We Go There)

### The Hub Town

**Safe zone where all players gather:**
```
╔════════════════════════════════════╗
║         BROGUE TOWN                ║
╠════════════════════════════════════╣
║                                    ║
║    [F]orge        [T]avern         ║
║      🔨            🍺               ║
║                                    ║
║    [M]arket       [G]uild Hall     ║
║      💰            🏛️               ║
║                                    ║
║         [D]ungeon Entrance         ║
║              ⬇️                     ║
╚════════════════════════════════════╝

12 players in town
[Global] Looking for group: Floor 10+
[Global] Selling Legacy Ore!
```

**Forge:**
- Craft items from ore
- Public crafting (others can see)
- Master crafters (NPC or player-run?)

**Tavern:**
- Quest board
- Hire NPCs
- Party finder
- Socialize

**Market:**
- Buy/sell ore and items
- Auction house
- Trading post

**Guild Hall:**
- Create/join guilds
- Guild vaults (shared Legacy Ore)
- Guild quests
- Leaderboards

### Dungeon Instances

**Option A: Shared Dungeons** (True MMO)
```
Multiple parties in same dungeon
Can see each other
Can team up or compete
Loot competition
World bosses (requires multiple parties)
```

**Option B: Instanced Dungeons** (WoW-style)
```
Each party gets own dungeon
Private, no interference
Traditional party experience
Can still have shared town
```

**Option C: Hybrid**
```
Floors 1-5: Shared (town outskirts, casual)
Floors 6-10: Instanced per party
Floors 11+: Shared (end-game, competitive)
Boss floors: Shared (world bosses!)
```

### Persistent Features

**Dungeon Evolution:**
```
Monday: Floor 5 has 10 monsters
Players farm it all week
Friday: Monsters depleted, respawn timer
Saturday: Monsters back, but HARDER (adaptive difficulty)
```

**Player Impact:**
```
Party clears boss on Floor 10
→ Boss room becomes safe zone
→ Other players can use it
→ Boss respawns after 7 days
```

**Seasonal Events:**
```
Winter Event: Ice dungeons appear
  - Special monsters
  - Ice-themed Legacy Ore
  - Limited-time recipes

Halloween: Haunted floors
  - Ghostly enemies
  - Cursed ore (high stats, drawbacks)
```

### Economy Design

**Currency:**
- Gold (earned from kills, loot)
- Legacy Tokens (from Legacy Ore sales, rare)

**Trading:**
- Player-to-player (direct trade)
- Market (listings, async)
- Auction house (bidding)

**Inflation Control:**
- Gold sinks (repair costs, crafting fees)
- Ore consumption (crafting destroys ore)
- Permadeath (lose gold on death?)

**Valuable Items:**
- High-stat ore (98+ quality)
- Legacy Ore (tradeable?)
- Rare recipes
- Cosmetics (colored @ symbols!)

---

## 📊 Comparison Matrix

| Feature | Host-Owned | Dedicated | MMO |
|---------|-----------|-----------|-----|
| **Setup Complexity** | Low | Medium | High |
| **Cost** | Free | $5-20/mo | $40+/mo |
| **Players** | 2-8 | 8-50 | 100+ |
| **Persistence** | No | Yes | Yes |
| **Database Needed** | No | Optional | Yes |
| **Social Features** | Party only | Multiple parties | Full social |
| **Dev Time** | 2 weeks | 4 weeks | 6+ months |
| **Maintenance** | None | Low | High |
| **Community** | Friends | Small | Large |
| **Monetization** | N/A | Donations? | Subs/Cosmetics |

---

## 🚀 Recommended Path: Progressive Implementation

### Phase 1: Host-Owned (MVP - 2-3 weeks)
```
Goal: Get 4 friends playing together ASAP

✓ One player hosts on their PC
✓ Basic WebSocket server
✓ 4 players, real-time movement
✓ Chat system
✓ Basic combat
✓ No persistence (session-based)

Success = "This is fun, we played for 2 hours!"
```

### Phase 2: Dedicated Server Support (4-6 weeks)
```
Goal: Allow community servers

✓ Same server code, dedicated mode
✓ Save/load dungeon state
✓ Multiple sessions on one server
✓ Basic persistence (resume dungeon)
✓ Server browser (list of public servers)

Success = "I'm running a public server, join us!"
```

### Phase 3: Enhanced Persistence (8-10 weeks)
```
Goal: Persistent world features

✓ Database integration (SQLite → PostgreSQL)
✓ Player accounts
✓ Inventory persistence
✓ Legacy Vault (per account)
✓ Basic trading system

Success = "I can log in anytime and my stuff is there"
```

### Phase 4: MMO Features (12-20 weeks)
```
Goal: True persistent world

✓ Hub town
✓ Multiple simultaneous parties
✓ Global chat, guilds
✓ Economy/market
✓ World bosses
✓ Leaderboards

Success = "This feels like a real MMO!"
```

**Key Insight:** Each phase is playable and fun on its own!

---

## 🎮 Real-World Examples

### Similar Games for Reference

**Text-Based MMOs (MUDs):**
- **Achaea, Aetolia, Lusternia** - Persistent worlds, thousands of players
- **BatMUD** - 30+ years old, still running
- Key learning: Text MMOs can build dedicated communities

**Modern Terminal Multiplayer:**
- **SSH games** (e.g., nethack.alt.org)
- **tty-share** collaborative sessions
- Proves demand for terminal-based multiplayer

**Roguelike Multiplayer:**
- **Crawl (DCSS)** - Has online play via SSH
- **ToME** - Had multiplayer briefly
- Brogue would be first with true co-op + class system

**What Makes Us Unique:**
- ✅ Real-time co-op (not turn-based)
- ✅ Class synergies (tank/DPS/heal)
- ✅ SWG-inspired ore system
- ✅ Terminal-based but modern networking
- ✅ Legacy system (meta-progression)

---

## 💰 Monetization (If Going MMO Route)

### Free-to-Play with Cosmetics (Ethical)

**Free:**
- Full game access
- All classes
- All gameplay features

**Premium ($5/month or one-time $30):**
- Cosmetic @ symbols (⚔️ 🛡️ 🏹 ✨)
- Custom colors (rainbow @, gold @)
- Title prefixes "[Legendary] PlayerName"
- Guild emblems
- No gameplay advantages!

### Community Funded

**Patreon/Ko-fi:**
- Server costs ($40/mo)
- Development time
- Supporters get cosmetics
- Public dashboard (where money goes)

### Self-Hosted (No Monetization)

**Open source:**
- Anyone can run a server
- Official server is one of many
- Community-driven
- "True spirit of roguelikes"

**Recommendation:** Open source + official server funded by donations

---

## 🔧 Technical Requirements by Option

### Host-Owned
```
Python packages:
  - websockets
  - asyncio
  - textual

Player requirements:
  - Python 3.10+
  - Terminal
  - Internet connection

Host requirements:
  - Port forwarding (or ngrok)
  - Decent internet
```

### Dedicated Server
```
VPS requirements:
  - 1GB RAM (4 players)
  - 2GB RAM (20 players)
  - 1 CPU core
  - 10GB storage
  - Ubuntu 22.04 LTS

Software:
  - Python 3.10+
  - systemd service
  - nginx (optional, for HTTPS)
  - Firewall configured
```

### MMO
```
VPS requirements:
  - 4GB+ RAM
  - 2+ CPU cores
  - 50GB+ storage
  - Database (PostgreSQL)

Software:
  - Python 3.10+
  - PostgreSQL 14+
  - Redis (caching)
  - nginx + certbot (HTTPS)
  - Monitoring (Prometheus, Grafana)
  - Backup system

Additional:
  - Admin tools
  - Moderation system
  - Anti-cheat
  - Rate limiting
  - DDoS protection
```

---

## ❓ Key Decision Questions

### 1. Vision: What's the end goal?

**A) Casual fun with friends**
→ Host-owned is perfect

**B) Small community (50-100 players)**
→ Dedicated server

**C) Large persistent world**
→ MMO architecture

### 2. Resources: What can we commit?

**Time:**
- 2-3 weeks → Host-owned
- 2-3 months → Dedicated
- 6+ months → MMO

**Money:**
- $0 → Host-owned
- $5-20/mo → Dedicated
- $50+/mo → MMO

**Team:**
- Solo dev → Start with host-owned
- 2-3 people → Can tackle dedicated/MMO

### 3. Community: Who's the audience?

**Just friends:**
→ Host-owned

**Terminal enthusiasts:**
→ Dedicated server (community builds)

**Broader gaming audience:**
→ MMO (needs polish, marketing)

### 4. Control: Who runs servers?

**Want full control:**
→ Host-owned (each player controls their game)

**Open to community servers:**
→ Dedicated (anyone can host)

**Official central server:**
→ MMO (we control it all)

---

## 🎯 My Recommendation

**Start with Hybrid: Host-Owned + Dedicated Server Support**

**Phase 1 (Now):**
Build host-owned mode to prove the concept is fun. Get friends playing in 2-3 weeks.

**Phase 2 (After validation):**
Add dedicated server support using the same codebase. Let community run servers.

**Phase 3 (If successful):**
Add persistence features progressively. Build toward MMO if there's demand.

**Why This Works:**
1. ✅ Fast to market (host-owned is simple)
2. ✅ Validates fun before big investment
3. ✅ Scales naturally with demand
4. ✅ Can go MMO later if it takes off
5. ✅ Community can help (run servers, test, feedback)

**The Key Question:**
> "Are we building a fun game for friends, or the next terminal-based MMO?"

Both are valid! But start small, prove it's fun, then scale up.

---

## 🚀 Immediate Next Steps

**To Decide:**
1. What's your vision? (Friends vs Community vs MMO)
2. Time commitment? (Weeks vs Months)
3. Budget for hosting? ($0 vs $5-20 vs $50+)

**To Build (Prototype):**
1. Simple WebSocket server (host-owned)
2. 2-player connection test
3. Shared map rendering
4. Basic chat
5. **Validate it's fun!**

Then scale up based on what works.

---

**Bottom Line:**

**Host-Owned** = Fast, free, fun with friends
**Dedicated** = Community servers, persistence
**MMO** = Persistent world, economy, huge scope

**My vote:** Start with host-owned + add dedicated support → Build toward MMO if it's awesome!

The technology decisions are reversible, but time investment isn't. Prototype fast, validate fun, then commit to bigger vision.

**Want to start with a simple host-owned prototype this session?** 🎮
