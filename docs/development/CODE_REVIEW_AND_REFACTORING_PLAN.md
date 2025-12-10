# Veinborn Code Review & Refactoring Plan

**Date**: 2025-10-25
**Session**: spark-storm-1025
**Reviewer**: Claude Code
**Status**: ANALYSIS COMPLETE - Ready for Implementation

---

## Executive Summary

The Veinborn codebase demonstrates **solid architectural foundations** with clean separation of concerns, proper use of design patterns, and good type safety. However, there are significant opportunities to improve **modularity**, **maintainability**, and **extensibility** through targeted refactoring.

**Overall Assessment**: 7/10
- Strengths: Clean architecture, Action pattern, Entity system, type hints
- Needs Work: Configuration management, code duplication, separation of concerns

---

## Strengths of Current Implementation

### 1. Clean Architecture ✅
```python
GameState → Holds all mutable state (clean data layer)
GameContext → Safe API facade (controlled access)
Systems → Process game logic (AI, etc.)
Actions → Drive state changes (serializable, testable)
```

**Why This is Good:**
- Clear separation between data and logic
- Testable in isolation
- Future-proof for multiplayer (serializable actions)
- Safe for Lua integration (controlled API)

### 2. Strong Design Patterns ✅
- **Action Pattern**: All game actions are first-class objects
- **Entity Hierarchy**: Unified base class with clean inheritance
- **Facade Pattern**: GameContext provides safe API
- **Factory Methods**: Monster.create_goblin(), etc.

### 3. Type Safety ✅
- Consistent use of type hints
- Dataclasses for structured data
- Enums for type-safe constants (EntityType, ActionResult)

### 4. Logging ✅
- Comprehensive structured logging
- Different log levels (debug, info, warning, error)
- Contextual information in log messages

---

## Critical Issues to Address

### Issue #1: Configuration Hell 🔥 **HIGH PRIORITY**

**Problem**: Game balance data is hardcoded throughout the codebase.

**Location**: `src/core/game.py:69-127`
```python
# BAD: Hardcoded magic numbers
if floor == 1:
    monster = Monster.create_goblin(x, y)
elif floor == 2:
    if i % 3 == 0:
        monster = Monster.create_orc(x, y)
# ... 50+ lines of similar code
```

**Impact**:
- Can't tweak game balance without changing code
- No data-driven design (violates design docs)
- Difficult to test different configurations
- Breaks "content should be in YAML" principle

**Solution**: Extract to configuration system

**New Structure**:
```
data/
├── balance/
│   ├── monster_spawns.yaml    # Floor-based spawn weights
│   ├── ore_veins.yaml          # Ore distribution by floor
│   └── game_constants.yaml     # All magic numbers
├── entities/
│   ├── monsters.yaml           # Monster definitions
│   ├── ores.yaml               # Ore type definitions
│   └── items.yaml              # Item definitions (future)
```

**Example YAML**:
```yaml
# data/balance/monster_spawns.yaml
floor_spawns:
  floor_1:
    count: 3
    weights:
      goblin: 100
  floor_2:
    count: 4
    weights:
      goblin: 67
      orc: 33
  floors_3_5:
    count_formula: "3 + floor // 2"
    weights:
      goblin: 50
      orc: 40
      troll: 10
```

**Benefits**:
- Easy balance tuning (no code changes)
- Data-driven (aligns with design vision)
- Can load custom content mods
- Better for testing (swap configs)

---

### Issue #2: God Class Anti-Pattern 🔥 **HIGH PRIORITY**

**Problem**: `Game` class has too many responsibilities (500+ lines)

**Current Responsibilities**:
- Game loop orchestration
- Monster spawning logic
- Ore vein spawning logic
- Turn processing
- Floor generation
- Player action handling
- Entity cleanup

**Violation**: Single Responsibility Principle

**Solution**: Extract into focused classes

**New Architecture**:
```python
# src/core/game.py (simplified)
class Game:
    """Orchestrates game systems (< 200 lines)"""
    def __init__(self):
        self.state = GameState()
        self.context = GameContext(self.state)
        self.spawner = EntitySpawner(config)
        self.turn_processor = TurnProcessor(self.context)
        self.floor_manager = FloorManager(self.context)

    def start_new_game(self):
        self.state = GameState(...)
        self.spawner.spawn_initial_entities(self.state)

    def handle_player_action(self, action_type, **kwargs):
        outcome = self._create_action(action_type, **kwargs).execute(self.context)
        if outcome.took_turn:
            self.turn_processor.process_turn()

# src/core/spawning/entity_spawner.py
class EntitySpawner:
    """Spawns monsters, ore veins from config"""
    def spawn_monsters_for_floor(self, floor: int) -> List[Monster]
    def spawn_ore_veins_for_floor(self, floor: int) -> List[OreVein]

# src/core/turn_processor.py
class TurnProcessor:
    """Handles turn progression, HP regen, AI updates"""
    def process_turn(self) -> None

# src/core/floor_manager.py
class FloorManager:
    """Manages floor transitions, victory conditions"""
    def descend_floor(self) -> None
```

**Benefits**:
- Each class < 200 lines (easier to understand)
- Single responsibility (easier to test)
- Better modularity (swap implementations)
- Clearer code organization

---

### Issue #3: Factory Sprawl 🔥 **MEDIUM PRIORITY**

**Problem**: Monster creation uses factory methods, should be data-driven

**Current Pattern**:
```python
# src/core/entities.py
class Monster(Entity):
    @classmethod
    def create_goblin(cls, x, y):
        return cls(name="Goblin", hp=6, attack=3, defense=1, ...)

    @classmethod
    def create_orc(cls, x, y):
        return cls(name="Orc", hp=12, attack=5, defense=2, ...)

    # ... 10+ more factory methods
```

**Problems**:
- New monster = new code
- Can't create monsters from YAML (future requirement)
- Stats hardcoded in Python
- Violates "content should be data" principle

**Solution**: Data-driven entity creation

```yaml
# data/entities/monsters.yaml
goblin:
  name: "Goblin"
  display_char: "g"
  color: "green"
  stats:
    hp: 6
    attack: 3
    defense: 1
    xp_reward: 5
  ai_type: "aggressive"
  description: "A weak but sneaky creature"

orc:
  name: "Orc"
  display_char: "o"
  color: "red"
  stats:
    hp: 12
    attack: 5
    defense: 2
    xp_reward: 15
  ai_type: "aggressive"
  description: "A brutish warrior"
```

```python
# src/core/content/entity_loader.py
class EntityLoader:
    """Load entity definitions from YAML"""

    def __init__(self, data_dir: Path):
        self.definitions = self._load_all_definitions(data_dir)

    def create_monster(self, monster_type: str, x: int, y: int) -> Monster:
        """Create monster from definition"""
        defn = self.definitions['monsters'][monster_type]
        return Monster(
            name=defn['name'],
            x=x, y=y,
            hp=defn['stats']['hp'],
            attack=defn['stats']['attack'],
            defense=defn['stats']['defense'],
            xp_reward=defn['stats']['xp_reward'],
            content_id=monster_type,
        )
```

**Benefits**:
- Add new monsters without code changes
- Designers can edit YAML files
- Easy to balance (tweak YAML, reload)
- Supports modding (custom YAML files)
- Aligns with Phase 3 Lua content system

---

### Issue #4: Duplicate Actor Lookup 🔥 **MEDIUM PRIORITY**

**Problem**: Every Action class duplicates actor lookup logic

**Example**: `src/core/actions/move_action.py:27-31, 96-100`
```python
# BAD: Duplicated in every action
def execute(self, context: GameContext) -> ActionOutcome:
    actor = context.get_entity(self.actor_id)
    if not actor:
        actor = context.get_player()
    if not actor:
        return ActionOutcome.failure("Actor not found")
```

**Impact**:
- Code duplication (DRY violation)
- Error-prone (easy to forget checks)
- Inconsistent error handling

**Solution**: Base class helper method

```python
# src/core/base/action.py
class Action(ABC):
    """Base class for all actions"""

    def _get_actor(self, context: 'GameContext') -> Optional['Entity']:
        """
        Get the actor entity (helper for subclasses).

        Tries entity registry first, then player special case.
        """
        actor = context.get_entity(self.actor_id)
        if not actor and self.actor_id == context.get_player().entity_id:
            actor = context.get_player()
        return actor

    def _get_actor_or_fail(self, context: 'GameContext') -> 'Entity':
        """Get actor or raise ActionExecutionError"""
        actor = self._get_actor(context)
        if not actor:
            raise ActionExecutionError(f"Actor not found: {self.actor_id}")
        return actor
```

**Usage in Subclasses**:
```python
class MoveAction(Action):
    def execute(self, context: GameContext) -> ActionOutcome:
        try:
            actor = self._get_actor_or_fail(context)
        except ActionExecutionError as e:
            return ActionOutcome.failure(str(e))

        # Rest of logic...
```

---

### Issue #5: Magic Strings & Numbers 🔥 **MEDIUM PRIORITY**

**Problem**: String literals and magic numbers scattered throughout code

**Examples**:
```python
# BAD: Magic strings
action_type == 'move'
ai_type = 'aggressive'
content_id = 'goblin'

# BAD: Magic numbers
if len(self.inventory) >= 20:  # Why 20?
if self.state.turn_count % 10 == 0:  # Why 10?
xp_for_next_level = current_level * 100  # Why 100?
```

**Solution**: Constants and Enums

```python
# src/core/constants.py
"""Game constants and balance values"""

# Inventory
MAX_INVENTORY_SIZE = 20

# HP Regeneration
HP_REGEN_INTERVAL_TURNS = 10
HP_REGEN_AMOUNT = 1

# Experience
XP_PER_LEVEL_BASE = 100
HP_GAIN_PER_LEVEL = 5
ATTACK_GAIN_PER_LEVEL = 1
DEFENSE_GAIN_PER_LEVEL = 1

# Victory
VICTORY_FLOOR = 100
```

```python
# src/core/base/entity.py (additions)
class AIType(Enum):
    """AI behavior types"""
    PASSIVE = "passive"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    FLEEING = "fleeing"
```

**Benefits**:
- Self-documenting (names explain purpose)
- Easy to tune (change in one place)
- Type-safe (Enums prevent typos)
- Find all usages (grep for constant name)

---

### Issue #6: Error Handling Inconsistency 🔥 **LOW PRIORITY**

**Problem**: Mix of None returns, False returns, and logging

**Examples**:
```python
# Pattern 1: Return None
def get_entity(self, entity_id: str) -> Optional[Entity]:
    return self.game_state.entities.get(entity_id)

# Pattern 2: Return False
def add_to_inventory(self, item: Entity) -> bool:
    if len(self.inventory) >= 20:
        return False  # But why? No error info!
    self.inventory.append(item)
    return True

# Pattern 3: Log and continue
if not context.is_walkable(new_x, new_y):
    logger.warning("Move blocked")
    return False
```

**Solution**: Consistent error handling strategy

```python
# src/core/exceptions.py
"""Game-specific exceptions"""

class VeinbornException(Exception):
    """Base exception for all game errors"""
    pass

class InventoryFullError(VeinbornException):
    """Raised when inventory is full"""
    pass

class InvalidActionError(VeinbornException):
    """Raised when action cannot be executed"""
    pass

class EntityNotFoundError(VeinbornException):
    """Raised when entity lookup fails"""
    pass
```

**Updated Code**:
```python
def add_to_inventory(self, item: Entity) -> None:
    """
    Add item to inventory.

    Raises:
        InventoryFullError: If inventory is at max capacity
    """
    if len(self.inventory) >= MAX_INVENTORY_SIZE:
        raise InventoryFullError(
            f"Inventory full ({MAX_INVENTORY_SIZE} items)"
        )

    self.inventory.append(item)
    item.x = None
    item.y = None
```

**Benefits**:
- Clear error semantics (exceptions vs None)
- Better error messages (context in exception)
- Easier debugging (stack traces)
- Client code can handle specific errors

---

## Recommended Refactoring Sequence

### Phase 1: Configuration Foundation (Week 1)
**Goal**: Extract all hardcoded values

1. ✅ Create `src/core/constants.py` with all magic numbers
2. ✅ Create `data/balance/` directory structure
3. ✅ Extract monster spawn weights to `monster_spawns.yaml`
4. ✅ Extract ore distribution to `ore_veins.yaml`
5. ✅ Create config loader system
6. ✅ Update Game class to use config

**Deliverable**: All game balance tunable via YAML

### Phase 2: Separation of Concerns (Week 2)
**Goal**: Break up God class

1. ✅ Create `EntitySpawner` class
2. ✅ Create `TurnProcessor` class
3. ✅ Create `FloorManager` class
4. ✅ Refactor `Game` to delegate to new classes
5. ✅ Write unit tests for each new class

**Deliverable**: Game class < 200 lines

### Phase 3: Data-Driven Content (Week 3)
**Goal**: Make entities data-driven

1. ✅ Create entity definitions in YAML
2. ✅ Create `EntityLoader` class
3. ✅ Replace factory methods with loader
4. ✅ Support custom content directories

**Deliverable**: Add new monsters via YAML only

### Phase 4: Code Quality (Week 4)
**Goal**: Eliminate duplication and improve type safety

1. ✅ Add action helper methods
2. ✅ Create exception hierarchy
3. ✅ Standardize error handling
4. ✅ Add type protocols for common interfaces
5. ✅ Code review and cleanup

**Deliverable**: Clean, maintainable codebase

---

## Testing Strategy

### Unit Tests to Add

```python
# tests/unit/test_entity_spawner.py
def test_spawn_monsters_floor_1():
    """Floor 1 should spawn only goblins"""
    spawner = EntitySpawner(test_config)
    monsters = spawner.spawn_monsters_for_floor(floor=1)
    assert all(m.name == "Goblin" for m in monsters)

# tests/unit/test_entity_loader.py
def test_load_monster_from_yaml():
    """Can create monster from YAML definition"""
    loader = EntityLoader("data/entities")
    goblin = loader.create_monster("goblin", x=5, y=10)
    assert goblin.name == "Goblin"
    assert goblin.hp == 6
    assert goblin.attack == 3

# tests/unit/test_turn_processor.py
def test_hp_regeneration():
    """Player regenerates 1 HP every 10 turns"""
    processor = TurnProcessor(mock_context)
    player.hp = 15  # Damaged
    for i in range(10):
        processor.process_turn()
    assert player.hp == 16  # Regenerated
```

### Integration Tests

```python
# tests/integration/test_floor_progression.py
def test_floor_2_difficulty():
    """Floor 2 should be harder than Floor 1"""
    game = Game()
    game.start_new_game()

    floor_1_monsters = len(game.context.get_entities_by_type(EntityType.MONSTER))

    game.descend_floor()
    floor_2_monsters = len(game.context.get_entities_by_type(EntityType.MONSTER))

    assert floor_2_monsters > floor_1_monsters
```

---

## Metrics to Track

**Code Quality Metrics**:
- Lines of code per class (target: < 200)
- Cyclomatic complexity (target: < 10 per function)
- Test coverage (target: > 80%)
- Number of magic numbers (target: 0)

**Before Refactoring**:
- `Game.py`: 394 lines
- Magic numbers: ~20
- Config files: 0
- Test coverage: Unknown

**After Refactoring Target**:
- `Game.py`: < 200 lines
- Magic numbers: 0
- Config files: 5+
- Test coverage: > 80%

---

## Architecture Decision Records (ADRs)

### ADR-001: Configuration Management
**Decision**: Use YAML for all game balance data

**Rationale**:
- Non-programmers can edit YAML
- Supports data-driven design vision
- Easy to version control
- Standard format (no custom parsing)

**Alternatives Considered**:
- JSON: Less human-friendly
- TOML: Less common in Python ecosystem
- Python modules: Requires code knowledge

### ADR-002: Entity Creation
**Decision**: Data-driven entity creation via YAML + EntityLoader

**Rationale**:
- Aligns with Phase 3 Lua content system
- Enables modding without code changes
- Separates content from code
- Better for balance iteration

**Alternatives Considered**:
- Keep factory methods: Doesn't scale
- Database: Over-engineered for single-player
- Code generation: Adds complexity

### ADR-003: Class Decomposition
**Decision**: Break Game into EntitySpawner, TurnProcessor, FloorManager

**Rationale**:
- Single Responsibility Principle
- Easier to test in isolation
- Clearer ownership of logic
- Better for future multiplayer refactor

**Alternatives Considered**:
- Keep monolithic: Harder to maintain
- Event-driven refactor now: Premature for MVP
- Full ECS: Over-engineered for current needs

---

## Implementation Checklist

### Phase 1: Configuration Foundation
- [ ] Create `src/core/constants.py`
- [ ] Create `data/balance/monster_spawns.yaml`
- [ ] Create `data/balance/ore_veins.yaml`
- [ ] Create `data/balance/game_constants.yaml`
- [ ] Create `src/core/config/` module
- [ ] Create `ConfigLoader` class
- [ ] Update `Game._spawn_monsters()` to use config
- [ ] Update `Game._spawn_ore_veins()` to use config
- [ ] Write tests for ConfigLoader
- [ ] Run game, verify behavior unchanged

### Phase 2: Separation of Concerns
- [ ] Create `src/core/spawning/entity_spawner.py`
- [ ] Create `src/core/turn_processor.py`
- [ ] Create `src/core/floor_manager.py`
- [ ] Move spawning logic to EntitySpawner
- [ ] Move turn logic to TurnProcessor
- [ ] Move floor logic to FloorManager
- [ ] Update Game class to use new classes
- [ ] Write tests for each new class
- [ ] Verify Game class < 200 lines
- [ ] Run full test suite

### Phase 3: Data-Driven Content
- [ ] Create `data/entities/monsters.yaml`
- [ ] Create `data/entities/ores.yaml`
- [ ] Create `src/core/content/entity_loader.py`
- [ ] Implement EntityLoader.create_monster()
- [ ] Implement EntityLoader.create_ore_vein()
- [ ] Update EntitySpawner to use EntityLoader
- [ ] Remove factory methods from Monster class
- [ ] Write tests for EntityLoader
- [ ] Add 2-3 new monsters via YAML only (test)
- [ ] Run game, verify all monsters work

### Phase 4: Code Quality
- [ ] Add `_get_actor()` helper to Action base class
- [ ] Create `src/core/exceptions.py`
- [ ] Update all actions to use helper
- [ ] Replace False returns with exceptions (where appropriate)
- [ ] Add type protocols (Damageable, Moveable)
- [ ] Run linter (pylint, mypy)
- [ ] Fix all type errors
- [ ] Code review session
- [ ] Update documentation

---

## Success Criteria

**Must Have**:
- ✅ All magic numbers extracted to constants
- ✅ Game balance in YAML files
- ✅ Game class < 250 lines
- ✅ No code duplication in Actions
- ✅ All tests pass

**Should Have**:
- ✅ Entity definitions in YAML
- ✅ Test coverage > 70%
- ✅ Consistent error handling
- ✅ ADRs documented

**Nice to Have**:
- ✅ Test coverage > 80%
- ✅ Automated balance testing
- ✅ Performance benchmarks

---

## Risk Assessment

### Low Risk
- ✅ Extract constants (pure refactor, no behavior change)
- ✅ Add helper methods (additive change)

### Medium Risk
- ⚠️ Break up Game class (large refactor, but well-defined)
- ⚠️ Config system (new dependency, could break initialization)

### High Risk
- 🔥 Data-driven entities (changes core creation logic)
- 🔥 Exception refactor (changes error semantics)

**Mitigation**:
- Comprehensive test suite before refactoring
- Incremental changes (one phase at a time)
- Rollback plan (git branches)
- Play-test after each phase

---

## Conclusion

The Veinborn codebase has **strong foundations** but suffers from common early-stage issues:
- Configuration hell (hardcoded values)
- God class anti-pattern (Game doing too much)
- Factory sprawl (content in code)

The proposed refactoring will:
- ✅ Make game balance easily tunable
- ✅ Improve code maintainability
- ✅ Enable data-driven content
- ✅ Prepare for Phase 2 multiplayer
- ✅ Support future Lua integration

**Recommended Start**: Phase 1 (Configuration Foundation)
**Estimated Time**: 4 weeks for all phases
**Risk Level**: Medium (mitigated by testing)

---

**Next Steps**:
1. Review this plan with team
2. Create git branch: `refactor/configuration-foundation`
3. Start Phase 1, Task 1: Create constants.py
4. Iterate, test, commit frequently
5. Celebrate clean code! 🎉
