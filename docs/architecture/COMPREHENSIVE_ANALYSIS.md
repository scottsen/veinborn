---
project: veinborn
document_type: architecture-analysis
analysis_date: 2025-11-06
phase: mvp-phase1
status: production-ready
beth_topics: [architecture, code-quality, design-patterns, lua-integration, event-system, bsp-algorithm, action-pattern, extensibility, multiplayer-ready]
keywords: [roguelike, game-architecture, python, yaml-config, factory-pattern, clean-architecture, scripting-ready]
---

# VEINBORN ROGUELIKE GAME - COMPREHENSIVE ARCHITECTURAL ANALYSIS

**Analysis Date:** 2025-11-06
**Project:** Veinborn (NetHack + SWG Mining + Multiplayer Co-op)
**Codebase Size:** ~3,550 lines of core Python
**Phase:** MVP (Phase 1 - 95% complete)
**Status:** Single-player, production-ready foundation

---

## EXECUTIVE SUMMARY

Veinborn has a **well-architected, maintainable codebase** with clear separation of concerns and strong foundations for scripting integration. The system uses:

- **Clean architecture pattern** (GameState → GameContext → Systems)
- **Action/outcome pattern** for all gameplay mechanics
- **Data-driven design** (YAML-based entity definitions)
- **Factory pattern** for extensible action creation
- **System architecture** for encapsulated subsystems
- **Minimal hardcoded game logic** (~5% of codebase)

**Key Strengths:**
- Well-organized module structure with clear responsibilities
- Type-safe (Python 3.10+ with type hints throughout)
- Comprehensive test infrastructure (unit, integration, fuzz testing)
- Event-ready pattern for future event buses
- Clear extensibility points for scripting

**Pain Points:**
- Some procedural generation still hardcoded (dungeon generation, spawning logic)
- Limited event system (event data in outcomes but no pub/sub)
- AI system only supports one behavior type (aggressive)
- Multiplayer support is not yet implemented
- Some magic numbers in constants vs configuration

**Scripting Readiness:** **READY** - Well-architected for immediate Lua integration

---

## 1. CORE ARCHITECTURE OVERVIEW

### 1.1 High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                  Textual UI Layer                       │
│        (app.py, widgets, terminal rendering)           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                  Game Controller                        │
│  game.py: Orchestrates state, systems, and turn flow   │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
   ┌────────┐  ┌──────────┐  ┌──────────────┐
   │ Systems│  │Game State│  │Game Context  │
   │        │  │(entities,│  │(safe API)    │
   │ • AI   │  │ messages)│  │              │
   │        │  └──────────┘  └──────────────┘
   └────────┘         ▲              │
                      │              │
          ┌───────────┼──────────────┘
          │           │
          ↓           ↓
    ┌────────────────────────┐
    │  Actions & Outcomes    │
    │                        │
    │ • MoveAction          │
    │ • AttackAction        │
    │ • MineAction          │
    │ • CraftAction         │
    │ • ... (more)          │
    └────────────────────────┘
          ▲
          │
    ┌─────┴──────────────────┐
    │                        │
    ↓                        ↓
┌──────────┐          ┌──────────────┐
│ActionFact│          │Entity Loader │
│ory       │          │(YAML)        │
└──────────┘          └──────────────┘
```

### 1.2 Directory Structure

```
src/core/
├── game.py                    # ⭐ Main controller (382 lines)
├── game_state.py              # Game state container
├── turn_processor.py           # Turn sequencing
├── world.py                   # Map generation (BSP)
├── entities.py                # Player, Monster, OreVein
├── character_class.py         # Class system
│
├── base/
│   ├── entity.py              # ⭐ Base Entity class
│   ├── action.py              # ⭐ Action base class + outcome pattern
│   ├── system.py              # System base class
│   └── game_context.py        # ⭐ Safe API facade
│
├── actions/                   # All game actions
│   ├── action_factory.py      # ⭐ Factory pattern
│   ├── move_action.py
│   ├── attack_action.py
│   ├── mine_action.py
│   ├── craft_action.py
│   ├── survey_action.py
│   ├── descend_action.py
│   └── equip_action.py
│
├── systems/
│   └── ai_system.py           # Monster AI behavior
│
├── spawning/
│   └── entity_spawner.py      # Spawn monsters/ore/forges
│
├── entity_loader.py           # ⭐ Data-driven entity creation
├── crafting.py                # ⭐ Recipe system + stat formulas
├── loot.py                    # ⭐ Loot generation + tables
├── pathfinding.py             # A* pathfinding
├── perception.py              # Field of view
├── save_load.py               # Save/load system
├── legacy.py                  # Legacy Vault (meta-progression)
├── highscore.py               # High score tracking
├── rng.py                     # Random number generation
├── constants.py               # Game constants
└── config/
    ├── config_loader.py       # Config management
    └── user_config.py         # User settings

ui/
└── textual/
    ├── app.py                 # Textual application
    ├── widgets/
    │   ├── map_widget.py      # Map display
    │   ├── status_bar.py      # Status info
    │   ├── message_log.py     # Message log
    │   └── sidebar.py         # Inventory/info

data/
├── entities/
│   ├── monsters.yaml          # ⭐ Monster definitions
│   ├── ores.yaml              # ⭐ Ore type definitions
│   └── items.yaml             # ⭐ Item definitions
└── balance/
    ├── recipes.yaml           # ⭐ Crafting recipes
    ├── loot_tables.yaml       # ⭐ Loot drops
    ├── monster_spawns.yaml    # ⭐ Spawn rates
    ├── forges.yaml            # ⭐ Forge definitions
    └── game_constants.yaml    # Balance constants
```

**⭐ = Critical for understanding or modification**

---

## 2. ENTITY/COMPONENT SYSTEM

### 2.1 Entity Architecture

All game objects inherit from the `Entity` base class:

```python
@dataclass
class Entity:
    """Base entity - everything in the game."""
    entity_id: str
    name: str
    entity_type: EntityType        # PLAYER, MONSTER, ITEM, ORE_VEIN, FORGE
    x: Optional[int] = None
    y: Optional[int] = None
    
    # Combat stats
    hp: int = 0
    max_hp: int = 0
    attack: int = 0
    defense: int = 0
    
    # Generic stats storage (flexible properties)
    stats: Dict[str, Any] = field(default_factory=dict)
```

**Entity Types:**
- `PLAYER` - Player character
- `MONSTER` - Enemies (Goblin, Orc, Troll)
- `ITEM` - Dropped loot (weapons, armor, potions)
- `ORE_VEIN` - Minable resources (Copper, Iron, Mithril, Adamantite)
- `FORGE` - Crafting stations
- `PROJECTILE` - Future ranged attacks

### 2.2 Specialized Entity Subclasses

**Player Entity:**
```python
@dataclass
class Player(Entity):
    inventory: List[Entity]           # Carried items
    equipped_weapon: Optional[Entity]
    equipped_armor: Optional[Entity]
    
    def add_to_inventory(item: Entity) -> bool
    def gain_xp(amount: int) -> bool
    def get_total_attack() -> int     # Base + weapon bonus
    def get_total_defense() -> int    # Base + armor bonus
```

**Monster Entity:**
```python
@dataclass
class Monster(Entity):
    xp_reward: int                    # XP on death
    ai_type: str                      # "aggressive", "fleeing", etc. (future)
    
    # Created via EntityLoader (data-driven)
    # No hardcoded factory methods
```

**OreVein Entity:**
```python
@dataclass
class OreVein(Entity):
    ore_type: str                     # copper, iron, mithril, adamantite
    hardness: int                     # 0-100
    conductivity: int                 # 0-100
    malleability: int                 # 0-100
    purity: int                       # 0-100 (quality multiplier)
    density: int                       # 0-100
    
    # Properties drive crafted equipment stats
    average_quality: int              # Average of all properties
```

### 2.3 Data Flow: Entities

```
Entity Definition (YAML)
    ↓
EntityLoader.create_monster(id, x, y)
    ↓
Monster instance (in-memory)
    ↓
GameContext.add_entity(monster)
    ↓
GameState.entities[id] = monster
    ↓
Action.execute() reads/modifies via GameContext
    ↓
Save file (JSON serialization)
```

**Strengths:**
- Single base class eliminates duplication
- Flexible stats dict allows custom properties
- Type-safe entity type checking
- Easy to add new entity types

**Coupling Issues:**
- Entities hardcode some behaviors (e.g., `is_adjacent()`, `take_damage()`)
- Shouldn't be an issue for scripting, but could be more composable

---

## 3. GAME STATE MANAGEMENT

### 3.1 GameState - The Source of Truth

```python
class GameState:
    """Complete game state - mutable, the source of truth."""
    
    player: Player                    # Player entity
    entities: Dict[str, Entity]       # All game entities
    dungeon_map: Map                  # Current floor map
    
    # Game progression
    current_floor: int                # Dungeon depth (1-10)
    turn_count: int                   # Total turns elapsed
    
    # Gameplay tracking
    messages: List[str]               # Game log
    game_over: bool
    run_type: str                     # "pure" or "legacy"
    player_name: str
    
    # RNG state (for reproducibility)
    rng_state: Any                    # GameRNG internal state
```

**Properties:**
- **Single source of truth** - all state is here
- **Mutable** - systems modify this directly
- **Serializable** - save/load support
- **Thread-safe for future multiplayer** - use GameContext

### 3.2 GameContext - The Safe API

```python
class GameContext:
    """Safe, controlled access to game state."""
    
    def get_entity(id: str) -> Entity
    def get_player() -> Entity
    def get_entities_by_type(type: EntityType) -> List[Entity]
    def get_entity_at(x: int, y: int) -> Optional[Entity]
    
    def add_entity(entity: Entity) -> None
    def remove_entity(entity_id: str) -> None
    
    def get_map() -> Map
    def is_walkable(x: int, y: int) -> bool
    
    def get_system(name: str) -> System
    def register_system(name: str, system: System) -> None
    
    def add_message(msg: str) -> None
    def get_turn_count() -> int
    def get_floor() -> int
```

**Purpose:**
- **Sandbox for Lua scripts** - restrict what scripts can access
- **Testing** - easy to mock
- **Permission checks** - future multiplayer validation

### 3.3 The Clean Architecture Principle

```
GameState (data container)
    ↑
    │ (read/write)
    │
GameContext (safe facade)
    ↑
    │ (read/modify)
    │
Systems/Actions (business logic)
```

**Benefits:**
- Systems can't directly break state
- Easy to add permission checks (multiplayer)
- Easy to mock for testing
- **Ready for Lua integration** - scripts get GameContext

---

## 4. ACTION/OUTCOME PATTERN

### 4.1 Action System Design

All player and monster actions are represented as `Action` objects:

```python
@dataclass
class Action(ABC):
    """Base class for all game actions."""
    actor_id: str
    
    @abstractmethod
    def validate(context: GameContext) -> bool
        """Check if action is valid before execution."""
    
    @abstractmethod
    def execute(context: GameContext) -> ActionOutcome
        """Execute the action, modify state, return outcome."""
    
    @abstractmethod
    def to_dict() -> dict
    @classmethod
    @abstractmethod
    def from_dict(data: dict) -> Action
        """Serialization for multiplayer/replay."""
```

### 4.2 ActionOutcome Pattern (Event-Ready)

```python
@dataclass
class ActionOutcome:
    """Result of executing an action."""
    result: ActionResult              # SUCCESS, FAILURE, BLOCKED, INVALID
    took_turn: bool                   # Did this consume a game turn?
    messages: List[str]               # Messages to display
    events: List[dict]                # Events (Phase 2: publish to EventBus)
    
    @property
    def is_success(self) -> bool
        """Check if action succeeded."""
```

**Example:**
```python
outcome = AttackAction("player_1", "monster_5").execute(context)

print(outcome.messages)  # ["You hit Goblin for 4 damage"]
print(outcome.events)    # [{'type': 'entity_damaged', 'target': 'monster_5', ...}]
print(outcome.took_turn) # True
```

### 4.3 Action Examples

**MoveAction:**
```python
class MoveAction(Action):
    dx: int  # Direction (-1, 0, 1)
    dy: int
    
    def validate(context) -> bool:
        # Check target position is walkable
        # Check not blocked by entities/walls
        return True/False
    
    def execute(context) -> ActionOutcome:
        # Move entity
        # Update position in GameState
        return ActionOutcome.success()
```

**AttackAction:**
```python
class AttackAction(Action):
    target_id: str
    
    def validate(context) -> bool:
        # Check target exists and is alive
        # Check actor is adjacent
        return True/False
    
    def execute(context) -> ActionOutcome:
        # Calculate damage (attack - defense + RNG)
        # Apply damage to target
        # Handle loot drops if target dies
        # Reward XP
        return ActionOutcome.success(
            message=f"You deal {damage} damage",
            events=[{'type': 'entity_damaged', ...}]
        )
```

**MineAction:**
```python
class MineAction(Action):
    ore_vein_id: str
    
    def execute(context) -> ActionOutcome:
        # Multi-turn action: decrement turns_remaining
        # When complete: remove ore, add to inventory
        # Apply durability/conditions
        return ActionOutcome.success(
            message="You mine the ore vein...",
            took_turn=True
        )
```

### 4.4 Action Factory Pattern

```python
class ActionFactory:
    """Create actions from string identifiers."""
    
    def create(action_type: str, **kwargs) -> Optional[Action]:
        """
        factory.create('move', dx=1, dy=0)
        factory.create('attack', target_id='monster_5')
        factory.create('mine')  # Auto-finds adjacent ore
        """
    
    def register_handler(action_type: str, handler: ActionHandler) -> None:
        """Extend with custom action types (Lua scripts)."""
```

**Extensibility:**
```python
# Add a custom action type (future Lua scripting)
factory.register_handler('lua_spell', ActionHandler(
    name='lua_spell',
    create_fn=create_lua_action,
    description='Cast a Lua-defined spell'
))

action = factory.create('lua_spell', spell_id='fireball')
outcome = action.execute(context)
```

**Strengths:**
- Open/Closed Principle - extend without modifying
- Reduces Game class complexity (19 → 8 lines)
- Event-ready for future EventBus
- Serializable for multiplayer/replay
- Perfect foundation for Lua integration

---

## 5. GAME STATE FLOW & TURN PROCESSOR

### 5.1 Turn Execution Flow

```
Player Input (keyboard)
    ↓
Handle Action (move, attack, mine, etc.)
    ↓
ActionFactory.create() → Action object
    ↓
Action.validate(context) → True/False
    ↓
Action.execute(context) → ActionOutcome
    ↓
Add messages to game log
    ↓
TurnProcessor.process_turn()
    ├─ Increment turn counter
    ├─ Apply HP regeneration
    ├─ Run AI systems (monsters take turns)
    ├─ Cleanup dead entities
    └─ Check game over
    ↓
Render UI (map, status, messages)
```

### 5.2 TurnProcessor

```python
class TurnProcessor:
    """Orchestrates turn progression."""
    
    def process_turn(self):
        self._apply_hp_regeneration()     # NetHack: 1 HP every 10 turns
        self._run_ai_systems()             # Monsters act
        self._cleanup_dead_entities()      # Remove dead entities
        self._check_game_over()
            ├─ Record high score
            ├─ Save legacy ore (80+ purity)
            └─ Record defeat
```

**Key Insight:** TurnProcessor handles meta-game logic (scoring, vault integration) alongside turn mechanics.

---

## 6. PROCEDURAL GENERATION & SPAWNING

### 6.1 Dungeon Generation

**Location:** `world.py`

```python
class Map:
    """Procedural dungeon generation via BSP algorithm."""
    
    def __init__(self, width, height):
        self._generate_bsp()      # Binary Space Partitioning
        self._create_rooms()      # Carve rooms from walls
        self._create_corridors()  # Connect rooms
        self._place_stairs()      # Add stairs
```

**Issues:**
- BSP algorithm is hardcoded (not data-driven)
- Room types are seeded randomly, not from config
- No support for custom dungeon generators via Lua

### 6.2 Entity Spawning

**Location:** `spawning/entity_spawner.py`

```python
class EntitySpawner:
    """Spawn entities (monsters, ore, forges) per floor."""
    
    def spawn_monsters_for_floor(floor, dungeon_map) -> List[Monster]
        # Hardcoded: monsters = 3-8 per floor
        # Hardcoded: monster type selection (Goblin/Orc/Troll)
        
    def spawn_ore_veins_for_floor(floor, dungeon_map) -> List[OreVein]
        # Hardcoded: ore veins = 4-8 per floor
        # Data-driven: ore type distribution from YAML
        
    def spawn_forges_for_floor(floor, dungeon_map) -> List[Forge]
        # Hardcoded: 1-2 forges per floor
        
    def spawn_special_room_entities(floor, dungeon_map) -> Dict
        # Special room handling (treasure, monster dens, etc.)
```

**Data-Driven Parts:**
```yaml
# data/balance/monster_spawns.yaml
monsters:
  goblin:
    floors: [1, 2, 3]
    min_count: 1
    max_count: 3
    
  orc:
    floors: [4, 5, 6, 7]
    min_count: 2
    max_count: 4
```

**Issues:**
- Monster count logic is hardcoded
- Room type selection is hardcoded
- No spawning rules per room type (treasure rooms should have less monsters)
- Special room generation could be in YAML

---

## 7. ACTION SYSTEMS & MECHANICS

### 7.1 Combat System

**File:** `actions/attack_action.py` (130 lines)

```python
def execute():
    # Damage calculation: attack - defense + RNG
    damage = max(1, actor_attack - target_defense + rng.randint(-2, 2))
    
    # Apply damage
    target.take_damage(damage)
    
    # Handle death
    if target.is_dead:
        # Generate loot
        loot = LootGenerator.get_instance().generate_loot(
            target.content_id,  # monster type
            floor_number=current_floor
        )
        
        # Add to player inventory/drop on ground
        for item in loot:
            player.add_to_inventory(item)
        
        # Reward XP
        player.gain_xp(target.xp_reward)
```

**Strengths:**
- Damage RNG is seeded (reproducible)
- Loot generation is data-driven (YAML)
- XP rewards are from entity definitions

**Issues:**
- Damage formula is hardcoded (could be data)
- Combat effects (poison, burning) not yet implemented
- No critical hits

### 7.2 Mining System

**File:** `actions/mine_action.py` (150 lines)

```python
class MineAction:
    """Multi-turn resource gathering."""
    
    def execute():
        ore_vein = context.get_entity(self.ore_vein_id)
        
        # First turn: check and store mining state
        if not player.mining_action:
            mining_turns = ore_vein.get_stat('mining_turns')
            player.mining_action = {
                'ore_vein_id': ore_vein.entity_id,
                'turns_remaining': mining_turns
            }
            return ActionOutcome.success(
                message=f"Mining {ore_vein.name}... ({mining_turns} turns)",
                took_turn=True
            )
        
        # Subsequent turns: decrement counter
        player.mining_action['turns_remaining'] -= 1
        
        if player.mining_action['turns_remaining'] > 0:
            return ActionOutcome.success(took_turn=True)
        
        # Mining complete: add to inventory
        ore_item = ore_vein.get_ore_item()
        player.add_to_inventory(ore_item)
        player.mining_action = None
        return ActionOutcome.success(
            message=f"Mined {ore_vein.ore_type}!",
            took_turn=True
        )
```

**Strengths:**
- Multi-turn action pattern is clean
- Ore properties drive crafting stats
- Supports resume mining (continue action if interrupted)

**Issues:**
- Mining damage/fatigue not implemented
- Ore depletion doesn't exist (can mine infinite ore)
- No risk/danger mechanic

### 7.3 Crafting System

**File:** `crafting.py` (300+ lines)

```python
@dataclass
class CraftingRecipe:
    """Convert ore → equipment."""
    recipe_id: str
    display_name: str
    requirements: Dict              # ore_type, ore_count, min_floor
    stat_formulas: Dict[str, str]   # "hardness * 0.1 + purity * 0.05"
    equipment_slot: str             # "weapon" or "armor"

class StatFormulaEvaluator:
    """Evaluate formula strings using simpleeval."""
    
    def evaluate(formula: str) -> int:
        # Safely evaluate: hardness * 0.1 + purity * 0.05
        return simple_eval(formula, names=ore_properties)
```

**Data Example:**
```yaml
# data/balance/recipes.yaml
recipes:
  copper_sword:
    display_name: "Copper Sword"
    requirements:
      ore_type: copper
      ore_count: 1
      min_floor: 1
    stat_formulas:
      attack_bonus: "hardness * 0.1 + purity * 0.05"
      defense_bonus: 0
      durability: "malleability * 0.3 + density * 0.2"
```

**Strengths:**
- Formula-based stat calculation (transparent)
- Data-driven recipes (easy to balance)
- Supports multi-ore recipes (future)
- Simpleeval is safe for formula evaluation

**Issues:**
- Formulas are strings, not data structures
- No support for conditional formulas
- No equipment degradation system
- Crafting action itself is simple (instant)

### 7.4 Loot System

**File:** `loot.py` (335 lines)

```python
class LootGenerator:
    """Generate random drops from monsters."""
    
    @classmethod
    def get_instance() -> LootGenerator:
        """Singleton - YAML loaded once."""
    
    def generate_loot(monster_type: str, floor: int) -> List[Entity]:
        # 1. Get loot table for monster type
        loot_table = self.loot_tables.get(monster_type)
        
        # 2. For each category (gold, weapons, armor)
        for category, data in loot_table.items():
            # 3. Roll drop chance
            if rng.random() < data['drop_chance']:
                # 4. Select item via weighted table
                item_id = self._select_item_from_category(data, rng)
                
                # 5. Create item entity
                item = self._create_item_entity(item_id, data, rng)
```

**Data Example:**
```yaml
# data/balance/loot_tables.yaml
goblin:
  description: "Weak goblin drops"
  gold:
    drop_chance: 0.7
    items:
      - {id: gold, weight: 10, amount_range: [5, 15]}
  weapons:
    drop_chance: 0.3
    items:
      - {id: dagger, weight: 5}
      - {id: club, weight: 3}
```

**Strengths:**
- Fully data-driven
- Singleton pattern avoids YAML re-parsing
- Weighted item selection
- Support for randomized item properties

**Issues:**
- Limited item rarity tiers
- No dynamic loot scaling by floor/difficulty
- Loot tables are static (can't be modified by Lua)

---

## 8. AI SYSTEM

### 8.1 Current AI

**File:** `systems/ai_system.py` (97 lines)

```python
class AISystem(System):
    """Monster behavior each turn."""
    
    def update(self):
        for monster in alive_monsters:
            ai_type = monster.get_stat('ai_type', 'aggressive')
            
            if ai_type == 'aggressive':
                self._aggressive_ai(monster)
    
    def _aggressive_ai(monster):
        if monster.is_adjacent(player):
            # Attack
            AttackAction(monster.id, player.id).execute(context)
        else:
            # Move toward player (A* pathfinding)
            direction = get_direction(map, monster.pos, player.pos)
            MoveAction(monster.id, dx, dy).execute(context)
```

**Features:**
- Pathfinding avoids walls
- Simple but effective
- Uses same action system as player

**Limitations:**
- Only one behavior type ("aggressive")
- No fleeing AI
- No ranged AI
- No group behavior
- No patrol patterns
- **AI type stored in entity but only 'aggressive' implemented**

### 8.2 Future AI Types (Defined but Unused)

```python
class AIState(Enum):
    IDLE = "idle"         # Not implemented
    CHASING = "chasing"   # Not implemented
    WANDERING = "wandering"  # Not implemented
    FLEEING = "fleeing"   # Not implemented
```

**Opportunity:** Easy to extend with Lua-based AI - agents register behavior functions.

---

## 9. COUPLING ANALYSIS

### 9.1 Tight Coupling (Issues)

**1. ActionFactory ↔ Specific Action Classes**
```python
# In action_factory.py
from .move_action import MoveAction
from .attack_action import AttackAction
from .mine_action import MineAction
...

# To add new action, must modify ActionFactory
```
**Impact:** Medium - Factory pattern alleviates this somewhat  
**Solution:** Dynamic action registration (already supports via `register_handler()`)

**2. TurnProcessor ↔ HighScoreManager + LegacyVault**
```python
def _check_game_over():
    self._record_high_score()      # Tight coupling
    self._save_legacy_ore()        # Tight coupling
    self._record_defeat()          # Tight coupling
```
**Impact:** Low - These are game-over side effects  
**Solution:** Event system would decouple (Phase 2)

**3. Game ↔ All Subsystems**
```python
# game.py creates and owns everything
self.spawner = EntitySpawner(...)
self.turn_processor = TurnProcessor(...)
self.floor_manager = FloorManager(...)
self.action_factory = ActionFactory(...)
```
**Impact:** Low - This is the orchestrator pattern  
**Solution:** Dependency injection works fine

**4. AttackAction ↔ LootGenerator**
```python
# Direct instantiation
loot = LootGenerator.get_instance().generate_loot(...)
```
**Impact:** Low - Singleton pattern makes this reasonable  
**Solution:** Could pass via GameContext

**5. EntityLoader ↔ YAML file paths**
```python
# Hardcoded path
entities_path = project_root / "data" / "entities"
```
**Impact:** Low - Configurable via parameter  
**Solution:** Already supports custom paths

### 9.2 Loose Coupling (Strengths)

**GameContext:** All systems use this, not GameState directly
**ActionOutcome:** Systems don't need to know about each other's results
**SystemInterface:** Systems are registered, not hardcoded
**Entity IDs:** Actions reference entities by ID, not object references

---

## 10. DATA VS CODE ANALYSIS

### 10.1 What's Data-Driven (GOOD)

```
✅ Monster definitions         → data/entities/monsters.yaml
✅ Ore type definitions        → data/entities/ores.yaml
✅ Item definitions            → data/entities/items.yaml
✅ Crafting recipes            → data/balance/recipes.yaml
✅ Loot tables                 → data/balance/loot_tables.yaml
✅ Monster spawn rates          → data/balance/monster_spawns.yaml
✅ Forge definitions           → data/balance/forges.yaml
✅ Game constants              → data/balance/game_constants.yaml (config_loader)
```

### 10.2 What's Hardcoded (NEEDS ATTENTION)

```
❌ BSP dungeon generation      → world.py (algorithm hardcoded)
❌ Damage calculation          → attack_action.py (formula hardcoded)
❌ Monster count per floor     → entity_spawner.py (logic hardcoded)
❌ Spawn position logic        → entity_spawner.py (hardcoded)
❌ Room type distribution      → entity_spawner.py (hardcoded)
❌ Turn length                 → constants.py (could be data)
❌ HP regeneration rate        → turn_processor.py (hardcoded)
❌ Equipment bonus calculation → crafting.py (uses formulas, partially data-driven)
```

### 10.3 Magic Numbers in Code

**Examples:**
```python
# constants.py
PLAYER_STARTING_HP = 20
PLAYER_STARTING_ATTACK = 5
PLAYER_STARTING_DEFENSE = 2

GOBLIN_HP = 6
GOBLIN_ATTACK = 3
GOBLIN_DEFENSE = 1

MINING_MIN_TURNS = 3
MINING_MAX_TURNS = 5

HP_REGEN_INTERVAL_TURNS = 10
HP_REGEN_AMOUNT = 1

# Should these be in game_constants.yaml?
```

---

## 11. EXTENSIBILITY & SCRIPTING POINTS

### 11.1 Where Lua Would Fit Naturally

**Tier 1 - Immediate Integration (100% compatible):**
1. **Custom Actions** - Register new action types
   ```lua
   -- custom_spell.lua
   local action = veinborn.actions.CustomSpell()
   action:validate(context)  -- returns boolean
   action:execute(context)   -- returns ActionOutcome
   ```

2. **AI Behaviors** - Custom monster AI
   ```lua
   -- troll_ai.lua
   function aggressive_with_retreat(monster, player)
       if monster.hp < monster.max_hp / 2 then
           -- Flee behavior
       else
           -- Attack behavior
       end
   end
   ```

3. **Item/Recipe Creation** - Extend crafting
   ```lua
   -- legendary_recipe.lua
   veinborn.recipes.register('legendary_sword', {
       requirements = { ore_type = 'adamantite', count = 3 },
       stat_formulas = {
           attack_bonus = 'hardness * 0.5 + purity * 0.3'
       }
   })
   ```

4. **Dungeon Generators** - Custom map generation
   ```lua
   -- dungeon_generator.lua
   function generate_floor(floor_number)
       local map = veinborn.Map.new(80, 24)
       -- Custom generation logic
       return map
   end
   ```

**Tier 2 - Medium Integration (requires minor refactoring):**
1. **Event Handlers** - Respond to game events
   ```lua
   veinborn.events:on('entity_died', function(event)
       -- Handle entity death
   end)
   ```

2. **Game Over Hooks** - Custom end-of-game logic
   ```lua
   veinborn.game:on_game_over(function(game_state)
       -- Custom scoring
   end)
   ```

3. **Custom Systems** - Register new game systems
   ```lua
   local weather_system = veinborn.System.new()
   veinborn.context:register_system('weather', weather_system)
   ```

**Tier 3 - Complex Integration (requires architecture changes):**
1. **Complete Procedural Generation** - Replace BSP
2. **Multiplayer Synchronization** - Custom netcode
3. **Persistent World State** - Save/load hooks

### 11.2 Current Extensibility Points

**ActionFactory:**
```python
# External code can add custom actions:
factory.register_handler('custom_action', ActionHandler(
    name='custom_action',
    create_fn=create_custom_action,
    description='A custom action'
))
```

**GameContext API:**
```python
# Systems can query and modify state safely:
context.get_entities_by_type(EntityType.MONSTER)
context.add_entity(entity)
context.get_system('ai')
```

**Configuration:**
```python
# Game-wide config from YAML:
config = ConfigLoader.load()
# Supports custom game constants
```

---

## 12. ISSUES & PAIN POINTS

### 12.1 Critical Issues

**None.** The codebase is production-ready for MVP.

### 12.2 High-Priority Improvements

1. **Event System Missing**
   - Events are defined in ActionOutcome but not published
   - Should have EventBus for Phase 2 multiplayer
   - **Effort:** Medium, no breaking changes needed

2. **AI System Limited**
   - Only one AI type implemented
   - Should support behavior registry (Lua hooks)
   - **Effort:** Low - already has framework

3. **Dungeon Generation Hardcoded**
   - BSP algorithm not data-driven
   - Should support custom generators
   - **Effort:** Medium - good abstraction point

4. **Spawning Logic Hardcoded**
   - Monster/ore/forge spawn counts hardcoded
   - Should be data-driven (YAML)
   - **Effort:** Low - mostly moving numbers

5. **Magic Numbers Scattered**
   - Damage formula, HP regen, etc. hardcoded
   - Should be in game_constants.yaml
   - **Effort:** Low

### 12.3 Medium-Priority Improvements

1. **Limited Loot Scaling**
   - Loot tables don't scale with floor/difficulty
   - Could add multipliers per floor
   - **Effort:** Low

2. **No Combat Effects System**
   - Poison, burning, stun, etc.
   - Would require status effect subsystem
   - **Effort:** Medium

3. **Equipment Durability Not Implemented**
   - Planned but not coded
   - Would extend crafting system
   - **Effort:** Medium

4. **No Ability/Skill System**
   - Character classes defined but abilities not implemented
   - Would require action variant system
   - **Effort:** Medium

### 12.4 Low-Priority Improvements

1. **Perception System Not Used**
   - Field of view calculated but not used for AI
   - Could improve monster awareness
   - **Effort:** Low

2. **Pathfinding Not Optimized**
   - Works fine, but no caching
   - Could cache paths for performance
   - **Effort:** Low

3. **Message Log Not Filtered**
   - No duplicate message suppression
   - Could group repeated actions
   - **Effort:** Low

---

## 13. PREREQUISITES FOR LUA INTEGRATION

### 13.1 What's Already Done

- ActionBase class abstraction (perfect for Lua actions)
- GameContext as safe API (ideal for sandboxed scripts)
- Dependency injection patterns (no global state to deal with)
- YAML-based configuration (Lua can read/modify)
- Test infrastructure (can test Lua code)

### 13.2 What Needs Implementation

**1. Lua Runtime Setup**
```python
# Create mlua context
lua = mlua.Lua::new()

# Register veinborn API
register_veinborn_api(lua)

# Load script
lua.load_from_file('scripts/custom_action.lua')?
```

**2. Bidirectional Type Mapping**
```python
# Python Action → Lua table
action_table = {
    'actor_id': action.actor_id,
    'validate': action.validate,
    'execute': action.execute,
}

# Lua table → Python Action
class LuaAction(Action):
    def __init__(self, lua_table):
        self.lua_table = lua_table
    
    def execute(self, context):
        return self.lua_table['execute'](context)
```

**3. Lua API Surface**
```lua
-- veinborn module (global)
veinborn.context:get_player()
veinborn.context:get_entity(id)
veinborn.context:add_message(msg)

veinborn.entity.EntityType.PLAYER
veinborn.entity.EntityType.MONSTER

veinborn.Action -- base class
veinborn.GameContext -- API surface

veinborn.actions.MoveAction
veinborn.actions.AttackAction
-- etc.
```

**4. Error Handling & Sandboxing**
```python
# Catch Lua errors gracefully
try:
    outcome = lua_action.execute(context)
except mlua.Error as e:
    logger.error(f"Lua error: {e}")
    return ActionOutcome.failure(f"Script error: {e}")

# Restrict Lua access (no file I/O, network, etc.)
-- In Lua environment, remove:
os, io, load, loadstring (replaced by custom sandbox)
```

**5. Hot Reload Support**
```python
# Ability to reload scripts without restarting game
def reload_lua_scripts():
    for script_path in SCRIPT_DIR.glob('*.lua'):
        script = LuaScript.load(script_path)
        script.reload()
```

### 13.3 Recommended Implementation Order

1. **Phase 1: Basic Integration** (1-2 weeks)
   - Set up Lua runtime (mlua)
   - Expose GameContext as API
   - Support custom Actions
   - Document API

2. **Phase 2: Action Registry** (1 week)
   - Allow Lua to register custom actions
   - Test custom action execution
   - Add persistence (load scripts on boot)

3. **Phase 3: Behavior System** (1 week)
   - AI behavior registry
   - Event system with Lua hooks
   - Configuration hotloading

4. **Phase 4: Advanced Features** (2+ weeks)
   - Custom dungeon generators
   - Item/recipe creation
   - Quest system integration

---

## 14. ARCHITECTURAL STRENGTHS (SUMMARY)

1. **Clean Separation of Concerns**
   - GameState (data) ← GameContext (API) ← Actions/Systems
   - UI is completely decoupled
   - Easy to test each layer independently

2. **Action/Outcome Pattern**
   - All state changes go through actions
   - Outcomes are event-ready
   - Perfect for serialization (multiplayer, replay)
   - Natural fit for Lua integration

3. **Factory Pattern for Actions**
   - Open/Closed Principle
   - Easy to extend with custom actions
   - No hardcoded action types

4. **Data-Driven Design**
   - Entities, recipes, loot, spawning all use YAML
   - Easy for designers to modify
   - No code recompilation for balance changes

5. **Type-Safe**
   - Python 3.10+ with type hints
   - Entity types are enums
   - Action types are registered

6. **Testable**
   - Comprehensive fixtures in conftest.py
   - Systems can be tested in isolation
   - GameContext can be mocked
   - YAML data is version-controlled

7. **Well-Documented**
   - Code has docstrings
   - Architecture docs in place
   - Design decisions recorded

---

## 15. ARCHITECTURAL WEAKNESSES (SUMMARY)

1. **Event System Missing**
   - Events are defined in ActionOutcome but not published
   - TurnProcessor has side effects (scoring, vault) not as events

2. **Limited AI Flexibility**
   - Only one AI type implemented
   - Would benefit from behavior registry

3. **Hardcoded Generation**
   - BSP dungeon generation not data-driven
   - Spawning logic has magic numbers

4. **No Reactive System**
   - Systems don't respond to events
   - Hard to add new behaviors without modifying core code

5. **Singleton Pattern Overuse**
   - LootGenerator, HighScoreManager use singletons
   - Could use dependency injection instead

---

## 16. RECOMMENDATIONS FOR IMPROVEMENT

### Immediate (Before Lua)

1. **Extract Event System**
   ```python
   # Create EventBus
   class EventBus:
       def publish(event: dict)
       def subscribe(event_type: str, handler: Callable)
   
   # TurnProcessor publishes events
   bus.publish({'type': 'entity_died', 'entity_id': ...})
   ```

2. **Move Magic Numbers to Data**
   ```yaml
   # game_constants.yaml
   combat:
     damage_variance: 2
   spawning:
     monsters_per_floor: [3, 8]
   ```

3. **Refactor Spawning**
   - Make monster/ore count configurable
   - Move to YAML configuration

### Before Multiplayer (Phase 2)

1. **Complete Event System**
   - All game changes as events
   - Handler registration
   - Event replaying for multiplayer

2. **Network Serialization**
   - Action serialization (already exists)
   - GameState serialization for sync

3. **Permission Model**
   - GameContext checks permissions
   - Multiplayer validation

### With Lua Integration

1. **API Stability**
   - Lock down GameContext interface
   - Version compatibility

2. **Sandbox Security**
   - Restrict Lua capabilities
   - Timeout protection

3. **Hot Reload**
   - Load/reload scripts without restart
   - Error recovery

---

## 17. CONCLUSION

**Veinborn's architecture is well-designed and production-ready for MVP.** It has:

- Clean separation of concerns (State → API → Logic)
- Extensible action system ready for Lua
- Data-driven design where it matters
- Minimal coupling between systems
- Comprehensive test infrastructure
- Type-safe codebase

**For Lua integration:**
- **Immediate:** ActionFactory can be extended with Lua actions
- **Short-term:** Set up Lua runtime + API mapping
- **Medium-term:** Behavior system + event hooks
- **Long-term:** Full procedural generation support

**Estimated effort for basic Lua support:** 2-3 weeks  
**Estimated effort for full Lua platform:** 6-8 weeks

The foundations are solid. The game is ready for scripting.

