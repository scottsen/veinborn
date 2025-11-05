# Bot Refactoring Design: Service Extraction

**Date**: 2025-10-29
**Status**: Design Phase
**Approach**: Option 2 - Extract Services (Separation of Concerns)

---

## Executive Summary

**Goal**: Refactor BrogueBot from god object (40+ methods, ~10 responsibilities) into focused services with clear boundaries.

**Strategy**: Extract three core services while maintaining inheritance model for specialized bots.

**Timeline**:
- Phase 1: Bug fixes (2 hours)
- Phase 2: Service extraction (4-6 hours)
- Total: 6-8 hours

---

## Current Architecture Problems

### God Object Antipattern

**BrogueBot has too many responsibilities:**
1. **Perception** - Finding entities, assessing threats
2. **Tactical Decisions** - Should I fight/flee/mine?
3. **Action Planning** - How do I execute decisions?
4. **Movement** - Pathfinding and positioning
5. **Statistics** - Tracking game outcomes
6. **Validation** - Game state invariants
7. **Reporting** - Console output and JSON logs
8. **Game Loop** - Turn management
9. **Error Handling** - Crash logging
10. **Entity Intelligence** - Threat rankings

**Consequences:**
- Hard to test (40+ methods all coupled to Game object)
- Hard to understand (1500+ lines in one class)
- Hard to extend (adding features touches many methods)
- Duplication (specialized bots copy-paste override patterns)

---

## Target Architecture

### Service Boundaries

```
┌─────────────────────────────────────────────────────┐
│              BrogueBot (Orchestrator)               │
│  • Wires services together                          │
│  • Manages game loop                                │
│  • Handles statistics & reporting                   │
└──────────┬───────────────┬───────────────┬──────────┘
           │               │               │
           ▼               ▼               ▼
┌──────────────────┐ ┌───────────────┐ ┌──────────────┐
│PerceptionService │ │TacticalDecision│ │ActionPlanner │
│                  │ │   Service      │ │              │
│• find_monsters() │ │• should_fight()│ │• plan_action()│
│• find_ore_veins()│ │• should_flee() │ │• move_toward()│
│• assess_threat() │ │• should_mine() │ │• flee_from() │
│• find_adjacent() │ │• can_win_fight│ │• create_move()│
└──────────────────┘ └───────────────┘ └──────────────┘
```

### Dependency Flow

```
BrogueBot
  ├─> PerceptionService (no dependencies)
  ├─> TacticalDecisionService (depends on PerceptionService)
  └─> ActionPlanner (depends on PerceptionService + TacticalDecisionService)
```

---

## Service Specifications

### 1. PerceptionService

**Responsibility**: Answer "What do I see?" - Extract information from game state

**Methods to Extract** (10 methods):
```python
class PerceptionService:
    """Pure functions for querying game state."""

    # Monster perception
    def find_monsters(self, game: Game) -> List[Entity]
    def find_nearest_monster(self, game: Game) -> Optional[Entity]
    def monster_in_view(self, game: Game, distance: float) -> Optional[Entity]
    def is_adjacent_to_monster(self, game: Game) -> Optional[Entity]

    # Ore perception
    def find_ore_veins(self, game: Game) -> List[Entity]
    def find_valuable_ore(self, game: Game) -> Optional[Entity]
    def find_jackpot_ore(self, game: Game) -> Optional[Entity]
    def find_adjacent_ore(self, game: Game) -> Optional[Entity]  # NEW - for validation

    # Environment perception
    def find_level_exit(self, game: Game) -> Optional[Tuple[int, int]]
    def on_stairs(self, game: Game) -> bool

    # Threat assessment
    def assess_threat(self, monster: Entity) -> ThreatLevel  # Returns enum not string

    # Equipment perception (Phase 5)
    def find_forges(self, game: Game) -> List[Entity]
    def find_nearest_forge(self, game: Game) -> Optional[Entity]
    def has_unequipped_gear(self, game: Game) -> Optional[Entity]
    def has_craftable_ore(self, game: Game) -> Optional[str]
```

**Key Changes:**
- All static/pure functions (no state)
- No logging (just return data)
- Add `find_adjacent_ore()` to fix mining bug
- Return `ThreatLevel` enum instead of strings

**File**: `tests/fuzz/services/perception_service.py`

---

### 2. TacticalDecisionService

**Responsibility**: Answer "What should I do?" - Make decisions based on perception

**Methods to Extract** (8 methods):
```python
@dataclass
class CombatConfig:
    """Configuration for combat decisions."""
    health_threshold: float = 0.3      # When is health "low"?
    safety_margin: float = 1.5         # Combat win calculation multiplier
    engagement_range: float = 5.0      # How far to pursue enemies
    flee_priority: int = 6             # Priority in decision tree

@dataclass
class MiningConfig:
    """Configuration for mining decisions."""
    min_purity: int = 70               # Minimum purity worth mining
    jackpot_purity: int = 90           # Drop everything for this
    survey_distance: float = 3.0       # How far to seek unsurveyed ore

class TacticalDecisionService:
    """Makes tactical decisions based on perception and configuration."""

    def __init__(
        self,
        perception: PerceptionService,
        combat_config: CombatConfig = None,
        mining_config: MiningConfig = None
    ):
        self.perception = perception
        self.combat = combat_config or CombatConfig()
        self.mining = mining_config or MiningConfig()

    # Health assessment
    def is_low_health(self, game: Game) -> bool

    # Combat decisions
    def can_win_fight(self, game: Game, monster: Entity) -> bool
    def should_fight(self, game: Game) -> bool
    def should_flee(self, game: Game) -> bool

    # Mining decisions
    def should_mine_strategically(self, game: Game, ore_vein: Entity) -> bool
    def should_survey_ore(self, game: Game) -> Optional[Entity]

    # Progression decisions
    def should_descend(self, game: Game) -> bool

    # Crafting decisions (Phase 5)
    def should_craft(self, game: Game) -> bool
```

**Key Changes:**
- Takes config in constructor (enables customization)
- Uses PerceptionService instead of accessing game directly
- All decisions use config values instead of hardcoded thresholds

**File**: `tests/fuzz/services/tactical_decision_service.py`

---

### 3. ActionPlanner

**Responsibility**: Answer "How do I do it?" - Convert decisions into game actions

**Methods to Extract** (5 methods):
```python
class ActionPlanner:
    """Plans and creates validated actions."""

    def __init__(
        self,
        perception: PerceptionService,
        decisions: TacticalDecisionService,
        verbose: bool = False
    ):
        self.perception = perception
        self.decisions = decisions
        self.verbose = verbose

    # High-level planning
    def plan_next_action(self, game: Game, mode: str = 'strategic') -> tuple[str, dict]

    # Movement actions
    def move_towards(self, game: Game, target: Entity) -> tuple[str, dict]
    def flee_from(self, game: Game, threat: Entity) -> tuple[str, dict]

    # Specialized planning
    def get_smart_action(self, game: Game) -> tuple[str, dict]
    def get_random_action(self, game: Game) -> tuple[str, dict]

    # Action validation (NEW - prevents bugs!)
    def validate_action(self, game: Game, action_type: str, kwargs: dict) -> bool
```

**Key Changes:**
- Uses services instead of direct game access
- Add `validate_action()` to catch bugs before execution
- Returns validated actions only
- Logs via verbose flag instead of self.log()

**File**: `tests/fuzz/services/action_planner.py`

---

### 4. BrogueBot (Refactored)

**Responsibility**: Orchestrate services, manage game loop, track statistics

**Remaining Methods** (~15 methods):
```python
class BrogueBot:
    """Orchestrates bot gameplay using services."""

    def __init__(
        self,
        verbose: bool = False,
        mode: str = 'strategic',
        player_name: str = 'Bot',
        combat_config: CombatConfig = None,
        mining_config: MiningConfig = None
    ):
        self.verbose = verbose
        self.mode = mode
        self.player_name = player_name
        self.stats = BotStats()
        self.error_log: List[Dict] = []

        # Wire up services
        self.perception = PerceptionService()
        self.decisions = TacticalDecisionService(
            perception=self.perception,
            combat_config=combat_config,
            mining_config=mining_config
        )
        self.planner = ActionPlanner(
            perception=self.perception,
            decisions=self.decisions,
            verbose=verbose
        )

    # Logging
    def log(self, message: str) -> None
    def log_error(self, error: str, game_state: Optional[Dict]) -> None

    # Validation
    def validate_game_state(self, game: Game) -> List[str]

    # Game loop
    def play_one_game(self, max_turns: int) -> Dict
    def run(self, num_games: int, max_turns_per_game: int) -> None

    # Reporting
    def print_progress(self) -> None
    def print_final_report(self, elapsed_seconds: float) -> None
    def save_game_results(self) -> None

    # Threat ranking (keep for now, maybe extract later)
    def _build_threat_rankings(self) -> Dict[str, float]
    def get_monster_threat_level(self, monster: Entity) -> str  # Delegates to perception
```

**Key Changes:**
- Much smaller (1500 lines → ~500 lines)
- Clear single responsibility (orchestration)
- Services injected via constructor (testable!)
- Config passed to services

---

## Specialized Bot Migration

### Before (Current):
```python
class WarriorBot(BrogueBot):
    def __init__(self, verbose: bool = False):
        super().__init__(verbose, mode='strategic', player_name='Grimbash')
        self.character_class = CharacterClass.WARRIOR

    # Override 5 methods with copy-pasted logic + number changes
    def is_low_health(self, game, threshold=0.2): ...
    def can_win_fight(self, game, monster): ...
    def should_fight(self, game): ...
    def should_flee(self, game): ...
    def get_smart_action(self, game): ...
```

### After (Services):
```python
class WarriorBot(BrogueBot):
    """Aggressive melee-focused bot."""

    def __init__(self, verbose: bool = False):
        # Pass warrior configs to base class
        super().__init__(
            verbose=verbose,
            mode='strategic',
            player_name='Grimbash',
            combat_config=CombatConfig(
                health_threshold=0.15,    # Flee later
                safety_margin=1.2,        # More aggressive
                engagement_range=7.0      # Chase farther
            ),
            mining_config=MiningConfig(
                min_purity=50,            # Less picky
                survey_distance=2.0       # Don't wander
            )
        )
        self.character_class = CharacterClass.WARRIOR

    # Optional: Override planner for custom action priority
    def get_smart_action(self, game: Game) -> tuple:
        """Warriors prioritize combat over everything."""
        # Can still override if needed, but most customization via config!
        return self.planner.get_smart_action(game)
```

**Benefits:**
- No more copy-paste method overrides
- Bot personality = just config values
- Can still override for truly custom logic
- Much shorter files (188 lines → ~50 lines)

---

## Migration Strategy

### Phase 1: Critical Bug Fixes (2 hours)

**Goal**: Make bot functional without refactoring

**Changes to `brogue_bot.py`:**

1. **Fix adjacency checks** (3 locations):
```python
# BEFORE (WRONG)
if dist <= 1:
    return ('mine', {})

# AFTER (CORRECT)
if game.state.player.is_adjacent(ore_vein):
    return ('mine', {})
```

2. **Add context validation to random actions**:
```python
def get_random_action(self, game: Game) -> tuple:
    action_weights = {'move': 70, 'wait': 30}  # Remove survey/mine

    # Only add survey/mine if adjacent to ore
    adjacent_ore = self._find_adjacent_ore_vein(game)
    if adjacent_ore:
        action_weights['survey'] = 10
        action_weights['mine'] = 10

    # ... rest of logic
```

3. **Fix stuck detection**:
```python
if is_stuck:
    # Try random action, but validate it first
    for attempt in range(5):
        action_type, kwargs = self.get_random_action(game)
        if self._validate_action_feasible(game, action_type, kwargs):
            break
    else:
        # All random actions failed - just wait
        action_type, kwargs = ('wait', {})
```

**Testing**: Run `profile_bot.py` - should complete >100 turns with 0 validation errors

---

### Phase 2: Service Extraction (4-6 hours)

**Step 1: Create service directory structure**
```
tests/fuzz/
├── services/
│   ├── __init__.py
│   ├── perception_service.py
│   ├── tactical_decision_service.py
│   └── action_planner.py
├── brogue_bot.py (refactored)
├── warrior_bot.py (refactored)
└── ... other bots
```

**Step 2: Extract PerceptionService** (1 hour)
- Copy 10 perception methods to new file
- Make all methods static or pure functions
- Remove `self.log()` calls
- Add type hints
- Write 5-10 unit tests

**Step 3: Extract TacticalDecisionService** (1 hour)
- Copy 8 decision methods
- Add config dataclasses
- Inject PerceptionService
- Replace hardcoded thresholds with config values
- Write 10-15 unit tests

**Step 4: Extract ActionPlanner** (1 hour)
- Copy action planning methods
- Inject both services
- Add action validation
- Write 5-10 unit tests

**Step 5: Refactor BrogueBot** (1 hour)
- Remove extracted methods
- Wire up services in `__init__`
- Update `play_one_game()` to use planner
- Verify all tests still pass

**Step 6: Update specialized bots** (1 hour)
- Refactor WarriorBot, RogueBot, MageBot, HealerBot
- Replace method overrides with config
- Keep custom `get_smart_action()` where needed
- Test each bot

---

## Testing Strategy

### Unit Tests (New)

**PerceptionService Tests** (`tests/unit/test_perception_service.py`):
```python
def test_find_monsters_returns_only_living():
    # Create game with 2 living, 1 dead monster
    assert len(perception.find_monsters(game)) == 2

def test_find_adjacent_ore_returns_none_when_not_adjacent():
    # Player at (5,5), ore at (10,10)
    assert perception.find_adjacent_ore(game) is None

def test_find_adjacent_ore_returns_ore_when_diagonal():
    # Player at (5,5), ore at (6,6) - diagonal = adjacent!
    assert perception.find_adjacent_ore(game) is not None

def test_assess_threat_returns_deadly_for_boss():
    boss = Monster(name="Dragon", hp=200, attack=50)
    assert perception.assess_threat(boss) == ThreatLevel.DEADLY
```

**TacticalDecisionService Tests** (`tests/unit/test_tactical_decision_service.py`):
```python
def test_is_low_health_respects_config():
    config = CombatConfig(health_threshold=0.5)
    decisions = TacticalDecisionService(perception, combat_config=config)

    # Player at 40% HP
    assert decisions.is_low_health(game) == True  # Below 50%

def test_can_win_fight_uses_safety_margin():
    # Create even-matched monster
    # With safety_margin=1.5, should return False
    # With safety_margin=1.0, should return True
    pass

def test_should_flee_when_low_health_and_monster_nearby():
    # Player at 20% HP, monster 3 tiles away
    assert decisions.should_flee(game) == True
```

**ActionPlanner Tests** (`tests/unit/test_action_planner.py`):
```python
def test_validate_action_rejects_mine_when_not_adjacent():
    action_valid = planner.validate_action(game, 'mine', {})
    assert action_valid == False

def test_plan_next_action_returns_flee_when_threatened():
    # Setup: player low HP, monster nearby
    action_type, kwargs = planner.plan_next_action(game)
    assert action_type == 'move'  # Moving to flee

def test_move_towards_uses_pathfinding():
    # Player at (5,5), target at (10,10)
    action_type, kwargs = planner.move_towards(game, target)
    assert action_type == 'move'
    assert 'dx' in kwargs and 'dy' in kwargs
```

### Integration Tests (Existing)

**Bot Integration Test** (`tests/unit/test_bot_mining.py` - update existing):
```python
def test_bot_completes_100_turns_without_errors():
    """Bot should play 100 turns with 0 validation failures."""
    bot = BrogueBot(verbose=False, mode='strategic')
    stats = bot.play_one_game(max_turns=100)

    assert stats['turns'] >= 100  # Completed turns
    assert len(bot.error_log) == 0  # No errors logged

def test_warrior_bot_uses_aggressive_config():
    """Warrior should fight more aggressively than base bot."""
    warrior = WarriorBot(verbose=False)

    # Check config was applied
    assert warrior.decisions.combat.health_threshold == 0.15
    assert warrior.decisions.combat.safety_margin == 1.2
```

---

## Success Criteria

### Phase 1 Complete When:
- ✅ Bot completes 500 turns in profile_bot.py
- ✅ 0 validation errors in console output
- ✅ 0 "not adjacent" errors
- ✅ All existing tests still pass

### Phase 2 Complete When:
- ✅ 3 new service files created
- ✅ 30+ unit tests written for services
- ✅ BrogueBot reduced from 1500 → ~500 lines
- ✅ All specialized bots updated
- ✅ All 385 game tests still pass
- ✅ Bot completes 500 turns with 0 errors
- ✅ Each service has <300 lines, clear responsibility

---

## Risk Assessment

### Low Risk:
- PerceptionService extraction (pure functions, easy to test)
- Adding unit tests (no behavior changes)

### Medium Risk:
- TacticalDecisionService (some complex logic)
- ActionPlanner (interacts with game state)
- Config changes breaking specialized bots

### High Risk:
- Changing action validation logic (could introduce regressions)
- Breaking game loop orchestration

### Mitigation:
1. **Extract incrementally** - One service at a time
2. **Test after each step** - Run full test suite + profile_bot
3. **Keep old code** - Comment out, don't delete (rollback option)
4. **Commit frequently** - Each service extraction is a commit

---

## Future Enhancements (Post-Refactor)

### Phase 3: Composition (Optional)
Once services are extracted, can add data-driven config:

```python
# Load bot personality from YAML
with open('bots/berserker.yaml') as f:
    config = BotConfig.from_yaml(f)
    bot = BrogueBot.from_config(config)
```

### Service Improvements:
1. **PathfindingService** - Extract pathfinding logic
2. **ValidationService** - Pre-validate all actions
3. **ThreatAssessmentService** - More sophisticated threat analysis
4. **InventoryService** - Equipment/crafting logic

---

## Open Questions

1. **Should we extract EntityLoader logic?**
   - Currently in BrogueBot.__init__
   - Could be its own service
   - Decision: Keep for now, extract later if needed

2. **How to handle verbose logging?**
   - Services shouldn't log directly
   - Option A: Return log messages with actions
   - Option B: Logging service
   - Decision: Pass verbose flag to ActionPlanner, log there

3. **Should services be stateless?**
   - PerceptionService: Yes (pure functions)
   - TacticalDecisionService: Yes (just config)
   - ActionPlanner: Yes (just config + verbose flag)
   - Decision: All stateless except BrogueBot (stats tracking)

---

## Next Steps

1. **Review this design** - Get feedback/approval
2. **Phase 1: Bug fixes** - Make bot functional (2 hours)
3. **Phase 2a: Extract PerceptionService** - First service (1 hour)
4. **Phase 2b-e: Extract remaining services** - Complete refactor (3-4 hours)
5. **Validation** - Run full test suite + overnight bot run

---

**Ready to proceed?** Start with Phase 1 (bug fixes) or jump to Phase 2 (extraction)?
