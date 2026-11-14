# Veinborn Architecture Documentation

**Last Updated:** 2026-04-17
**Current Phase:** Single-player feature-complete; multiplayer playable in the TUI (one engine, intents in, snapshots out), awaiting its first human playtest

> ⚠️ **Stale references ahead.** References below to `/docs/future-multiplayer/` are defunct — that directory was archived out of the repo (machine-local, not portable for contributors; see `docs/INDEX.md`). The current, in-repo multiplayer design lives at **`docs/design/MULTIPLAYER_DESIGN_2025.md`**. When following a `/docs/future-multiplayer/...` link, use that file instead. See `docs/PROJECT_REVIEW_2026-04-17.md` for the full audit.

---

## ⚠️ IMPORTANT: MVP Architecture (Not Phase 2)

**This directory contains architecture docs for Veinborn MVP (single-player).**

**What's here:**
- ✅ MVP architecture (simple Python game loop)
- ✅ Development guidelines
- ✅ Optional clean patterns
- ✅ Future planning docs

**What's NOT here:**
- ❌ NATS/messaging (moved to `/docs/future-multiplayer/`) *(archived, not in this repo — see `docs/design/MULTIPLAYER_DESIGN_2025.md`)*
- ❌ Microservices (moved to `/docs/future-multiplayer/`) *(archived, not in this repo — see `docs/design/MULTIPLAYER_DESIGN_2025.md`)*
- ❌ Deployment infrastructure (moved to `/docs/future-multiplayer/`) *(archived, not in this repo — see `docs/design/MULTIPLAYER_DESIGN_2025.md`)*

**If you're looking for Phase 2 (multiplayer):** See `/docs/future-multiplayer/` *(archived, not in this repo — see `docs/design/MULTIPLAYER_DESIGN_2025.md`)*

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

### 4. [EVENTS_ASYNC_OBSERVABILITY_GUIDE.md](EVENTS_ASYNC_OBSERVABILITY_GUIDE.md) ⭐ ESSENTIAL (25 min)
   - Event-driven patterns for MVP (without over-engineering)
   - Async/await with Textual (critical integration patterns)
   - Game state observability & telemetry
   - What to instrument NOW vs later
   - **Read BEFORE starting to code!**

### 5. [CONTENT_SYSTEM.md](CONTENT_SYSTEM.md) (10 min)
   - YAML-based content loading
   - Monster/recipe definitions
   - Data-driven design
   - **Read before adding content**

---

### [AI_ARCHITECTURE.md](AI_ARCHITECTURE.md) (15 min)
   - Monster AI in three layers: engine (perception, morale, speed), tactics, abilities for any actor
   - Status: proposed (ADR-019); work tracked as `VB-47` and children
   - **Read before touching `src/core/systems/ai_system.py` or `src/core/content/ai/`**

---

### [MULTIPLAYER_ARCHITECTURE_PLAN.md](MULTIPLAYER_ARCHITECTURE_PLAN.md) (20 min)
   - One engine for single-player and multiplayer: intents in, per-viewer snapshots out, turn scheduler policy, seats, shared protocol package
   - Status: phases 0-4 built (`VB-88`..`VB-102`); phase 5 open (rejoin `VB-103`, fog of war `VB-105`)
   - **Read before touching `src/server/`, `src/ui/multiplayer_client.py` or the turn/floor loop**

---

## 📋 Optional but Useful

### 6. [BASE_CLASS_ARCHITECTURE.md](BASE_CLASS_ARCHITECTURE.md) (45 min)
   - ✅ **NOW HAS PHASE MARKERS** - Clear MVP vs Phase 2/3 sections
   - Clean base class design (Entity, Action, System)
   - Reduces code duplication
   - Makes mining implementation easier
   - Makes Phase 2 refactor easier
   - **For MVP:** Read sections 1, 3, 4, 8 (skip Components, Events, Context)
   - **Time to implement MVP parts:** 2-3 hours
   - **Verdict:** Recommended but not required for MVP

### 7. [ARCHITECTURAL_ASSESSMENT.md](ARCHITECTURAL_ASSESSMENT.md) (20 min)
   - **NEW**: Consolidated architectural analysis
   - Coupling analysis (tight vs loose coupling patterns)
   - Data-driven vs hardcoded design decisions
   - Extensibility points for scripting integration
   - Architectural strengths and weaknesses
   - **Useful for understanding architectural decisions**

### 8. [RANDOMNESS_ANALYSIS.md](RANDOMNESS_ANALYSIS.md) (15 min)
   - **NEW**: RNG and seeding analysis
   - ⚠️ No seeding system currently implemented
   - Analysis of where `random` is used in the codebase
   - Impact analysis (can't reproduce bugs, replay runs, etc.)
   - Implementation recommendations for future seeding system
   - **Useful for understanding RNG design decisions**

### 9. [../EXTENDING.md](../EXTENDING.md) (10 min)
   - How content plugs into the engine: decorator registries and `src/core/content/`
   - Replaces the old Lua integration plan (removed 2026-11-11, ADR-018 in DECISIONS.md)

### 10. [USING_TIA_AST.md](USING_TIA_AST.md) (30 min)
   - **Practical guide** for using TIA AST tools during development
   - Code quality checking (complexity, security, dependencies)
   - Workflow examples (pre-commit checks, refactoring guidance)
   - **Use for automated code quality**

### 11. [DECISIONS.md](DECISIONS.md) (10 min)
   - Architecture Decision Records (ADR)
   - **Mix of MVP and Phase 2 decisions**
   - Read with caution - some are for Phase 2

---

## What's NOT Here (originally moved to future-multiplayer/, now archived)

These docs (DEVELOPMENT_GUIDELINES.md, LOGGING_OBSERVABILITY.md, MESSAGING_ARCHITECTURE.md,
INFRASTRUCTURE_DEPLOYMENT.md, ADR-010-PODMAN-CONTAINER-TECHNOLOGY.md, EXTENSIBILITY_PATTERNS.md)
covered NATS/microservices/Podman infrastructure that was never built — Phase 2 multiplayer
shipped as a simpler in-process WebSocket server instead (`src/server/`). The
`/docs/future-multiplayer/` directory that held them is archived, not in this repo (see
`docs/INDEX.md`). For the design that actually shipped, see `docs/design/MULTIPLAYER_DESIGN_2025.md`.

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

### Path 3: "I want to know about multiplayer"

1. Read: [MULTIPLAYER_ARCHITECTURE_PLAN.md](MULTIPLAYER_ARCHITECTURE_PLAN.md) → how it is built (one engine, intents, per-viewer snapshots, rounds, seats) and what is left
2. Play it: [../MULTIPLAYER_PLAYTEST.md](../MULTIPLAYER_PLAYTEST.md)
3. Protocol details: `src/server/README.md`; the original vision: `docs/design/MULTIPLAYER_DESIGN_2025.md` (much of it, e.g. NATS/microservices, was never built)

---

## Document Status

| Document | Phase | Status | Use for MVP? |
|----------|-------|--------|--------------|
| 00_ARCHITECTURE_OVERVIEW.md | MVP | ✅ Active | YES - Read first |
| MVP_DEVELOPMENT_GUIDELINES.md | MVP | ✅ Active | YES - Essential (incl. advanced practices) |
| MVP_TESTING_GUIDE.md | MVP | ✅ Active | YES - Essential |
| EVENTS_ASYNC_OBSERVABILITY_GUIDE.md | MVP | ✅ Active | YES - Essential (before coding!) |
| BASE_CLASS_ARCHITECTURE.md | MVP+Future | ⚠️ Optional | Optional - has phase markers |
| CONTENT_SYSTEM.md | MVP | ✅ Active | YES - YAML content |
| ARCHITECTURAL_ASSESSMENT.md | All | ⚠️ Optional | Reference - architectural analysis |
| RANDOMNESS_ANALYSIS.md | All | ⚠️ Optional | Reference - RNG design |
| USING_TIA_AST.md | MVP | ✅ Active | YES - Code quality tools |
| DECISIONS.md | Mixed | ⚠️ Caution | Mix of phases |
| ~~OPERATIONAL_EXCELLENCE_GUIDELINES.md~~ | MVP | ➡️ Consolidated | Merged into MVP_DEVELOPMENT_GUIDELINES.md |
| ~~COMPREHENSIVE_ANALYSIS.md~~ | Archive | ➡️ Extracted | Unique sections in ARCHITECTURAL_ASSESSMENT.md |
| ~~DEVELOPMENT_GUIDELINES.md~~ | Phase 2 | ➡️ Archived | Not in this repo — see `docs/design/MULTIPLAYER_DESIGN_2025.md` |
| ~~LOGGING_OBSERVABILITY.md~~ | Phase 2 | ➡️ Archived | Not in this repo — see `docs/design/MULTIPLAYER_DESIGN_2025.md` |

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
| Code style & advanced practices | `MVP_DEVELOPMENT_GUIDELINES.md` | 20 min |
| Testing approach | `MVP_TESTING_GUIDE.md` | 20 min |
| **Events/Async/Observability** | `EVENTS_ASYNC_OBSERVABILITY_GUIDE.md` | 25 min |
| YAML content | `CONTENT_SYSTEM.md` | 10 min |
| Code quality tools | `USING_TIA_AST.md` | 15 min |
| Architectural analysis | `ARCHITECTURAL_ASSESSMENT.md` | 20 min |
| RNG design | `RANDOMNESS_ANALYSIS.md` | 15 min |

### For Phase 2 (multiplayer — shipped, WebSocket-based, not the NATS/microservices design below):
| Need | Document | Status |
|------|----------|--------|
| Multiplayer architecture (what shipped) | `docs/design/MULTIPLAYER_DESIGN_2025.md` | ✅ Current |
| NATS setup | ~~`/docs/future-multiplayer/VEINBORN_NATS_INFRASTRUCTURE.md`~~ | Archived, not in this repo — this design was superseded by the simpler WebSocket server |
| Microservices | ~~`/docs/future-multiplayer/VEINBORN_MICROSERVICE_ARCHITECTURE.md`~~ | Archived, not in this repo — this design was superseded by the simpler WebSocket server |

---

## Common Pitfalls

### ❌ DON'T: Implement full architecture from BASE_CLASS_ARCHITECTURE.md

**Problem:** The doc shows event-driven, message-based patterns.

**For MVP:** Use simpler version:
- Simple base classes (Entity, maybe Action)
- Direct function calls (not events)
- No NATS, no scripting language

**When to use full version:** Phase 2 refactor (8-12 weeks out)

**Skip for now:**
- Everything in `/docs/future-multiplayer/` (Phase 2) *(archived, not in this repo — see `docs/design/MULTIPLAYER_DESIGN_2025.md`)*

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

**Last reviewed:** 2026-01-13

**Changes in this update (2026-01-13 consolidation):**
- ✅ **RESTORED**: `RANDOMNESS_ANALYSIS.md` from archive (RNG and seeding analysis - critical missing doc)
- ✅ **NEW**: Created `ARCHITECTURAL_ASSESSMENT.md` (extracted unique sections from archived COMPREHENSIVE_ANALYSIS.md)
- ✅ **CONSOLIDATED**: Merged `OPERATIONAL_EXCELLENCE_GUIDELINES.md` → `MVP_DEVELOPMENT_GUIDELINES.md` (added "Advanced Development Practices" section)
- ✅ Updated architecture README to reflect consolidation (15→17 files)
- ✅ Removed references to archived `OPERATIONAL_EXCELLENCE_GUIDELINES.md`
- ✅ Updated all cross-references and file paths

**Previous changes (2025-10-24):**
- ✅ Created `EVENTS_ASYNC_OBSERVABILITY_GUIDE.md` (event patterns, async/await with Textual, game telemetry)
- ✅ Created `OPERATIONAL_EXCELLENCE_GUIDELINES.md` (small methods, logging, error handling, performance)
- ✅ Moved `DEVELOPMENT_GUIDELINES.md` → `/future-multiplayer/` (Phase 2 infrastructure) *(archived, not in this repo — see `docs/design/MULTIPLAYER_DESIGN_2025.md`)*
- ✅ Moved `LOGGING_OBSERVABILITY.md` → `/future-multiplayer/` (Phase 2 observability) *(archived, not in this repo — see `docs/design/MULTIPLAYER_DESIGN_2025.md`)*
- ✅ Created `MVP_DEVELOPMENT_GUIDELINES.md` (simple Python, pytest)
- ✅ Created `MVP_TESTING_GUIDE.md` (unit tests, TDD, manual testing)
- ✅ Added phase markers to `BASE_CLASS_ARCHITECTURE.md` (clear MVP vs Phase 2/3 sections)

**Next review:** When starting Phase 2 (after MVP complete)
