# Logging Improvements Summary

**Date**: 2025-10-29
**Session**: destined-sword-1029

## Overview

Implemented easy, high-value logging improvements to enhance debugging capabilities for the bot refactoring project.

---

## Improvements Implemented

### 1. ✅ Verbose Decision Logging (TacticalDecisionService)

**Added**: Optional verbose logging to show WHY decisions are made

**Changes**:
- Added `verbose` parameter to `__init__`
- Renamed `self.combat` → `self.combat_config` for clarity
- Renamed `self.mining` → `self.mining_config` for clarity
- Added logging to key methods:
  - `can_win_fight()`: Shows combat calculations
  - `should_fight()`: Shows reasons for engagement
  - `should_flee()`: Shows reasons for fleeing
  - `should_descend()`: Shows progression decisions

**Example Output**:
```
[DECISION] can_win_fight vs Goblin: True (kill=1.5 vs die=30.0*1.2)
[DECISION] should_fight: True (can win vs Goblin)
[DECISION] should_flee: True (low HP: 15/30, Orc nearby)
[DECISION] should_descend: True (floor cleared)
```

**Benefit**: Can now see the exact calculations and thresholds that drive bot behavior.

---

### 2. ✅ Perception Logging (PerceptionService)

**Added**: Optional verbose logging to show what the bot perceives

**Changes**:
- Converted from all `@staticmethod` to instance methods
- Added `verbose` parameter to `__init__`
- Added logging to key perception methods:
  - `find_monsters()`: Shows count and names
  - `find_nearest_monster()`: Shows distance

**Example Output**:
```
[PERCEPTION] find_monsters: 3 alive (Goblin, Goblin, Goblin)
[PERCEPTION] find_nearest_monster: Goblin at distance 13.2
```

**Benefit**: Can see exactly what entities the bot detects and at what distances.

---

### 3. ✅ Enhanced Error Context (AttackAction)

**Added**: Entity names and positions to validation error messages

**Changes**:
- Updated `cannot attack non-combat entities` error to include:
  - Entity name
  - Entity type
  - Entity position (x, y)
  - Actor position (x, y)

**Before**:
```
core.base.action - WARNING - AttackAction validation failed: cannot attack non-combat entities
core.actions.attack_action - ERROR - AttackAction execution failed validation
```

**After**:
```
core.base.action - WARNING - AttackAction validation failed: cannot attack Copper Ore Vein (ore_vein) - non-combat entity at (5,6)
core.actions.attack_action - ERROR - AttackAction execution failed validation
```

**Benefit**: Errors immediately show what entity was targeted and where, making debugging much faster.

---

### 4. ✅ Service Integration Updates

**Updated**: BrogueBot to pass verbose flag to all services

**Changes**:
```python
# Before
self.perception = PerceptionService()
self.decisions = TacticalDecisionService(self.perception, ...)
self.planner = ActionPlanner(self.perception, self.decisions, verbose=verbose)

# After
self.perception = PerceptionService(verbose=verbose)
self.decisions = TacticalDecisionService(
    self.perception,
    combat_config=...,
    mining_config=...,
    verbose=verbose
)
self.planner = ActionPlanner(self.perception, self.decisions, verbose=verbose)
```

**Benefit**: Verbose mode now propagates through entire service stack.

---

## Usage

### Running with Verbose Logging

```bash
# WarriorBot with full logging
python tests/fuzz/warrior_bot.py --games 1 -v

# RogueBot with full logging
python tests/fuzz/rogue_bot.py --games 1 -v
```

### Log Output Levels

**Standard Output** (no -v flag):
- Bot actions with emojis (`[BOT]` prefix)
- Turn summaries every 10 turns
- Error messages

**Verbose Output** (-v flag):
- All standard output PLUS:
- Perception logging (`[PERCEPTION]` prefix)
- Decision logging (`[DECISION]` prefix)
- Action planning details
- A* pathfinding routes
- Enhanced error context

---

## Files Modified

### Services
1. `tests/fuzz/services/tactical_decision_service.py`
   - Added verbose parameter and logging
   - Renamed config attributes for clarity
   - ~30 lines of logging added

2. `tests/fuzz/services/perception_service.py`
   - Converted from staticmethods to instance methods
   - Added verbose parameter and logging
   - ~10 lines of logging added

3. `tests/fuzz/brogue_bot.py`
   - Updated service initialization to pass verbose
   - 3 lines changed

### Core Game
4. `src/core/actions/attack_action.py`
   - Enhanced error message with entity context
   - 5 lines modified

---

## Impact Assessment

### Debugging Capability Improvements

**Before**:
- ⚠️ Could see WHAT action was taken
- ❌ Could NOT see WHY decision was made
- ⚠️ Errors showed reason but not context

**After**:
- ✅ Can see WHAT action was taken
- ✅ Can see WHY decision was made (combat calculations, thresholds)
- ✅ Can see WHAT the bot perceives (monsters, distances)
- ✅ Errors show full context (entity names, positions)

### Performance Impact

- **Negligible**: Logging only occurs when verbose=True
- **No impact** on production bots (verbose=False by default)
- **Log volume**: ~2-3x more output in verbose mode

### Code Quality

- **Service API improved**: Consistent verbose parameter across all services
- **Better naming**: `combat_config` and `mining_config` more explicit
- **Maintained compatibility**: All existing bots work without changes

---

## Testing Results

All refactored bots tested successfully with new logging:

```bash
# WarriorBot
python tests/fuzz/warrior_bot.py --games 1 -v
✅ Combat decisions logged correctly
✅ Perception data shows monster detection
✅ Enhanced errors show entity context

# RogueBot, MageBot, HealerBot
✅ All bots working with new logging
✅ Decision logic visible and correct
✅ No performance degradation
```

---

## Example Debugging Session

**Problem**: Bot keeps trying to attack ore veins

**Before Improvements**:
```
core.actions.attack_action - ERROR - AttackAction execution failed validation
```
→ Need to add debug prints, restart bot, wait for issue to reproduce

**After Improvements**:
```
[PERCEPTION] find_nearest_monster: Goblin at distance 13.2
[DECISION] should_fight: False (no monsters in range 7.0)
[BOT] ⚔️  Pursuing Goblin!
core.base.action - WARNING - AttackAction validation failed: 
  cannot attack Copper Ore Vein (ore_vein) - non-combat entity at (5,6)
```
→ Immediately see: Bot is pursuing Goblin but bumping into ore at (5,6)
→ Fix: Check movement pathfinding around ore veins

---

## Validation Against Original Goals

From `LOGGING_VALIDATION.md` recommendations:

| Priority | Recommendation | Status |
|----------|---------------|--------|
| 1 | Add decision logging to TacticalDecisionService | ✅ Complete |
| 2 | Enhance error messages with entity context | ✅ Complete |
| 3 | Add perception logging (low priority) | ✅ Complete |

**All recommendations implemented!**

---

## Next Steps (Optional Future Enhancements)

1. **Add combat outcome logging**: Log actual damage dealt vs predicted
2. **Add mining decision logging**: Why ore was/wasn't mined
3. **Add service timing**: How long each decision takes
4. **Structured logging**: Export to JSON for analysis

These are nice-to-have but not critical for current development.

---

## Conclusion

The logging improvements provide **excellent debugging visibility** into bot decision-making while maintaining zero performance impact on production bots. All three recommended improvements from the validation report have been successfully implemented and tested.

**Status**: ✅ Production-ready
**Effort**: ~1 hour
**Value**: High - significantly reduces debugging time
