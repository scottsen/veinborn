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

## 🔧 I Want to Mod with Lua

**Extend the game with Lua scripts:**

→ **[LUA_API.md](LUA_API.md)** - Complete Lua API reference 📚
→ **[LUA_EVENT_MODDING_GUIDE.md](LUA_EVENT_MODDING_GUIDE.md)** - Event system modding
→ **[LUA_AI_MODDING_GUIDE.md](LUA_AI_MODDING_GUIDE.md)** - AI behavior modding
→ **[Example scripts](../scripts/)** - Working examples

**Path:** Read LUA_API → Copy example → Modify → Test → Share!

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
→ **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - What's implemented (source of truth) ✅
→ **[MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md)** - Current priorities
→ **[development/README.md](development/README.md)** - Development workflows

**Path:** START_HERE → PROJECT_STATUS → Pick a task → Code → Test → PR!

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

→ **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Complete status (1063 tests, 100% pass) ⭐
→ **[STATUS_DASHBOARD.md](STATUS_DASHBOARD.md)** - Quick overview (2 min)
→ **[MVP_ROADMAP.md](MVP_ROADMAP.md)** - Future plans
→ **[VEINBORN_CONSOLIDATED_DESIGN.md](VEINBORN_CONSOLIDATED_DESIGN.md)** - Game vision

**Source of Truth:** PROJECT_STATUS.md (always accurate, check here first!)

---

## 🔍 Quick Reference

### Common Questions

| Question | Answer |
|----------|--------|
| **How do I run the game?** | [../QUICKSTART.md](../QUICKSTART.md) or `python3 run_textual.py` |
| **What controls do I use?** | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |
| **What's implemented?** | [PROJECT_STATUS.md](PROJECT_STATUS.md) (1063 tests ✅) |
| **What's next?** | [MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md) |
| **How do I add monsters?** | [CONTENT_CREATION.md](CONTENT_CREATION.md) |
| **How do I mod with Lua?** | [LUA_API.md](LUA_API.md) |
| **How do I contribute?** | [START_HERE.md](START_HERE.md) |
| **Where's the code?** | `src/core/` - well-structured Python |

### File Locations

| Looking for... | Location |
|----------------|----------|
| **Game code** | `src/core/` |
| **Tests** | `tests/` (1063 passing!) |
| **Data files** | `data/balance/`, `data/entities/` |
| **Lua scripts** | `scripts/actions/`, `scripts/events/`, `scripts/ai/` |
| **Documentation** | `docs/` (you are here) |

---

## 📂 Documentation Structure

```
docs/
├── README.md (you are here)           # Documentation hub
├── INDEX.md                           # Detailed index
├── START_HERE.md                      # Developer onboarding
├── PROJECT_STATUS.md                  # Current state (source of truth)
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
2. **Read PROJECT_STATUS.md** to understand current state
3. **Check INDEX.md** for comprehensive documentation index
4. **Ask questions** on GitHub issues or discussions

---

## 📝 Documentation Quality

✅ **Accurate** - Major cleanup in Nov 2025, metrics verified
✅ **Comprehensive** - 47 docs covering all aspects
✅ **Current** - PROJECT_STATUS.md is source of truth (1063 tests, 100%)
⚠️ **Some overlap** - Architecture docs have redundancy (consolidation planned)

**Recent updates:**
- 2025-11-06: Fixed test counts, Legacy Vault status, Lua Phase 3 status
- 2025-11-14: Added multiplayer documentation
- 2026-01-08: Added QUICKSTART.md, archived analysis artifacts

---

**Happy developing! 🎮🚀**

*Last updated: 2026-01-08*
