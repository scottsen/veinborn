# Veinborn UI Layouts

This directory contains Textual CSS (.tcss) layout files for customizing the Veinborn UI.

## Available Layouts

### `default.tcss` (Classic Single Sidebar) ⭐ **DEFAULT**
Single right sidebar containing everything:
- Player stats at top
- Inventory in middle
- Monsters below
- Controls at bottom
- Map fills left side

Best for traditional roguelike feel.

### `split-sidebars.tcss` (Inventory Left, Stats Right) 🆕
Three-panel layout with inventory separated:
- **Inventory on LEFT** (dedicated panel)
- **Player stats/monsters on RIGHT**
- **Map in the MIDDLE** (fills remaining space)

Best for users who want inventory prominently displayed.

### `compact.tcss` (Maximum Map Space)
Minimalist layout for small terminals:
- Narrow sidebars (20 width instead of 25)
- Smaller message log (6 lines instead of 10)
- More screen space for the map

## How to Use

### 1. Choose a layout in your config file

Edit `~/.veinbornrc`:

```ini
[ui]
layout = split-sidebars
```

Options: `default`, `split-sidebars`, `compact`, or custom filename (without .tcss)

### 2. Or use environment variable

```bash
export VEINBORN_UI_LAYOUT=split-sidebars
veinborn
```

### 3. Or create your own layout

Copy an existing layout:
```bash
cp data/ui/layouts/default.tcss ~/.config/veinborn/my-layout.tcss
```

Edit it, then use:
```ini
[ui]
layout = my-layout
```

## Creating Custom Layouts

Veinborn uses **Textual CSS** (tcss), which is similar to web CSS but designed for terminals.

### Available Widgets

- `StatusBar` - Top status line (HP, turn, position)
- `MapWidget` - The dungeon map
- `Sidebar` - Player stats, monsters, controls
- `InventoryWidget` - Inventory list
- `MessageLog` - Bottom message log
- `ChatInput` - Chat overlay (multiplayer)

### Common Properties

```css
/* Positioning */
dock: top | bottom | left | right;  /* Dock to screen edge */
layout: horizontal | vertical | grid;  /* Container layout */

/* Sizing */
width: 25;              /* Fixed width (cells) */
height: 10;             /* Fixed height (lines) */
width: 50%;             /* Percentage of parent */
height: 1fr;            /* Fractional unit (fills space) */

/* Grid layout (for complex layouts) */
grid-size: 3;           /* Number of columns */
grid-rows: 1 1fr 10;    /* Row heights */
column-span: 2;         /* Widget spans 2 columns */
row-span: 1;            /* Widget spans 1 row */

/* Visual */
background: $panel;     /* Background color */
border: solid $primary; /* Border style */
padding: 1;             /* Internal padding */
```

### Example: Two-Column Layout

```css
/* data/ui/layouts/two-col.tcss */

Screen {
    layout: grid;
    grid-size: 2;  /* 2 columns */
}

MapWidget {
    column-span: 1;  /* Left column */
}

Sidebar {
    column-span: 1;  /* Right column */
    overflow-y: auto;  /* Scrollable if content overflows */
}
```

## Layout Search Path

Veinborn looks for layouts in this order:

1. `~/.config/veinborn/<layout>.tcss` (user override)
2. `data/ui/layouts/<layout>.tcss` (built-in)

This means you can override built-in layouts by creating a file with the same name in your config directory.

## Textual CSS Documentation

For full CSS reference, see:
https://textual.textualize.io/guide/CSS/

## Tips

- **Test layouts quickly**: Edit .tcss files and restart Veinborn
- **Copy before modifying**: Always work from a copy of a built-in layout
- **Use percentage heights**: `60%` and `40%` instead of fixed heights adapt to terminal size
- **Check terminal size**: Layouts optimized for 80x24 may look different on 120x40

## Troubleshooting

**Layout not loading?**
- Check filename matches config (without .tcss extension)
- Verify file exists in `data/ui/layouts/` or `~/.config/veinborn/`
- Look for syntax errors in .tcss file

**Widgets overlapping?**
- Check `column-span` and `row-span` don't exceed `grid-size`
- Ensure docked widgets have explicit widths/heights

**Want to contribute a layout?**
Open a PR with your .tcss file and a screenshot!
