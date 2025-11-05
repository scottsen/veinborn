# Brogue Design Archive

**Archived:** 2025-10-22
**Session:** garnet-pigment-1022
**Reason:** Design consolidation - these docs contain conflicting visions or deprecated systems

---

## Why These Docs Were Archived

During design review (garnet-pigment-1022), we identified multiple conflicting visions for Brogue:
- Vision A: Emotional single-player story ("Walking in Big Brother's Footsteps")
- Vision B: Cosmic power fantasy with essence mastery
- Vision C: Multiplayer co-op resource hunter

**Final decision:** Brogue = NetHack + SWG Mining + Multiplayer Co-op (mechanical focus, not emotional story)

These archived docs represent abandoned or conflicting design directions.

---

## Archived Documents

### design/

**BROGUE_CORE_CONCEPT.md**
- **Conflict:** Emotional "Big Brother" story with memory-triggered progression
- **Why archived:** Game is mechanical, not narrative-driven
- **Good ideas:** Brother quest hook (kept simplified), emotional progression (removed)

**COMPREHENSIVE_DESIGN.md**
- **Conflict:** "Deep Dungeons & Destiny" - 15 essence types, reality-shaping endgame
- **Why archived:** Massive scope creep, wrong game concept
- **Good ideas:** Some material concepts (simplified in MINING_CRAFTING_DESIGN.md)

### systems/

**CRAFTING_MATERIALS.md**
- **Conflict:** 12-property material system (Density, Resonance, Balance, Grain, etc.)
- **Why archived:** Duplicate/conflicting with 5-property ore system
- **Current system:** 5 properties (Hardness, Conductivity, Malleability, Purity, Density)

**CHARACTER_PROGRESSION.md**
- **Conflict:** Memory-based skill unlocks, environmental affinities (5 types × 4 levels)
- **Why archived:** Too complex for MVP, conflicts with mechanical focus
- **Good ideas:** Some progression concepts (simplified in Legacy Vault)

### mechanics/

**CORE_MECHANICS.md**
- **Status:** Generic roguelike guidance, mostly outdated
- **Why archived:** Superseded by consolidated design
- **Good ideas:** MVP guidance (incorporated into CONSOLIDATED_DESIGN.md)

### Top-level docs

**DEVELOPMENT_ROADMAP.md**
- **Status:** Outdated timeline and phases
- **Why archived:** New roadmap in CONSOLIDATED_DESIGN.md

**PROJECT_OVERVIEW.md**
- **Status:** Old vision (before consolidation)
- **Why archived:** Replaced by CONSOLIDATED_DESIGN.md

**671d7169-c4f8-8012-95b0-3f125454471e_Brogue Game Design Overview.json**
- **Status:** Unknown JSON artifact
- **Why archived:** Not markdown, unclear purpose

---

## Current Design Docs (Active)

See `/home/scottsen/src/tia/projects/brogue/docs/`:

**Master Design:**
- ✅ **BROGUE_CONSOLIDATED_DESIGN.md** (in session dir, to be moved here)

**Core Systems:**
- ✅ `systems/COMBAT_SYSTEM.md` (kept - core combat mechanics)
- ✅ `multiplayer/BROGUE_MINING_CRAFTING_DESIGN.md` (kept - 5-property ore system)
- ✅ `UI_FRAMEWORK.md` (kept - Textual decision)

**Multiplayer Design:**
- ✅ `multiplayer/BROGUE_TURN_SYSTEM.md` (kept - brilliant simultaneous turns)
- ✅ `multiplayer/BROGUE_MULTIPLAYER_DESIGN.md` (kept - 4-player co-op)
- ✅ `multiplayer/BROGUE_PROBLEMS_AND_SOLUTIONS.md` (kept - problem-first architecture)
- ✅ `multiplayer/BROGUE_MUD_AND_INSTANCES.md` (kept - research/decisions)
- ✅ `multiplayer/README.md` (kept - multiplayer overview)

**Infrastructure:**
- ✅ `multiplayer/BROGUE_NATS_INFRASTRUCTURE.md` (kept)
- ✅ `multiplayer/BROGUE_MESSAGE_TAXONOMY.md` (kept)
- ✅ `multiplayer/BROGUE_PROXY_ROUTING.md` (kept)
- ✅ `multiplayer/BROGUE_MICROSERVICE_ARCHITECTURE.md` (kept)
- ✅ `multiplayer/BROGUE_SERVER_ARCHITECTURE.md` (kept)

**Future/Research:**
- ✅ `multiplayer/BROGUE_MUD_CONTENT_CREATION.md` (kept - research)
- ✅ `multiplayer/BROGUE_YAML_CONTENT_SYSTEM.md` (kept - player content ideas)

---

## What Changed

### Systems Removed
- ❌ Essence mastery (15 types, complex combinations)
- ❌ Memory-based progression ("Remember when Big Bro...")
- ❌ Environmental affinities (20 unlock paths)
- ❌ 12-property material system
- ❌ Material mastery levels (1-5 progression)

### Systems Kept/Simplified
- ✅ 5-property ore system (clean, SWG-inspired)
- ✅ Simultaneous turn allocation (brilliant)
- ✅ Personal loot from shared resources
- ✅ Legacy Vault + street cred (meta-progression)
- ✅ Mining risk/reward (vulnerable while mining)
- ✅ 4-player co-op classes

### Vision Clarified
- **Name:** Brogue (Rogue + Bros + save your Bro quest)
- **Game:** NetHack + SWG Mining + Multiplayer Co-op
- **Focus:** Mechanical depth, not emotional story
- **Quest:** Simple motivation (save your bro), not narrative focus

---

## If You Need Something From These Docs

These are archived, not deleted. If you need to reference:

1. Check this README for what was in each doc
2. Read the archived file if you need specific details
3. Incorporate into current design if it fits the mechanical vision

**But remember:** The consolidated design is the source of truth now.

---

**Archived by:** TIA analysis (garnet-pigment-1022)
**Consolidated design:** See BROGUE_CONSOLIDATED_DESIGN.md
