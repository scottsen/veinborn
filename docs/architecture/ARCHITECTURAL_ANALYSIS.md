# Brogue Bot Architecture Analysis

**Date**: 2025-10-26
**Session**: eternal-hammer-1026
**Focus**: Bot testing revealed fundamental architectural issues

---

## Executive Summary

Bot testing revealed 662k+ validation failures and infinite loops attacking loot items. Root cause analysis shows **architectural design issues** rather than simple bugs:

1. **Items treated as "alive" entities** → Trigger bump combat instead of pickup
2. **No perception/visibility API** → Bot accesses raw game state (cheating)
3. **Pathfinding ignores entity occupation** → Routes through occupied tiles
4. **Missing proper game state API** → No clean interface for bot/AI needs

---

## Root Cause: Item Entity Design

### The Bug

**Location**: `src/core/base/entity.py:62`, `src/core/loot.py:235-247`

```python
# Entity base class
@dataclass
class Entity:
    is_alive: bool = True  # ← Default is True!

# Item creation
entity = Entity(
    entity_type=EntityType.ITEM,
    hp=0,
    max_hp=0,
    # is_alive NOT explicitly set → defaults to True
)
```

**Impact**: Items are created with `is_alive=True`, causing:
- Bump combat triggers on items (attacks for 0 damage)
- Bot pathfinding routes to items
- Player can't walk over loot naturally
- Infinite loops attacking immovable items

### Move Validation Logic

**Location**: `src/core/actions/move_action.py:91`

```python
target = context.get_entity_at(new_x, new_y)
if target and target.is_alive:  # ← Items pass this check!
    # Redirect to attack
    return attack_action()
```

**Expected**: Only attack monsters/NPCs
**Actual**: Attacks any entity with `is_alive=True` (including items)

---

## Architecture Problem: No Perception API

### Current Bot Access (Cheating)

```python
# Bot directly accesses internal state
def find_monsters(self, game: Game) -> List[Entity]:
    return [
        entity for entity in game.state.entities.values()  # ← Sees ALL entities
        if isinstance(entity, Monster) and entity.is_alive
    ]
```

**Problems**:
- Bot sees entire map (no fog of war)
- Bot knows exact monster positions (wallhack)
- Bot knows ALL entity locations (omniscience)
- No distinction between "seen" vs "hidden"

### What Bot Should See

A real player can only see:
- Entities within line of sight
- Explored map tiles
- Items on ground in visible areas
- Recent messages/feedback

### What's Missing

```python
# Needed APIs:
game.get_visible_entities(viewer_pos, radius) → List[Entity]
game.get_visible_monsters(player) → List[Monster]
game.get_visible_items(player) → List[Item]
game.get_explored_tiles() → Set[Tuple[int, int]]
game.is_tile_visible(pos) → bool
```

---

## Architecture Problem: Pathfinding Ignores Entities

### Current Implementation

**Location**: `src/core/pathfinding.py:266-274`

```python
def _is_valid_neighbor(game_map, neighbor_pos, closed_set):
    if not game_map.in_bounds(*neighbor_pos):
        return False
    if not game_map.is_walkable(*neighbor_pos):  # ← Only checks tile type!
        return False
    # Missing: Check if entity occupies tile
    return True
```

**Problem**: Pathfinding only checks **tile walkability** (floor vs wall), not **entity occupation**.

### Why This Causes Issues

1. Player paths to ore vein at (10, 10)
2. Monster drops loot at (9, 10) (adjacent)
3. Pathfinding says (9, 10) is "walkable" (floor tile)
4. Bot tries to move to (9, 10)
5. Bump combat with item → attacks loot
6. Retries same path → infinite loop

### Entity-Aware Pathfinding Options

**Option 1**: Make pathfinding entity-aware
```python
def _is_valid_neighbor(game_map, neighbor_pos, closed_set, context):
    # ... existing checks ...

    # Check if entity blocks this tile
    entity = context.get_entity_at(*neighbor_pos)
    if entity and entity.blocks_movement():
        return False
    return True
```

**Option 2**: Separate entity from walkability
```python
# Pathfinding finds routes ignoring entities
path = find_path(map, start, goal)

# Bot validates each step for entity occupation
for step in path:
    if context.get_entity_at(step):
        # Re-path or handle obstruction
```

**Option 3**: Path around entities (current approach - broken)
```python
# Current: Path to adjacent position for combat
adjacent_goal = find_closest_adjacent_position(map, target, source)
# Problem: adjacent might have loot, causing attacks
```

---

## Bot "Cheating" Analysis

### Internal State Access

| What Bot Accesses | Should See? | Current Access | Notes |
|-------------------|-------------|----------------|-------|
| `game.state.entities` | ❌ | ✅ Full dict | Omniscient - sees all monsters/items |
| `game.state.dungeon_map` | ⚠️ | ✅ Full map | Should only see explored tiles |
| `game.state.player` | ✅ | ✅ | Legit - knows own stats |
| `game.state.messages` | ✅ | ✅ | Legit - player sees these |
| `entity.content_id` | ❌ | ✅ | Meta-knowledge of YAML IDs |
| Monster stats from YAML | ❌ | ✅ | Perfect information (cheating) |

### Legitimate vs Cheating

**Legitimate Bot Knowledge**:
- Player HP/stats
- Visible map tiles (if fog of war existed)
- Entities within line of sight
- Game messages
- Items in inventory

**Current Cheating**:
- Exact positions of ALL monsters (even through walls)
- Exact stats of monsters (reads YAML directly)
- Entire dungeon map layout
- All ore vein locations and properties
- Item locations before seeing them

---

## Design Recommendations

### Priority 1: Fix Item `is_alive` Bug

**Location**: `src/core/loot.py:235-247`

```python
entity = Entity(
    entity_type=EntityType.ITEM,
    name=item_def.get('display_name', ...),
    hp=0,
    max_hp=0,
    is_alive=False,  # ← ADD THIS
)
```

**Impact**: Immediate fix for infinite attack loops

### Priority 2: Add Perception API

**New File**: `src/core/perception.py`

```python
class PerceptionSystem:
    """Manages what entities can see/know about the game world."""

    def get_visible_entities(
        self,
        game: Game,
        observer: Entity,
        radius: float = 10.0,
        line_of_sight: bool = True
    ) -> List[Entity]:
        """Get entities visible to observer."""
        visible = []
        for entity in game.state.entities.values():
            if entity == observer:
                continue

            distance = observer.distance_to(entity)
            if distance > radius:
                continue

            if line_of_sight and not self._has_line_of_sight(game, observer, entity):
                continue

            visible.append(entity)
        return visible

    def get_visible_monsters(self, game: Game, observer: Entity) -> List[Monster]:
        """Get monsters visible to observer."""
        from core.entities import Monster
        return [
            e for e in self.get_visible_entities(game, observer)
            if isinstance(e, Monster) and e.is_alive
        ]

    def get_visible_items(self, game: Game, observer: Entity) -> List[Entity]:
        """Get items visible to observer."""
        return [
            e for e in self.get_visible_entities(game, observer)
            if e.entity_type == EntityType.ITEM
        ]
```

**Usage in Bot**:
```python
# Before (cheating)
monsters = [e for e in game.state.entities.values() if isinstance(e, Monster)]

# After (legitimate)
perception = game.perception  # or PerceptionSystem(game)
monsters = perception.get_visible_monsters(game, game.state.player)
```

### Priority 3: Entity Blocking Logic

**Add to Entity**:
```python
@dataclass
class Entity:
    # ... existing fields ...

    def blocks_movement(self) -> bool:
        """Does this entity block movement?"""
        if self.entity_type == EntityType.MONSTER:
            return self.is_alive
        if self.entity_type == EntityType.PLAYER:
            return self.is_alive
        if self.entity_type == EntityType.ITEM:
            return False  # Items don't block movement
        if self.entity_type == EntityType.ORE_VEIN:
            return True  # Ore blocks movement
        return False
```

**Update MoveAction**:
```python
target = context.get_entity_at(new_x, new_y)
if target and target.blocks_movement():  # ← Changed from is_alive
    # Bump into blocking entity
    if target.entity_type in [EntityType.MONSTER, EntityType.PLAYER]:
        return attack_action()  # ← Only attack living things
    else:
        return failure("Path blocked")  # ← Can't attack ore veins
```

### Priority 4: Game State API

**Add to Game class**:
```python
class Game:
    def __init__(self):
        self.perception = PerceptionSystem()

    # Clean API for AI/bots
    def get_visible_monsters(self, observer: Entity = None) -> List[Monster]:
        observer = observer or self.state.player
        return self.perception.get_visible_monsters(self, observer)

    def get_visible_items(self, observer: Entity = None) -> List[Entity]:
        observer = observer or self.state.player
        return self.perception.get_visible_items(self, observer)

    def get_nearby_ore(self, observer: Entity = None, radius: float = 5.0) -> List[OreVein]:
        observer = observer or self.state.player
        entities = self.perception.get_visible_entities(self, observer, radius)
        return [e for e in entities if isinstance(e, OreVein)]
```

---

## Bot Design Patterns

### Pattern 1: Entity Type Filtering

**Current (scattered)**:
```python
# In bot code
monsters = [e for e in game.state.entities.values() if isinstance(e, Monster)]
ore_veins = [e for e in game.state.entities.values() if isinstance(e, OreVein)]
```

**Recommended (centralized)**:
```python
# In Game API
monsters = game.get_visible_monsters()
ore_veins = game.get_nearby_ore(radius=10.0)
```

### Pattern 2: Pathfinding Goals

**Current Issues**:
- Pathfinding to monsters uses `path_adjacent=True` (correct)
- Pathfinding to ore uses `path_adjacent=False` (correct)
- But doesn't handle item/entity blocking

**Recommended**:
```python
class PathfindingGoal:
    """Defines pathfinding behavior for different target types."""

    @staticmethod
    def to_monster(game, player_pos, monster):
        """Path to attack a monster."""
        # Find closest adjacent walkable position
        goal = find_closest_adjacent_position(
            game.state.dungeon_map,
            (monster.x, monster.y),
            player_pos,
            exclude_occupied=True  # ← NEW: skip entity-occupied tiles
        )
        return goal

    @staticmethod
    def to_ore(game, player_pos, ore):
        """Path to mine ore."""
        # Path directly to ore position
        return (ore.x, ore.y)

    @staticmethod
    def to_item(game, player_pos, item):
        """Path to pickup item."""
        # Path directly to item (items don't block)
        return (item.x, item.y)
```

---

## Testing Implications

### What Tests Revealed

1. **Bot gets stuck attacking items** → Design flaw, not code bug
2. **662k validation failures** → Pathfinding doesn't account for entities
3. **100k turn limit hit** → Infinite loops in decision making
4. **0 monsters killed** → Bot can't reach combat due to item blocking

### What Tests Should Verify

- ✅ Pathfinding around entities (not just walls)
- ✅ Items don't block movement
- ✅ Bump combat only on living creatures
- ✅ Bot uses perception API (not raw state)
- ✅ No infinite action loops

---

## Implementation Roadmap

### Phase 1: Critical Fixes (1 hour)
1. Set `is_alive=False` for items in loot creation
2. Update `blocks_movement()` logic in MoveAction
3. Add basic entity type checks to prevent attacking items

### Phase 2: Perception API (2-3 hours)
1. Create `PerceptionSystem` class
2. Add visibility/line-of-sight methods
3. Add fog of war to map (explored vs unexplored)
4. Update bot to use perception API

### Phase 3: Pathfinding Improvements (2-3 hours)
1. Add `exclude_occupied` parameter to pathfinding
2. Create `PathfindingGoal` patterns
3. Add entity-aware neighbor validation
4. Test with complex entity layouts

### Phase 4: Clean Game API (1-2 hours)
1. Add convenience methods to Game class
2. Deprecate direct `game.state.entities` access
3. Document proper API usage
4. Update all AI systems to use new API

---

## Lessons Learned

### Design Principles Violated

1. **Separation of Concerns**: Items use same lifecycle as monsters (`is_alive`)
2. **Information Hiding**: Bot accesses raw game state instead of API
3. **Single Responsibility**: Pathfinding should focus on terrain, not entities
4. **Dependency Inversion**: Bot depends on concrete GameState instead of abstraction

### Better Design

```
┌─────────────┐
│ Bot / AI    │
└──────┬──────┘
       │ uses
       ↓
┌─────────────┐
│ Game API    │ ← Clean interface
└──────┬──────┘
       │ uses
       ↓
┌─────────────┐
│ Perception  │ ← Visibility/knowledge
└──────┬──────┘
       │ queries
       ↓
┌─────────────┐
│ GameState   │ ← Raw data
└─────────────┘
```

---

## Conclusion

**Bot testing was successful** - not because it passed, but because it revealed fundamental architectural issues:

1. **Semantic Modeling**: Items shouldn't be "alive"
2. **API Design**: Need clean interfaces for AI access
3. **Separation**: Pathfinding ≠ Entity navigation
4. **Perception**: What you know ≠ What exists

**Next Steps**:
1. Fix immediate `is_alive` bug (5 minutes)
2. Design perception API (discussion + spec)
3. Implement entity-aware pathfinding
4. Create comprehensive bot testing suite

**Files to Modify**:
- `src/core/loot.py` - Set items to `is_alive=False`
- `src/core/base/entity.py` - Add `blocks_movement()` method
- `src/core/actions/move_action.py` - Check `blocks_movement()` not `is_alive`
- `src/core/perception.py` - NEW: Visibility system
- `src/core/game.py` - Add perception API methods
- `tests/fuzz/brogue_bot.py` - Use new APIs

---

**Generated**: 2025-10-26
**Session**: eternal-hammer-1026
**Purpose**: Architectural analysis from bot testing failures
