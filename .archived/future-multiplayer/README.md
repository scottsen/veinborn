# Brogue Multiplayer Design Documentation

**Created:** Oct 21, 2025
**Session:** icy-temple-1021
**Status:** Design Complete, **NOT CURRENT WORK**
**Type:** 4-Player Co-op Multiplayer Expansion (Phase 2)

---

## ⚠️ IMPORTANT: Phase 2 Documentation - NOT FOR IMMEDIATE IMPLEMENTATION

**This directory contains Phase 2 (multiplayer) architecture.**

**Current phase:** MVP (Single-Player) - See `/docs/START_HERE.md`
**When to implement:** AFTER MVP is complete (8-12 weeks from now)
**Why wait:** MVP needs to be fun first, then add multiplayer

**For current work, see:**
- `/docs/MVP_CURRENT_FOCUS.md` - What to build NOW
- `/docs/MVP_ROADMAP.md` - Week-by-week tasks
- `/docs/architecture/00_ARCHITECTURE_OVERVIEW.md` - MVP architecture

**This documentation is for future planning only. Do not implement yet!**

---

## Overview

This directory contains comprehensive design documentation for Brogue's multiplayer expansion. What started as a simple request for mining mechanics evolved into a complete multiplayer co-op roguelike design combining the best elements of:

- **Roguelikes**: Terminal-based, procedural generation, permadeath
- **MUDs**: Social hub, persistent world elements, player content
- **Diablo**: Instance-based dungeons, personal loot, invite-only co-op
- **Star Wars Galaxies**: Resource hunting with random property spawns

## Design Documents (Read in Order)

### Core Gameplay Systems

1. **[BROGUE_MINING_CRAFTING_DESIGN.md](./BROGUE_MINING_CRAFTING_DESIGN.md)** (650 lines)
   - **Start here** - Foundation of the system
   - Turn-based mining mechanics (3-5 turns, vulnerable while mining)
   - SWG-inspired ore properties (5 stats: hardness, conductivity, malleability, purity, density)
   - Class synergies (Warrior/Mage/Ranger/Healer ore preferences)
   - Crafting formulas and progression
   - Legacy Ore system (meta-progression + "street cred")
   - Resource hunting gameplay loop

2. **[BROGUE_TURN_SYSTEM.md](./BROGUE_TURN_SYSTEM.md)** (900 lines)
   - **The breakthrough** - Simultaneous turn allocation
   - Why round-robin fails (75% waiting time)
   - 4 actions per round, anyone can take them
   - 10 strategic scenarios (healer emergency, race for kill, mining sacrifice)
   - Emergent meta-strategies (healer carry, speedrun, balanced rotation)
   - Boss tactical mode with planning phase
   - UI designs for turn allocation display

3. **[BROGUE_MULTIPLAYER_DESIGN.md](./BROGUE_MULTIPLAYER_DESIGN.md)** (780 lines)
   - Complete feature specification
   - 4-player co-op with colored @ symbols (Red, Blue, Green, Yellow)
   - Class designs (Tank, DPS, Stealth, Healing)
   - Real-time + tactical pause hybrid
   - In-game /chat system
   - Party progression (shared Legacy Vault)
   - Boss fights requiring coordination
   - Network protocol overview

### Architecture & Technical Design

4. **[BROGUE_PROBLEMS_AND_SOLUTIONS.md](./BROGUE_PROBLEMS_AND_SOLUTIONS.md)** (NEW - 350 lines)
   - **Problem-first thinking** - Technology choices justified
   - 7 problem categories: Rendering, Communication, State, Concurrency, Reliability, Deployment, Observability
   - Maps each technology to specific problems (TUI → Textual, Messaging → NATS, Persistence → PostgreSQL)
   - Complete technology stack with rationale
   - Clear status for each solution (Solved, In Design, Future)

5. **[BROGUE_NATS_INFRASTRUCTURE.md](./BROGUE_NATS_INFRASTRUCTURE.md)** (NEW - 900 lines)
   - **Complete NATS guide** - Server setup, Python integration, deployment
   - NATS server installation and configuration
   - Python `nats.py` library patterns (pub/sub, request/reply, queue groups)
   - JetStream for reliable messaging
   - tia-proxy nginx configuration for WebSocket routing
   - SSL/TLS setup with Let's Encrypt
   - Production deployment architecture (clustering, monitoring)
   - Zero-downtime deploy strategies

6. **[BROGUE_MESSAGE_TAXONOMY.md](./BROGUE_MESSAGE_TAXONOMY.md)** (NEW - 1000 lines)
   - **Message classification framework** - All message types categorized
   - 6 message categories: Actions, State Updates, Chat, Critical Events, Service Queries, Work Queues
   - Pydantic models for type safety
   - Message abstractions (BrogueMessage base class, MessageRegistry, MessageBus)
   - Subject naming conventions for NATS
   - Reliability guarantees per message type
   - Complete code examples

7. **[BROGUE_PROXY_ROUTING.md](./BROGUE_PROXY_ROUTING.md)** (NEW - 650 lines)
   - **nginx reverse proxy configuration** - Load balancing, SSL, security
   - Complete nginx configs (dev, staging, production)
   - Load balancing strategies (least_conn, ip_hash, round robin)
   - SSL certificate setup (Let's Encrypt/certbot)
   - Health checks and monitoring
   - Rate limiting and DDoS protection
   - Zero-downtime deployment workflow

8. **[BROGUE_MICROSERVICE_ARCHITECTURE.md](./BROGUE_MICROSERVICE_ARCHITECTURE.md)** (720 lines)
   - **How to build it** - Technical implementation guide
   - Authoritative server (clients are "dumb")
   - 3 microservices: GameState, Connection, Persistence
   - Client-server protocol (JSON over WebSocket)
   - Delta updates (96% bandwidth savings)
   - Security & validation
   - Cheat-proof design

9. **[BROGUE_SERVER_ARCHITECTURE.md](./BROGUE_SERVER_ARCHITECTURE.md)** (580 lines)
   - Deployment options comparison
   - Host-owned vs Dedicated vs MMO models
   - Cost analysis ($0, $5-20/mo, $40+/mo)
   - Docker/Kubernetes deployment
   - Hybrid approach (support both)
   - Progressive implementation path

### MUD-Inspired Features

10. **[BROGUE_MUD_AND_INSTANCES.md](./BROGUE_MUD_AND_INSTANCES.md)** (850 lines)
   - **The pivot** - Why Diablo instances > Persistent MMO
   - MUD research (Achaea 28 years, BatMUD 35 years!)
   - 10 lessons from 30 years of MUD design
   - Diablo instance model (private dungeons, personal loot)
   - Hybrid model: Hub town (persistent) + Dungeon instances (private)
   - Personal loot from shared ore veins (everyone gets their own roll!)
   - Comparison matrix: MUD vs Diablo vs Hybrid

11. **[BROGUE_MUD_CONTENT_CREATION.md](./BROGUE_MUD_CONTENT_CREATION.md)** (1050 lines)
   - Research: How MUDs do player content
   - In-game coding systems (LPC, MOO, softcode)
   - Real examples from active MUDs
   - Security lessons (sandboxing, resource limits)
   - What Brogue could adopt

12. **[BROGUE_YAML_CONTENT_SYSTEM.md](./BROGUE_YAML_CONTENT_SYSTEM.md)** (1100 lines)
   - **Safe player content** - YAML configs instead of scripting
   - Player houses (customize rooms/objects)
   - Dungeon templates (tweak generation parameters)
   - NPC dialogues (conversation trees)
   - Quest system (objectives, rewards)
   - Validation (Pydantic models, server-side checks)
   - Community workshop (upload/download, ratings)
   - Git integration (version control your content!)

**Total:** ~9,530 lines of comprehensive design documentation

---

## Key Design Decisions

### 1. SWG-Style Ore Properties (Not Simple Loot)
- Creates resource hunting mini-game
- Class specialization (warriors want hardness, mages want conductivity)
- Replayability (different spawns each run)
- Dopamine hit when you find perfect ore (98 hardness iron!)

### 2. Simultaneous Turns (Not Round-Robin)
**Simple rule:** "4 actions per round, anyone can take them"

**Creates infinite strategic depth:**
- Cooperative: "Healer, take all 4 turns to mass heal"
- Competitive: "Race you to that goblin!"
- Specialist: "Rogue scouts ahead (4 stealth moves)"
- Emergency: "Everyone hold, mining this Legacy Ore (4 turns)"

**Like Go:** Trivial rules, infinite complexity

### 3. Diablo Instances (Not Persistent MMO)

| Feature | Persistent MMO | Diablo Instances |
|---------|----------------|------------------|
| Development | 6+ months | 4-8 weeks |
| Cost | $40+/month | Free or $5-20 |
| Loot Competition | Fighting over ore | Everyone gets their own! |
| Griefing | Major problem | Invite-only = no griefing |
| Moderation | Critical | Minimal |

**The Killer Feature:** Personal loot from shared ore veins
```
Same ore vein:
  Alice mines → Iron Ore (H:90! Amazing!)
  Bob mines   → Iron Ore (H:45, meh)
  Carol mines → Iron Ore (H:78, good)

Everyone gets their own roll!
```

### 4. YAML Configs (Not In-Game Scripting)
✅ Safe - No code execution
✅ Simple - Human-readable
✅ Validated - Server checks all values
✅ Shareable - Copy/paste, Git, workshop
✅ Git-friendly - Version control works perfectly

**80% of the power, 20% of the risk**

---

## What Makes This Design Unique

**No one has made:**
- Terminal-based 4-player co-op roguelike
- With Diablo-style personal loot instances
- With SWG-inspired ore hunting (random stat spawns)
- With MUD-style social hub (persistent town)
- With roguelite meta-progression (Legacy Ore + street cred)
- With YAML-based player content creation

**Closest comparisons:**
- **DCSS** - Terminal roguelike, but no co-op
- **Diablo** - Instances + loot, but graphical
- **MUDs** - Terminal multiplayer, but not roguelike
- **Hades** - Roguelite progression, but single-player

**This combines the best of all four!**

---

## Implementation Status

### ✅ Complete
- All core systems designed
- Architecture decisions made
- Technical specifications documented
- Open questions identified
- Implementation path clear

### 🔄 Next Steps

**MVP Prototype (Week 1-2):**
1. Simple WebSocket server (host-owned)
2. Create server architecture:
   - `server/game_server.py` - WebSocket server
   - `server/game_state.py` - Authoritative state
   - `client/network.py` - Network layer for Textual
3. Test with 2 players first

**Validation criteria:**
- ✓ 2 players can connect
- ✓ Both see same dungeon
- ✓ Movement synchronized
- ✓ Chat works
- ✓ Clients are "dumb" (server validates everything)

### Open Questions to Resolve

1. **Starting class:** Choose at game start, or develop through play?
2. **Ore visibility:** Visible from adjacent tiles, or only when explored?
3. **Multi-ore crafting:** One ore per item, or combine multiple?
4. **Death mechanics:** Individual death (wait) vs party wipe (all die)?
5. **Voice chat:** In-game, external (Discord), or text only?

---

## Integration with Original Brogue

### Original Game (Single-Player)
- **Theme:** Emotional story about finding your big brother
- **Progression:** Learning through memory and loss
- **Focus:** Narrative-driven, personal journey
- **Location:** `/docs/design/BROGUE_CORE_CONCEPT.md`

### Multiplayer Expansion (This Design)
- **Theme:** Co-op adventure with friends
- **Progression:** Resource hunting, crafting, meta-progression
- **Focus:** Mechanical depth, social play, replayability
- **Can coexist:** Single-player story mode + multiplayer co-op mode

**Both modes can exist in the same game!**

---

## Resources

### Active MUDs (Research)
```bash
# Achaea (modern MUD, great UX)
telnet achaea.com 23

# Aardwolf (complex crafting)
telnet aardwolf.com 23
```

### Technical References
- **Evennia**: https://www.evennia.com/ (Python MUD framework)
- **websockets**: https://websockets.readthedocs.io/ (Python WebSocket library)
- **r/MUD**: Active community, design discussions

---

## Session History

**Session:** icy-temple-1021 (Oct 21, 2025)
**Duration:** ~3 hours
**Outcome:** Complete game design documented

**User Insights That Shaped Design:**
1. "I want mining when we find random piles of ore" → Mining system
2. "I loved Star Wars Galaxies mechanics" → Ore property system
3. "Turns is turns bitches. Mash fast." → Simultaneous turns
4. "Team can let healer take all 4 turns, or race to stab mobs" → Strategic depth discovered
5. "This is a MUD?" → Research existing solutions
6. "Diablo mechanic - my map, invite friends" → Pivoted entire architecture
7. "YAML config" → Safe player content creation

**Full session documentation:**
`/home/scottsen/src/tia/sessions/icy-temple-1021/README.md`

---

## Quick Reference

**Documents by purpose:**
- Getting started? → MINING_CRAFTING_DESIGN.md
- Understanding the breakthrough? → TURN_SYSTEM.md
- **Understanding technology choices?** → **PROBLEMS_AND_SOLUTIONS.md** (NEW)
- **Setting up NATS?** → **NATS_INFRASTRUCTURE.md** (NEW)
- **Designing messages?** → **MESSAGE_TAXONOMY.md** (NEW)
- **Configuring tia-proxy?** → **PROXY_ROUTING.md** (NEW)
- Implementing the prototype? → MICROSERVICE_ARCHITECTURE.md
- Deployment planning? → SERVER_ARCHITECTURE.md
- Feature checklist? → MULTIPLAYER_DESIGN.md
- Player content system? → YAML_CONTENT_SYSTEM.md
- Why this approach? → MUD_AND_INSTANCES.md

**Technology Stack (Oct 22 update):**
- **TUI**: Textual (already implemented)
- **Client ↔ Server**: WebSockets
- **Service ↔ Service**: NATS (pub/sub + JetStream)
- **Database**: PostgreSQL (chosen over MySQL for JSONB, better concurrency)
- **Proxy**: nginx (tia-proxy)
- **Language**: Python 3.10+ (asyncio)

**Design is 100% complete. Infrastructure documented. Ready to code.** 🚀
