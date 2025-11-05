# Using TIA AST for Brogue Development

**Purpose**: Practical guide for using TIA AST tools during Brogue development
**Audience**: Developers working on the Brogue codebase
**Philosophy**: Use AST tools to **help**, not **gate** - these are developer aids, not blockers

---

## Quick Start

```bash
# Always run from project root
cd /home/scottsen/src/tia/projects/brogue

# Quick health check (takes ~5 seconds)
tia ast audit src/

# Check your changes before committing (optional, not required)
tia ast metrics src/core/my_new_file.py
```

---

## Common Development Tasks

### 1. Understanding Existing Code

**Task**: "I need to understand how spawning works"

```bash
# See the structure
tia ast tree src/core/spawning/entity_spawner.py

# Output:
└── entity_spawner.py
    └── EntitySpawner
        ├── __init__()
        ├── spawn_monsters_for_floor()
        ├── spawn_ore_veins_for_floor()
        ├── _weighted_random_choice()
        └── _create_monster_by_type()
```

**Task**: "Find all spawn-related functions"

```bash
# Search across the codebase
tia ast search 'spawn' src/ --type callable

# Output shows all functions/methods with 'spawn' in the name
```

**Task**: "Show me the code structure with complexity"

```bash
tia ast tree src/core/game.py --complexity --lines

# Shows which functions are complex, with line numbers
```

---

### 2. Checking Your New Code

**Task**: "Is my new feature too complex?"

```bash
# Check complexity of your new file
tia ast metrics src/core/my_new_system.py

# Look for:
# - 🟢 Excellent (complexity < 8) - great!
# - 🔵 Good (complexity < 15) - acceptable
# - 🟡 Fair (complexity 15-20) - consider refactoring
# - 🔴 Poor (complexity > 20) - definitely refactor
```

**Example Output:**
```
🟢 src/core/my_new_system.py (excellent)
   📏 Lines: 150 (logical: 95, comments: 25)
   🔄 Complexity: 7, Nesting: 2
```

**Task**: "Did I introduce any security issues?"

```bash
# Quick security scan
tia ast dangerous src/core/my_new_file.py

# If output is empty or shows zero issues, you're good!
```

---

### 3. Refactoring Guidance

**Task**: "Which functions should I refactor first?"

```bash
# Find complex functions
tia ast functions src/core/ --complex-only

# Output shows functions with high complexity
# Focus on these for refactoring
```

**Task**: "Did my refactoring improve things?"

```bash
# BEFORE refactoring - save baseline
tia ast metrics src/core/game.py > /tmp/before.txt

# ... do your refactoring ...

# AFTER refactoring - compare
tia ast metrics src/core/game.py > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt

# Look for:
# - Lower complexity numbers ✅
# - Fewer complex functions ✅
# - Better ratings (poor → good → excellent) ✅
```

---

### 4. Finding Code Patterns

**Task**: "Find all places where we handle player actions"

```bash
# Search for action-related code
tia ast search 'action' src/ --type callable

# Finds all functions/methods related to actions
```

**Task**: "Find all factory methods"

```bash
# Search for create_* methods
tia ast search 'create' src/core/entities.py --type callable

# Output:
  ⚙️  create_goblin:XX-YY
  ⚙️  create_orc:XX-YY
  ⚙️  create_troll:XX-YY
```

**Task**: "Find all classes in the codebase"

```bash
tia ast search '.*' src/core/ --type class --regex

# Shows all class definitions
```

---

### 5. Dependency Checking

**Task**: "Did I introduce circular imports?"

```bash
# Check for circular dependencies
tia ast dependencies src/core/ --circular-only

# Output:
✅ No circular imports detected   # Good!

# OR if there's a problem:
🔴 Circular import detected:
   src/core/game.py → src/core/entities.py → src/core/game.py
```

**Task**: "What does this file depend on?"

```bash
# See all imports and dependencies
tia ast dependencies src/core/game.py

# Shows what the file imports and uses
```

---

## Workflow Examples

### Pre-Commit Self-Check (Optional)

**When**: Before committing significant changes
**Why**: Catch issues early, not later in review

```bash
# Quick 3-command check (~10 seconds)
tia ast metrics src/core/my_changes.py --complex-only
tia ast dangerous src/core/my_changes.py
tia ast dependencies src/core/ --circular-only

# If all look good, commit with confidence!
```

### Weekly Code Review

**When**: Friday afternoon / sprint retrospective
**Why**: Track code quality over time

```bash
# Generate quality report
tia ast audit src/ > reports/quality_$(date +%Y%m%d).txt

# Review trends:
# - Is average complexity increasing or decreasing?
# - Any new security issues?
# - How many files are "excellent" vs "good" vs "fair"?
```

### Onboarding New Developers

**When**: New team member joins
**Why**: Help them understand the codebase quickly

```bash
# Show the architecture
tia ast tree src/core/ --complexity

# Find the key systems
tia ast search 'System' src/ --type class

# Show the main game loop
tia ast tree src/core/game.py --lines
```

---

## Understanding the Output

### Complexity Scores

**What they mean:**

| Complexity | Rating | Action |
|------------|--------|--------|
| 1-7 | 🟢 Excellent | Keep it this way! |
| 8-14 | 🔵 Good | Acceptable, monitor |
| 15-20 | 🟡 Fair | Consider refactoring |
| 21+ | 🔴 Poor | Definitely refactor |

**Example from Brogue:**
- `entity_spawner.py`: Complexity 7 🟢
- `turn_processor.py`: Complexity 7 🟢
- `floor_manager.py`: Complexity 6 🟢
- `game.py`: Complexity 19 🔵 (acceptable for orchestrator)

### Search Types

**Common confusion:** `--type function` vs `--type callable`

```bash
# ❌ Wrong: Only finds standalone functions (module-level)
tia ast search 'spawn' src/ --type function
# (Won't find class methods!)

# ✅ Right: Finds both functions AND methods
tia ast search 'spawn' src/ --type callable
# (Finds everything!)

# 💡 Best: Omit --type for broad search
tia ast search 'spawn' src/
# (Finds functions, methods, calls, everything)
```

**Type Reference:**
- `function` - Standalone functions only (def at module level)
- `method` - Class methods only (def inside class)
- `callable` - Both functions and methods ⭐ **Most useful**
- `class` - Class definitions
- `call` - Function/method calls (usage)
- `variable` - Variable references

---

## Real Brogue Examples

### Example 1: Analyzing the Refactoring

**Before Phase 2:**
```bash
# Old monolithic game.py
tia ast metrics src/core/game.py

# Output:
🔴 src/core/game.py (poor)
   📏 Lines: 393 (logical: 280)
   🔄 Complexity: 35, Nesting: 6
   ⚠️  Issues: 5 complex functions
```

**After Phase 2:**
```bash
# New modular architecture
tia ast metrics src/core/game.py src/core/spawning/entity_spawner.py \
               src/core/turn_processor.py src/core/floor_manager.py

# Output:
🔵 src/core/game.py (good)
   🔄 Complexity: 19
🟢 src/core/spawning/entity_spawner.py (excellent)
   🔄 Complexity: 7
🟢 src/core/turn_processor.py (excellent)
   🔄 Complexity: 7
🟢 src/core/floor_manager.py (excellent)
   🔄 Complexity: 6
```

**Result:** Went from 1 poor file → 3 excellent + 1 good files! 🎉

### Example 2: Finding All Actions

```bash
tia ast search 'Action' src/core/actions/ --type class

# Output shows all action types:
  🏗️  MoveAction
  🏗️  AttackAction
  🏗️  MineAction
  🏗️  SurveyAction
  🏗️  DescendAction
```

### Example 3: Understanding Turn Processing

```bash
tia ast tree src/core/turn_processor.py --lines --complexity

# Shows the structure with line numbers
# Helps you quickly navigate to specific methods
```

---

## Tips & Best Practices

### 1. Run from Project Root

```bash
# ✅ Do this:
cd /home/scottsen/src/tia/projects/brogue
tia ast metrics src/core/game.py

# ❌ Not this:
cd /some/other/directory
tia ast metrics /home/scottsen/src/tia/projects/brogue/src/core/game.py
# (Might not produce output)
```

### 2. Use Specific Paths

```bash
# ✅ Check specific files you changed
tia ast metrics src/core/my_new_file.py

# 🤔 Checking everything takes longer
tia ast metrics src/
# (Still works, just slower)
```

### 3. Save Baselines for Comparison

```bash
# Before major refactoring
tia ast audit src/ > baseline.txt

# After refactoring
tia ast audit src/ > after.txt

# Compare
diff baseline.txt after.txt
```

### 4. Use Search Liberally

```bash
# Don't remember where something is?
tia ast search 'victory' src/

# Shows all occurrences with context
```

### 5. Check Dependencies After Adding Imports

```bash
# After adding new imports
tia ast dependencies src/core/ --circular-only

# Make sure you didn't create circular imports
```

---

## What to Check When

### ✅ Every Time You Write a New File

```bash
tia ast metrics src/core/my_new_file.py
```

**Look for:** Complexity < 15, no critical issues

### ✅ When Refactoring

```bash
# Before
tia ast metrics src/core/file.py > /tmp/before.txt

# After
tia ast metrics src/core/file.py > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt
```

**Look for:** Lower complexity, better ratings

### ✅ When Adding Complex Logic

```bash
tia ast functions src/core/my_file.py --complex-only
```

**Look for:** No functions with complexity > 20

### ✅ When Confused About Code

```bash
tia ast tree src/core/confusing_file.py
```

**Look for:** Overall structure and organization

### ✅ Weekly or Monthly

```bash
tia ast audit src/
```

**Look for:** Trends over time

---

## Common Questions

**Q: What if my code shows "fair" or "poor" complexity?**

A: It's not a blocker! Consider refactoring, but prioritize working features. Use the Action Factory pattern example (see PHASE_2_COMPLETE.md) for ideas.

**Q: Do I have to run these before every commit?**

A: No! These are **helpful tools**, not requirements. Run them when:
- You're unsure about code quality
- You're doing major refactoring
- You want to understand existing code
- You're curious about metrics

**Q: Can I ignore security warnings?**

A: Investigate them! But if it's a false positive (like using `eval()` in a controlled test), that's okay. Use judgment.

**Q: What's a "good" complexity score for Brogue?**

A: Based on our codebase:
- Game orchestrator: ~15-20 (acceptable)
- Systems/components: <10 (excellent)
- Utility functions: <5 (excellent)

**Q: How often should I run comprehensive audits?**

A: Up to you! Suggestions:
- Weekly: Quick check
- Monthly: Full audit with report
- Before major releases: Comprehensive review

---

## Integration with Development

### With VS Code / IDEs

You can run TIA AST from your IDE terminal:

```bash
# In VS Code terminal (Ctrl+`)
tia ast tree src/core/game.py
```

### With Git Workflow

```bash
# Before creating a PR (optional)
git diff --name-only main | grep '\.py$' | xargs tia ast metrics

# Shows metrics for changed files only
```

### With Code Reviews

Reviewer can check:
```bash
# What changed?
tia ast metrics src/core/changed_file.py

# Any new security issues?
tia ast dangerous src/core/changed_file.py

# Overall structure good?
tia ast tree src/core/changed_file.py
```

---

## Quick Reference Card

```bash
# UNDERSTANDING CODE
tia ast tree <file>                   # Show structure
tia ast search <pattern> src/         # Find pattern
tia ast tree <file> --complexity      # Structure + metrics

# CHECKING QUALITY
tia ast metrics <file>                # Complexity check
tia ast functions <file> --complex    # Find complex functions
tia ast audit src/                    # Full health check

# SECURITY & DEPS
tia ast dangerous <file>              # Security scan
tia ast dependencies src/ --circular  # Check circular imports

# BEFORE COMMITTING (optional)
tia ast metrics <changed_files>       # Quick quality check
tia ast dangerous <changed_files>     # Quick security check
```

---

## Advanced: Tracking Metrics Over Time

Create a simple tracking script:

```bash
#!/bin/bash
# save as: bin/track-quality.sh

DATE=$(date +%Y%m%d)
REPORT_DIR="reports/quality"
mkdir -p "$REPORT_DIR"

echo "📊 Generating quality report for $DATE..."

tia ast audit src/ > "$REPORT_DIR/audit_$DATE.txt"
tia ast metrics src/core/ > "$REPORT_DIR/metrics_$DATE.txt"

echo "✅ Reports saved to $REPORT_DIR/"
echo ""
echo "📈 Compare with previous:"
echo "  diff $REPORT_DIR/audit_*.txt | tail -20"
```

Usage:
```bash
chmod +x bin/track-quality.sh
./bin/track-quality.sh
```

---

## Summary

**TIA AST is a developer aid, not a gatekeeper.**

Use it to:
- ✅ Understand code faster
- ✅ Catch issues early
- ✅ Guide refactoring decisions
- ✅ Track quality over time

Don't use it to:
- ❌ Block commits
- ❌ Reject PRs automatically
- ❌ Create bureaucracy

**The goal:** Better code through helpful tools, not gates.

---

## Getting Help

```bash
# General help
tia ast --help

# Command-specific help
tia ast metrics --help
tia ast search --help
tia ast tree --help

# See real examples
tia ast workflows
```

**Questions?** Check the TIA AST documentation or ask the team!

---

**Last Updated:** 2025-10-25
**Brogue Version:** Post-Phase 2 Refactoring
**TIA AST Version:** 1.3
