# Veinborn Operational Excellence Guidelines

**Document Type:** Coding Standards & Best Practices
**Audience:** All Developers
**Status:** Active
**Last Updated:** 2025-10-24

---

## Overview

This document defines operational excellence standards for Veinborn, covering practices that ensure:
- **Maintainability**: Code that's easy to read, understand, and modify
- **Reliability**: Systems that fail gracefully and recover automatically
- **Observability**: Deep visibility into system behavior
- **Performance**: Efficient, scalable implementations

**Companion documents:**
- `MVP_DEVELOPMENT_GUIDELINES.md` - Code style, testing basics
- `MVP_TESTING_GUIDE.md` - Testing methodology
- `BASE_CLASS_ARCHITECTURE.md` - Design patterns

---

## Table of Contents

1. [Automated Code Quality Scanning](#1-automated-code-quality-scanning)
2. [Method & Function Design](#2-method--function-design)
3. [Single Responsibility Principle](#3-single-responsibility-principle)
4. [Logging Architecture](#4-logging-architecture)
5. [Error Handling Standards](#5-error-handling-standards)
6. [Performance Guidelines](#6-performance-guidelines)
7. [Configuration Management](#7-configuration-management)
8. [Code Review Standards](#8-code-review-standards)
9. [Debugging Practices](#9-debugging-practices)
10. [Documentation Standards](#10-documentation-standards)

---

## 1. Automated Code Quality Scanning

### TIA AST Scanners

**Use TIA's built-in AST scanners to automatically enforce coding standards.**

#### Quick Start

```bash
# Scan for complexity issues
tia ast scan complexity src/ --min-severity high

# Scan for security issues
tia ast scan security src/

# Scan for all issues
tia ast scan all src/ --format json > quality-report.json
```

#### Available Scanners

**Complexity Scanner** - Finds code complexity issues:
```bash
tia ast scan complexity src/
```

Detects:
- Functions > 50 lines (MEDIUM) or > 100 lines (HIGH)
- Functions with > 5 parameters (MEDIUM) or > 7 (HIGH)
- Deep nesting > 4 levels (MEDIUM)
- Long if/elif chains > 5 conditions (MEDIUM)

**Security Scanner** - Finds dangerous patterns:
```bash
tia ast scan security src/
```

Detects:
- eval() / exec() usage
- shell command injection risks
- unsafe pickle usage
- hardcoded secrets

**Import Scanner** - Analyzes dependencies:
```bash
tia ast scan imports src/
```

Detects:
- Circular import risks
- Missing dependencies
- Security risks in imports

#### Current Veinborn Code Quality

**Complexity scan results** (as of 2025-10-25):

```
📊 High-Severity Issues Found:

1. mine_action.py execute()    - 145 lines ⚠️  (target: <50)
2. pathfinding.py find_path()  - 112 lines ⚠️  (target: <50)
3. attack_action.py execute()  - 103 lines ⚠️  (target: <50)
4. Entity.__init__()           - 10 parameters ⚠️  (target: <5)
5. Monster.__init__()          - 9 parameters ⚠️  (target: <5)
```

**Action Items:**
- Refactor execute() methods to extract sub-functions
- Convert Entity/Monster constructors to use dataclasses or config objects

#### Integration with Development Workflow

**Pre-commit checks:**
```bash
# Add to git pre-commit hook
tia ast scan complexity src/ --min-severity high
if [ $? -ne 0 ]; then
  echo "❌ Code quality issues found. Please fix before committing."
  exit 1
fi
```

**CI/CD integration:**
```bash
# Add to GitHub Actions / CI pipeline
- name: Code Quality Scan
  run: tia ast scan all src/ --format json > reports/quality.json
```

#### Creating Custom Scanners

TIA's scanner architecture makes it easy to create game-specific scanners:

**Example: Game Balance Scanner**

```python
from lib.tia.ast.scanners.base_scanner import BaseScanner, ScanResult, Severity

class GameBalanceScanner(BaseScanner):
    """Scan for game balance issues."""

    name = "game-balance"
    description = "Find game balance issues (OP stats, broken progression)"
    category = "quality"
    file_patterns = ["*.py"]

    def scan_file(self, file_path: str) -> List[ScanResult]:
        # Your custom logic here
        # Check for stat values > threshold, etc.
        return []
```

**That's it!** Drop in `lib/tia/ast/scanners/` and it's auto-discovered.

**Learn more:**
- TIA AST docs: `/home/scottsen/src/tia/docs/domains/ast/`
- Base scanner: `/home/scottsen/src/tia/lib/tia/ast/scanners/base_scanner.py`
- Examples: `/home/scottsen/src/tia/lib/tia/ast/scanners/complexity_scanner.py`

---

## 2. Method & Function Design

### Small Methods Rule

**Guideline:** Keep methods small, focused, and easy to understand.

**Limits:**
- **Target**: 10-20 lines per method
- **Maximum**: 40 lines (if you exceed this, refactor!)
- **Cyclomatic complexity**: ≤ 5 (max 5 decision points)

```python
# ❌ BAD - Too long, does too much (70+ lines)
def process_turn(self):
    """Process a complete game turn."""
    # Get player input
    key = self.get_key_press()
    if key == 'h':
        dx, dy = -1, 0
    elif key == 'j':
        dx, dy = 0, 1
    # ... 10 more directions

    # Validate move
    new_x = self.player.x + dx
    new_y = self.player.y + dy
    if new_x < 0 or new_x >= self.map.width:
        return
    # ... more validation

    # Check for combat
    target = self.get_entity_at(new_x, new_y)
    if target:
        damage = self.player.attack - target.defense
        # ... 20 more lines of combat logic

    # Process monsters
    for monster in self.monsters:
        # ... 20 more lines of AI

    # Update UI
    # ... 10 more lines


# ✅ GOOD - Small, focused methods
def process_turn(self):
    """Process a complete game turn."""
    action = self._get_player_action()
    outcome = action.execute(self.context)

    if outcome.took_turn:
        self._process_monster_turns()
        self._update_ui(outcome)

def _get_player_action(self) -> Action:
    """Convert player input to action."""
    key = self.input_handler.get_key()
    return self.input_handler.key_to_action(key, self.player.entity_id)

def _process_monster_turns(self):
    """Run AI for all monsters."""
    self.ai_system.update()

def _update_ui(self, outcome: ActionOutcome):
    """Update UI with action outcome."""
    for message in outcome.messages:
        self.message_log.add(message)
    self.ui.refresh()
```

### Function Composition

**Pattern:** Build complex operations from small, composable functions.

```python
# ✅ Composable functions
def calculate_final_damage(attacker: Entity, defender: Entity) -> int:
    """Calculate final damage after all modifiers."""
    base_damage = _calculate_base_damage(attacker, defender)
    critical_damage = _apply_critical_multiplier(base_damage, attacker)
    final_damage = _apply_damage_reduction(critical_damage, defender)
    return max(1, final_damage)  # Always at least 1 damage

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

### Early Returns

**Pattern:** Use early returns to reduce nesting.

```python
# ❌ BAD - Deep nesting
def process_mining(self, player: Entity, ore_vein: Entity) -> ActionOutcome:
    if player.is_alive:
        if ore_vein is not None:
            if player.is_adjacent(ore_vein):
                if not ore_vein.is_mined:
                    # Actual logic here
                    return self._mine_ore(player, ore_vein)
                else:
                    return ActionOutcome.failure("Already mined")
            else:
                return ActionOutcome.failure("Too far away")
        else:
            return ActionOutcome.failure("No ore vein")
    else:
        return ActionOutcome.failure("Player is dead")


# ✅ GOOD - Early returns, flat structure
def process_mining(self, player: Entity, ore_vein: Entity) -> ActionOutcome:
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

    # Happy path - actual mining logic
    return self._mine_ore(player, ore_vein)
```

### Single Purpose Functions

**Rule:** Each function should do ONE thing and do it well.

```python
# ❌ BAD - Function does multiple things
def process_combat_and_update_ui(attacker: Entity, defender: Entity):
    """Attack and update UI."""
    # Combat logic
    damage = attacker.attack - defender.defense
    defender.take_damage(damage)

    # UI updates
    self.message_log.add(f"{attacker.name} hits {defender.name}!")
    self.ui.refresh()

    # Stats tracking
    self.stats.total_damage_dealt += damage

    # Achievement check
    if self.stats.total_damage_dealt > 1000:
        self.unlock_achievement("big_hitter")


# ✅ GOOD - Separate concerns
def resolve_attack(attacker: Entity, defender: Entity) -> AttackResult:
    """Calculate and apply attack damage."""
    damage = self._calculate_damage(attacker, defender)
    actual_damage = defender.take_damage(damage)

    return AttackResult(
        attacker_id=attacker.entity_id,
        defender_id=defender.entity_id,
        damage=actual_damage,
        killed=not defender.is_alive,
    )

def update_combat_ui(result: AttackResult):
    """Update UI with combat result."""
    message = self._format_combat_message(result)
    self.message_log.add(message)
    self.ui.refresh()

def track_combat_stats(result: AttackResult):
    """Track combat statistics."""
    self.stats.total_damage_dealt += result.damage
    self._check_combat_achievements()
```

---

## 2. Single Responsibility Principle

### Class Responsibilities

**Rule:** Each class should have ONE reason to change.

```python
# ❌ BAD - God class with multiple responsibilities
class Game:
    """Manages entire game (TOO MUCH!)."""

    def __init__(self):
        self.player = Player()
        self.monsters = []
        self.map = None
        self.ui = UI()
        self.database = Database()
        self.network = NetworkClient()

    def process_turn(self):
        """Game logic"""
        pass

    def render(self):
        """Rendering"""
        pass

    def save_game(self):
        """Persistence"""
        pass

    def connect_to_server(self):
        """Networking"""
        pass

    def load_config(self):
        """Configuration"""
        pass


# ✅ GOOD - Separated responsibilities
class Game:
    """Coordinates game systems (ONE job: orchestration)."""

    def __init__(self, context: GameContext):
        self.context = context
        self.state = GameState()
        self.systems = self._init_systems()

    def process_turn(self, action: Action):
        """Process one game turn."""
        outcome = action.execute(self.context)
        if outcome.took_turn:
            self.systems.update_all()
        return outcome


class GameRenderer:
    """Renders game state to UI (ONE job: rendering)."""

    def render(self, state: GameState):
        """Render current game state."""
        self._render_map(state.map)
        self._render_entities(state.entities)
        self._render_ui(state.player)


class GamePersistence:
    """Saves/loads game state (ONE job: persistence)."""

    def save(self, state: GameState, path: Path):
        """Save game state to file."""
        data = state.to_dict()
        with open(path, 'w') as f:
            json.dump(data, f)

    def load(self, path: Path) -> GameState:
        """Load game state from file."""
        with open(path) as f:
            data = json.load(f)
        return GameState.from_dict(data)
```

### Responsibility Indicators

**Ask yourself:**
- Can I describe this class/function in one sentence without using "and"?
- How many different reasons would cause me to change this code?
- If I need to modify behavior X, do I have to touch code related to Y?

**Good signs (✅):**
- Class name is a noun (Player, CombatSystem, ContentLoader)
- Method name starts with verb (calculate, validate, process)
- Few dependencies (constructor takes 1-3 parameters)
- No "Manager" or "Helper" in class name

**Bad signs (❌):**
- Class name contains "And" (PlayerAndMonsterManager)
- Method does "X and also Y"
- Constructor takes 5+ parameters
- "Util" or "Helper" classes (often code smell)

---

## 3. Logging Architecture

### Structured Logging

**Setup:**

```python
# src/core/logging/logger.py
import logging
import json
from datetime import datetime
from typing import Any, Dict

class StructuredLogger:
    """Structured logger with consistent format."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}

    def with_context(self, **kwargs) -> 'StructuredLogger':
        """Add context that persists across log calls."""
        new_logger = StructuredLogger(self.logger.name)
        new_logger.context = {**self.context, **kwargs}
        return new_logger

    def info(self, message: str, **extra):
        """Log info message with structured data."""
        self._log(logging.INFO, message, extra)

    def error(self, message: str, **extra):
        """Log error message with structured data."""
        self._log(logging.ERROR, message, extra)

    def _log(self, level: int, message: str, extra: Dict[str, Any]):
        """Internal logging with structure."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'message': message,
            'level': logging.getLevelName(level),
            **self.context,
            **extra,
        }
        self.logger.log(level, json.dumps(log_data))


# Usage
logger = StructuredLogger(__name__)

# Add persistent context
player_logger = logger.with_context(
    player_id='p123',
    session_id='s456',
)

# Log with additional fields
player_logger.info(
    "Player action executed",
    action_type="move",
    from_pos=(10, 5),
    to_pos=(11, 5),
    turn=42,
)
# Output: {"timestamp": "2025-10-24T...", "message": "Player action executed",
#          "level": "INFO", "player_id": "p123", "action_type": "move", ...}
```

### Logging Levels (Detailed)

| Level | When to Use | Examples | Searchable? |
|-------|-------------|----------|-------------|
| **DEBUG** | Development details, debugging | Turn processing steps, state transitions | High volume |
| **INFO** | Normal operations, milestones | Game started, level completed, player logged in | Medium volume |
| **WARNING** | Unusual but recoverable | Retry attempts, deprecated features used | Low volume |
| **ERROR** | Operation failed, needs attention | Save failed, invalid action, API error | Very low volume |
| **CRITICAL** | System failure, data loss | Database corruption, server crash | Rare |

### What to Log

```python
# ✅ GOOD - Log important operations
class CombatSystem:
    def __init__(self):
        self.logger = StructuredLogger(__name__)

    def resolve_attack(self, attacker: Entity, defender: Entity) -> AttackResult:
        """Resolve combat attack."""
        # Log entry with context
        self.logger.info(
            "Combat attack started",
            attacker_id=attacker.entity_id,
            defender_id=defender.entity_id,
            attacker_hp=attacker.hp,
            defender_hp=defender.hp,
        )

        damage = self._calculate_damage(attacker, defender)
        actual_damage = defender.take_damage(damage)

        # Log result
        self.logger.info(
            "Combat attack resolved",
            attacker_id=attacker.entity_id,
            defender_id=defender.entity_id,
            damage=actual_damage,
            defender_hp_remaining=defender.hp,
            defender_died=not defender.is_alive,
        )

        return AttackResult(damage=actual_damage, killed=not defender.is_alive)


# ❌ BAD - Too much/too little logging
def bad_logging_example(self, x: int, y: int):
    print(f"Checking position")  # ❌ Uses print instead of logger
    # ❌ No logging of important operation
    result = self._complex_calculation(x, y)
    return result
```

### Performance Logging

```python
import time
from contextlib import contextmanager

@contextmanager
def log_performance(logger: StructuredLogger, operation: str, **context):
    """Context manager for logging operation performance."""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        logger.info(
            f"{operation} completed",
            operation=operation,
            duration_ms=int(duration * 1000),
            **context,
        )


# Usage
with log_performance(logger, "dungeon_generation", width=80, height=24):
    dungeon = self.generator.generate(80, 24)
# Logs: {"operation": "dungeon_generation", "duration_ms": 45, "width": 80, "height": 24}
```

---

## 4. Error Handling Standards

### Exception Hierarchy

```python
# src/core/exceptions.py
class VeinbornError(Exception):
    """Base exception for all Veinborn errors."""
    pass


# Game logic errors (recoverable)
class GameError(VeinbornError):
    """Error in game logic."""
    pass

class InvalidActionError(GameError):
    """Action cannot be performed."""
    pass

class InvalidStateError(GameError):
    """Game state is invalid."""
    pass


# Data errors
class DataError(VeinbornError):
    """Error loading/validating data."""
    pass

class ContentValidationError(DataError):
    """Content YAML validation failed."""
    pass


# System errors (usually not recoverable)
class SystemError(VeinbornError):
    """System-level error."""
    pass

class SaveLoadError(SystemError):
    """Failed to save/load game."""
    pass

class NetworkError(SystemError):
    """Network communication failed."""
    pass
```

### Error Handling Patterns

```python
# ✅ GOOD - Specific exceptions, proper handling
def load_monster_content(self, monster_id: str) -> MonsterData:
    """Load monster from content system."""
    try:
        path = self.content_dir / f"monsters/{monster_id}.yaml"

        if not path.exists():
            raise ContentValidationError(
                f"Monster content not found: {monster_id}",
                monster_id=monster_id,
                path=str(path),
            )

        with open(path) as f:
            data = yaml.safe_load(f)

        # Validate with Pydantic
        monster = MonsterData(**data)
        return monster

    except yaml.YAMLError as e:
        raise ContentValidationError(
            f"Invalid YAML in monster content: {monster_id}",
            monster_id=monster_id,
            original_error=str(e),
        ) from e

    except ValidationError as e:
        raise ContentValidationError(
            f"Monster content validation failed: {monster_id}",
            monster_id=monster_id,
            errors=e.errors(),
        ) from e


# ❌ BAD - Swallowing exceptions, bare except
def bad_error_handling(self, monster_id: str):
    try:
        return self._load(monster_id)
    except:  # ❌ Bare except catches everything!
        return None  # ❌ Silent failure, no logging!
```

### Custom Exception Data

```python
class VeinbornError(Exception):
    """Base exception with structured data."""

    def __init__(self, message: str, **context):
        super().__init__(message)
        self.message = message
        self.context = context

    def to_dict(self) -> dict:
        """Convert to structured format for logging."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            **self.context,
        }


# Usage
try:
    action.execute(context)
except InvalidActionError as e:
    logger.error(
        "Action execution failed",
        **e.to_dict(),  # Includes all context
    )
```

### Fail Fast vs Graceful Degradation

```python
# Development: Fail fast
if config.environment == "development":
    def validate_entity(entity: Entity):
        """Strict validation in development."""
        if entity.hp < 0:
            raise InvalidStateError(
                "Entity HP cannot be negative",
                entity_id=entity.entity_id,
                hp=entity.hp,
            )

# Production: Graceful degradation
else:
    def validate_entity(entity: Entity):
        """Graceful validation in production."""
        if entity.hp < 0:
            logger.error(
                "Invalid entity state detected, auto-correcting",
                entity_id=entity.entity_id,
                hp=entity.hp,
            )
            entity.hp = 0  # Auto-fix instead of crashing
```

---

## 5. Performance Guidelines

### Profiling Before Optimizing

**Rule:** Never optimize without measuring first.

```python
# Use cProfile for profiling
import cProfile
import pstats

def profile_game_loop():
    """Profile game loop performance."""
    profiler = cProfile.Profile()
    profiler.enable()

    # Run game for 100 turns
    for _ in range(100):
        game.process_turn()

    profiler.disable()

    # Print stats
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions


# Use timeit for micro-benchmarks
import timeit

def benchmark_pathfinding():
    """Compare pathfinding algorithms."""
    setup = "from src.core.pathfinding import astar, dijkstra"

    astar_time = timeit.timeit(
        "astar(start, goal, map)",
        setup=setup,
        number=1000,
    )

    print(f"A* average: {astar_time / 1000:.4f}s")
```

### Performance Targets (MVP)

| Operation | Target | Maximum | How to Measure |
|-----------|--------|---------|----------------|
| **Player action** | < 16ms | < 50ms | 60 FPS minimum |
| **Dungeon generation** | < 100ms | < 500ms | Feels instant |
| **Monster AI (per monster)** | < 1ms | < 5ms | 100 monsters = 100ms |
| **Save game** | < 500ms | < 2s | Acceptable delay |
| **Load game** | < 1s | < 5s | Acceptable delay |

### Optimization Patterns

```python
# ✅ GOOD - Cache expensive calculations
class Monster:
    def __init__(self):
        self._cached_path: Optional[List[Tuple[int, int]]] = None
        self._cached_path_target: Optional[Tuple[int, int]] = None

    def get_path_to(self, target_x: int, target_y: int) -> List[Tuple[int, int]]:
        """Get path to target (with caching)."""
        target = (target_x, target_y)

        # Use cached path if target hasn't moved
        if self._cached_path_target == target and self._cached_path:
            return self._cached_path

        # Recalculate path
        path = self._calculate_path(target_x, target_y)
        self._cached_path = path
        self._cached_path_target = target
        return path


# ✅ GOOD - Avoid unnecessary work
class CombatSystem:
    def get_targets_in_range(self, entity: Entity, radius: int) -> List[Entity]:
        """Get entities within range (optimized)."""
        # Early exit for empty
        if not self.context.entities:
            return []

        # Squared distance to avoid sqrt
        radius_sq = radius * radius

        targets = []
        for other in self.context.entities.values():
            if other == entity or not other.is_alive:
                continue  # Skip self and dead entities

            dx = other.x - entity.x
            dy = other.y - entity.y
            dist_sq = dx * dx + dy * dy

            if dist_sq <= radius_sq:
                targets.append(other)

        return targets


# ❌ BAD - Unnecessary sorting/filtering
def bad_performance(self):
    # ❌ Sorts entire list every frame
    sorted_monsters = sorted(self.monsters, key=lambda m: m.hp)

    # ❌ Multiple iterations
    alive_monsters = [m for m in sorted_monsters if m.is_alive]
    nearby_monsters = [m for m in alive_monsters if m.distance_to(player) < 10]

    return nearby_monsters


# ✅ GOOD - Single pass with generator
def good_performance(self):
    # ✅ Single iteration, no intermediate lists
    return [
        m for m in self.monsters
        if m.is_alive and m.distance_to(player) < 10
    ]
```

---

## 6. Configuration Management

### Configuration Structure

```python
# src/core/config.py
from dataclasses import dataclass
from pathlib import Path
import os
import yaml

@dataclass
class GameConfig:
    """Game configuration."""

    # Environment
    environment: str = "development"  # development, staging, production

    # Logging
    log_level: str = "INFO"
    log_file: str = "veinborn.log"

    # Performance
    target_fps: int = 60
    max_monsters_per_floor: int = 50
    pathfinding_cache_size: int = 1000

    # Content
    content_dir: Path = Path("data")
    hot_reload_enabled: bool = True

    # Persistence
    save_dir: Path = Path("saves")
    autosave_interval: int = 300  # seconds

    # Multiplayer (Phase 2)
    server_url: str = "nats://localhost:4222"
    enable_multiplayer: bool = False

    @classmethod
    def load(cls, config_file: Path = Path("config.yaml")) -> 'GameConfig':
        """Load configuration from YAML."""
        if config_file.exists():
            with open(config_file) as f:
                data = yaml.safe_load(f)
            return cls(**data)
        return cls()

    @classmethod
    def from_env(cls) -> 'GameConfig':
        """Load configuration from environment variables."""
        return cls(
            environment=os.getenv('VEINBORN_ENV', 'development'),
            log_level=os.getenv('VEINBORN_LOG_LEVEL', 'INFO'),
            hot_reload_enabled=os.getenv('VEINBORN_HOT_RELOAD', 'true') == 'true',
        )


# config.yaml (development)
environment: development
log_level: DEBUG
hot_reload_enabled: true
target_fps: 60


# config.prod.yaml (production)
environment: production
log_level: INFO
hot_reload_enabled: false
target_fps: 60
```

### Environment-Specific Settings

```python
# Load config based on environment
config_file = Path(f"config.{os.getenv('VEINBORN_ENV', 'development')}.yaml")
config = GameConfig.load(config_file)

# Override with environment variables
if os.getenv('VEINBORN_LOG_LEVEL'):
    config.log_level = os.getenv('VEINBORN_LOG_LEVEL')

# Use config
logger.setLevel(config.log_level)
game = Game(config=config)
```

---

## 7. Code Review Standards

### Code Review Checklist

**Before Submitting PR:**
- [ ] All tests pass (`pytest tests/`)
- [ ] Code coverage ≥ 80% for new code
- [ ] No linting errors (`ruff check src/`)
- [ ] Type checking passes (`mypy src/`)
- [ ] Manual testing completed
- [ ] Documentation updated (if needed)
- [ ] Commit messages follow convention

**Reviewer Checklist:**
- [ ] Code is readable and well-documented
- [ ] Methods are small (< 40 lines)
- [ ] Single responsibility maintained
- [ ] Error handling is appropriate
- [ ] Logging is adequate
- [ ] Performance impact considered
- [ ] Tests cover edge cases
- [ ] No security issues

### Review Guidelines

```python
# ✅ GOOD - Self-documenting code
def calculate_ore_mining_time(ore_vein: OreVein, miner: Entity) -> int:
    """Calculate turns required to mine ore.

    Mining time is based on:
    - Ore hardness (harder = longer)
    - Miner's mining skill (higher = faster)

    Args:
        ore_vein: The ore vein being mined
        miner: The entity mining

    Returns:
        Number of turns required (minimum 3, maximum 10)
    """
    base_time = 3
    hardness_modifier = ore_vein.hardness // 25  # +0-4 turns
    skill_modifier = miner.get_stat('mining_skill', 0) // 2  # -0-5 turns

    final_time = base_time + hardness_modifier - skill_modifier
    return max(3, min(10, final_time))


# ❌ BAD - Requires reviewer to figure out logic
def calc(o, m):
    t = 3 + o.h // 25 - m.s // 2  # ??? What is this formula?
    return max(3, min(10, t))
```

---

## 8. Debugging Practices

### Debugging Tools

```python
# 1. Python debugger (pdb)
import pdb

def complex_function():
    result = calculate_something()
    pdb.set_trace()  # Breakpoint: inspect variables
    return process(result)


# 2. pytest debugging
# Run: pytest --pdb tests/
# Drops into debugger on test failure


# 3. Rich console for pretty debugging
from rich.console import Console
console = Console()

def debug_entity_state(entity: Entity):
    """Print entity state for debugging."""
    console.print(f"[bold]Entity {entity.name}[/bold]")
    console.print(f"  HP: {entity.hp}/{entity.max_hp}")
    console.print(f"  Position: ({entity.x}, {entity.y})")
    console.print(f"  Stats: {entity.stats}")


# 4. Assert early and often (development)
def process_action(action: Action, context: GameContext):
    assert action is not None, "Action cannot be None"
    assert context is not None, "Context cannot be None"
    assert action.actor_id in context.entities, f"Actor {action.actor_id} not found"

    # Process action
    return action.execute(context)
```

---

## 9. Documentation Standards

### Docstring Format

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

### Code Comments

```python
# ✅ GOOD - Comments explain WHY, not WHAT
def calculate_damage(attacker: Entity, defender: Entity) -> int:
    """Calculate combat damage."""
    # Base damage from attack stat
    base_damage = attacker.attack

    # Apply defense reduction
    # Note: We always deal at least 1 damage to prevent
    # invincible enemies due to high defense
    final_damage = max(1, base_damage - defender.defense)

    return final_damage


# ❌ BAD - Comments just repeat code
def bad_comments(x, y):
    # Add x and y
    result = x + y

    # Return result
    return result
```

---

## Summary

### Operational Excellence Checklist

**Code Quality:**
- [ ] Methods are small (≤ 40 lines)
- [ ] Single responsibility maintained
- [ ] Early returns reduce nesting
- [ ] Functions are composable

**Logging:**
- [ ] Structured logging used
- [ ] Appropriate log levels
- [ ] Performance logged
- [ ] Context included

**Error Handling:**
- [ ] Specific exceptions
- [ ] Proper error hierarchy
- [ ] No silent failures
- [ ] Errors logged with context

**Performance:**
- [ ] Profiled before optimizing
- [ ] Targets met
- [ ] Caching used appropriately
- [ ] No premature optimization

**Configuration:**
- [ ] Environment-specific configs
- [ ] No hardcoded values
- [ ] Easy to override
- [ ] Documented defaults

**Code Review:**
- [ ] Tests pass
- [ ] Coverage adequate
- [ ] Documented
- [ ] Reviewed

---

**Next Steps:**
1. Read this alongside `MVP_DEVELOPMENT_GUIDELINES.md`
2. Use code review checklist for all PRs
3. Set up structured logging
4. Define exception hierarchy
5. Create configuration files

**For multiplayer operational excellence:** See `/docs/future-multiplayer/OBSERVABILITY.md` (Phase 2)

---

**Remember:** Operational excellence is about building systems that are easy to understand, debug, and maintain. Write code for the next person (who might be you in 6 months)!
