# Data-Driven Rendering: Proof of Concept

**Goal**: Make entity rendering automatic by storing display metadata in Entity.stats

## Current State (Manual, Error-Prone)

```python
# map_widget.py - Every entity type needs custom code
def _render_cell(self, world_x, world_y, player, game_map):
    # Player
    if world_x == player.x and world_y == player.y:
        return Segment("@", Style(color="bright_yellow", bold=True))

    # Monsters
    entity = self._get_entity_at(world_x, world_y, EntityType.MONSTER)
    if entity:
        char = entity.name[0].lower()  # Hardcoded logic
        return Segment(char, Style(color="bright_red", bold=True))

    # Ore veins
    entity = self._get_entity_at(world_x, world_y, EntityType.ORE_VEIN)
    if entity:
        return Segment('*', self._get_ore_vein_style(entity))  # Hardcoded symbol

    # ❌ EASY TO FORGET NEW TYPES (like Forge!)
```

**Problem**: Adding `EntityType.FORGE` doesn't automatically add rendering

## Target State (Data-Driven, Automatic)

```python
# map_widget.py - Single code path for all entities
def _render_cell(self, world_x, world_y, player, game_map):
    # Player
    if world_x == player.x and world_y == player.y:
        return Segment("@", Style(color="bright_yellow", bold=True))

    # All other entities - automatic!
    entity = self._get_any_entity_at(world_x, world_y)
    if entity:
        symbol = entity.display_symbol
        color = entity.display_color
        return Segment(symbol, Style(color=color, bold=True))

    # Terrain...
```

**Benefit**: New entity types work automatically if they have display metadata

## Implementation Steps

### Step 1: Add Display Properties to Entity Base Class

```python
# src/core/base/entity.py

@dataclass
class Entity:
    # ... existing fields ...

    @property
    def display_symbol(self) -> str:
        """Get rendering symbol for this entity."""
        # Priority: explicit stat > type-based default > fallback
        if 'display_symbol' in self.stats:
            return self.stats['display_symbol']

        # Type-based defaults (during migration)
        if self.entity_type == EntityType.MONSTER:
            return self.name[0].lower()  # First letter
        elif self.entity_type == EntityType.ORE_VEIN:
            return '*'
        elif self.entity_type == EntityType.FORGE:
            return '&'
        elif self.entity_type == EntityType.ITEM:
            return ')'

        return '?'  # Fallback

    @property
    def display_color(self) -> str:
        """Get rendering color for this entity."""
        if 'display_color' in self.stats:
            return self.stats['display_color']

        # Type-based defaults
        if self.entity_type == EntityType.MONSTER:
            return 'bright_red'
        elif self.entity_type == EntityType.ORE_VEIN:
            # Check ore type for specific color
            ore_type = self.get_stat('ore_type', 'copper')
            return {'copper': 'yellow', 'iron': 'bright_white',
                    'mithril': 'bright_cyan', 'adamantite': 'bright_magenta'}.get(ore_type, 'white')
        elif self.entity_type == EntityType.FORGE:
            forge_type = self.get_stat('forge_type', 'basic_forge')
            if 'master' in forge_type:
                return 'yellow'
            elif 'iron' in forge_type:
                return 'bright_white'
            return 'yellow'

        return 'white'  # Fallback
```

### Step 2: Load Display Metadata from YAML

```python
# src/core/entity_loader.py

def load_forge_config(forge_type: str) -> dict:
    """Load forge configuration from YAML."""
    config = ConfigLoader.get_config()
    forge_data = config.forge_types.get(forge_type, {})

    return {
        'forge_type': forge_type,
        'recipes': forge_data.get('recipes', []),
        'description': forge_data.get('description', ''),
        # NEW: Load display metadata
        'display_symbol': forge_data.get('symbol', '&'),
        'display_color': forge_data.get('color', 'yellow'),
    }

def create_forge(forge_type: str, x: int, y: int) -> Forge:
    """Create a forge with display metadata from config."""
    config = load_forge_config(forge_type)

    forge = Forge(forge_type=forge_type, x=x, y=y)

    # Store display metadata in stats
    forge.set_stat('display_symbol', config['display_symbol'])
    forge.set_stat('display_color', config['display_color'])
    forge.set_stat('recipes', config['recipes'])
    forge.set_stat('description', config['description'])

    return forge
```

### Step 3: Simplify MapWidget

```python
# src/ui/textual/widgets/map_widget.py

def _render_cell(self, world_x, world_y, player, game_map):
    """Render a single map cell."""
    # Out of bounds
    if world_x >= game_map.width:
        return Segment(" ")

    # Player position
    if world_x == player.x and world_y == player.y:
        return Segment("@", Style(color="bright_yellow", bold=True))

    # All entities (single code path!)
    entity = self._get_any_entity_at(world_x, world_y)
    if entity:
        symbol = entity.display_symbol
        color = entity.display_color
        return Segment(symbol, Style(color=color, bold=True))

    # Render terrain
    if 0 <= world_x < game_map.width and 0 <= world_y < game_map.height:
        tile = game_map.tiles[world_x][world_y]
        char = self.MAP_CHARS.get(tile.tile_type, '?')
        style = self._get_terrain_style(tile.tile_type)
        return Segment(char, style)

    return Segment(" ")

def _get_any_entity_at(self, x, y):
    """Find any entity at position (priority order)."""
    # Check in priority order: Monster > Forge > Ore Vein > Item
    for entity_type in [EntityType.MONSTER, EntityType.FORGE, EntityType.ORE_VEIN, EntityType.ITEM]:
        entity = self._get_entity_at(x, y, entity_type)
        if entity:
            return entity
    return None
```

## Migration Path

### Phase 1: Add Properties (No Breaking Changes)
- Add `display_symbol` and `display_color` properties to Entity
- Properties check stats first, fall back to current hardcoded logic
- No behavior changes yet

### Phase 2: Start Loading from YAML
- Update EntityLoader to store display metadata in stats
- New entities get metadata, old ones use fallbacks
- Gradual migration

### Phase 3: Simplify Rendering
- Update MapWidget to use entity properties
- Remove type-specific rendering methods
- Keep fallbacks in Entity properties for safety

### Phase 4: Full Data-Driven (Future)
- All entities load display metadata from YAML
- Remove fallback logic from Entity properties
- YAML is single source of truth

## Benefits

1. **Bug Prevention**: New entity types automatically work
2. **Modding-Friendly**: Change symbols via data files, no code changes
3. **Single Source of Truth**: YAML files define appearance
4. **Less Code**: One rendering path instead of N type-specific paths
5. **Extensibility**: Easy to add display_bold, display_background, etc.

## Testing Strategy

```python
def test_entity_has_display_metadata():
    """All entities must have display_symbol and display_color."""
    entity = create_any_entity()

    assert hasattr(entity, 'display_symbol')
    assert hasattr(entity, 'display_color')
    assert entity.display_symbol != '?', "Entity missing display symbol"
    assert entity.display_color != 'white', "Entity missing display color"
```

## Next Steps

1. Add `display_symbol` and `display_color` properties to Entity ✅ (Safe, non-breaking)
2. Write test for new properties
3. Update one entity type (e.g., Forge) to load from YAML
4. Update MapWidget to use properties for that type
5. Gradually migrate other entity types
6. Remove hardcoded rendering logic

## Files to Change

1. `src/core/base/entity.py` - Add display properties
2. `src/core/entity_loader.py` - Load display metadata from YAML
3. `src/core/spawning/entity_spawner.py` - Use EntityLoader for display metadata
4. `src/ui/textual/widgets/map_widget.py` - Simplify to single rendering path
5. `tests/unit/test_entity.py` - Test display properties
6. `tests/unit/ui/test_entity_rendering.py` - Test all types render correctly
