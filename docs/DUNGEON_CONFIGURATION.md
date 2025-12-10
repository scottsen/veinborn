# Dungeon Generation Configuration Guide

This guide explains how to customize dungeon layouts in Veinborn using the `data/balance/dungeon_generation.yaml` configuration file.

## Overview

Veinborn uses a Binary Space Partitioning (BSP) algorithm to generate dungeons. The configuration file allows you to control:

- **BSP Algorithm**: How the dungeon space is divided into regions
- **Room Parameters**: Size and placement of rooms
- **Corridor Generation**: How rooms are connected
- **Floor-Specific Variations**: Different settings for different dungeon depths
- **Presets**: Pre-configured dungeon types for quick experimentation

## Configuration File Location

```
data/balance/dungeon_generation.yaml
```

## BSP Algorithm Explained

The dungeon generation works as follows:

1. **Start** with the full map rectangle (e.g., 80×24 tiles)
2. **Split** the space recursively into smaller regions
3. **Create** a room in each final region (leaf node)
4. **Connect** rooms with L-shaped corridors

### Key BSP Parameters

**`bsp.min_split_size`** (default: 6)
- Controls when to stop splitting regions
- Larger values = fewer, larger rooms
- Smaller values = more, smaller rooms

**`bsp.aspect_ratio_threshold`** (default: 1.25)
- When a region becomes elongated (1.25× longer in one direction), force split in that direction
- Prevents overly narrow or wide regions

**`bsp.split_ratio`** (default: 0.33 - 0.67)
- Controls where to place the split within a region
- Range of 33%-67% creates variety while avoiding extreme splits

## Room Parameters

**`rooms.min_size`** (default: 4)
- Minimum dimensions for rooms (in tiles)
- Rooms will be at least this size in both width and height

**`rooms.padding`** (default: 1)
- Space between room edges and BSP region boundaries
- Creates natural spacing between adjacent rooms

## Corridor Parameters

**`corridors.style`** (default: "l_shaped")
- Currently only L-shaped corridors are implemented
- Future: straight, winding, maze-like corridors

**`corridors.direction_probability`** (default: 0.5)
- For L-shaped corridors: probability of horizontal-first vs vertical-first
- 0.5 = 50/50 chance, creates layout variety

## Customizing Dungeons

### Example 1: Small, Cramped Dungeons

For tight, claustrophobic dungeons with many small rooms:

```yaml
bsp:
  min_split_size: 5  # More splits allowed

rooms:
  min_size: 3  # Smaller rooms

corridors:
  direction_probability: 0.5
```

### Example 2: Large, Open Dungeons

For spacious dungeons with fewer, larger rooms:

```yaml
bsp:
  min_split_size: 10  # Fewer splits

rooms:
  min_size: 6  # Larger minimum size
  padding: 2  # More spacing

corridors:
  direction_probability: 0.5
```

### Example 3: Maze-like Dungeons

For complex, interconnected layouts:

```yaml
bsp:
  min_split_size: 4  # Maximum splits
  aspect_ratio_threshold: 1.1  # Split more freely

rooms:
  min_size: 3  # Small rooms

corridors:
  direction_probability: 0.5
```

## Using Presets

The configuration file includes several presets:

- **standard**: Current default balanced layout
- **small_cramped**: Many small rooms, tight spaces
- **large_open**: Fewer large rooms, open combat
- **maze**: Maximum room density, complex layout

To use a preset, copy its values to the main configuration sections.

## Floor-Specific Overrides

You can customize dungeons for specific floor depths:

```yaml
floor_overrides:
  floor_1:
    rooms:
      min_size: 3  # Smaller rooms on floor 1
    bsp:
      min_split_size: 5

  floor_10:
    rooms:
      min_size: 5  # Larger rooms on deeper floors
    bsp:
      min_split_size: 8
```

## Testing Your Configuration

After making changes:

1. **Restart the game** - Configuration is loaded at startup
2. **Generate new maps** - Descend stairs or start new game
3. **Observe differences** - Notice room sizes, layout density, spacing

## Technical Details

### Implementation

- **Configuration Loading**: `src/core/config/config_loader.py`
- **Dungeon Generation**: `src/core/world.py`
- **Fallback Values**: If config loading fails, hardcoded defaults ensure the game works

### Backward Compatibility

All default values match the original hardcoded values, ensuring:
- Existing saves work correctly
- Default gameplay is unchanged
- Configuration is purely additive

### Performance

Configuration is loaded once at startup (singleton pattern). No performance impact during dungeon generation.

## Troubleshooting

**Problem**: Changes don't appear in-game
- **Solution**: Restart the game - config is loaded at startup

**Problem**: Game crashes after config change
- **Solution**: Check YAML syntax with `python -c "import yaml; yaml.safe_load(open('data/balance/dungeon_generation.yaml'))"`

**Problem**: Dungeons look broken
- **Solution**: Check that `min_split_size` is reasonable (4-10), and `min_size` fits within rooms

## Related Configuration Files

- `spawning.yaml` - Special room types and entity spawning
- `monster_spawns.yaml` - Monster counts and types per floor
- `ore_veins.yaml` - Ore vein distribution

## Examples in Action

### Default Configuration
- Balanced mix of room sizes
- Good variety in layouts
- Suitable for all play styles

### Small Cramped (min_split_size: 5, min_size: 3)
- Many small rooms
- Challenging navigation
- Favors ranged combat and tactics

### Large Open (min_split_size: 10, min_size: 6)
- Fewer large rooms
- Open combat spaces
- Favors melee combat

### Maze (min_split_size: 4, min_size: 3)
- Maximum room count
- Complex interconnections
- Challenging exploration

## Future Enhancements

Potential additions to the system:
- Multiple corridor styles (straight, winding, maze)
- Room shape variations (circular, irregular)
- Special room placement rules
- Themed dungeon types (catacombs, caverns, fortress)

---

**Version**: 1.0.0
**Last Updated**: 2025-11-06
**Related PR**: Dungeon Generation Configuration
**Author**: Veinborn Development Team
