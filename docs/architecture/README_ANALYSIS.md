---
project: veinborn
document_type: documentation-index
analysis_date: 2025-11-06
status: production-ready
beth_topics: [architecture, documentation-index, getting-started, lua-integration, reading-guide]
keywords: [roguelike, architecture-docs, comprehensive-analysis, quick-reference, navigation]
---

# VEINBORN ARCHITECTURAL ANALYSIS - DOCUMENTATION INDEX

**Analysis Date:** November 6, 2025
**Codebase:** ~3,550 lines of core Python
**Status:** Production-ready | Scripting-ready | Ready for Lua integration

---

## START HERE

New to Veinborn's architecture? Start with this guide:

1. **Read this README first** (5 min)
2. **Read ANALYSIS_QUICK_REFERENCE.md** (15 min) for summary
3. **Play the game** (`python3 run_textual.py`) (10 min)
4. **Read COMPREHENSIVE_ANALYSIS.md** (45 min) for deep dive

---

## DOCUMENT GUIDE

### ANALYSIS_QUICK_REFERENCE.md (251 lines, 8.7 KB)
**Purpose:** Quick lookups and summary tables  
**Read Time:** 15 minutes  
**Best For:** Getting oriented, finding specific answers

**Contains:**
- Key findings at a glance
- Architecture pattern overview
- Strengths and pain points summary
- File guide - what to read first
- Statistics and scorecards
- Lua integration roadmap
- Critical paths for scripting
- Gotchas and limitations

**When to Use:**
- "Where should I look for X?"
- "How ready is this for Lua?"
- "What are the main issues?"
- "Which files matter most?"

---

### COMPREHENSIVE_ANALYSIS.md (1,405 lines, 40 KB)
**Purpose:** Complete architectural analysis  
**Read Time:** 45 minutes  
**Best For:** Deep understanding, implementation planning

**Contains:**
- Executive summary
- Core architecture overview
- Entity/component system (detailed)
- Game state management
- Action/outcome pattern (with examples)
- Game state flow & turn processor
- Procedural generation & spawning
- All action systems (combat, mining, crafting, loot)
- AI system analysis
- Coupling analysis (tight/loose)
- Data vs code breakdown
- Extensibility & scripting points
- Issues & pain points (categorized)
- Improvements roadmap
- Prerequisites for Lua integration
- Architecture strengths/weaknesses (summary)
- Conclusion with recommendations

**When to Use:**
- "I need to understand system X"
- "How is action Y implemented?"
- "Where should I add custom code?"
- "What's the best way to extend this?"
- "How do I add Lua support?"

---

## OTHER RELEVANT DOCUMENTATION

### In This Directory

- **00_ARCHITECTURE_OVERVIEW.md** (15 KB)
  Original architecture documentation, good for high-level overview

- **SYSTEM_INTERACTIONS.md** (18 KB)
  How different systems talk to each other, data flow diagrams

- **MVP_TESTING_GUIDE.md** (18 KB)
  Testing patterns, fixtures, and examples

- **LUA_INTEGRATION_STRATEGY.md** (24 KB)
  Detailed Lua integration planning (may be outdated)

- **OPERATIONAL_EXCELLENCE_GUIDELINES.md** (32 KB)
  Development practices, testing, deployment

### In Project Root

- **README.md**
  Project overview, quick start, feature list

- **docs/START_HERE.md**
  Developer onboarding guide

- **docs/PROJECT_STATUS.md**
  Comprehensive current status report

---

## QUICK ANSWERS

### "Is this code ready for production?"
**Yes.** Production-ready for MVP (Phase 1). See:
- ANALYSIS_QUICK_REFERENCE.md → "Key Findings at a Glance"
- COMPREHENSIVE_ANALYSIS.md → "Executive Summary"

### "Can I add Lua scripting to this?"
**Yes, immediately.** The architecture is designed for it. See:
- ANALYSIS_QUICK_REFERENCE.md → "Lua Integration Roadmap"
- COMPREHENSIVE_ANALYSIS.md → "Section 11: Extensibility & Scripting Points"
- COMPREHENSIVE_ANALYSIS.md → "Section 13: Prerequisites for Lua Integration"

### "What are the main architectural patterns?"
See: ANALYSIS_QUICK_REFERENCE.md → "Architecture Pattern"  
Or: COMPREHENSIVE_ANALYSIS.md → "Section 16: Recommended Improvements"

### "Where's the hardcoded stuff?"
See: COMPREHENSIVE_ANALYSIS.md → "Section 10: Data vs Code Analysis"

### "How do I understand system X?"
See: ANALYSIS_QUICK_REFERENCE.md → "File Guide - What to Read First"

### "What needs to be fixed before adding features?"
See: COMPREHENSIVE_ANALYSIS.md → "Section 12: Issues & Pain Points"

### "What's the effort estimate for Lua?"
See: ANALYSIS_QUICK_REFERENCE.md → "Recommended Improvements"
- Basic Lua support: 2-3 weeks
- Full Lua platform: 6-8 weeks

---

## KEY STATISTICS

**Codebase:**
- 3,550 lines of core Python
- 25 core modules
- 8 action types
- 6 entity types
- 8 YAML configuration files
- Full Python 3.10+ type hints

**Architecture Quality:** 5/5
**Code Organization:** 5/5
**Type Safety:** 5/5
**Data-Driven Design:** 4/5
**Coupling:** 4/5 (Excellent)
**Testability:** 5/5
**Lua Readiness:** 5/5

**Overall Score:** 4.8/5 ⭐⭐⭐⭐⭐

---

## ARCHITECTURAL HIGHLIGHTS

**The Good:**
✅ Clean separation of concerns (GameState → GameContext → Logic)
✅ Action/Outcome pattern (serializable, event-ready)
✅ Data-driven design (80% in YAML files)
✅ Factory pattern for extensibility
✅ Type-safe throughout
✅ Minimal coupling
✅ Production-ready test infrastructure

**Areas for Improvement:**
⚠️ Dungeon generation hardcoded (3-4 days to fix)
⚠️ Spawning logic hardcoded (1-2 days to fix)
⚠️ AI system limited (1-2 days to extend)
⚠️ Event system missing (2-3 days to add)
⚠️ Some magic numbers (1 day to centralize)

---

## RECOMMENDED READING SEQUENCE

### If You Have 15 Minutes
1. This README (5 min)
2. ANALYSIS_QUICK_REFERENCE.md (10 min)

### If You Have 1 Hour
1. This README (5 min)
2. ANALYSIS_QUICK_REFERENCE.md (15 min)
3. Play the game (`python3 run_textual.py`) (15 min)
4. COMPREHENSIVE_ANALYSIS.md sections 1-4 (25 min)

### If You Have 2 Hours
1. This README (5 min)
2. ANALYSIS_QUICK_REFERENCE.md (15 min)
3. Play the game (15 min)
4. COMPREHENSIVE_ANALYSIS.md all sections (85 min)

### If You're Planning to Add Lua
1. This README (5 min)
2. ANALYSIS_QUICK_REFERENCE.md (15 min)
3. COMPREHENSIVE_ANALYSIS.md sections 4, 11, 13 (30 min)
4. src/core/base/action.py (10 min)
5. src/core/actions/action_factory.py (15 min)
6. src/core/base/game_context.py (10 min)

---

## HOW TO USE THESE DOCUMENTS

### During Development
- Keep ANALYSIS_QUICK_REFERENCE.md open as a reference
- Use "File Guide" when you need to find something
- Use "Critical Paths" for scripting integration

### When Adding Features
- Check COMPREHENSIVE_ANALYSIS.md for where to add code
- Look at existing patterns in the file guide
- Review "Extensibility Points" before starting

### When Planning Lua Integration
- Read all of COMPREHENSIVE_ANALYSIS.md Section 13
- Understand GameContext API (COMPREHENSIVE_ANALYSIS.md Section 3)
- Study ActionFactory pattern (COMPREHENSIVE_ANALYSIS.md Section 4.4)
- Follow the Lua Integration Roadmap (ANALYSIS_QUICK_REFERENCE.md)

### When Debugging
- Use COMPREHENSIVE_ANALYSIS.md Section 9 (Coupling Analysis)
- Check Section 12 (Issues & Pain Points)
- Review system interactions in SYSTEM_INTERACTIONS.md

---

## FILE LOCATIONS

### These Analysis Documents
```
/home/scottsen/src/projects/veinborn/docs/architecture/
├── README_ANALYSIS.md                    # This file
├── ANALYSIS_QUICK_REFERENCE.md           # Quick reference (read this first!)
└── COMPREHENSIVE_ANALYSIS.md             # Full analysis (detailed)
```

### Source Code (What the Analysis Covers)
```
/home/scottsen/src/projects/veinborn/
├── src/core/
│   ├── game.py                          # Game controller
│   ├── base/                            # Core abstractions
│   │   ├── action.py                    # Action system
│   │   ├── entity.py                    # Entity base class
│   │   └── game_context.py              # Safe API
│   ├── actions/                         # All game actions
│   ├── systems/                         # Game systems
│   ├── entities.py                      # Entity types
│   ├── crafting.py                      # Crafting system
│   ├── loot.py                          # Loot generation
│   └── ...                              # Other systems
│
└── data/                                # Data-driven config
    ├── entities/                        # Entity definitions
    └── balance/                         # Balance config
```

---

## NEXT STEPS

**If you're just exploring:**
1. Read ANALYSIS_QUICK_REFERENCE.md
2. Play the game to see it in action
3. Read key files from the "File Guide"

**If you're planning to contribute:**
1. Read ANALYSIS_QUICK_REFERENCE.md
2. Read COMPREHENSIVE_ANALYSIS.md sections 1-7
3. Review the specific system you'll work on
4. Check existing tests for patterns

**If you're planning Lua integration:**
1. Read ANALYSIS_QUICK_REFERENCE.md → "Lua Integration Roadmap"
2. Read COMPREHENSIVE_ANALYSIS.md → "Section 13: Prerequisites"
3. Read COMPREHENSIVE_ANALYSIS.md → "Section 11: Extensibility Points"
4. Study action_factory.py and game_context.py
5. Follow the roadmap

**If you're adding features:**
1. Understand the pattern in COMPREHENSIVE_ANALYSIS.md
2. Find similar code in the file guide
3. Follow the existing pattern
4. Test your changes

---

## CONTACT / QUESTIONS

These documents were generated by analyzing:
- 3,550 lines of core game code
- 25 core modules
- 8 YAML configuration files
- Comprehensive test infrastructure

All analysis is based on the actual codebase as of November 6, 2025.

For questions about specific systems, refer to the relevant section in the appropriate document:

| Question | Document | Section |
|----------|----------|---------|
| Is this ready for Lua? | QUICK_REFERENCE | Lua Integration Roadmap |
| How do I add an action? | COMPREHENSIVE | Section 11.2 |
| Where's the coupling? | COMPREHENSIVE | Section 9 |
| What's data vs code? | COMPREHENSIVE | Section 10 |
| How does combat work? | COMPREHENSIVE | Section 7.1 |

---

**Generated:** November 6, 2025  
**Analysis Quality:** Comprehensive (full codebase review)  
**Status:** Ready for use

