# Veinborn Randomness, Replayability & Seeding Analysis

**Date**: 2025-10-25
**Session**: lightning-sage-1025
**Status**: 🔴 **NO SEEDING CURRENTLY IMPLEMENTED**

---

## Executive Summary

**Current State**: ❌ No seed system, games are NOT replayable

**Impact**:
- ❌ Can't reproduce bugs
- ❌ Can't replay interesting runs
- ❌ Can't do seeded competitions
- ❌ Can't test deterministically
- ❌ No speedrunning practice mode

**Recommendation**: Implement seed system (optional enhancement for Phase 4)

---

## Current Randomness Usage

### Where Random is Used

```bash
$ grep -r "import random" src/core/

src/core/spawning/entity_spawner.py:import random
src/core/entities.py:import random
src/core/world.py:import random
src/core/game.py:import random
```

### Specific Random Calls

#### 1. Entity Spawning (`entity_spawner.py`)

```python
def _weighted_random_choice(self, weights: Dict[str, int]) -> str:
    """Weighted random selection for monster/ore types."""
    return random.choice(items)  # ← NOT SEEDED
```

**What it affects:**
- Which monsters spawn on each floor
- Which ore types appear

**Current behavior:** Different every game

#### 2. Ore Generation (`entities.py`)

```python
def generate_random(cls, ore_type: str, x: int, y: int, floor: int):
    """Generate ore with random properties."""
    # Jackpot spawn (5% chance)
    if random.random() < 0.05:  # ← NOT SEEDED
        # ... boost properties

    hardness = random.randint(min_prop, max_prop)      # ← NOT SEEDED
    conductivity = random.randint(min_prop, max_prop)  # ← NOT SEEDED
    malleability = random.randint(min_prop, max_prop)  # ← NOT SEEDED
    purity = random.randint(min_prop, max_prop)        # ← NOT SEEDED
    density = random.randint(min_prop, max_prop)       # ← NOT SEEDED
```

**What it affects:**
- Ore vein quality (0-100 for each property)
- Jackpot spawns (rare, high-quality ore)

**Current behavior:** Different every game

#### 3. Map Generation (`world.py`)

```python
def _generate_bsp_tree(self, ...):
    """Generate dungeon using Binary Space Partitioning."""
    split_horizontal = random.choice([True, False])    # ← NOT SEEDED
    split_pos = random.randint(height // 3, ...)       # ← NOT SEEDED

def _create_room(self, node):
    """Create room in BSP leaf."""
    room_width = random.randint(min_room_size, ...)    # ← NOT SEEDED
    room_height = random.randint(min_room_size, ...)   # ← NOT SEEDED
    room_x = node.x + padding + random.randint(...)    # ← NOT SEEDED
    room_y = node.y + padding + random.randint(...)    # ← NOT SEEDED

def _create_corridors(self, ...):
    """Connect rooms with corridors."""
    if random.random() < 0.5:        # ← NOT SEEDED (L or zig-zag)
    if random.random() < 0.1:        # ← NOT SEEDED (door placement)
```

**What it affects:**
- Room placement and sizes
- Corridor routes
- Door positions
- Overall dungeon layout

**Current behavior:** Completely different map every game

---

## What This Means

### Problem 1: Can't Reproduce Bugs 🐛

**Scenario:**
```
Player: "I found a bug on floor 5!"
Developer: "Can you give me the seed to reproduce it?"
Player: "...there are no seeds"
Developer: "Well, I guess we'll never see that bug"
```

**Impact:** Bugs in rare configurations go unfixed

### Problem 2: Can't Replay Interesting Runs 🎮

**Scenario:**
```
Player: "OMG I just got 3 mithril veins with 95+ purity on floor 1!"
Friend: "No way! Let me try!"
Player: "...I can't share the seed"
Friend: "Sad face"
```

**Impact:** Cool discoveries aren't shareable

### Problem 3: Can't Do Seeded Competitions 🏆

**Scenario:**
```
Tournament: "Everyone play seed 12345"
Veinborn: "I don't have seeds"
Tournament: "...nevermind then"
```

**Impact:** No competitive scene possible

### Problem 4: Can't Test Deterministically 🧪

**Scenario:**
```python
def test_floor_5_is_hard():
    game = Game()
    game.start_new_game()
    # ... get to floor 5 ...
    # Floor 5 different every test run!
    assert ??? # What do we even test?
```

**Impact:** Flaky tests, hard to validate balance

### Problem 5: No Speedrunning Practice 🏃

**Scenario:**
```
Speedrunner: "I want to practice seed 'good_start' 100 times"
Veinborn: "Every run is different"
Speedrunner: "How do I optimize routing?"
```

**Impact:** No speedrunning community

---

## How Other Roguelikes Handle This

### Example 1: Nethack

```
Seed: 1234567890
Every run with seed 1234567890 is IDENTICAL:
- Same dungeon layout
- Same monster spawns
- Same item locations
- 100% reproducible
```

### Example 2: Spelunky

```
Daily Challenge: Seed 2025-10-25
Everyone gets same seed for 24 hours
Leaderboards compare performance
```

### Example 3: Binding of Isaac

```
Seed: ABCD 1234
Share seeds via code
"Try this broken OP seed!"
Community engagement
```

### Example 4: Dwarf Fortress

```
World Seed: fortress2025
Adventure Mode Seed: adventure2025
Different seeds for different random elements
```

---

## Proposed Solution: Seed System

### Design Goals

1. **Optional** - Seed is optional (default: random)
2. **Persistent** - Seed saved with game state
3. **Shareable** - Human-readable seed format
4. **Complete** - Controls ALL randomness
5. **Backward Compatible** - Old saves still work

### Architecture

```python
# NEW: src/core/rng.py
"""
Centralized Random Number Generator with seeding support.

Design:
- Singleton RNG instance
- Seed-based initialization
- All randomness goes through this
- Reproducible if seeded
"""

import random
from typing import Optional

class GameRNG:
    """
    Centralized RNG for reproducible gameplay.

    Usage:
        rng = GameRNG.get_instance()
        value = rng.randint(1, 10)

    Seeding:
        GameRNG.initialize(seed=12345)  # Seeded run
        GameRNG.initialize()            # Random run
    """

    _instance: Optional['GameRNG'] = None
    _seed: Optional[int] = None

    def __init__(self, seed: Optional[int] = None):
        """Initialize RNG with optional seed."""
        self._seed = seed
        self._rng = random.Random(seed)

    @classmethod
    def initialize(cls, seed: Optional[int] = None) -> 'GameRNG':
        """
        Initialize global RNG instance.

        Args:
            seed: Seed value (None = random)

        Returns:
            GameRNG instance
        """
        cls._instance = cls(seed)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'GameRNG':
        """Get global RNG instance (lazy init)."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def seed(self) -> Optional[int]:
        """Get current seed (None if random)."""
        return self._seed

    # Delegate to internal RNG
    def randint(self, a: int, b: int) -> int:
        """Random integer in [a, b]."""
        return self._rng.randint(a, b)

    def random(self) -> float:
        """Random float in [0.0, 1.0)."""
        return self._rng.random()

    def choice(self, seq):
        """Choose random element from sequence."""
        return self._rng.choice(seq)

    def shuffle(self, seq):
        """Shuffle sequence in-place."""
        return self._rng.shuffle(seq)

    def getstate(self):
        """Get RNG state (for save/load)."""
        return self._rng.getstate()

    def setstate(self, state):
        """Set RNG state (for save/load)."""
        self._rng.setstate(state)
```

### Integration Points

#### 1. GameState (store seed)

```python
@dataclass
class GameState:
    # ... existing fields ...

    # NEW: Seed for reproducibility
    seed: Optional[int] = None
    rng_state: Optional[tuple] = None  # For save/load
```

#### 2. Game (initialize RNG)

```python
class Game:
    def start_new_game(self, seed: Optional[int] = None) -> None:
        """
        Start new game with optional seed.

        Args:
            seed: Seed value (None = random)
        """
        # Initialize RNG
        rng = GameRNG.initialize(seed)

        # Store seed in state
        self.state = GameState(
            player=player,
            seed=rng.seed,  # Store for display/save
            # ... other fields ...
        )
```

#### 3. Replace All random.* Calls

**Before:**
```python
import random
monster_type = random.choice(items)
```

**After:**
```python
from core.rng import GameRNG
monster_type = GameRNG.get_instance().choice(items)
```

### Usage Examples

#### Random Run (Current Behavior)

```python
game = Game()
game.start_new_game()  # seed=None (default)
# Different every time
```

#### Seeded Run (Reproducible)

```python
game = Game()
game.start_new_game(seed=12345)
# Same every time with seed 12345
```

#### Share Seeds

```python
# Player finds awesome run
game = Game()
game.start_new_game(seed=99999)
# Share "Seed: 99999" with friends
# Everyone gets same experience!
```

#### Testing

```python
def test_floor_5_balance():
    """Test floor 5 is beatable (deterministic)."""
    game = Game()
    game.start_new_game(seed=54321)  # Fixed seed
    # ... get to floor 5 ...
    # ALWAYS same monsters, same layout
    # Test is reproducible!
```

---

## Implementation Checklist

### Phase 1: Core RNG System

- [ ] Create `src/core/rng.py` with GameRNG class
- [ ] Add `seed` and `rng_state` to GameState
- [ ] Update Game.start_new_game() to accept seed
- [ ] Write tests for GameRNG

### Phase 2: Migration

- [ ] Replace `random.*` in `entity_spawner.py` with GameRNG
- [ ] Replace `random.*` in `entities.py` with GameRNG
- [ ] Replace `random.*` in `world.py` with GameRNG
- [ ] Remove unused `import random` statements

### Phase 3: UI Integration

- [ ] Add seed display to UI
- [ ] Add seed input for new game
- [ ] Show seed in game over screen
- [ ] Add seed to save files

### Phase 4: Testing & Validation

- [ ] Test same seed = same game
- [ ] Test different seeds = different games
- [ ] Test save/load preserves seed
- [ ] Add deterministic balance tests

---

## Benefits

### For Players

✅ **Share discoveries** - "Try seed 12345!"
✅ **Replay great runs** - Practice favorite layouts
✅ **Compete fairly** - Same seed competitions
✅ **Report bugs** - "Bug on seed X, floor Y"

### For Developers

✅ **Reproduce bugs** - Debug with exact conditions
✅ **Test deterministically** - Reliable test results
✅ **Balance testing** - Test specific scenarios
✅ **Performance profiling** - Consistent conditions

### For Community

✅ **Speedrunning** - Practice mode with seeds
✅ **Competitions** - Fair seeded tournaments
✅ **Content creation** - "Top 10 broken seeds"
✅ **Challenge runs** - Community seed challenges

---

## Trade-offs

### Pros

✅ Reproducible gameplay
✅ Better debugging
✅ Community engagement
✅ Competitive scene
✅ Deterministic testing

### Cons

⚠️ More complex RNG management
⚠️ Must track RNG state in saves
⚠️ Breaking change (old saves incompatible)
⚠️ Migration effort (replace all random.* calls)

### Mitigation

- Make seed optional (default: random)
- Handle old saves gracefully (generate new seed)
- Comprehensive testing
- Clear migration guide

---

## Current vs Proposed

### Current State

```python
# Somewhere in code
import random
value = random.randint(1, 100)  # ← Who knows what this affects?

# Start game
game.start_new_game()  # Different every time

# Bug report
"I found a bug!"
"Can you reproduce it?"
"...no"
```

### With Seed System

```python
# Centralized RNG
from core.rng import GameRNG
value = GameRNG.get_instance().randint(1, 100)  # ← Controlled!

# Start game
game.start_new_game(seed=12345)  # Same every time!

# Bug report
"I found a bug on seed 12345, floor 5"
"Thanks! Reproducing now..."
```

---

## Seed Format Ideas

### Simple: Integer

```python
seed = 12345
game.start_new_game(seed=12345)
```

**Pros:** Easy to implement
**Cons:** Not memorable

### Readable: String Hash

```python
seed_str = "epic-victory-2025"
seed = hash(seed_str) & 0x7FFFFFFF  # Convert to int
game.start_new_game(seed=seed)
```

**Pros:** Memorable, shareable
**Cons:** Collisions possible

### Hybrid: String or Int

```python
def parse_seed(seed_input):
    """Accept string or int."""
    if isinstance(seed_input, int):
        return seed_input
    return hash(seed_input) & 0x7FFFFFFF

game.start_new_game(seed=parse_seed("awesome-run"))
game.start_new_game(seed=parse_seed(12345))
```

**Pros:** Best of both
**Cons:** More complex

---

## Save/Load Considerations

### Save Format (with seed)

```json
{
  "version": "2.0",
  "seed": 12345,
  "rng_state": "(3, tuple_of_ints, None)",
  "turn_count": 150,
  "current_floor": 5,
  "player": { ... },
  "entities": [ ... ]
}
```

### Load Logic

```python
def load_game(save_data):
    """Load game with seed restoration."""
    # Restore RNG
    seed = save_data.get('seed')
    rng = GameRNG.initialize(seed)

    if 'rng_state' in save_data:
        # Restore exact RNG state
        rng.setstate(save_data['rng_state'])

    # Restore game state
    # ...
```

---

## Testing Strategy

### Determinism Test

```python
def test_same_seed_same_game():
    """Same seed produces identical games."""
    # Run 1
    game1 = Game()
    game1.start_new_game(seed=12345)
    floor1_monsters = [m.name for m in game1.get_monsters()]

    # Run 2
    game2 = Game()
    game2.start_new_game(seed=12345)
    floor2_monsters = [m.name for m in game2.get_monsters()]

    # Should be identical
    assert floor1_monsters == floor2_monsters
```

### Uniqueness Test

```python
def test_different_seeds_different_games():
    """Different seeds produce different games."""
    game1 = Game()
    game1.start_new_game(seed=111)
    floor1_monsters = [m.name for m in game1.get_monsters()]

    game2 = Game()
    game2.start_new_game(seed=222)
    floor2_monsters = [m.name for m in game2.get_monsters()]

    # Should be different (statistically)
    assert floor1_monsters != floor2_monsters
```

### Save/Load Test

```python
def test_save_load_preserves_rng():
    """Save/load maintains RNG state."""
    game = Game()
    game.start_new_game(seed=12345)

    # Generate some random values
    rng = GameRNG.get_instance()
    before_save = [rng.randint(1, 100) for _ in range(10)]

    # Save game
    save_data = game.save()

    # Load game
    game2 = Game()
    game2.load(save_data)

    # Generate more values
    rng2 = GameRNG.get_instance()
    after_load = [rng2.randint(1, 100) for _ in range(10)]

    # Sequence should continue correctly
    # (not restart from seed)
```

---

## Recommendation

### Priority: MEDIUM (Phase 4 Enhancement)

**Rationale:**
- Not blocking current gameplay
- Significant value for community
- Enables competitive scene
- Better debugging

**Timeline:**
- Phase 1-3: Complete (done!)
- Phase 4: Code quality + RNG system
- Estimated: 2-3 days work

**Risk:** LOW
- Well-understood pattern
- Isolated changes (RNG class)
- Backward compatible (optional seed)

---

## Summary

### Current State: 🔴 NO SEEDING

**Randomness used in:**
- Entity spawning (monster types)
- Ore generation (properties)
- Map generation (layout)

**Problems:**
- ❌ Can't reproduce bugs
- ❌ Can't replay runs
- ❌ Can't do competitions
- ❌ Can't test deterministically

### Proposed Solution: Seed System

**Core idea:**
- Centralized GameRNG class
- Optional seed parameter
- All randomness goes through it
- Reproducible if seeded

**Benefits:**
- ✅ Reproducible gameplay
- ✅ Better debugging
- ✅ Community features
- ✅ Competitive scene
- ✅ Deterministic testing

**Implementation:**
- Create GameRNG class
- Migrate random.* calls
- Add UI integration
- Test thoroughly

---

## Next Steps

**If you want seeding:**
1. Create `src/core/rng.py` with GameRNG
2. Add seed to GameState
3. Migrate random.* calls
4. Test determinism

**If not priority:**
- Document as future enhancement
- Keep in backlog for Phase 4
- Focus on Phase 3 (Data-Driven Entities) first

---

**Decision needed:** Implement now, or later?

**My recommendation:** Phase 4 enhancement (after Phase 3 complete)

**Reasoning:** Current refactoring is awesome, don't want to distract from completing Phase 3 next!

---

**Status**: 🔴 Not implemented (documented for future)
**Priority**: Medium (Phase 4)
**Complexity**: Medium (2-3 days)
**Risk**: Low (well-understood)
**Value**: High (community features)
