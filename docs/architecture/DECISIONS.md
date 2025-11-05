# Brogue Architecture Decision Records

**Last Updated**: 2025-10-23
**Purpose**: Track major architectural decisions, their rationale, and current status

---

## How to Use This Document

- **Status Key**: ✅ Implemented | 📋 Planned | 🔄 In Progress | ❌ Rejected
- **Docs**: Links to detailed documentation
- **Date**: When decision was made

---

## Phase 1 (MVP) Decisions

### ADR-001: Textual UI Framework
**Date**: 2025-10-14
**Status**: ✅ Implemented
**Decision**: Use Textual framework for terminal UI
**Rationale**: Modern widget-based architecture, better than curses/Blessed, active development
**Docs**: `docs/UI_FRAMEWORK.md`
**Impact**: Clean, composable UI components working in production

---

### ADR-002: Entity Base Class Pattern
**Date**: 2025-10-23
**Status**: 📋 Planned (Week 1-2)
**Decision**: Unified Entity base for Player/Monster/Items/OreVeins
**Rationale**:
- Code reuse (take_damage, heal, move methods common to all)
- Lua-ready (uniform API surface)
- Multiplayer serialization (single to_dict/from_dict)
- Testing (easy mocking)

**Docs**: `docs/architecture/BASE_CLASS_ARCHITECTURE.md`
**Impact**: Foundation for clean, extensible architecture

---

### ADR-003: Action Command Pattern
**Date**: 2025-10-23
**Status**: 📋 Planned (Week 1-2)
**Decision**: Serializable Action objects for player/monster actions
**Rationale**:
- Testable (create actions directly)
- Replayable (save action history)
- Multiplayer-ready (serialize to NATS)
- Lua-compatible (scripts return Actions)

**Docs**: `docs/architecture/BASE_CLASS_ARCHITECTURE.md`
**Impact**: Enables multiplayer, testing, Lua integration

---

### ADR-004: System Architecture Pattern
**Date**: 2025-10-23
**Status**: 📋 Planned (Week 1-3)
**Decision**: Game logic processors as independent System classes
**Rationale**:
- Separation of concerns (CombatSystem, AISystem, MiningSystem)
- Testable (mock dependencies)
- Pluggable (enable/disable systems)
- Lua API surface (systems callable from scripts)

**Docs**: `docs/architecture/BASE_CLASS_ARCHITECTURE.md`
**Impact**: Clean architecture, easier maintenance

---

### ADR-005: Lua-Ready Architecture
**Date**: 2025-10-23
**Status**: 📋 Planned (implement during MVP Weeks 1-4)
**Decision**: Design 5 architectural patterns now for future Lua integration
**Rationale**:
- Zero cost now (good design regardless)
- Saves 3-4 weeks later (no refactoring needed)
- Better architecture even without Lua

**Key Decisions**:
1. YAML data files (Week 3)
2. System classes (Week 1-2)
3. Event bus (Week 3-4)
4. Utility functions (ongoing)
5. Schema versioning (Week 3)

**Docs**: `docs/architecture/LUA_INTEGRATION_STRATEGY.md`
**Impact**: Future-proof architecture, easier Lua integration in Phase 3

---

### ADR-006: YAML Data Files
**Date**: 2025-10-23 (planned for Week 3)
**Status**: 📋 Planned
**Decision**: Move content (items, monsters, recipes) to YAML
**Rationale**:
- Data-driven design
- Designer-friendly (no code changes)
- Lua-ready (add script path field later)
- Hot-reload support

**Docs**: `docs/MVP_ROADMAP.md` Week 3, `docs/architecture/CONTENT_SYSTEM.md`
**Impact**: Faster iteration, designer empowerment

---

### ADR-007: Event Bus Architecture
**Date**: 2025-10-23 (planned for Week 3-4)
**Status**: 📋 Planned
**Decision**: Internal event bus for decoupled communication
**Rationale**:
- Decoupling (publishers don't know subscribers)
- Extensibility (add achievements without touching core)
- Lua hooks (scripts subscribe to events)
- Multiplayer-ready (needed for Phase 2 anyway)

**Docs**: `docs/architecture/BASE_CLASS_ARCHITECTURE.md`
**Impact**: Plugin architecture, easier feature additions

---

### ADR-008: GameContext Facade
**Date**: 2025-10-23 (planned for Week 3-4)
**Status**: 📋 Planned
**Decision**: Controlled API surface for game state access
**Rationale**:
- Safe (no direct state manipulation)
- Lua API surface (context becomes scripting API)
- Testable (mock context)
- Permission checks (for multiplayer)

**Docs**: `docs/architecture/BASE_CLASS_ARCHITECTURE.md`
**Impact**: Clean API, easier Lua integration, better testing

---

### ADR-009: Containers from Day 1
**Date**: 2025-10-23
**Status**: 📋 Planned (MVP Week 1-2)
**Decision**: Use containerization for development environment from the start
**Rationale**:
- Consistent environment ("works on my machine" eliminated)
- Phase 2 transition trivial (already containerized)
- Easy onboarding
- Zero migration pain

**See**: ADR-010 for specific container technology choice (Podman)
**Docs**: `docs/architecture/INFRASTRUCTURE_DEPLOYMENT.md`
**Impact**: 2-3 hours upfront, saves 2-3 days during Phase 2 migration

---

### ADR-010: Podman Container Technology
**Date**: 2025-10-23
**Status**: ✅ Accepted
**Decision**: Use Podman over Docker for all containerization
**Rationale**:
- **Security**: Rootless by default, no root daemon to attack
- **Pod architecture**: Native pod concept maps perfectly to microservices
- **Kubernetes migration**: `podman generate kube` creates K8s YAML seamlessly
- **systemd integration**: `podman generate systemd` for production deployment
- **Docker-compatible**: Same commands, same Dockerfiles, easy transition

**Key Benefits**:
1. Rootless containers limit attack surface (critical for game servers)
2. Pods group related services (game + metrics + logs)
3. Zero refactoring: Dev pods → systemd → Kubernetes
4. Native systemd integration (pods as systemd units)
5. No daemon = lower overhead, better security

**Docs**: `docs/future-multiplayer/INFRASTRUCTURE_DEPLOYMENT.md`, `docs/future-multiplayer/ADR-010-PODMAN-CONTAINER-TECHNOLOGY.md`
**Impact**: Better security, seamless K8s migration, cleaner production deployment

---

## Phase 2 (Multiplayer) Decisions

### ADR-011: NATS Messaging Infrastructure
**Date**: 2025-10-21
**Status**: 📋 Designed
**Decision**: Use NATS for service-to-service messaging
**Rationale**:
- Fast pub/sub performance
- HA clustering built-in
- JetStream for persistence
- No Zookeeper dependency (vs Kafka)

**Docs**: `docs/future-multiplayer/BROGUE_NATS_INFRASTRUCTURE.md`, `docs/future-multiplayer/MESSAGING_ARCHITECTURE.md`
**Impact**: Scalable, reliable messaging layer

---

### ADR-012: Server-Authoritative Architecture
**Date**: 2025-10-21
**Status**: 📋 Designed
**Decision**: Server owns all game logic, clients render only
**Rationale**:
- Anti-cheat (impossible to hack)
- Multiple client types (terminal, web, mobile)
- Replay support (server logs all actions)
- Easier testing (deterministic state)

**Docs**: `docs/future-multiplayer/BROGUE_SERVER_ARCHITECTURE.md`, `docs/future-multiplayer/BROGUE_MICROSERVICE_ARCHITECTURE.md`
**Impact**: Secure, flexible architecture

---

### ADR-013: PostgreSQL Database
**Date**: 2025-10-22
**Status**: 📋 Designed
**Decision**: PostgreSQL over MongoDB/MySQL
**Rationale**:
- ACID guarantees (critical for trades, inventory)
- JSONB support (flexible schema)
- asyncpg performance (3x psycopg2)
- Better tooling/monitoring

**Docs**: `docs/future-multiplayer/BROGUE_MICROSERVICE_ARCHITECTURE.md`
**Impact**: Reliable, performant persistence

---

### ADR-014: Pydantic for Messages
**Date**: 2025-10-22
**Status**: 📋 Designed
**Decision**: Use Pydantic v2 for all messages
**Rationale**:
- Runtime validation (catches bugs)
- JSON serialization built-in
- Settings from env vars (12-factor)
- Better error messages

**Docs**: `docs/future-multiplayer/MESSAGING_ARCHITECTURE.md`, `docs/future-multiplayer/BROGUE_MESSAGE_TAXONOMY.md`
**Impact**: Type-safe messaging, better debugging

---

### ADR-015: Diablo-Style Instances
**Date**: 2025-10-21
**Status**: 📋 Designed
**Decision**: Private dungeon instances, not persistent MMO
**Rationale**:
- Simpler development (4-8 weeks vs 6+ months)
- Cheaper hosting ($0-20/mo vs $40+/mo)
- No griefing (invite-only)
- Personal loot (no competition)

**Docs**: `docs/future-multiplayer/BROGUE_MUD_AND_INSTANCES.md`
**Impact**: Faster development, better player experience

---

### ADR-016: Simultaneous Turn Allocation
**Date**: 2025-10-21
**Status**: 📋 Designed
**Decision**: "4 actions per round, anyone can take them"
**Rationale**:
- Simple rule, infinite strategic depth
- Cooperative gameplay (healer takes 4 turns)
- Competitive gameplay (race to kill)
- Specialist gameplay (rogue scouts 4 moves)

**Docs**: `docs/future-multiplayer/BROGUE_TURN_SYSTEM.md`
**Impact**: Unique, compelling multiplayer mechanics

---

### ADR-017: WebSocket Client Protocol
**Date**: 2025-10-21
**Status**: 📋 Designed
**Decision**: WebSocket for client-server communication
**Rationale**:
- Real-time bidirectional
- Browser-compatible
- Good Python support (websockets library)
- Industry standard

**Docs**: `docs/future-multiplayer/BROGUE_MICROSERVICE_ARCHITECTURE.md`
**Impact**: Web client support, real-time gameplay

---

## Rejected Decisions

### ADR-R01: Emotional Story Progression
**Date**: 2025-10-22
**Status**: ❌ Rejected
**Decision**: Focus on mechanical gameplay, not narrative progression
**Rationale**: Better fit for roguelike genre, replayability focus
**Docs**: `docs/Archive/` (old design)
**Why Rejected**: Conflicted with roguelike replayability, too complex

---

### ADR-R02: 12-Property Material System
**Date**: 2025-10-22
**Status**: ❌ Rejected
**Decision**: Use 5 properties, not 12
**Rationale**: Simpler, easier to balance, still interesting
**Docs**: `docs/BROGUE_CONSOLIDATED_DESIGN.md`
**Why Rejected**: Over-engineered, hard to balance, diminishing returns

---

### ADR-R03: Persistent MMO World
**Date**: 2025-10-21
**Status**: ❌ Rejected
**Decision**: Use Diablo instances, not shared MMO world
**Rationale**: Development cost, loot competition, griefing concerns
**Docs**: `docs/future-multiplayer/BROGUE_MUD_AND_INSTANCES.md`
**Why Rejected**: Too expensive, too complex, worse player experience

---

### ADR-R04: Essence Mastery System
**Date**: 2025-10-22
**Status**: ❌ Rejected
**Decision**: Focus on ore properties, not essence collection
**Rationale**: Ore hunting provides same dopamine hit with less complexity
**Docs**: `docs/Archive/` (old design)
**Why Rejected**: Over-complex, conflicted with core mining loop

---

## Decision Process

### How to Add a New ADR

1. **Identify the decision**: Major architectural choice needed
2. **Document alternatives**: What are the options?
3. **Choose rationale**: Why this option over others?
4. **Add to this doc**: Create new ADR entry
5. **Link documentation**: Reference detailed docs
6. **Update status**: As implementation proceeds

### What Counts as an ADR?

**✅ Record these**:
- Technology choices (frameworks, libraries, databases)
- Architectural patterns (Entity base class, Action pattern)
- Major design decisions (instance-based vs MMO)
- Protocol choices (WebSocket, NATS)

**❌ Don't record these**:
- Bug fixes
- Small refactors
- Content additions (new monsters)
- Minor optimizations

---

## ADR Summary

### Phase 1 (MVP) - 10 Decisions
- **Implemented/Accepted**: 2 (Textual UI, Podman)
- **Planned**: 8 (Entity, Action, System, Lua-ready, YAML, Events, Context, Containers)

### Phase 2 (Multiplayer) - 7 Decisions
- **Designed**: 7 (NATS, Server-authoritative, PostgreSQL, Pydantic, Instances, Turns, WebSocket)

### Rejected - 4 Decisions
- All properly documented with rationale

**Total**: 21 major architectural decisions tracked

---

## Next Review

**When**: After MVP Phase 1 completion (Week 6)
**Focus**: Review implemented decisions, update status
**Add**: Any new decisions made during implementation

---

**Maintained By**: Architecture team
**Updates**: Add when making major architectural decisions
**Format**: Keep concise, link to detailed docs
