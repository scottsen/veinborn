# Veinborn Layout System - Quick Start

## Testing the New Layout System

### 1. Default Layout (3-Column) ⭐

**Veinborn now uses the 3-column layout by default!**

Just launch Veinborn:
```bash
veinborn
```

You should see:
- **Map on the left** (60% width)
- **Player stats/monsters in the middle** (20% width)
- **Inventory on the right** (20% width) - separate from stats!

### 2. Switch to Other Layouts

Try other built-in layouts by editing `~/.veinbornrc`:

**Classic stacked** (original layout):
```ini
[ui]
layout = default
```

**Compact** (more map space):
```ini
[ui]
layout = compact
```

**Back to 3-column** (the default):
```ini
[ui]
layout = grid-3col
```

### 3. Use Environment Variable (Quick Testing)

No config file needed:

```bash
VEINBORN_UI_LAYOUT=grid-3col ./veinborn
VEINBORN_UI_LAYOUT=compact ./veinborn
VEINBORN_UI_LAYOUT=default ./veinborn
```

### 4. Create Your Own Layout

Copy a built-in layout:
```bash
mkdir -p ~/.config/veinborn
cp data/ui/layouts/grid-3col.tcss ~/.config/veinborn/my-layout.tcss
```

Edit `~/.config/veinborn/my-layout.tcss` to customize.

Then use it:
```ini
[ui]
layout = my-layout
```

## Available Layouts

| Layout      | Description                                  | Default |
|-------------|----------------------------------------------|---------|
| `grid-3col` | Three columns (map, stats, inventory)        | ⭐ YES  |
| `default`   | Original sidebar (stats + inventory stacked) |         |
| `compact`   | Narrow sidebars for maximum map space        |         |

## Full Documentation

See `data/ui/layouts/README.md` for:
- Complete CSS reference
- Creating custom layouts
- Textual CSS properties
- Troubleshooting

## Quick CSS Reference

Common properties to customize:

```css
/* Widget sizing */
width: 25;          /* Fixed width (characters) */
height: 10;         /* Fixed height (lines) */
width: 50%;         /* Percentage of parent */
height: 60%;        /* Percentage of parent */

/* Grid layout */
grid-size: 3;       /* 3 columns */
grid-rows: 1 1fr 10;  /* Row heights */
column-span: 2;     /* Widget spans 2 columns */

/* Positioning */
dock: right;        /* Dock to edge */
padding: 1;         /* Internal spacing */
border: solid $primary;  /* Border style */
```

## Troubleshooting

**Layout not loading?**
- Check `~/.veinbornrc` syntax (INI format)
- Verify layout file exists: `ls data/ui/layouts/`
- Check logs: look for "Loaded layout:" message

**Widgets overlapping?**
- Grid layouts: check `grid-size` matches column spans
- Dock layouts: ensure fixed widths/heights set

**Want to reset to defaults?**
Remove layout line from `~/.veinbornrc` or set:
```ini
[ui]
layout = grid-3col
```
