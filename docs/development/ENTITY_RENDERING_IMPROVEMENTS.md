# Entity Rendering Improvements

**Created**: 2026-01-13
**Context**: Bug discovered where forges were invisible (rendered as floor tiles) but blocked movement
**Question**: How do we prevent these types of bugs in the future?

## Root Cause Analysis

### The Bug
1. Forge entity type exists (`EntityType.FORGE`)
2. Forges spawn correctly and block movement
3. YAML files have rendering metadata (`symbol: "&"`, `color: "yellow"`)
4. **But**: `map_widget.py` had no rendering case for forges → fell through to terrain rendering

### Why It Happened
**Architectural gap**: No forcing function when adding new entity types

Current flow:
```
EntityType enum → Entity classes → Spawning → ??? → Rendering
                                              ↑
                                    Missing connection!
```

Rendering is **manually maintained** in `map_widget.py`:
- Hardcoded checks: `EntityType.MONSTER`, `EntityType.ORE_VEIN`
- No mechanism to ensure new entity types get rendering code
- No validation that all entity types have rendering

### Data vs Code Disconnect

**YAML files have rendering metadata** (`data/balance/forges.yaml`):
```yaml
basic_forge:
  symbol: "&"
  color: "copper"
```

**But this metadata is never loaded**:
- EntityLoader doesn't extract `symbol`/`color` into Entity.stats
- Rendering code doesn't use entity metadata
- Each entity type has custom rendering logic

## Prevention Strategies

### Strategy 1: Data-Driven Rendering (Recommended)

**Architecture**: Entities carry their own display metadata

**Implementation**:
1. EntityLoader stores `symbol` and `color` from YAML → `Entity.stats`
2. Entity base class has `display_symbol` and `display_color` properties
3. MapWidget uses entity's own metadata (single code path for all entities)

**Benefits**:
- ✅ Adding new entity type automatically works if YAML has symbol/color
- ✅ No code changes needed for new entity types
- ✅ Single source of truth (YAML)
- ✅ Modding-friendly (change symbols via data files)

**Code Example**:
```python
# In Entity base class
@property
def display_symbol(self) -> str:
    """Get rendering symbol for this entity."""
    return self.get_stat('display_symbol', '?')

@property
def display_color(self) -> str:
    """Get rendering color for this entity."""
    return self.get_stat('display_color', 'white')

# In MapWidget._render_cell()
entity = self._get_entity_at(world_x, world_y)
if entity and entity != player:
    return Segment(entity.display_symbol, Style(color=entity.display_color))
```

**Migration Path**:
1. Add display metadata loading to EntityLoader
2. Add default fallbacks to Entity class (e.g., monster → first letter)
3. Simplify MapWidget to use entity metadata
4. Deprecate hardcoded rendering logic

### Strategy 2: Exhaustive Entity Type Registry

**Architecture**: Central registry that enforces completeness

**Implementation**:
```python
# In src/ui/textual/widgets/entity_display.py
ENTITY_RENDERING = {
    EntityType.PLAYER: {'symbol': '@', 'color': 'bright_yellow'},
    EntityType.MONSTER: {'symbol': lambda e: e.name[0].lower(), 'color': 'bright_red'},
    EntityType.ORE_VEIN: {'symbol': '*', 'color': lambda e: ORE_COLORS[e.ore_type]},
    EntityType.FORGE: {'symbol': '&', 'color': lambda e: FORGE_COLORS[e.forge_type]},
    EntityType.ITEM: {'symbol': ')', 'color': 'bright_cyan'},
    EntityType.NPC: {'symbol': 'n', 'color': 'bright_green'},
}

# Runtime validation
assert set(ENTITY_RENDERING.keys()) == set(EntityType), \
    f"Missing rendering for: {set(EntityType) - set(ENTITY_RENDERING.keys())}"
```

**Benefits**:
- ✅ Runtime assertion catches missing entity types
- ✅ Single file to check for all rendering logic
- ❌ Still requires manual code changes per entity type

### Strategy 3: Comprehensive Rendering Tests

**Test Coverage**: Verify every entity type renders

**Implementation**:
```python
# tests/unit/ui/test_entity_rendering.py
import pytest
from core.base.entity import EntityType, Entity
from ui.textual.widgets.map_widget import MapWidget

@pytest.mark.parametrize("entity_type", list(EntityType))
def test_all_entity_types_render(entity_type, mock_game_state):
    """Every entity type must render with a visible symbol."""
    # Create entity of each type
    entity = create_entity_of_type(entity_type, x=5, y=5)
    mock_game_state.entities[entity.entity_id] = entity

    # Render
    widget = MapWidget(game_state=mock_game_state)
    segment = widget._render_cell(5, 5, mock_player, mock_map)

    # Assertions
    assert segment.text != '·', f"{entity_type} renders as floor (invisible)"
    assert segment.text != ' ', f"{entity_type} renders as blank (invisible)"
    assert segment.text != '?', f"{entity_type} has no symbol defined"
    assert len(segment.text) == 1, f"{entity_type} symbol must be 1 character"
```

**Benefits**:
- ✅ Catches missing rendering immediately
- ✅ Parametrized test = runs for all entity types
- ✅ Red/Green feedback loop

### Strategy 4: Integration Smoke Test

**Test Coverage**: Full game render on startup

**Implementation**:
```python
# tests/integration/test_game_rendering.py
def test_all_spawned_entities_visible():
    """Every entity that spawns must be visible on map."""
    game = create_test_game(seed=42)

    # Get all spawned entities
    for entity in game.state.entities.values():
        if entity.x is None or entity.y is None:
            continue  # Skip inventory items

        # Render that cell
        segment = game.ui.map_widget._render_cell(
            entity.x, entity.y, game.state.player, game.state.dungeon_map
        )

        # Should not be terrain
        assert segment.text in EXPECTED_ENTITY_SYMBOLS, \
            f"{entity.name} ({entity.entity_type}) at ({entity.x},{entity.y}) " \
            f"renders as '{segment.text}' (expected entity symbol)"
```

## Recommended Approach

**Phase 1: Quick Win (Immediate)**
- Add Strategy 3 test (`test_all_entity_types_render`)
- Catches regression immediately if new entity types added
- ~30 minutes to implement

**Phase 2: Architecture (Next sprint)**
- Implement Strategy 1 (data-driven rendering)
- Load `symbol`/`color` from YAML → Entity.stats
- Simplify MapWidget to single rendering path
- Maintains modding-friendly architecture

**Phase 3: Validation (Ongoing)**
- Add Strategy 2 registry with runtime assertion as safety net
- Keep even after data-driven approach (defense-in-depth)

## Implementation Checklist

When adding a new entity type, ensure:

- [ ] Entity class exists (e.g., `class Forge(Entity)`)
- [ ] EntityType enum has the type (e.g., `FORGE = "forge"`)
- [ ] YAML file has `symbol` and `color` metadata
- [ ] EntityLoader loads display metadata to Entity.stats
- [ ] Test file has test case for this entity type
- [ ] MapWidget rendering code handles this type (or uses entity metadata)
- [ ] Sidebar/UI shows relevant info for this type (if applicable)

## Files to Update

When adding new entity type:
1. `src/core/base/entity.py` - EntityType enum
2. `src/core/entities.py` - Entity subclass
3. `data/entities/*.yaml` or `data/balance/*.yaml` - Entity definitions
4. `src/core/entity_loader.py` - Loading logic (if needed)
5. `src/ui/textual/widgets/map_widget.py` - Rendering (until Strategy 1 done)
6. `tests/unit/ui/test_entity_rendering.py` - Test coverage

## Related Issues

- Entity display metadata in YAML not currently loaded
- MapWidget has manual rendering per entity type
- No forcing function for completeness
- Modding documentation should mention display metadata

## References

- Brogue (inspiration): Entities have glyph + foreColor + backColor
- Cogmind: Data-driven entity display (symbols in data files)
- NetHack: Monster symbols defined in central table
