# Logging Validation Report

**Date**: 2025-10-29
**Purpose**: Validate that logs contain sufficient information for debugging various bug types

---

## Summary

**Overall Assessment**: ✅ **GOOD** - Logs provide sufficient debugging information for most common bug types, with some minor gaps for advanced debugging scenarios.

---

## Log Files Structure

### 1. Main Log File
- **Location**: `/projects/brogue/logs/bot_tests.log`
- **Size**: ~20M lines (comprehensive)
- **Format**: Python logging with timestamps, module, level, message
- **Retention**: Continuous append (grows over time)

### 2. Results JSON Files
- **Location**: `/projects/brogue/logs/bot_results_<botname>_<timestamp>.json`
- **Content**: Aggregate game statistics per bot run
- **Data**: turns, floors reached, kills, damage, ore mined, death cause

---

## Information Available by Bug Type

### ✅ EXCELLENT: Combat Bugs

**Available Information**:
- Action type and parameters
- Entity names and types
- Threat level assessments
- Position coordinates (x, y)
- HP values before/after
- Damage dealt/taken
- Kill confirmations and XP awards
- Attack validation failures with reasons

**Example Log**:
```
[BOT] ⚔️  Fighting Goblin (ThreatLevel.TRIVIAL) at (7,11)
[BOT]    A* pathfinding: (7,10) → (7,11)
core.actions.attack_action - INFO - AttackAction damage dealt
core.game_state - INFO - Game message: Player hits Goblin for 4 damage!
```

**Debugging Capability**: Can fully reconstruct combat sequences, identify damage calculation bugs, track entity states.

---

### ✅ EXCELLENT: Movement & Pathfinding Bugs

**Available Information**:
- Current position and target position
- A* pathfinding routes
- Movement success/failure
- Blocked movement reasons ("tile not walkable")
- Stuck detection (position + turn count)
- Random action attempts when stuck

**Example Log**:
```
[BOT]    A* pathfinding: (7,8) → (7,9)
core.actions.move_action - INFO - MoveAction executed successfully: moved from (7,8) to (7,9)
[BOT]    ⚠️  Action move {'dx': -1, 'dy': 1} FAILED!
[BOT] ⚠️  STUCK DETECTED at (7, 10) for 5 turns - trying random action!
```

**Debugging Capability**: Can trace movement paths, identify wall collisions, detect infinite loops.

---

### ✅ GOOD: Bot Decision-Making Bugs

**Available Information**:
- Bot actions with emojis (pursuing, fleeing, exploring, mining)
- Turn summaries every 10 turns (position, HP, floor, monster count)
- Monster pursuit decisions
- Flee decisions with HP context
- Mining/surveying decisions
- Equipment crafting attempts

**Example Log**:
```
[BOT] Turn 20: Player @ (7,9), HP=29/30, Floor=1, Level=1, Monsters=1, Nearest=@ (11,3), dist=7.2
[BOT] 💀 Low health! Fleeing to stairs! (HP: 15/30, distance: 5.2)
[BOT] ⚔️  Pursuing Giant Bat!
```

**Debugging Capability**: Can understand bot strategy, identify poor decisions, track health-based behavior changes.

**Gap**: Decision service reasoning not logged (e.g., WHY did should_fight() return false?)

---

### ⚠️ PARTIAL: Service-Level Decision Logic Bugs

**Available Information**:
- ActionPlanner decisions and actions (logged)
- Final action chosen
- Config values used (health_threshold, safety_margin, etc.)

**Missing Information**:
- PerceptionService outputs (what monsters/ore were detected)
- TacticalDecisionService logic (why should_fight/should_flee returned true/false)
- Combat power calculations
- Threat assessment details
- Mining strategy evaluation

**Example of What's Missing**:
```
# Would be helpful but not logged:
[DECISION] should_fight: False (HP: 15/30 < threshold: 18.0, safety_margin: 1.5, threat: deadly)
[PERCEPTION] find_monsters: 3 monsters found at [(5,6), (7,11), (15,3)]
[TACTICAL] can_win_fight: False (turns_to_kill=15 > turns_to_die=8 * 1.5)
```

**Debugging Capability**: Can see WHAT action was taken, but not always WHY a specific decision was made.

**Workaround**: Can infer from config values and game state, but requires manual calculation.

---

### ✅ GOOD: Mining & Crafting Bugs

**Available Information**:
- Ore surveying actions
- Ore types and purity values
- Mining attempts and completion
- Crafting attempts at forges
- Equipment equipping
- Jackpot ore detection

**Example Log**:
```
[BOT] 🔍 Surveying copper ore...
[BOT] ⛏️  Mining high-quality iron ore (purity: 85)!
[BOT] 🔨 Crafting Iron Sword at forge!
[BOT] 🎽 Equipping Iron Sword!
```

**Debugging Capability**: Can track resource gathering, crafting flow, equipment progression.

---

### ✅ GOOD: Game State & Progression Bugs

**Available Information**:
- Game initialization (player position, monster count, ore count)
- Level progression
- Floor transitions
- XP gains and level ups
- Game end conditions
- Turn counts

**Example Log**:
```
core.game - INFO - Game started: Player at (11, 4), 5 monsters, 8 ore veins
core.game_state - INFO - Game message: Gained 10 XP!
```

**Debugging Capability**: Can track game progression, identify level-up bugs, verify spawn rates.

---

### ⚠️ PARTIAL: Validation & Error Bugs

**Available Information**:
- Validation failure messages
- Error reasons (e.g., "cannot attack non-combat entities")
- Action type that failed

**Missing Information**:
- Entity ID or name being targeted
- Position where error occurred
- Game state snapshot at error time

**Example Current Error**:
```
core.base.action - WARNING - AttackAction validation failed: cannot attack non-combat entities
core.actions.attack_action - ERROR - AttackAction execution failed validation
```

**Example Improved Error**:
```
core.actions.attack_action - ERROR - AttackAction failed: cannot attack Copper Ore Vein (non-combat) at (5,6) [player at (5,7)]
```

**Debugging Capability**: Can identify error type, but context is limited.

---

## Log Levels Available

1. **DEBUG**: Low-level details (subsystem init, entity spawning)
2. **INFO**: Normal game flow (actions, state changes, messages)
3. **WARNING**: Blocked actions, validation issues
4. **ERROR**: Failed actions, validation failures
5. **BOT**: Custom bot-level logging (prefixed with [BOT])

---

## Recommendations

### Priority 1: Add Decision Logging (Optional Enhancement)

Add optional verbose decision logging to TacticalDecisionService:

```python
class TacticalDecisionService:
    def __init__(self, ..., verbose_decisions=False):
        self.verbose_decisions = verbose_decisions
    
    def should_fight(self, game):
        result = self._calculate_should_fight(game)
        if self.verbose_decisions:
            print(f"[DECISION] should_fight={result} (hp={game.state.player.hp}, threshold={self.combat_config.health_threshold})")
        return result
```

**Benefit**: Would help debug WHY bots make specific decisions.

**Downside**: Increases log size significantly.

---

### Priority 2: Enhance Error Context

Add entity context to validation errors:

```python
# In AttackAction validation
if not target.is_combatant():
    raise ValidationError(
        f"cannot attack {target.name} ({target.entity_type}) - non-combat entity at ({target.x},{target.y})"
    )
```

**Benefit**: Errors immediately show what entity caused the problem.

**Effort**: Low (update error messages).

---

### Priority 3: Add Perception Logging (Low Priority)

Add optional logging to PerceptionService to show what was detected:

```python
def find_monsters(self, game):
    monsters = [...]
    if self.verbose:
        print(f"[PERCEPTION] find_monsters: {len(monsters)} found")
    return monsters
```

**Benefit**: Shows what the bot "sees" at each turn.

**Downside**: Very verbose, may clutter logs.

---

## Current State: VALIDATED ✅

The logging system provides **sufficient debugging information** for the following bug types:

1. ✅ Combat bugs (damage, kills, HP)
2. ✅ Movement bugs (pathfinding, stuck detection)
3. ✅ Bot behavior bugs (can see actions taken)
4. ✅ Mining/crafting bugs (resource gathering flow)
5. ✅ Game progression bugs (levels, floors, XP)
6. ⚠️ Decision logic bugs (can infer, but not explicit)
7. ⚠️ Validation errors (reason given, but limited context)

**Conclusion**: The current logging is **production-ready** for bot development and testing. Optional enhancements would improve debugging of decision-making logic, but are not critical.

---

## Test Results from Validation

All bots tested successfully with comprehensive logging:

- **WarriorBot**: ✅ Combat and pursuit decisions logged
- **RogueBot**: ✅ Exploration and evasion logged  
- **MageBot**: ✅ Flee decisions and safety behavior logged
- **HealerBot**: ✅ Defensive tanking and methodical clearing logged

**Log Volume**: ~20M lines for extended play sessions (manageable).

**Performance Impact**: Negligible (logging is async).
