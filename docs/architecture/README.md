# Brogue Architecture Documentation

**Last Updated:** 2025-10-24
**Current Phase:** MVP (Single-Player)

---

## ⚠️ IMPORTANT: MVP Architecture (Not Phase 2)

**This directory contains architecture docs for Brogue MVP (single-player).**

**What's here:**
- ✅ MVP architecture (simple Python game loop)
- ✅ Development guidelines
- ✅ Optional clean patterns
- ✅ Future planning docs

**What's NOT here:**
- ❌ NATS/messaging (moved to `/docs/future-multiplayer/`)
- ❌ Microservices (moved to `/docs/future-multiplayer/`)
- ❌ Deployment infrastructure (moved to `/docs/future-multiplayer/`)

**If you're looking for Phase 2 (multiplayer):** See `/docs/future-multiplayer/`

---

## 📖 Start Here for MVP Implementation

**New developer? Read in this order:**

### 1. [00_ARCHITECTURE_OVERVIEW.md](00_ARCHITECTURE_OVERVIEW.md) ⭐ START HERE (20 min)
   - MVP architecture (simple Python game loop)
   - Core systems explained (game state, entities, map generation)
   - How to add new features (mining, crafting)
   - Testing strategy for MVP
   - **Read this first!**

### 2. [MVP_DEVELOPMENT_GUIDELINES.md](MVP_DEVELOPMENT_GUIDELINES.md) ⭐ ESSENTIAL (15 min)
   - Code style and standards for MVP
   - Technology stack (simple Python, pytest)
   - Git workflow
   - Python best practices
   - **Follow these guidelines**

### 3. [MVP_TESTING_GUIDE.md](MVP_TESTING_GUIDE.md) ⭐ ESSENTIAL (20 min)
   - Unit testing with pytest
   - Integration testing workflows
   - Test-Driven Development (TDD)
   - Manual playtesting checklist
   - **Read before writing tests**

### 4. [OPERATIONAL_EXCELLENCE_GUIDELINES.md](OPERATIONAL_EXCELLENCE_GUIDELINES.md) ⭐ ESSENTIAL (30 min)
   - Small methods & single responsibility
   - Comprehensive logging architecture
   - Error handling patterns
   - Performance guidelines
   - Configuration management
   - **Read for operational best practices**

### 5. [EVENTS_ASYNC_OBSERVABILITY_GUIDE.md](EVENTS_ASYNC_OBSERVABILITY_GUIDE.md) ⭐ ESSENTIAL (25 min)
   - Event-driven patterns for MVP (without over-engineering)
   - Async/await with Textual (critical integration patterns)
   - Game state observability & telemetry
   - What to instrument NOW vs later
   - **Read BEFORE starting to code!**

### 6. [CONTENT_SYSTEM.md](CONTENT_SYSTEM.md) (10 min)
   - YAML-based content loading
   - Monster/recipe definitions
   - Data-driven design
   - **Read before adding content**

---

## 📋 Optional but Useful

### 7. [BASE_CLASS_ARCHITECTURE.md](BASE_CLASS_ARCHITECTURE.md) (45 min)
   - ✅ **NOW HAS PHASE MARKERS** - Clear MVP vs Phase 2/3 sections
   - Clean base class design (Entity, Action, System)
   - Reduces code duplication
   - Makes mining implementation easier
   - Makes Phase 2 refactor easier
   - **For MVP:** Read sections 1, 3, 4, 8 (skip Components, Events, Context)
   - **Time to implement MVP parts:** 2-3 hours
   - **Verdict:** Recommended but not required for MVP

### 8. [LUA_INTEGRATION_STRATEGY.md](LUA_INTEGRATION_STRATEGY.md) (30 min)
   - **Future planning only** (Phase 3)
   - Decisions to make during MVP (YAML content, clean interfaces)
   - Zero cost now, saves time later
   - **Don't implement Lua yet**, just be aware

### 9. [DECISIONS.md](DECISIONS.md) (10 min)
   - Architecture Decision Records (ADR)
   - **Mix of MVP and Phase 2 decisions**
   - Read with caution - some are for Phase 2

---

## What's NOT Here (Moved to future-multiplayer/)

These docs were moved because they're for Phase 2 (multiplayer):

| Document | New Location | Why Moved |
|----------|--------------|-----------|
| DEVELOPMENT_GUIDELINES.md | `/docs/future-multiplayer/` | NATS, PostgreSQL, microservices (Phase 2) |
| LOGGING_OBSERVABILITY.md | `/docs/future-multiplayer/` | Prometheus, Grafana, ELK stack (Phase 2) |
| MESSAGING_ARCHITECTURE.md | `/docs/future-multiplayer/` | NATS, microservices (Phase 2) |
| INFRASTRUCTURE_DEPLOYMENT.md | `/docs/future-multiplayer/` | Podman, deployment (Phase 2) |
| ADR-010-PODMAN-CONTAINER-TECHNOLOGY.md | `/docs/future-multiplayer/` | Container tech (Phase 2) |
| EXTENSIBILITY_PATTERNS.md | `/docs/future-multiplayer/` | Plugin systems, event bus (Phase 2) |

**MVP uses simple Python game loop, not message-based architecture.**

**For MVP development guidelines:** See `MVP_DEVELOPMENT_GUIDELINES.md` (simple Python, pytest)

---

## Reading Paths

### Path 1: "I want to implement mining system NOW" (Start here!)

1. Read: `00_ARCHITECTURE_OVERVIEW.md` → Focus on "Adding New Systems" section
2. Read: `/docs/MVP_ROADMAP.md` → Week 1-2 tasks (detailed breakdown)
3. Read: `/docs/MVP_CURRENT_FOCUS.md` → Implementation hub
4. Read: `MVP_DEVELOPMENT_GUIDELINES.md` → Code style and testing
5. Optional: `BASE_CLASS_ARCHITECTURE.md` → If you want clean base classes (MVP sections only)
6. **Start coding** in `src/core/`

**Time:** 1-2 hours reading, then implement

### Path 2: "I want to understand the architecture" (Architecture overview)

1. Read: `00_ARCHITECTURE_OVERVIEW.md` → Complete overview of MVP
2. Read: `MVP_DEVELOPMENT_GUIDELINES.md` → Code standards for MVP
3. Read: `MVP_TESTING_GUIDE.md` → Testing approach
4. Read: `CONTENT_SYSTEM.md` → YAML content loading
5. Skim: `BASE_CLASS_ARCHITECTURE.md` → Optional patterns (MVP sections)

**Time:** 2-3 hours reading

### Path 3: "I want to know about multiplayer" (Future planning)

1. **STOP!** → Don't implement Phase 2 yet!
2. Read: `/docs/future-multiplayer/README.md` → Overview of Phase 2
3. Understand: Phase 2 comes AFTER MVP complete (8-12 weeks)
4. **Go back to implementing MVP** → Focus on current work

**Time:** Don't spend too much time here, focus on MVP

---

## Document Status

| Document | Phase | Status | Use for MVP? |
|----------|-------|--------|--------------|
| 00_ARCHITECTURE_OVERVIEW.md | MVP | ✅ Active | YES - Read first |
| MVP_DEVELOPMENT_GUIDELINES.md | MVP | ✅ Active | YES - Essential |
| MVP_TESTING_GUIDE.md | MVP | ✅ Active | YES - Essential |
| OPERATIONAL_EXCELLENCE_GUIDELINES.md | MVP | ✅ Active | YES - Essential |
| EVENTS_ASYNC_OBSERVABILITY_GUIDE.md | MVP | ✅ Active | YES - Essential (before coding!) |
| BASE_CLASS_ARCHITECTURE.md | MVP+Future | ⚠️ Optional | Optional - has phase markers |
| CONTENT_SYSTEM.md | MVP | ✅ Active | YES - YAML content |
| LUA_INTEGRATION_STRATEGY.md | Phase 3 | 📋 Planning | Awareness only |
| DECISIONS.md | Mixed | ⚠️ Caution | Mix of phases |
| ~~DEVELOPMENT_GUIDELINES.md~~ | Phase 2 | ➡️ Moved | In /future-multiplayer/ |
| ~~LOGGING_OBSERVABILITY.md~~ | Phase 2 | ➡️ Moved | In /future-multiplayer/ |

**Legend:**
- ✅ Active - Read and use for MVP
- ⚠️ Optional - Useful but not required
- ⚠️ Simplify - Use simpler version for MVP
- ⚠️ Caution - Contains Phase 2 info
- 📋 Planning - Future phase, don't implement

---

## Quick Reference

### For MVP Implementation:
| Need | Document | Time |
|------|----------|------|
| Architecture overview | `00_ARCHITECTURE_OVERVIEW.md` | 20 min |
| What to build next | `/docs/MVP_ROADMAP.md` | 10 min |
| How to start coding | `/docs/MVP_CURRENT_FOCUS.md` | 15 min |
| Code style | `MVP_DEVELOPMENT_GUIDELINES.md` | 15 min |
| Testing approach | `MVP_TESTING_GUIDE.md` | 20 min |
| Operational excellence | `OPERATIONAL_EXCELLENCE_GUIDELINES.md` | 30 min |
| **Events/Async/Observability** | `EVENTS_ASYNC_OBSERVABILITY_GUIDE.md` | 25 min |
| YAML content | `CONTENT_SYSTEM.md` | 10 min |

### For Phase 2 (Future):
| Need | Document | When |
|------|----------|------|
| Multiplayer architecture | `/docs/future-multiplayer/` | After MVP complete |
| NATS setup | `/docs/future-multiplayer/BROGUE_NATS_INFRASTRUCTURE.md` | Phase 2 only |
| Microservices | `/docs/future-multiplayer/BROGUE_MICROSERVICE_ARCHITECTURE.md` | Phase 2 only |

---

## Common Pitfalls

### ❌ DON'T: Implement full architecture from BASE_CLASS_ARCHITECTURE.md

**Problem:** The doc shows event-driven, message-based patterns.

**For MVP:** Use simpler version:
- Simple base classes (Entity, maybe Action)
- Direct function calls (not events)
- No NATS, no event bus, no Lua

**When to use full version:** Phase 2 refactor (8-12 weeks out)

### ❌ DON'T: Spend too much time on LUA_INTEGRATION_STRATEGY.md

**Problem:** It's 25KB of Phase 3 planning.

**For MVP:** Just be aware:
1. Use YAML for content (not hardcoded)
2. Keep interfaces clean (makes Lua easier later)

**When to implement Lua:** Phase 3 (after multiplayer)

### ❌ DON'T: Implement Phase 2 infrastructure

**Problem:** Phase 2 docs (now in `/docs/future-multiplayer/`) describe NATS, PostgreSQL, Prometheus, Grafana.

**For MVP:** Use simple approaches from `MVP_DEVELOPMENT_GUIDELINES.md`:
```python
# Simple logging
import logging
logger = logging.getLogger(__name__)
logger.info("Player mined ore: %s", ore.ore_type)
```

**When to add infrastructure:** Phase 2 (distributed systems)

### ❌ DON'T: Read docs in `/docs/future-multiplayer/` too much

**Problem:** Tempting to implement Phase 2 architecture.

**For MVP:** Stay focused on simple game loop.

**When to read:** After MVP is complete and fun

---

## Questions?

### "Which docs should I read for MVP?"

**Essential (must read):**
1. `00_ARCHITECTURE_OVERVIEW.md` - How MVP works
2. `MVP_DEVELOPMENT_GUIDELINES.md` - Code style and standards
3. `MVP_TESTING_GUIDE.md` - Testing approach
4. `OPERATIONAL_EXCELLENCE_GUIDELINES.md` - Best practices for maintainability
5. **`EVENTS_ASYNC_OBSERVABILITY_GUIDE.md` - Events, async/await, telemetry (READ BEFORE CODING!)**
6. `/docs/MVP_ROADMAP.md` - What to build
7. `/docs/MVP_CURRENT_FOCUS.md` - Implementation hub

**Optional (read if interested):**
- `BASE_CLASS_ARCHITECTURE.md` - Clean patterns (MVP sections only)
- `CONTENT_SYSTEM.md` - YAML content

**Skip for now:**
- Everything in `/docs/future-multiplayer/` (Phase 2)
- Most of `LUA_INTEGRATION_STRATEGY.md` (Phase 3)

### "Should I implement Entity base class?"

**Optional, but recommended:**

**Benefits:**
- Less code duplication (Player, Monster, OreVein share code)
- Cleaner architecture
- Easier Phase 2 refactor

**Cost:** 2-3 hours to implement

**Verdict:** Do it in Week 1 if you have time, or Week 3 during cleanup.

**See:** `BASE_CLASS_ARCHITECTURE.md` for details

### "What's the difference between MVP and Phase 2?"

| Aspect | MVP (Now) | Phase 2 (Future) |
|--------|-----------|------------------|
| Game mode | Single-player | 4-player co-op |
| Architecture | Simple Python loop | Event-driven, NATS |
| Communication | Function calls | Messages |
| Deployment | Local Python script | Microservices, Podman |
| State | In-memory | Distributed |
| Complexity | Simple | Complex |

**MVP is intentionally simple!** Add complexity in Phase 2 when needed for multiplayer.

---

## Next Steps

1. **New to project?** → Read `/docs/START_HERE.md`
2. **Ready to implement?** → Read `00_ARCHITECTURE_OVERVIEW.md`
3. **Pick a task?** → Read `/docs/MVP_CURRENT_FOCUS.md`
4. **Start coding?** → Read `/docs/MVP_ROADMAP.md` (Week 1-2 tasks)

**Remember:** MVP = simple Python game, Phase 2 = multiplayer complexity

---

**Last reviewed:** 2025-10-24

**Changes in this update:**
- ✅ **NEW**: Created `EVENTS_ASYNC_OBSERVABILITY_GUIDE.md` (event patterns, async/await with Textual, game telemetry)
- ✅ **NEW**: Created `OPERATIONAL_EXCELLENCE_GUIDELINES.md` (small methods, logging, error handling, performance)
- ✅ Moved `DEVELOPMENT_GUIDELINES.md` → `/future-multiplayer/` (Phase 2 infrastructure)
- ✅ Moved `LOGGING_OBSERVABILITY.md` → `/future-multiplayer/` (Phase 2 observability)
- ✅ Created `MVP_DEVELOPMENT_GUIDELINES.md` (simple Python, pytest)
- ✅ Created `MVP_TESTING_GUIDE.md` (unit tests, TDD, manual testing)
- ✅ Added phase markers to `BASE_CLASS_ARCHITECTURE.md` (clear MVP vs Phase 2/3 sections)
- ✅ Updated all cross-references and file paths

**Next review:** When starting Phase 2 (after MVP complete)
