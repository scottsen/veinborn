# UI Debugging Guide

## Quick Debug

### In-Game Debug Key

Press **Shift+D** while playing to dump UI state to logs.

You'll see a message: "UI debug info dumped to logs/veinborn.log"

### View the Debug Output

```bash
# In another terminal
tail -f logs/veinborn.log

# Or after playing
less logs/veinborn.log
```

## What Gets Logged

When you press Shift+D, it logs:

1. **CSS_PATH**: Which layout file is being used
2. **Widget visibility**: Whether each widget is displayed
3. **Widget styles**: CSS properties applied to each widget
4. **Game state**: Whether widgets have access to game data
5. **Inventory content**: What the inventory widget is trying to render

## Debug Output Example

```
INFO: === UI DEBUG DUMP ===
INFO: CSS_PATH: /home/scottsen/src/projects/veinborn/data/ui/layouts/default.tcss
INFO: Sidebar: visible=True, styles=...
INFO: InventoryWidget: visible=True, styles=...
INFO:   InventoryWidget has game_state: True
INFO:   Player inventory items: 1
INFO: MapWidget: visible=True, styles=...
INFO: MessageLog: visible=True, styles=...
INFO: Manual render_content() result:
=== INVENTORY ===
(1/20 items)

 1. Copper Ore
    (ore)
```

## Common Issues to Check

### InventoryWidget shows but is black

Look for:
```
INFO: InventoryWidget: visible=True
INFO: InventoryWidget has game_state: False  ← Problem!
```

**Fix**: Widget doesn't have game state - initialization issue

### CSS not loading

Look for:
```
INFO: CSS_PATH: NOT SET  ← Problem!
```

**Fix**: Layout file not found - check file path

### Widget has wrong size/position

Look for:
```
INFO: InventoryWidget: styles=height: 0  ← Problem!
```

**Fix**: CSS not applied - check layout file syntax

## Enable More Logging

Edit `~/.veinbornrc`:

```ini
[debug]
log_level = DEBUG
```

Then view logs:
```bash
tail -f logs/veinborn.log
```

You'll see:
- Every widget render call
- CSS loading
- Content updates
- Layout calculations

## Test Commands

```bash
# Test layout loading
python -c "from src.ui.textual.app import VeinbornApp; app = VeinbornApp(); print('CSS:', app.CSS_PATH)"

# Test widget rendering
python -c "
from src.ui.textual.widgets.inventory_widget import InventoryWidget
from src.core.game import Game
game = Game()
game.start_new_game()
widget = InventoryWidget(game_state=game.state)
print(widget.render_content())
"
```

## Reporting Issues

When reporting UI bugs, include:

1. Screenshot showing the problem
2. Output from pressing Shift+D
3. Relevant lines from `logs/veinborn.log`
4. Your layout config from `~/.veinbornrc`

Example:
```
The inventory widget is black.

Debug output:
INFO: InventoryWidget: visible=True
INFO: InventoryWidget has game_state: True
INFO: Player inventory items: 3
INFO: Manual render_content() result: === INVENTORY === ...

Layout: default (from ~/.veinbornrc)
```
