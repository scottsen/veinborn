# Entity Rendering Bug Prevention - Summary

**Session**: lingering-gale-0113 (2026-01-13)
**Bug Fixed**: Forge invisible but blocking movement
**Question**: How do we prevent this type of bug?

## What We Discovered

### The Gap
Current architecture has **no forcing function** when adding new entity types:
- ✅ EntityType enum updated
- ✅ Entity class created
- ✅ Spawning works
- ✅ Collision detection works
- ❌ **Rendering forgotten** → invisible entity!

### Root Cause
**Manual rendering per entity type** in `map_widget.py`:
```python
if entity_type == MONSTER: render_monster()
if entity_type == ORE_VEIN: render_ore()
# ❌ FORGE case missing → falls through to terrain
```

## What We Delivered

### 1. Analysis Document ✅
**File**: `docs/development/ENTITY_RENDERING_IMPROVEMENTS.md`

Comprehensive analysis covering:
- Root cause breakdown
- 4 prevention strategies (tests, data-driven, registry, smoke tests)
- Recommended phased approach
- Implementation checklist

### 2. Test Suite ✅
**File**: `tests/unit/ui/test_entity_rendering.py`

Parametrized tests that catch missing rendering:
```python
@pytest.mark.parametrize("entity_type", list(EntityType))
def test_all_entity_types_have_visible_symbols(entity_type):
    """Every entity type must render with visible symbol."""
```

**Test Results**:
- ✅ MONSTER: Renders correctly
- ✅ ORE_VEIN: Renders correctly
- ✅ FORGE: Renders correctly (after our fix!)
- ❌ ITEM: Falls through to '?' terrain symbol
- ❌ NPC: Falls through to '?' terrain symbol

**Proves the test works** - it catches gaps!

### 3. Architecture Guide ✅
**File**: `docs/development/DATA_DRIVEN_RENDERING_POC.md`

Proof-of-concept for data-driven rendering:
- Entities carry display metadata (symbol, color)
- Single rendering path for all entity types
- Load metadata from YAML files
- Migration path from current state

### 4. Regression Test ✅
Specific test for the forge bug:
```python
def test_forge_visibility_regression():
    """Regression test for forge rendering bug (2026-01-13)."""
    forge = Forge(forge_type="basic_forge", x=5, y=5)
    segment = widget._render_cell(5, 5, player, mock_map)
    assert segment.text == '&', "Forge should render as '&'"
    assert segment.text != '·', "Forge must not render as floor"
```

**Status**: ✅ PASSING (confirms our fix works)

## Recommended Next Steps

### Immediate (Quick Win)
1. ✅ **Add rendering tests** - Already implemented!
2. Run tests in CI to catch future regressions
3. Fix ITEM and NPC rendering (test will guide you)

### Short-term (This Sprint)
1. Add `display_symbol` and `display_color` properties to Entity base class
2. Update MapWidget to use entity properties (single code path)
3. All tests pass, rendering now bulletproof

### Long-term (Future)
1. Load display metadata from YAML files
2. Make rendering fully data-driven
3. Enable modding via data files

## Impact

### Before
- ❌ Easy to forget rendering for new entity types
- ❌ No tests to catch it
- ❌ Manual code per entity type

### After
- ✅ Tests catch missing rendering immediately
- ✅ Clear path to data-driven architecture
- ✅ Documented checklist for new entity types
- ✅ Forge bug fixed + regression test prevents recurrence

## Test Coverage Added

```bash
# Run entity rendering tests
pytest tests/unit/ui/test_entity_rendering.py -v

# Key tests:
# - test_all_entity_types_have_visible_symbols (parametrized)
# - test_forge_visibility_regression (specific bug)
# - test_player_renders_distinctly
# - test_ore_vein_colors (parametrized)
# - test_multiple_entities_same_cell_priority
```

## Files Created/Modified

### New Files
- `docs/development/ENTITY_RENDERING_IMPROVEMENTS.md` - Full analysis
- `docs/development/DATA_DRIVEN_RENDERING_POC.md` - Architecture guide
- `docs/development/PREVENTION_SUMMARY.md` - This file
- `tests/unit/ui/test_entity_rendering.py` - Test suite

### Modified Files (Bug Fix)
- `src/ui/textual/widgets/map_widget.py` - Added forge rendering
- `src/core/actions/move_action.py` - Added bump-to-mine
- `src/ui/textual/app.py` - Removed M key binding
- `src/ui/textual/widgets/sidebar.py` - Updated controls hint

## Key Insight

**Architecture insight**: When you have an enum (EntityType) that drives behavior, you need a **forcing function** to ensure all cases are handled:

1. **Tests** (immediate) - Parametrized test over all enum values
2. **Registry pattern** (short-term) - Runtime assertion checking completeness
3. **Data-driven** (long-term) - Behavior defined in data, not code

This prevents "forgot to handle the new case" bugs.

## Related Patterns

Similar forcing functions needed for:
- ActionFactory (all EntityTypes need action handlers?)
- SaveLoad (all EntityTypes serializable?)
- Event system (all EntityTypes emit/receive events?)

Consider applying this pattern elsewhere in the codebase.

---

**Conclusion**: We not only fixed the bug, but created **infrastructure to prevent entire class of bugs**. Tests catch regressions, documentation guides future work, and architecture path improves maintainability.
