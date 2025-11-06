# Brogue: Extract Dungeon Generation to YAML Configuration

## Context

You're working on the Brogue roguelike game, completing the final high-priority architectural improvement: making dungeon generation data-driven.

**Current Status:**
- 4 of 5 architectural pain points resolved (spawning, events, AI, formulas)
- Dungeon generation is currently hardcoded in `src/core/world.py`
- BSP (Binary Space Partitioning) algorithm parameters are magic numbers
- All 596 tests currently passing

**Goal:** Extract hardcoded dungeon generation parameters to `data/balance/dungeon_generation.yaml`, making dungeon layouts configurable without code changes.

---

## Problem Statement

Currently in `src/core/world.py`, dungeon generation uses hardcoded values:
- Room sizes (MIN_ROOM_SIZE, MAX_ROOM_SIZE)
- Split thresholds for BSP algorithm
- Corridor generation rules
- Special room placement logic
- Floor-specific variations

This makes it impossible to:
- Create custom dungeon types (small/large/linear/maze-like)
- Tune dungeon complexity per floor
- Experiment with different layouts without code changes
- Enable modding/configuration by non-programmers

---

## Success Criteria

✅ **Configuration File Created:**
- `data/balance/dungeon_generation.yaml` with comprehensive parameters
- Covers all hardcoded values in dungeon generation
- Well-documented with comments explaining each parameter
- Includes examples for different dungeon types (standard, small, large, maze)

✅ **Code Integration:**
- `ConfigLoader` extended with dungeon generation accessors
- `World` class refactored to read from configuration
- All magic numbers replaced with config lookups
- Fallback values for backwards compatibility

✅ **Testing:**
- All existing 596 tests still passing
- New tests for configuration loading (`test_config_loader.py`)
- Validation that different configs produce different dungeons
- Edge case testing (min/max values)

✅ **Documentation:**
- Config file has inline comments explaining parameters
- Code comments explain BSP algorithm and how config affects it
- README or doc explaining how to create custom dungeon types

---

## Implementation Plan

### Phase 1: Analysis (30 minutes)

**1.1 Study Current Implementation**

Read and understand the dungeon generation code:

```bash
# Main files to review
tia read src/core/world.py --section "dungeon generation"
tia read src/core/world.py --function generate_dungeon
tia read src/core/world.py --function _generate_bsp_dungeon
```

**1.2 Identify All Hardcoded Values**

Look for:
- Room dimension constants (MIN_ROOM_SIZE, MAX_ROOM_SIZE)
- BSP split thresholds
- Corridor width/placement rules
- Special room placement logic
- Floor-specific modifiers
- Random number ranges for generation

**1.3 Review Similar Patterns**

Study how other configs are structured:

```bash
tia read data/balance/spawning.yaml
tia read data/balance/ai_behaviors.yaml
tia read data/balance/formulas.yaml
```

### Phase 2: Configuration Design (30 minutes)

**2.1 Create Configuration Structure**

Design `data/balance/dungeon_generation.yaml` with sections:

```yaml
# Dungeon Generation Configuration
#
# Controls BSP-based dungeon generation algorithm parameters

# Base Room Configuration
rooms:
  min_width: 4        # Minimum room width (tiles)
  max_width: 10       # Maximum room width (tiles)
  min_height: 4       # Minimum room height (tiles)
  max_height: 10      # Maximum room height (tiles)
  min_area: 16        # Minimum room area (width × height)

# BSP Algorithm Parameters
bsp:
  min_split_size: 8   # Don't split regions smaller than this
  split_ratio_min: 0.4  # Minimum split ratio (40/60)
  split_ratio_max: 0.6  # Maximum split ratio (60/40)
  max_depth: 4        # Maximum BSP tree depth

# Corridor Configuration
corridors:
  width: 1            # Corridor width (tiles)
  style: "l_shaped"   # Options: straight, l_shaped, winding

# Special Rooms
special_rooms:
  forge_placement: "random"  # Where to place forge room
  vault_enabled: true
  vault_probability: 0.15    # 15% chance per floor

# Floor-Specific Overrides (optional)
floor_overrides:
  floor_1:
    rooms:
      max_width: 8    # Smaller rooms on floor 1
      max_height: 8
  floor_5:
    special_rooms:
      vault_probability: 0.3  # More vaults on deeper floors

# Dungeon Presets (for easy configuration)
presets:
  standard:
    # Current default settings
  small_rooms:
    rooms:
      max_width: 6
      max_height: 6
  large_rooms:
    rooms:
      min_width: 8
      max_width: 15
      min_height: 8
      max_height: 15
  maze:
    bsp:
      max_depth: 6
    corridors:
      style: "winding"

meta:
  version: "1.0.0"
  created: "2025-11-06"
  description: "Dungeon generation parameters for BSP algorithm"
```

**2.2 Design ConfigLoader Extensions**

Plan new methods for `src/core/config/config_loader.py`:

```python
class GameConfig:
    def get_room_min_width(self) -> int: ...
    def get_room_max_width(self) -> int: ...
    def get_room_min_height(self) -> int: ...
    def get_room_max_height(self) -> int: ...
    def get_bsp_min_split_size(self) -> int: ...
    def get_bsp_split_ratio_range(self) -> Tuple[float, float]: ...
    def get_corridor_width(self) -> int: ...
    def get_dungeon_preset(self, name: str) -> Dict[str, Any]: ...
    # ... etc
```

### Phase 3: Implementation (2-3 hours)

**3.1 Create Configuration File**

```bash
# Create the YAML file
# Location: /home/scottsen/src/projects/brogue/data/balance/dungeon_generation.yaml
```

Use the structure designed in Phase 2, ensuring:
- All values have comments explaining their purpose
- Sensible defaults that match current behavior
- Include preset examples

**3.2 Extend ConfigLoader**

Edit `src/core/config/config_loader.py`:

1. Add dungeon_generation to `__init__`:
```python
self.dungeon_generation = self._load_yaml(
    config_dir / 'dungeon_generation.yaml'
)
```

2. Add accessor methods following the pattern from formulas/AI:
```python
def get_room_min_width(self) -> int:
    """Get minimum room width for dungeon generation."""
    return self.dungeon_generation['rooms']['min_width']

def get_room_max_width(self) -> int:
    """Get maximum room width for dungeon generation."""
    return self.dungeon_generation['rooms']['max_width']

# ... add all other accessors
```

3. Add method to get floor-specific overrides:
```python
def get_dungeon_config_for_floor(self, floor: int) -> Dict[str, Any]:
    """Get dungeon configuration with floor-specific overrides applied."""
    base_config = self.dungeon_generation.copy()

    overrides = base_config.get('floor_overrides', {}).get(f'floor_{floor}', {})
    # Merge overrides into base config

    return merged_config
```

**3.3 Refactor World Class**

Edit `src/core/world.py`:

1. Import ConfigLoader:
```python
from .config.config_loader import ConfigLoader
```

2. Replace all hardcoded constants with config lookups:

**Before:**
```python
MIN_ROOM_SIZE = 4
MAX_ROOM_SIZE = 10

def _create_room(self):
    width = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
    height = random.randint(MIN_ROOM_SIZE, MAX_ROOM_SIZE)
```

**After:**
```python
def _create_room(self):
    config = ConfigLoader.get_config()
    width = random.randint(
        config.get_room_min_width(),
        config.get_room_max_width()
    )
    height = random.randint(
        config.get_room_min_height(),
        config.get_room_max_height()
    )
```

3. Apply this pattern to all hardcoded values:
   - BSP split thresholds
   - Corridor generation
   - Special room placement
   - Any other magic numbers

4. Add error handling with fallbacks:
```python
try:
    config = ConfigLoader.get_config()
    min_width = config.get_room_min_width()
except Exception:
    # Fallback to hardcoded defaults if config fails
    min_width = 4
```

### Phase 4: Testing (1-2 hours)

**4.1 Verify Existing Tests Pass**

```bash
cd /home/scottsen/src/projects/brogue
python -m pytest --tb=line -q
```

Should still have all 596 tests passing.

**4.2 Add Configuration Tests**

Edit `tests/unit/test_config_loader.py`:

```python
def test_dungeon_generation_config_loads():
    """Test that dungeon generation config loads successfully."""
    config = ConfigLoader.get_config()

    # Test room configuration
    assert config.get_room_min_width() > 0
    assert config.get_room_max_width() >= config.get_room_min_width()
    assert config.get_room_min_height() > 0
    assert config.get_room_max_height() >= config.get_room_min_height()

    # Test BSP parameters
    assert config.get_bsp_min_split_size() > 0

    # Test corridor configuration
    assert config.get_corridor_width() > 0

def test_dungeon_floor_overrides():
    """Test floor-specific configuration overrides."""
    config = ConfigLoader.get_config()

    # Test that floor overrides are applied correctly
    floor_1_config = config.get_dungeon_config_for_floor(1)
    floor_5_config = config.get_dungeon_config_for_floor(5)

    # Verify overrides are different
    assert floor_1_config != floor_5_config  # If overrides exist

def test_dungeon_preset_loading():
    """Test loading dungeon presets."""
    config = ConfigLoader.get_config()

    standard = config.get_dungeon_preset('standard')
    assert standard is not None

    maze = config.get_dungeon_preset('maze')
    assert maze is not None
```

**4.3 Validate Different Configs Produce Different Dungeons**

Add integration test:

```python
def test_config_affects_dungeon_generation():
    """Verify that configuration changes affect dungeon generation."""
    # This might be a visual/manual test or statistical test
    # Generate dungeons with different configs and verify differences
    pass
```

**4.4 Run Full Test Suite**

```bash
python -m pytest --tb=line -q
python -m pytest tests/unit/test_config_loader.py -v
```

### Phase 5: Documentation (30 minutes)

**5.1 Update Configuration File**

Ensure `dungeon_generation.yaml` has:
- Clear comments for every parameter
- Examples showing how to create custom dungeon types
- Meta section with version and description

**5.2 Add Code Comments**

In `world.py`, add comments explaining:
- How BSP algorithm works
- How configuration affects generation
- What each parameter controls

**5.3 Create Usage Examples**

Add to file or create `docs/DUNGEON_CONFIGURATION.md`:

```markdown
# Dungeon Configuration Guide

## Creating Custom Dungeon Types

### Small Cramped Dungeons
Edit `data/balance/dungeon_generation.yaml`:
```yaml
rooms:
  max_width: 6
  max_height: 6
```

### Large Open Dungeons
```yaml
rooms:
  min_width: 8
  max_width: 15
  min_height: 8
  max_height: 15
```

### Maze-like Dungeons
```yaml
bsp:
  max_depth: 6
corridors:
  style: "winding"
```
```

---

## Key Files

**Configuration:**
- `/home/scottsen/src/projects/brogue/data/balance/dungeon_generation.yaml` (CREATE)

**Implementation:**
- `/home/scottsen/src/projects/brogue/src/core/world.py` (MODIFY)
- `/home/scottsen/src/projects/brogue/src/core/config/config_loader.py` (MODIFY)

**Testing:**
- `/home/scottsen/src/projects/brogue/tests/unit/test_config_loader.py` (MODIFY)

**Documentation:**
- Consider creating `docs/DUNGEON_CONFIGURATION.md` (OPTIONAL)

---

## Technical Considerations

### 1. Binary Space Partitioning (BSP)

The dungeon generation uses BSP algorithm:
1. Start with full map rectangle
2. Recursively split into smaller regions
3. Create a room in each leaf region
4. Connect rooms with corridors

**Config Impact:**
- `bsp.min_split_size` - stops splitting when region too small
- `bsp.max_depth` - limits recursion depth (more depth = more rooms)
- `bsp.split_ratio_*` - controls how evenly regions are split

### 2. Backwards Compatibility

Use try/except with fallbacks:
```python
try:
    min_width = config.get_room_min_width()
except Exception:
    min_width = 4  # Original hardcoded value
```

This ensures code works even if config file is missing.

### 3. Random Number Generation

Dungeon generation uses RNG, so:
- Same config + same seed = same dungeon
- Different configs = different dungeons (even with same seed)
- Test this behavior to validate config is working

### 4. Performance

Configuration loading happens once at startup (singleton pattern).
No performance impact during dungeon generation.

---

## Testing Strategy

**Unit Tests:**
- Config file loads correctly ✓
- All accessor methods work ✓
- Floor overrides apply correctly ✓
- Preset loading works ✓

**Integration Tests:**
- Dungeon generation completes successfully ✓
- Different configs produce different results ✓
- All room sizes within configured bounds ✓

**Regression Tests:**
- All 596 existing tests still pass ✓
- Game plays normally ✓

---

## Commit Strategy

**Commit 1: Configuration Structure**
```
Add dungeon generation configuration file

- Create data/balance/dungeon_generation.yaml
- Define all BSP algorithm parameters
- Add room size, corridor, and special room configs
- Include preset examples (standard, small, large, maze)
```

**Commit 2: ConfigLoader Integration**
```
Extend ConfigLoader for dungeon generation

- Add dungeon_generation.yaml loading
- Implement accessor methods for all parameters
- Add floor-specific override support
- Add preset loading functionality
```

**Commit 3: World Class Refactoring**
```
Refactor World to use dungeon generation config

- Replace hardcoded constants with config lookups
- Apply configuration to BSP algorithm
- Add fallback values for backwards compatibility
- Maintain all existing behavior as default
```

**Commit 4: Testing & Validation**
```
Add tests for dungeon generation configuration

- Test config file loading
- Test all accessor methods
- Validate floor overrides
- Verify different configs affect generation
```

---

## Expected Timeline

- **Phase 1 (Analysis):** 30 minutes
- **Phase 2 (Design):** 30 minutes
- **Phase 3 (Implementation):** 2-3 hours
- **Phase 4 (Testing):** 1-2 hours
- **Phase 5 (Documentation):** 30 minutes

**Total: 4.5 - 6.5 hours** (fits within 3-4 day estimate with buffer)

---

## Success Validation

Before marking complete, verify:

1. ✅ `data/balance/dungeon_generation.yaml` exists and is well-documented
2. ✅ `ConfigLoader` has all necessary accessor methods
3. ✅ `World` class reads from configuration
4. ✅ All 596+ tests passing
5. ✅ No hardcoded dungeon generation values remain in `world.py`
6. ✅ Documentation explains how to customize dungeons
7. ✅ Commits are clean with good messages

---

## Questions / Blockers

If you encounter issues:

1. **Can't find hardcoded values?**
   - Search for: `MIN_ROOM`, `MAX_ROOM`, `SPLIT`, magic numbers in world.py

2. **Tests failing after refactor?**
   - Check that default config values match original hardcoded values
   - Ensure random seed handling hasn't changed

3. **Config not loading?**
   - Verify YAML syntax with `python -c "import yaml; yaml.safe_load(open('data/balance/dungeon_generation.yaml'))"`
   - Check ConfigLoader singleton pattern

4. **BSP algorithm unclear?**
   - Read existing code carefully
   - BSP creates tree of rectangular regions, then places rooms in leaves
   - Config controls split thresholds and room sizes

---

## Related Work

This completes the architectural refactoring series:
- ✅ PR #11 - Spawning configuration
- ✅ PR #12 - EventBus system
- ✅ PR #13 - AI behaviors + formulas
- ✅ PR #14 - Bot equipment intelligence
- 🔄 **THIS PR** - Dungeon generation configuration

After this, all 5 high-priority architectural improvements will be complete!

---

**Repository:** `/home/scottsen/src/projects/brogue`
**Branch:** Create new branch: `feature/dungeon-generation-config`
**Current Tests:** 596 passing
**Target:** 596+ passing (add new config tests)

Good luck! This is the final piece to complete the architectural cleanup. 🎯
