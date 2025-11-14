# Brogue Documentation Index

**Welcome to the Brogue documentation!** This page will help you find what you need.

---

## 🎯 Start Here (New to Brogue?)

### For Players
| Document | Time | Purpose |
|----------|------|---------|
| **[HOW_TO_PLAY.md](../HOW_TO_PLAY.md)** ⭐ | 5 min | **Complete gameplay guide - START HERE!** |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | 2 min | Controls & keybinds quick lookup |
| **[README.md](../README.md)** | 5 min | Project overview |

**Recommended path:** HOW_TO_PLAY → Play the game → Have fun!

### For Developers
| Document | Time | Purpose |
|----------|------|---------|
| **[START_HERE.md](START_HERE.md)** ⭐ | 15 min | **Developer onboarding - START HERE!** |
| **[PROJECT_STATUS.md](PROJECT_STATUS.md)** | 10 min | What's implemented (everything!) |
| **[MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md)** | 5 min | Current priorities |
| **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** | 2 min | Commands, file locations |

**Recommended path:** START_HERE → PROJECT_STATUS → Pick a task → Code!

---

## 📊 Current Status & Planning

| Document | Purpose | Audience |
|----------|---------|----------|
| **[STATUS_DASHBOARD.md](STATUS_DASHBOARD.md)** ⭐ | 🎯 **One-page at-a-glance status** (2 min read) | Everyone |
| **[PROJECT_STATUS.md](PROJECT_STATUS.md)** | ✅ Comprehensive status report (858/860 tests, 100% accurate) | Everyone |
| **[MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md)** | 🎯 Current priorities and next steps | Developers |
| **[MVP_ROADMAP.md](MVP_ROADMAP.md)** | 📋 High-level roadmap | Project managers |

**Quick status check:** → **STATUS_DASHBOARD.md** (2 min)
**Detailed status:** → **PROJECT_STATUS.md** (10 min, 100% accurate)

---

## 🎮 Game Design

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **[BROGUE_CONSOLIDATED_DESIGN.md](BROGUE_CONSOLIDATED_DESIGN.md)** | Master game design document | Understanding the vision |
| **[MECHANICS_REFERENCE.md](MECHANICS_REFERENCE.md)** | Detailed mechanics reference | Implementing features |
| **[systems/](systems/)** | System-specific designs | Working on specific systems |

---

## 🏗️ Architecture & Development

### Architecture Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[architecture/README.md](architecture/README.md)** | Architecture navigation hub | Developers |
| **[architecture/00_ARCHITECTURE_OVERVIEW.md](architecture/00_ARCHITECTURE_OVERVIEW.md)** | System architecture overview | New developers |
| **[architecture/BASE_CLASS_ARCHITECTURE.md](architecture/BASE_CLASS_ARCHITECTURE.md)** | Core design patterns | Implementers |
| **[architecture/DECISIONS.md](architecture/DECISIONS.md)** | Architectural decisions (ADRs) | Technical leads |

### Development Guides

| Document | Purpose | Audience |
|----------|---------|----------|
| **[development/README.md](development/README.md)** | Development guide index | Developers |
| **[development/DEBUG_INSTRUCTIONS.md](development/DEBUG_INSTRUCTIONS.md)** | How to debug the game | Everyone |
| **[development/TESTING_ACTION_FACTORY.md](development/TESTING_ACTION_FACTORY.md)** | Testing guide | Test writers |
| **[development/CODE_REVIEW_STANDARDS.md](development/CODE_REVIEW_STANDARDS.md)** | Code quality standards | Reviewers |

---

## 📦 Content Creation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[CONTENT_CREATION.md](CONTENT_CREATION.md)** | Adding monsters, items, recipes | Content creators |
| **[DATA_FILES_GUIDE.md](DATA_FILES_GUIDE.md)** | Working with YAML data files | Everyone |

---

## 🗃️ Archived Documentation

⚠️ **Note:** The following documentation has been archived as it's either outdated or not part of the current MVP focus.

| Directory | Contents | Location |
|-----------|----------|----------|
| **Archive/** | Old/conflicting designs, historical summaries | `../.archived/Archive/` |
| **future-multiplayer/** | Phase 2 multiplayer designs (16+ docs) | `../.archived/future-multiplayer/` |

**For current design:** Read [BROGUE_CONSOLIDATED_DESIGN.md](BROGUE_CONSOLIDATED_DESIGN.md) instead!

---

## 🎯 Common Scenarios

### "I'm new, where do I start?"
1. Read [README.md](../README.md) (5 min)
2. Read [START_HERE.md](START_HERE.md) (15 min)
3. Run the game: `python3 run_textual.py`
4. Check [MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md) for tasks

### "I want to add a feature"
1. Check [PROJECT_STATUS.md](PROJECT_STATUS.md) - is it done?
2. Check [MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md) - is it planned?
3. Read relevant system docs in [systems/](systems/)
4. Check [architecture/](architecture/) for patterns
5. Write tests, implement, playtest!

### "I want to add content (monsters, items)"
1. Read [CONTENT_CREATION.md](CONTENT_CREATION.md)
2. Check [DATA_FILES_GUIDE.md](DATA_FILES_GUIDE.md)
3. Edit YAML files in `data/`
4. Test and play!

### "How does X work?"
1. Check [BROGUE_CONSOLIDATED_DESIGN.md](BROGUE_CONSOLIDATED_DESIGN.md) - design
2. Check [PROJECT_STATUS.md](PROJECT_STATUS.md) - implementation status
3. Check [architecture/](architecture/) - technical details
4. Read the code in `src/core/`

### "What should I work on?"
1. Read [MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md)
2. Check [PROJECT_STATUS.md](PROJECT_STATUS.md) for gaps
3. Pick a task that interests you
4. Ask if unsure!

### "Is X complete?"
✅ Check [PROJECT_STATUS.md](PROJECT_STATUS.md) - it's 100% accurate!

---

## 📞 Need Help?

| Question | Check |
|----------|-------|
| "How do I run the game?" | [README.md](../README.md) or [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |
| "What's the vision?" | [BROGUE_CONSOLIDATED_DESIGN.md](BROGUE_CONSOLIDATED_DESIGN.md) |
| "What's done?" | [PROJECT_STATUS.md](PROJECT_STATUS.md) |
| "What's next?" | [MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md) |
| "How does X work?" | [architecture/](architecture/) or read `src/core/` |
| "How do I test?" | [development/TESTING_ACTION_FACTORY.md](development/TESTING_ACTION_FACTORY.md) |
| "Where's file X?" | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |

---

## 🎮 Quick Links

### Essential Reading
- [README.md](../README.md) - Start here!
- [START_HERE.md](START_HERE.md) - Developer guide
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Truth about current state
- [BROGUE_CONSOLIDATED_DESIGN.md](BROGUE_CONSOLIDATED_DESIGN.md) - Game vision

### Working on MVP
- [MVP_CURRENT_FOCUS.md](MVP_CURRENT_FOCUS.md) - What to build now
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Commands & locations
- [architecture/00_ARCHITECTURE_OVERVIEW.md](architecture/00_ARCHITECTURE_OVERVIEW.md) - How it works

### Adding Content
- [CONTENT_CREATION.md](CONTENT_CREATION.md) - Add monsters/items/recipes
- [DATA_FILES_GUIDE.md](DATA_FILES_GUIDE.md) - Work with YAML files

---

**Last Updated:** 2025-11-05
**Maintained By:** Brogue development team

**Found an issue with the docs?** Please update this index!
