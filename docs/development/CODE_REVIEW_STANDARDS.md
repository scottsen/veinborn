# Brogue Code Review Standards

**Document Type:** Code Review Reference
**Audience:** Code reviewers, developers
**Status:** Active
**Last Updated:** 2025-10-25

---

## Quick Reference Checklist

Use this during code reviews to ensure consistency with project standards.

### ✅ Code Style
- [ ] **Line length** ≤ 120 characters
- [ ] **Type hints** on all public functions/methods
- [ ] **PEP 8** compliance (4 spaces, no tabs)
- [ ] **Naming**: Classes=`PascalCase`, functions=`snake_case`, constants=`UPPER_SNAKE_CASE`
- [ ] **Imports** ordered: stdlib → third-party → local
- [ ] **Blank lines**: 2 before classes, 1 before methods

### ✅ Function Design
- [ ] **Function length**: Target 10-20 lines, max 40 lines
- [ ] **Cyclomatic complexity** ≤ 5 decision points
- [ ] **Single purpose**: Each function does ONE thing
- [ ] **Early returns**: Avoid deep nesting (max 3 levels)
- [ ] **Composition**: Complex logic built from small functions

### ✅ Documentation
- [ ] **Docstrings**: Google-style with Args, Returns, Raises, Example
- [ ] **Comments**: Explain WHY, not WHAT
- [ ] **Complex logic** documented inline

### ✅ Error Handling
- [ ] **Uses exception hierarchy** (BrogueError subclasses)
- [ ] **No bare except** clauses
- [ ] **Specific exceptions** (InvalidActionError, not generic Exception)
- [ ] **Proper error messages** with context

### ✅ Testing
- [ ] **Unit tests** for new logic
- [ ] **Test coverage** maintained (≥ 60% current baseline)
- [ ] **Tests behavior**, not implementation
- [ ] **Integration tests** for workflows

### ✅ Logging
- [ ] **Uses structured logging** (not print statements)
- [ ] **Appropriate log levels** (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- [ ] **Logs important operations** with context
- [ ] **No sensitive data** in logs

---

## 🔍 AST Code Analysis Tools

The TIA AST domain provides powerful code analysis via **hierarchical commands**:

```bash
# Browse available scanners
tia ast scanner list

# Run specific scanner
tia ast scanner run security src --critical-only
tia ast scanner run complexity src --complex-only

# Comprehensive audit (runs all scanners)
tia ast scanner audit src

# Get scanner information
tia ast scanner info dangerous
```

### 🎮 Brogue-Specific Scanners

Brogue has **5 custom scanners** designed specifically for this project's needs:

```bash
# Check CODE_REVIEW_STANDARDS.md compliance
tia ast scan --scanner brogue-standards src/

# Validate Action pattern compliance
tia ast scan --scanner brogue-action-validator src/

# Find duplicate actor lookup patterns
tia ast scan --scanner brogue-actor-lookup src/

# Detect hardcoded game balance values
tia ast scan --scanner brogue-magic-numbers src/

# Verify Phase 3 factory migration
tia ast scan --scanner brogue-deprecated-factory src/
```

**What They Check:**
- ✅ **brogue-standards**: Function length, complexity, type hints, docstrings, exception hierarchy
- ✅ **brogue-action-validator**: Action class patterns, proper validation methods, ActionOutcome returns
- ✅ **brogue-actor-lookup**: Duplicate `game_state.entities.get()` patterns (should use helpers)
- ✅ **brogue-magic-numbers**: Hardcoded values that should be in YAML configs
- ✅ **brogue-deprecated-factory**: Old factory patterns that should use new architecture

**💡 Creating Custom Scanners is Easy!**
These 5 scanners were created in ~2 hours total. Each scanner:
- Inherits from `BaseScanner` (minimal interface)
- Implements one method: `scan_file()`
- Auto-discovered (just name it `*_scanner.py`)
- Gets all output formats for free (json, yaml, csv, pretty, markdown)

Want to enforce YOUR project patterns? See [TIA's Custom Scanner Guide](https://github.com/scottsen/tia/blob/master/docs/ast/CREATING_CUSTOM_SCANNERS.md) for a 3-minute tutorial.

**Quick Scans:**
- **Security**: `tia ast scanner run security src --critical-only`
- **Complexity**: `tia ast scanner run complexity src --complex-only`
- **Functions**: `tia ast functions src --complex-only`
- **Dependencies**: `tia ast dependencies src --circular-only`
- **Brogue Standards**: `tia ast scan --scanner brogue-standards src/`
- **Brogue Actions**: `tia ast scan --scanner brogue-action-validator src/core/actions`

See [Tools](#tools) section below for complete command reference.

---

## Detailed Standards

### 1. Code Style Standards

**Source:** [docs/architecture/MVP_DEVELOPMENT_GUIDELINES.md](docs/architecture/MVP_DEVELOPMENT_GUIDELINES.md#code-style)

#### Type Hints (REQUIRED)

All public functions and methods must have type hints:

```python
# ✅ GOOD
def process_move(player: Player, dx: int, dy: int) -> bool:
    """Move player by offset."""
    new_x = player.x + dx
    new_y = player.y + dy
    return is_walkable(new_x, new_y)

# ❌ BAD - Missing type hints
def process_move(player, dx, dy):
    new_x = player.x + dx
    new_y = player.y + dy
    return is_walkable(new_x, new_y)
```

**Exceptions:**
- Internal helper functions (prefixed with `_`) may omit type hints if trivial
- Lambda functions

#### Formatting

- **Line length**: 120 characters maximum
- **Indentation**: 4 spaces (never tabs)
- **Imports**: Group and order:
  ```python
  # Standard library
  import os
  import sys
  from typing import Dict, List

  # Third-party
  import pytest
  from textual.app import App

  # Local
  from src.core.entities import Player
  from src.core.game import Game
  ```
- **Blank lines**:
  - 2 blank lines before class definitions
  - 1 blank line before method definitions
  - 1 blank line between logical sections in functions

#### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| **Classes** | PascalCase | `OreVein`, `GameState`, `MiningAction` |
| **Functions/Methods** | snake_case | `generate_dungeon()`, `take_damage()` |
| **Constants** | UPPER_SNAKE_CASE | `MAX_HP`, `DEFAULT_FOV_RADIUS` |
| **Private** | _leading_underscore | `_internal_helper()`, `_calculate()` |
| **Module-level private** | _leading_underscore | `_logger`, `_config` |

---

### 2. Function Design Patterns

**Source:** [docs/architecture/OPERATIONAL_EXCELLENCE_GUIDELINES.md](docs/architecture/OPERATIONAL_EXCELLENCE_GUIDELINES.md#method--function-design)

#### Small Methods Rule

**Target:** 10-20 lines per method
**Maximum:** 40 lines (refactor if exceeded!)
**Cyclomatic complexity:** ≤ 5 decision points

```python
# ✅ GOOD - Small, focused (13 lines)
def process_turn(self):
    """Process a complete game turn."""
    action = self._get_player_action()
    outcome = action.execute(self.context)

    if outcome.took_turn:
        self._process_monster_turns()
        self._update_ui(outcome)

# ❌ BAD - Too long (70+ lines)
def process_turn(self):
    """Process a complete game turn."""
    # Get player input (10 lines)
    # Validate move (15 lines)
    # Check for combat (20 lines)
    # Process monsters (20 lines)
    # Update UI (10 lines)
    # ... 70+ lines total
```

#### Early Returns Pattern

Use early returns to avoid deep nesting:

```python
# ✅ GOOD - Flat structure with early returns
def process_mining(player: Entity, ore_vein: Entity) -> ActionOutcome:
    """Process mining action with validation."""
    # Validate preconditions
    if not player.is_alive:
        return ActionOutcome.failure("Player is dead")

    if ore_vein is None:
        return ActionOutcome.failure("No ore vein")

    if not player.is_adjacent(ore_vein):
        return ActionOutcome.failure("Too far away")

    if ore_vein.is_mined:
        return ActionOutcome.failure("Already mined")

    # Happy path - actual logic
    return self._mine_ore(player, ore_vein)

# ❌ BAD - Deep nesting (4 levels)
def process_mining(player: Entity, ore_vein: Entity) -> ActionOutcome:
    if player.is_alive:
        if ore_vein is not None:
            if player.is_adjacent(ore_vein):
                if not ore_vein.is_mined:
                    return self._mine_ore(player, ore_vein)
```

**Rule:** Max 3 levels of nesting. If you need more, refactor.

#### Single Purpose Functions

Each function should do ONE thing:

```python
# ✅ GOOD - Separated concerns
def calculate_damage(attacker: Entity, defender: Entity) -> int:
    """Calculate combat damage."""
    base_damage = attacker.attack - defender.defense
    return max(1, base_damage)

def apply_damage(entity: Entity, damage: int) -> None:
    """Apply damage to entity."""
    entity.hp = max(0, entity.hp - damage)

def log_combat(attacker_id: str, defender_id: str, damage: int) -> None:
    """Log combat event."""
    logger.info("Combat", attacker=attacker_id, defender=defender_id, damage=damage)

# ❌ BAD - Does multiple things
def process_combat_and_log(attacker: Entity, defender: Entity):
    """Process combat and update UI and log."""  # 3 responsibilities!
    damage = attacker.attack - defender.defense  # Combat logic
    defender.hp -= damage                        # Combat logic
    ui.show_message(f"{damage} damage!")        # UI update
    stats.track_damage(damage)                   # Stats tracking
    logger.info("Combat", damage=damage)         # Logging
```

#### Function Composition

Build complex operations from small, composable functions:

```python
# ✅ GOOD - Composed from small functions
def calculate_final_damage(attacker: Entity, defender: Entity) -> int:
    """Calculate final damage after all modifiers."""
    base_damage = _calculate_base_damage(attacker, defender)
    critical_damage = _apply_critical_multiplier(base_damage, attacker)
    final_damage = _apply_damage_reduction(critical_damage, defender)
    return max(1, final_damage)

def _calculate_base_damage(attacker: Entity, defender: Entity) -> int:
    """Calculate base damage before modifiers."""
    return max(0, attacker.attack - defender.defense)

def _apply_critical_multiplier(damage: int, attacker: Entity) -> int:
    """Apply critical hit multiplier if applicable."""
    crit_chance = attacker.get_stat('crit_chance', 0.0)
    if random.random() < crit_chance:
        return int(damage * 2.0)
    return damage

def _apply_damage_reduction(damage: int, defender: Entity) -> int:
    """Apply damage reduction from armor/buffs."""
    reduction = defender.get_stat('damage_reduction', 0)
    return max(0, damage - reduction)
```

---

### 3. Documentation Standards

**Source:** [docs/architecture/OPERATIONAL_EXCELLENCE_GUIDELINES.md](docs/architecture/OPERATIONAL_EXCELLENCE_GUIDELINES.md#documentation-standards)

#### Docstring Format (Google Style)

All public functions/methods/classes must have docstrings:

```python
def mine_ore_vein(
    player: Entity,
    ore_vein: Entity,
    *,
    use_tool: bool = True,
) -> MiningResult:
    """Mine an ore vein and add ore to inventory.

    Mining is a multi-turn action that depends on ore hardness
    and player mining skill. The player must remain adjacent
    to the ore vein for the entire mining duration.

    Args:
        player: The player entity performing the mining
        ore_vein: The ore vein to mine
        use_tool: Whether to use equipped mining tool (default: True)

    Returns:
        MiningResult with success status and ore item if successful

    Raises:
        InvalidActionError: If player is not adjacent to ore vein
        InvalidStateError: If ore vein is already mined

    Example:
        >>> player = Player(x=10, y=10)
        >>> ore = OreVein(x=11, y=10, hardness=75)
        >>> result = mine_ore_vein(player, ore)
        >>> if result.success:
        ...     print(f"Mined {result.ore.name}")

    See Also:
        - survey_ore_vein: Survey ore before mining
        - MiningSystem: Full mining system documentation
    """
    # Implementation
    pass
```

**Required Sections:**
- Summary (first line)
- Args (if function has parameters)
- Returns (if function returns a value)
- Raises (if function can raise exceptions)

**Optional Sections:**
- Example (recommended for complex functions)
- See Also (for related functions)
- Note/Warning (for important context)

#### Code Comments

Comments should explain **WHY**, not **WHAT**:

```python
# ✅ GOOD - Explains reasoning
def calculate_damage(attacker: Entity, defender: Entity) -> int:
    """Calculate combat damage."""
    # Base damage from attack stat
    base_damage = attacker.attack

    # Apply defense reduction
    # Note: We always deal at least 1 damage to prevent
    # invincible enemies due to high defense
    final_damage = max(1, base_damage - defender.defense)

    return final_damage

# ❌ BAD - Just repeats code
def calculate_damage(attacker, defender):
    # Add x and y
    result = attacker.attack - defender.defense
    # Return result
    return result
```

**When to comment:**
- Complex algorithms (e.g., BSP dungeon generation)
- Non-obvious design decisions
- Workarounds for bugs/limitations
- Performance optimizations

**When NOT to comment:**
- Self-explanatory code
- Obvious operations
- Repeating type hints or function name

---

### 4. Error Handling Standards

**Source:** [docs/architecture/OPERATIONAL_EXCELLENCE_GUIDELINES.md](docs/architecture/OPERATIONAL_EXCELLENCE_GUIDELINES.md#error-handling-standards)

#### Exception Hierarchy

Use the project exception hierarchy defined in `src/core/exceptions.py`:

```python
BrogueError (base)
├── GameError (recoverable game logic)
│   ├── InvalidActionError
│   └── InvalidStateError
├── DataError (loading/validation)
│   └── ContentValidationError
└── SystemError (usually not recoverable)
    ├── SaveLoadError
    └── NetworkError
```

#### Exception Usage

```python
# ✅ GOOD - Specific exceptions with context
def execute_move(player: Entity, dx: int, dy: int) -> ActionOutcome:
    """Execute move action."""
    new_x = player.x + dx
    new_y = player.y + dy

    if not self._is_in_bounds(new_x, new_y):
        raise InvalidActionError(
            f"Move out of bounds: ({new_x}, {new_y})",
            entity_id=player.entity_id,
            attempted_position=(new_x, new_y)
        )

    if not self._is_walkable(new_x, new_y):
        raise InvalidActionError(
            f"Tile not walkable: ({new_x}, {new_y})",
            entity_id=player.entity_id,
            attempted_position=(new_x, new_y)
        )

    player.x = new_x
    player.y = new_y
    return ActionOutcome.success("Moved")

# ❌ BAD - Generic exceptions, bare except
def execute_move(player, dx, dy):
    try:
        new_x = player.x + dx
        new_y = player.y + dy
        player.x = new_x
        player.y = new_y
    except:  # ❌ Bare except
        raise Exception("Move failed")  # ❌ Generic exception
```

**Rules:**
- **Never use bare `except:`** - always specify exception type
- **Use specific exceptions** - not generic `Exception`
- **Include context** - entity IDs, positions, state info
- **Document exceptions** - in docstring `Raises:` section

#### Error Handling Patterns

```python
# ✅ GOOD - Proper error handling
def load_config(path: str) -> GameConfig:
    """Load game configuration from YAML file.

    Raises:
        ContentValidationError: If YAML validation fails
        SaveLoadError: If file cannot be read
    """
    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise SaveLoadError(f"Config file not found: {path}")
    except yaml.YAMLError as e:
        raise ContentValidationError(f"Invalid YAML: {e}")

    try:
        return GameConfig.parse_obj(data)
    except ValidationError as e:
        raise ContentValidationError(f"Config validation failed: {e}")

# ❌ BAD - Swallows exceptions
def load_config(path):
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except:  # ❌ Catches everything, no logging
        return {}  # ❌ Silent failure
```

---

### 5. Testing Standards

**Source:** [docs/architecture/MVP_TESTING_GUIDE.md](docs/architecture/MVP_TESTING_GUIDE.md)

#### Coverage Requirements

- **Minimum coverage**: 60% (current baseline)
- **Target coverage**: 80% for new code
- **Critical systems**: 90%+ (combat, progression, save/load)

#### Test Structure

```python
# ✅ GOOD - Tests behavior, clear assertions
def test_player_takes_damage():
    """Player HP decreases when damaged."""
    # Arrange
    player = Player(hp=100, max_hp=100)

    # Act
    player.take_damage(30)

    # Assert
    assert player.hp == 70

def test_player_cannot_go_below_zero_hp():
    """Player HP stops at 0, not negative."""
    # Arrange
    player = Player(hp=10, max_hp=100)

    # Act
    player.take_damage(50)

    # Assert
    assert player.hp == 0
    assert not player.is_alive

# ❌ BAD - Tests implementation, unclear assertions
def test_player_damage():
    p = Player(hp=100, max_hp=100)
    p.hp -= 30  # ❌ Testing implementation, not behavior
    assert p.hp < 100  # ❌ Weak assertion
```

**Rules:**
- **Test behavior**, not implementation
- **One concept per test** - don't test multiple things
- **Clear test names** - describe what's being tested
- **Arrange-Act-Assert** pattern
- **Use fixtures** for common setup

#### Integration Tests

For workflows that involve multiple systems:

```python
# ✅ GOOD - Integration test for mining workflow
def test_full_mining_workflow():
    """Test complete mining workflow from discovery to inventory."""
    # Arrange
    game = Game()
    game.generate_new_dungeon()
    ore_vein = game.map.get_ore_at(10, 10)

    # Act & Assert - Survey
    game.handle_survey_action(10, 10)
    assert ore_vein.is_surveyed

    # Act & Assert - Mine (takes 4 turns)
    for turn in range(4):
        game.handle_mining_action(10, 10)

    # Assert - Ore in inventory
    assert len(game.player.inventory.ores) == 1
    assert ore_vein.is_mined
```

---

### 6. Logging Standards

**Source:** [docs/architecture/OPERATIONAL_EXCELLENCE_GUIDELINES.md](docs/architecture/OPERATIONAL_EXCELLENCE_GUIDELINES.md#logging-architecture)

#### Use Structured Logging

**Never use `print()` for logging:**

```python
# ✅ GOOD - Structured logging
logger = logging.getLogger(__name__)

def resolve_attack(attacker: Entity, defender: Entity) -> AttackResult:
    """Resolve combat attack."""
    logger.info(
        "Combat attack started",
        extra={
            'attacker_id': attacker.entity_id,
            'defender_id': defender.entity_id,
            'attacker_hp': attacker.hp,
            'defender_hp': defender.hp,
        }
    )

    damage = self._calculate_damage(attacker, defender)
    actual_damage = defender.take_damage(damage)

    logger.info(
        "Combat attack resolved",
        extra={
            'attacker_id': attacker.entity_id,
            'defender_id': defender.entity_id,
            'damage': actual_damage,
            'defender_hp_remaining': defender.hp,
            'defender_died': not defender.is_alive,
        }
    )

    return AttackResult(damage=actual_damage, killed=not defender.is_alive)

# ❌ BAD - Uses print
def resolve_attack(attacker, defender):
    print(f"Attacking {defender}")  # ❌ No structure, no log levels
    damage = attacker.attack - defender.defense
    print(f"Damage: {damage}")
    return damage
```

#### Log Levels

| Level | When to Use | Examples |
|-------|-------------|----------|
| **DEBUG** | Development details, debugging | Turn processing steps, state transitions |
| **INFO** | Normal operations, milestones | Game started, level completed, player action |
| **WARNING** | Unusual but recoverable | Retry attempts, deprecated features used |
| **ERROR** | Operation failed, needs attention | Save failed, invalid action, API error |
| **CRITICAL** | System failure, data loss | Database corruption, server crash |

**Rules:**
- Use appropriate log level
- Include context (entity IDs, positions, etc.)
- No sensitive data (passwords, tokens)
- Log entry/exit for important operations
- Log errors with full context

---

## Common Violations & Fixes

### Violation: Long Functions

**Problem:**
```python
# ❌ 150 lines in one function
def process_game_turn(self):
    # ... 150 lines
```

**Fix:**
```python
# ✅ Decomposed into small functions
def process_game_turn(self):
    action = self._get_player_action()
    self._execute_action(action)
    self._process_monster_turns()
    self._update_ui()
```

### Violation: Missing Type Hints

**Problem:**
```python
# ❌ No type hints
def calculate_damage(attacker, defender):
    return max(1, attacker.attack - defender.defense)
```

**Fix:**
```python
# ✅ Type hints added
def calculate_damage(attacker: Entity, defender: Entity) -> int:
    """Calculate combat damage."""
    return max(1, attacker.attack - defender.defense)
```

### Violation: Generic Exceptions

**Problem:**
```python
# ❌ Generic Exception
def load_save_file(path):
    if not os.path.exists(path):
        raise Exception("File not found")
```

**Fix:**
```python
# ✅ Specific exception from hierarchy
def load_save_file(path: str) -> SaveData:
    """Load save file.

    Raises:
        SaveLoadError: If file not found or invalid
    """
    if not os.path.exists(path):
        raise SaveLoadError(f"Save file not found: {path}")
```

### Violation: Print Statements

**Problem:**
```python
# ❌ Using print for logging
def mine_ore(player, ore):
    print(f"Mining {ore.name}")
    # ... logic
    print("Mining complete")
```

**Fix:**
```python
# ✅ Structured logging
logger = logging.getLogger(__name__)

def mine_ore(player: Entity, ore: OreVein) -> None:
    """Mine an ore vein."""
    logger.info("Mining started", extra={
        'player_id': player.entity_id,
        'ore_type': ore.name,
        'hardness': ore.hardness,
    })
    # ... logic
    logger.info("Mining complete", extra={
        'player_id': player.entity_id,
        'ore_type': ore.name,
    })
```

### Violation: No Tests

**Problem:**
```python
# ❌ New feature, no tests
def new_crafting_system():
    # ... 200 lines of logic
    # ... no tests
```

**Fix:**
```python
# ✅ Tests added
# tests/test_crafting.py
def test_craft_simple_sword():
    """Crafting simple sword requires iron ore."""
    player = Player()
    player.inventory.add_ore(OreType.IRON, quantity=2)

    result = craft_item(player, Recipe.SIMPLE_SWORD)

    assert result.success
    assert player.inventory.has_item(ItemType.SIMPLE_SWORD)
    assert player.inventory.ore_count(OreType.IRON) == 0
```

---

## Code Review Process

### 1. Before Review

Reviewer should:
- [ ] Read this document
- [ ] Check [CODE_REVIEW_AND_REFACTORING_PLAN.md](CODE_REVIEW_AND_REFACTORING_PLAN.md) for known issues
- [ ] Understand current phase (MVP Phase 1)

### 2. During Review

Check each file against:
- [ ] Quick Reference Checklist (top of this doc)
- [ ] Detailed standards (above)
- [ ] Run tests: `pytest --cov=src`
- [ ] Check complexity: `tia ast scanner run complexity src`
- [ ] Check security: `tia ast scanner run security src --critical-only`
- [ ] Run comprehensive audit: `tia ast scanner audit src`

### 3. Categorize Issues

**Critical (Must Fix):**
- Security vulnerabilities
- Data loss bugs
- Crashes
- Test failures

**Should Fix (Before Merge):**
- Missing type hints
- Missing tests
- PEP 8 violations
- Generic exceptions

**Nice to Have (Future):**
- Function length improvements
- Additional test coverage
- Documentation enhancements
- Performance optimizations

### 4. Provide Feedback

Format:
```markdown
## File: src/core/game.py

### Critical Issues
- Line 123: Bare except clause - use specific exception

### Should Fix
- Line 45-89: Function too long (45 lines), target 10-20 lines
- Line 67: Missing type hint on parameter `data`

### Nice to Have
- Consider extracting _validate_move() for reusability
```

---

## Tools

### Automated Checks

```bash
# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Browse available AST scanners
tia ast scanner list

# Run comprehensive audit (all scanners)
tia ast scanner audit src

# Check code complexity
tia ast scanner run complexity src --complex-only

# Check for security issues (critical only)
tia ast scanner run security src --critical-only

# Check for circular dependencies
tia ast dependencies src --circular-only

# Check specific file
tia ast scanner run metrics src/core/game.py

# Get detailed info about a scanner
tia ast scanner info dangerous

# Brogue-specific scanners
tia ast scan --scanner brogue-standards src/                    # CODE_REVIEW_STANDARDS.md compliance
tia ast scan --scanner brogue-action-validator src/core/actions # Action pattern validation
tia ast scan --scanner brogue-magic-numbers src/                # Hardcoded values detection
```

### Manual Checks

```bash
# Read code with structure view
tia read src/core/game.py

# Search for patterns (semantic AST search)
tia ast search "exception" src --type all

# View function signatures and complexity
tia ast functions src/core/game.py --signatures --details

# AST tree visualization
tia ast tree src/core/game.py --complexity

# Iterate through files with filters
tia ast iterate src --type files --filter 'is_python=true'
```

---

## Reference Documents

For detailed information, consult these source documents:

**Essential:**
- [MVP_DEVELOPMENT_GUIDELINES.md](docs/architecture/MVP_DEVELOPMENT_GUIDELINES.md) - Code style, testing, git workflow
- [OPERATIONAL_EXCELLENCE_GUIDELINES.md](docs/architecture/OPERATIONAL_EXCELLENCE_GUIDELINES.md) - Function design, logging, error handling
- [MVP_TESTING_GUIDE.md](docs/architecture/MVP_TESTING_GUIDE.md) - Testing patterns, fixtures, coverage

**Context:**
- [00_ARCHITECTURE_OVERVIEW.md](docs/architecture/00_ARCHITECTURE_OVERVIEW.md) - System architecture
- [CODE_REVIEW_AND_REFACTORING_PLAN.md](CODE_REVIEW_AND_REFACTORING_PLAN.md) - Known issues
- [PHASE_5_COMPLETE.md](PHASE_5_COMPLETE.md) - Current implementation status

**Specific Systems:**
- [PLAYER_CONFIG_AND_CLASSES.md](docs/PLAYER_CONFIG_AND_CLASSES.md) - Character classes
- [HIGH_SCORE_SYSTEM_DESIGN.md](docs/HIGH_SCORE_SYSTEM_DESIGN.md) - Scoring mechanics

---

## Metrics Baseline (Current)

Use these as comparison points:

**Code Metrics:**
- Files: 42 Python files
- Total LOC: 6,839 lines
- Avg Complexity: 8.9 (excellent)
- Quality: 60% Excellent, 36% Good, 4% Fair

**Test Metrics:**
- Tests: 254 tests (all passing)
- Coverage: 60.93%
- Core logic: 85%+ coverage
- Actions: 15-20% coverage (needs improvement)

**Security:**
- Critical risks: 0
- High risks: 0
- Circular imports: 0

---

## Questions?

- **Code style unclear?** See [MVP_DEVELOPMENT_GUIDELINES.md](docs/architecture/MVP_DEVELOPMENT_GUIDELINES.md)
- **Function too complex?** See [OPERATIONAL_EXCELLENCE_GUIDELINES.md](docs/architecture/OPERATIONAL_EXCELLENCE_GUIDELINES.md#method--function-design)
- **How to test?** See [MVP_TESTING_GUIDE.md](docs/architecture/MVP_TESTING_GUIDE.md)
- **Architecture questions?** See [00_ARCHITECTURE_OVERVIEW.md](docs/architecture/00_ARCHITECTURE_OVERVIEW.md)

---

**Last Updated:** 2025-11-15 (Updated AST commands to hierarchical syntax)
**Maintainer:** TIA System
**Review Cycle:** Update after each major refactoring phase
