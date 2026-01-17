# Constants Migration Plan - YAML Integration

**Session**: neon-dawn-0113 (2026-01-13)
**Objective**: Migrate from hardcoded `constants.py` to YAML-driven configuration via `GameConfig`

---

## Current State Analysis

### Duplication Identified

Many values exist in **both** `constants.py` and `game_constants.yaml`:

| Constant | constants.py | game_constants.yaml | Status |
|----------|-------------|---------------------|---------|
| Player starting stats | ✅ | ✅ | **Duplicate** |
| HP regeneration | ✅ | ✅ | **Duplicate** |
| Map dimensions | ✅ | ✅ | **Duplicate** |
| Inventory max size | ✅ | ✅ | **Duplicate** |
| Victory floor | ✅ | ✅ | **Duplicate** |
| Min damage | ✅ | ✅ | **Duplicate** |
| AI types | ✅ (Enum) | ✅ (dict) | **Duplicate** |
| Message log size | ✅ | ✅ | **Duplicate** |
| Debug settings | ✅ | ✅ | **Duplicate** |

### Still Hardcoded in constants.py

Values **only** in `constants.py` that should be in YAML:

| Constant | Used In | Destination |
|----------|---------|-------------|
| `MINING_MIN_TURNS`, `MINING_MAX_TURNS` | entities.py | game_constants.yaml → mining section |
| `LEGACY_ORE_PURITY_THRESHOLD` | (future use) | game_constants.yaml → legacy section |
| Monster stats (GOBLIN_HP, etc.) | entities.py | Already in monsters.yaml ✅ |

### Files Importing from constants.py

**4 files** need migration:

1. **game.py** (5 imports)
   - `DEFAULT_MAP_WIDTH`, `DEFAULT_MAP_HEIGHT`
   - `PLAYER_STARTING_HP`, `PLAYER_STARTING_ATTACK`, `PLAYER_STARTING_DEFENSE`

2. **entities.py** (11 imports)
   - `GOBLIN_HP`, `GOBLIN_ATTACK`, `GOBLIN_DEFENSE`, `GOBLIN_XP_REWARD`
   - `ORC_HP`, `ORC_ATTACK`, `ORC_DEFENSE`, `ORC_XP_REWARD`
   - `TROLL_HP`, `TROLL_ATTACK`, `TROLL_DEFENSE`, `TROLL_XP_REWARD`
   - **Issue**: These should come from monsters.yaml via EntityLoader, not constants

3. **floor_manager.py** (3 imports)
   - `DEFAULT_MAP_WIDTH`, `DEFAULT_MAP_HEIGHT`
   - `VICTORY_FLOOR`

4. **turn_processor.py** (2 imports)
   - `HP_REGEN_INTERVAL_TURNS`, `HP_REGEN_AMOUNT`

---

## Migration Strategy

### Phase 1: Add Missing Values to YAML ✅

Add to `data/balance/game_constants.yaml`:

```yaml
# Mining system
mining:
  min_turns: 3
  max_turns: 5
  description: "Multi-turn mining duration (randomized per vein)"

# Legacy system
legacy:
  ore_purity_threshold: 80
  description: "Ore with 80+ purity saved to vault (survives death)"
```

### Phase 2: Update Code to Use GameConfig 🔄

#### game.py
- **Current**: Imports 5 constants
- **New**: Use `self.config.game_constants['map']['default_width']` and similar
- **Access**: Already has `self.config` (GameConfig instance)

#### entities.py
- **Current**: Imports 11 monster stat constants + 2 mining constants
- **Monster stats**: These are **unused** (legacy from before EntityLoader)
- **Mining**: Add to GameConfig, access via config
- **Action**: Remove monster stat imports (dead code), add mining config

#### floor_manager.py
- **Current**: Imports 3 constants
- **New**: Pass config values as parameters or inject GameConfig
- **Challenge**: FloorManager doesn't currently have config reference

#### turn_processor.py
- **Current**: Imports 2 HP regen constants
- **New**: Pass config values via constructor
- **Challenge**: TurnProcessor doesn't currently have config reference

### Phase 3: Refactor constants.py 🔄

**Keep** (for type safety):
- `AIType` Enum
- `MonsterType` Enum
- `OreType` Enum

**Remove** (now in YAML):
- All numeric constants
- All spawn weights
- All quality ranges

**Result**: `constants.py` becomes `types.py` or `enums.py` (just Enums)

---

## Implementation Steps

### Step 1: Add missing constants to YAML ✅
```bash
# Edit data/balance/game_constants.yaml
# Add mining and legacy sections
```

### Step 2: Update game.py ✅
```python
# Before:
from .constants import DEFAULT_MAP_WIDTH, DEFAULT_MAP_HEIGHT, ...

# After:
# Use self.config.game_constants['map']['default_width']
```

### Step 3: Update entities.py ✅
```python
# Before:
from .constants import GOBLIN_HP, ..., MINING_MIN_TURNS, MINING_MAX_TURNS

# After:
# Remove monster stats (unused - EntityLoader handles this)
# Add mining config access via GameConfig
```

### Step 4: Update floor_manager.py ✅
```python
# Option A: Pass config values as constructor parameters
# Option B: Inject GameConfig instance
```

### Step 5: Update turn_processor.py ✅
```python
# Pass HP regen values via constructor parameters
```

### Step 6: Clean up constants.py ✅
```python
# Keep only Enums, remove all numeric constants
# Consider renaming to types.py or enums.py
```

### Step 7: Run tests ✅
```bash
pytest tests/ -v
# Expect: 1063 tests passing (no regressions)
```

### Step 8: Update documentation ✅
- Update ARCHITECTURAL_ASSESSMENT.md (remove hardcoded complaints)
- Update DATA_FILES_GUIDE.md (document game_constants.yaml additions)

---

## Benefits

### Immediate
- ✅ Single source of truth (no duplication)
- ✅ Easier balance tuning (edit YAML, no code changes)
- ✅ Cleaner architecture (config-driven design)
- ✅ Better separation of concerns (code vs data)

### Future
- ✅ Hot-reloading support (reload config without restart)
- ✅ Modding friendly (users can edit YAML files)
- ✅ A/B testing (swap config files easily)
- ✅ Multiple game modes (different config presets)

---

## Risks & Mitigation

### Risk 1: Breaking existing code
**Mitigation**: Comprehensive test suite (1063 tests), step-by-step migration

### Risk 2: Performance regression (YAML access slower than constants)
**Mitigation**: GameConfig caches parsed YAML, negligible impact

### Risk 3: Type safety loss (constants were type-checked, YAML is not)
**Mitigation**: Keep Enums in constants.py for type safety

### Risk 4: Missing config values at runtime
**Mitigation**: GameConfig provides defaults, clear error messages

---

## Testing Strategy

### Unit Tests
- Test GameConfig loads all expected values
- Test each migrated file imports correctly
- Test config value access patterns

### Integration Tests
- Run full game loop (start → play → die/win)
- Verify spawning uses config values
- Verify HP regen uses config values

### Regression Tests
- All 1063 existing tests must pass
- No behavioral changes expected

---

## Timeline Estimate

- **Step 1** (Add YAML): 10 minutes
- **Step 2** (game.py): 20 minutes
- **Step 3** (entities.py): 30 minutes
- **Step 4** (floor_manager.py): 25 minutes
- **Step 5** (turn_processor.py): 20 minutes
- **Step 6** (constants.py cleanup): 15 minutes
- **Step 7** (Testing): 30 minutes
- **Step 8** (Documentation): 20 minutes

**Total**: ~3 hours (vs original estimate 4-6 hours)

---

## Success Criteria

✅ All imports from constants.py removed (except Enums)
✅ All numeric values now in game_constants.yaml
✅ All 1063 tests passing (100%)
✅ No duplicate values between constants.py and YAML
✅ Documentation updated to reflect YAML-first approach
✅ Clean commit with clear migration message

---

**Status**: ⏳ In Progress (neon-dawn-0113)
**Next**: Execute Step 1 (Add missing constants to YAML)
