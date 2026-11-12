# Veinborn Documentation Hub

**Welcome!** Choose your path to find the right documentation.

---

## 🎮 I Want to Play

**New to Veinborn?** Start here:

→ **[../QUICKSTART.md](../QUICKSTART.md)** - Get playing in 5 minutes ⚡
→ **[../HOW_TO_PLAY.md](../HOW_TO_PLAY.md)** - Complete gameplay guide
→ **[MECHANICS_REFERENCE.md](MECHANICS_REFERENCE.md)** - How systems work
→ **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Keybind cheat sheet

**Path:** QUICKSTART → Play the game → Have fun!

---

## 🎨 I Want to Create Content

**Add monsters, items, or recipes:**

→ **[CONTENT_CREATION.md](CONTENT_CREATION.md)** - Adding game content
→ **[DATA_FILES_GUIDE.md](DATA_FILES_GUIDE.md)** - Working with YAML files
→ **[DUNGEON_CONFIGURATION.md](DUNGEON_CONFIGURATION.md)** - Dungeon generation

**Path:** Read CONTENT_CREATION → Edit YAML → Test in game → Iterate!

---

## 🔧 I Want to Extend the Game

**Add AI behaviours, abilities and event handlers in Python:**

→ **[EXTENDING.md](EXTENDING.md)** - One file per piece of content, registered with a decorator
→ **[Shipped content](../src/core/content/)** - Working examples to copy

**Path:** Read EXTENDING → Copy a content module → Modify → Test

---

## 🌐 I Want Multiplayer Info

**Learn about multiplayer features:**

→ **[MULTIPLAYER_CHAT.md](MULTIPLAYER_CHAT.md)** - Chat system
→ **[design/MULTIPLAYER_DESIGN_2025.md](design/MULTIPLAYER_DESIGN_2025.md)** - Full design philosophy

**Status:** Phase 2 complete (2+ player co-op working), Phase 3 in progress

---

## 👨‍💻 I Want to Contribute Code

**Join development:**

→ **[START_HERE.md](START_HERE.md)** - Developer onboarding (15 min) 📖
→ **[STATUS_DASHBOARD.md](STATUS_DASHBOARD.md)** - What's implemented (source of truth) ✅
→ **[MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md)** - Current priorities
→ **[development/README.md](development/README.md)** - Development workflows

**Path:** START_HERE → STATUS_DASHBOARD → Pick a task → Code → Test → PR!

---

## 🏗️ I Want Architecture Details

**Understand the technical design:**

→ **[architecture/README.md](architecture/README.md)** - Architecture hub
→ **[architecture/00_ARCHITECTURE_OVERVIEW.md](architecture/00_ARCHITECTURE_OVERVIEW.md)** - High-level overview
→ **[architecture/BASE_CLASS_ARCHITECTURE.md](architecture/BASE_CLASS_ARCHITECTURE.md)** - Core patterns
→ **[architecture/EVENT_SYSTEM.md](architecture/EVENT_SYSTEM.md)** - Event system design

**Path:** OVERVIEW → Specific system docs → Source code

---

## 📊 I Want Project Status

**Current state and plans:**

→ **[PROJECT_REVIEW_2026-04-17.md](PROJECT_REVIEW_2026-04-17.md)** - Current audit ⭐
→ **[STATUS_DASHBOARD.md](STATUS_DASHBOARD.md)** - Quick overview (2 min)
→ **[MVP_ROADMAP.md](MVP_ROADMAP.md)** - Future plans
→ **[VEINBORN_CONSOLIDATED_DESIGN.md](VEINBORN_CONSOLIDATED_DESIGN.md)** - Game vision

**Source of Truth:** PROJECT_REVIEW_2026-04-17.md for the audited state and evidence; STATUS_DASHBOARD.md for the quick view.

---

## 🔍 Quick Reference

### Common Questions

| Question | Answer |
|----------|--------|
| **How do I run the game?** | [../QUICKSTART.md](../QUICKSTART.md) or `python3 run_textual.py` |
| **What controls do I use?** | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |
| **What's implemented?** | [PROJECT_REVIEW_2026-04-17.md](PROJECT_REVIEW_2026-04-17.md) — audited; SP clean, MP experimental |
| **What's next?** | [MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md) |
| **How do I add monsters?** | [CONTENT_CREATION.md](CONTENT_CREATION.md) |
| **How do I add behaviours, abilities, events?** | [EXTENDING.md](EXTENDING.md) |
| **How do I contribute?** | [START_HERE.md](START_HERE.md) |
| **Where's the code?** | `src/core/` - well-structured Python |

### File Locations

| Looking for... | Location |
|----------------|----------|
| **Game code** | `src/core/` |
| **Tests** | `tests/` (1065 passing / 0 failing / 2 skipped) |
| **Data files** | `data/balance/`, `data/entities/` |
| **Content modules** | `src/core/content/` (`ai/`, `abilities/`, `events/`) |
| **Documentation** | `docs/` (you are here) |

---

## 📂 Documentation Structure

```
docs/
├── README.md (you are here)           # Documentation hub
├── INDEX.md                           # Detailed index
├── START_HERE.md                      # Developer onboarding
├── STATUS_DASHBOARD.md                 # Current state (source of truth)
├── QUICK_REFERENCE.md                 # Keybinds & commands
│
├── architecture/                      # Technical design
├── development/                       # Developer workflows
├── design/                            # Game design documents
└── systems/                           # System-specific docs
```

**Full index:** [INDEX.md](INDEX.md)

---

## 🆘 Need Help?

1. **Check the relevant section above** based on what you want to do
2. **Read STATUS_DASHBOARD.md** to understand current state
3. **Check INDEX.md** for comprehensive documentation index
4. **Ask questions** on GitHub issues or discussions

---

## 📝 Documentation Quality

⚠️ **Under revalidation.** The 2026-04-17 audit (`PROJECT_REVIEW_2026-04-17.md`) found stale test-count claims, missing file references, outdated controls, and architecture docs still pointing at the non-existent `future-multiplayer/` directory. Controls and test-count claims are now fixed; the `future-multiplayer/`/`~/Archive` reference cleanup is also now done (`VB-6`, 2026-08-05). A 2026-08-04 follow-up review found a critical floor-11+ crash bug (`VB-1`) and confirmed multiplayer reconnection was non-functional end-to-end (`VB-2`) — both are now fixed (2026-08-05). **All open doc and code issues are now tracked in `TASKS.md`** (`tt list --project veinborn`) rather than living only in review docs — check there for current status before trusting narrative claims in any doc, including this one.

**Recent updates:**
- 2026-04-17: Trust-restore — fixed pytest asyncio marker, added WaitAction, aligned GameSession with GameContext, fixed chat fixture, updated headline docs with real test numbers
- 2026-08-04: Full code review + bug hunt — found floor-11 crash, confirmed MP reconnection broken, filed 15 issues to `TASKS.md` (`VB-1` through `VB-15`)
- 2026-08-05: Fixed floor-11+ crash (`VB-1`), seeded-MP crash (`VB-3`), MP session leak (`VB-5`), and wired up multiplayer reconnection (`VB-2`) — all test-covered

---

**Happy developing! 🎮🚀**

*Last updated: 2026-08-04*
