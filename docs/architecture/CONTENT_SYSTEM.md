# Veinborn Content System: Data-Driven Design & Scripting

**Document Type:** Content Architecture
**Audience:** Content Designers, Gameplay Programmers
**Status:** Active
**Last Updated:** 2025-10-23

---

## Overview

Veinborn's content system enables designers to create game content (monsters, abilities, quests) without programming. This document covers:

1. **YAML-based content** (Phase 1 - Now)
2. **Expression language** for simple logic
3. **Scripting** (Lua/Python) for complex behavior (Phase 2+)

**Philosophy:** Start simple (YAML), add complexity only when needed.

---

## 1. YAML Content System (Phase 1)

### Monster Definitions

```yaml
# data/monsters/goblin.yaml
id: goblin
name: Goblin
description: A small, green-skinned creature with sharp teeth.

# Stats
stats:
  hp: 6
  max_hp: 6
  attack: 3
  defense: 1
  speed: 5

# AI Behavior
behavior:
  ai_type: aggressive     # References AI plugin
  aggro_range: 5          # Tiles
  flee_at_hp_percent: 20  # Flee when low HP

# Loot Table
loot_table:
  - item: gold
    min: 1
    max: 5
    chance: 1.0  # 100%

  - item: rusty_dagger
    chance: 0.15  # 15%

  - item: healing_potion
    chance: 0.05  # 5%

# Abilities
abilities:
  - id: basic_attack
    cooldown: 0
    damage_multiplier: 1.0

# XP & Spawning
xp_reward: 10

spawn_rules:
  min_floor: 1
  max_floor: 5
  spawn_weight: 10        # Common
  spawn_groups: [1, 2, 3] # Solo or small packs
```

### Ability Definitions

```yaml
# data/abilities/heal.yaml
id: heal
name: Heal
class: healer
description: Restore health to an ally.

# Targeting
type: targeted
target_type: ally
range: 5

# Cost
cost:
  mana: 10

# Effects
effects:
  - type: heal
    amount:
      base: 8
      scaling:
        - stat: max_mana
          ratio: 0.2  # 20% of max mana

# Cooldown
cooldown: 3  # turns

# Visual
visual:
  animation: green_sparkles
  sound: healing_chime

# Events published
publishes_events:
  - ABILITY_USED
  - PLAYER_HEALED
```

### Recipe Definitions

```yaml
# data/recipes/iron_sword.yaml
id: iron_sword
name: Iron Sword
category: weapon
description: A sturdy iron blade.

# Ingredients
ingredients:
  - item: iron_ore
    amount: 3
    min_hardness: 50  # Ore quality requirement

  - item: wood_handle
    amount: 1

# Crafting
crafting_station: forge
time_to_craft: 5  # turns

# Result
result:
  item: iron_sword
  stats:
    damage: 8
    durability: 100

  # Inherit from materials!
  inherit_from_material:
    - ore_property: hardness
      item_stat: durability
      ratio: 1.0  # 1:1 mapping

    - ore_property: purity
      item_stat: damage
      ratio: 0.1  # Slight damage bonus
```

---

## 2. Content Loader

### Pydantic Schemas (Validation)

```python
# veinborn/content/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class MonsterStats(BaseModel):
    hp: int
    max_hp: int
    attack: int
    defense: int
    speed: int

class LootEntry(BaseModel):
    item: str
    min: int = 1
    max: int = 1
    chance: float = 1.0

class MonsterDefinition(BaseModel):
    """Validates monster YAML structure"""
    id: str
    name: str
    description: str
    stats: MonsterStats
    behavior: Dict[str, Any]
    loot_table: List[LootEntry]
    abilities: List[Dict[str, Any]]
    xp_reward: int
    spawn_rules: Dict[str, Any] = {}
```

### Content Loader

```python
# veinborn/content/loader.py
import yaml
from pathlib import Path
from pydantic import ValidationError
from typing import Dict

class ContentLoader:
    """Load and validate all content from YAML"""

    def __init__(self, content_dir: Path = Path("data")):
        self.content_dir = content_dir
        self.monsters: Dict[str, MonsterDefinition] = {}
        self.abilities: Dict[str, Any] = {}
        self.recipes: Dict[str, Any] = {}

    def load_all(self):
        """Load all content at startup"""
        self.load_monsters()
        self.load_abilities()
        self.load_recipes()

    def load_monsters(self):
        """Load all monster definitions"""
        for yaml_file in (self.content_dir / "monsters").glob("*.yaml"):
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

                try:
                    monster = MonsterDefinition(**data)
                    self.monsters[monster.id] = monster
                except ValidationError as e:
                    print(f"Invalid monster {yaml_file}: {e}")

    def get_monster(self, monster_id: str) -> MonsterDefinition:
        """Get monster definition by ID"""
        return self.monsters[monster_id]

# Usage:
content = ContentLoader()
content.load_all()

# Spawn monster from definition
goblin_def = content.get_monster("goblin")
goblin = Monster.from_definition(goblin_def)
```

---

## 3. Expression Language (Simple Logic)

For simple conditionals without full scripting:

```python
# requirements.txt
simpleeval>=0.9.13

# veinborn/content/expressions.py
from simpleeval import simple_eval

def eval_condition(expr: str, context: dict) -> bool:
    """Safely evaluate condition expression"""
    return simple_eval(expr, names=context)
```

### Usage in YAML

```yaml
# data/quests/goblin_revenge.yaml
quest:
  id: goblin_revenge

  on_complete:
    # Simple expression evaluation
    conditions:
      - "player.has_item('goblin_ear')"
      - "player.level >= 5"

    actions:
      - give_item: legendary_sword
      - give_xp: 500
      - show_dialog: "You've avenged my family!"

  on_fail:
    condition: "player.level < 5"
    actions:
      - show_dialog: "You're not ready yet."
```

**Benefits:**
- ✅ Safe (no code execution)
- ✅ Simple syntax (Python-like)
- ✅ Good for conditionals
- ❌ Limited (no loops, functions)

---

## 4. Scripting (Phase 2+)

When YAML isn't expressive enough, add scripting.

### When to Use Scripting

| Content Type | YAML Enough? | Need Scripting? |
|--------------|--------------|-----------------|
| Simple monster | ✅ Yes | ❌ No |
| Boss with phases | 🤔 Maybe | ✅ Probably |
| NPC dialog trees | ❌ No | ✅ Yes |
| Quest logic | ❌ No | ✅ Yes |
| Player houses | ❌ No | ✅ Yes (sandboxed) |

### Option A: Embedded Lua (Recommended)

**Why Lua:**
- ✅ Industry standard (WoW, Roblox, Factorio)
- ✅ Sandboxable (safe for untrusted code)
- ✅ Fast (LuaJIT is very fast)
- ✅ Simple syntax (non-programmers can learn)

**Setup:**

```python
# requirements.txt
lupa>=2.0

# veinborn/scripting/lua_engine.py
from lupa import LuaRuntime

class LuaScriptEngine:
    def __init__(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self._setup_sandbox()

    def _setup_sandbox(self):
        """Disable dangerous functions"""
        self.lua.execute("""
            -- Disable dangerous globals
            os = nil
            io = nil
            require = nil
            dofile = nil
            loadfile = nil

            -- Safe globals only
            safe_env = {
                math = math,
                table = table,
                string = string,
            }
        """)

    def load_script(self, script_path: str):
        """Load Lua script"""
        with open(script_path) as f:
            return self.lua.execute(f.read())

    def call_function(self, func_name: str, *args):
        """Call Lua function from Python"""
        func = self.lua.globals()[func_name]
        return func(*args)
```

**Lua Script Example:**

```lua
-- data/bosses/dragon.lua
function dragon_ai(dragon, players)
    -- Phase 1: Normal attacks
    if dragon.hp_percent > 0.5 then
        dragon:use_random_attack({"fire_breath", "claw"})

    -- Phase 2: Summon adds
    elseif dragon.hp_percent > 0.25 then
        if not dragon.adds_summoned then
            dragon:summon("goblin", count=3)
            dragon.adds_summoned = true
        end
        dragon:use_random_attack({"fire_breath", "claw", "tail_swipe"})

    -- Phase 3: Berserk
    else
        dragon:apply_status("berserk")
        dragon:use_attack("mega_fireball")
    end
end

function on_player_died(dragon, player)
    -- Taunt when player dies
    dragon:say("Pathetic mortal!")
end
```

**Python API for Lua:**

```python
# veinborn/scripting/api.py
class LuaEntityAPI:
    """Safe API exposed to Lua scripts"""

    def __init__(self, entity):
        self._entity = entity

    def use_attack(self, attack_name: str):
        """Use specific attack"""
        attack = self._entity.abilities[attack_name]
        self._entity.use_ability(attack)

    def summon(self, monster_type: str, count: int = 1):
        """Summon monsters"""
        if count > 5:
            count = 5  # Limit to prevent abuse
        for _ in range(count):
            game.spawn_monster(monster_type, near=self._entity.pos)

    # ❌ NOT exposed: entity._internal_state
    # Keep internals hidden from scripts!

# Inject API into Lua
lua.globals().dragon = LuaEntityAPI(dragon_instance)
lua.call_function("dragon_ai", lua.globals().dragon, players)
```

### Option B: Sandboxed Python

**For player-created content (houses, custom modes):**

```python
# veinborn/scripting/python_sandbox.py
import ast

class RestrictedPython:
    """Execute Python in restricted environment"""

    ALLOWED_BUILTINS = {
        'abs', 'all', 'any', 'bool', 'dict', 'enumerate',
        'float', 'int', 'len', 'list', 'max', 'min',
        'range', 'round', 'sorted', 'str', 'sum', 'tuple', 'zip',
    }

    def execute(self, code: str, safe_api: dict):
        """Execute Python code with restricted globals"""
        # Parse and validate AST
        tree = ast.parse(code)
        self._validate_ast(tree)

        # Restricted builtins
        globals = {
            '__builtins__': {k: __builtins__[k] for k in self.ALLOWED_BUILTINS},
        }
        globals.update(safe_api)

        # Execute
        exec(compile(tree, '<script>', 'exec'), globals)
        return globals

    def _validate_ast(self, tree):
        """Ensure no dangerous operations"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                raise SecurityError("Imports not allowed")
            # ... more validation ...
```

**Player House Script:**

```python
# ~/.veinborn/houses/alice/entrance.py
def on_player_enter(player):
    """Called when player enters room"""
    if player.name == "alice":
        game.announce("Welcome home, Alice!")
    elif player.name in friends:
        game.announce(f"Welcome, {player.name}!")
    else:
        game.announce("Private residence.")
        game.teleport_to_town(player)

def on_use_lever(player):
    """Custom puzzle lever"""
    global secret_door_open

    if secret_door_open:
        game.close_door("secret")
        secret_door_open = False
    else:
        game.open_door("secret")
        secret_door_open = True
        player.give_achievement("FOUND_SECRET")

# Room state
friends = ["bob", "carol", "dave"]
secret_door_open = False
```

---

## 5. Security Considerations

### Sandbox Checklist

```python
# ✅ Safe - sandboxed API
player.give_item("sword")
game.spawn_monster("goblin")

# ❌ Dangerous - NEVER expose!
import os
os.system("rm -rf /")

__import__("os").system("malicious")

open("/etc/passwd").read()

while True: pass  # Infinite loop
```

**Sandbox Requirements:**
- ✅ No file I/O (`open`, `io`)
- ✅ No network (`socket`, `urllib`)
- ✅ No imports (`import`, `__import__`)
- ✅ No introspection (`getattr`, `setattr`, `eval`)
- ✅ No subprocess (`os.system`, `subprocess`)
- ✅ CPU/memory limits (timeout after 1s, max 10MB)

---

## 6. Hot-Reload (Development)

```python
# veinborn/dev/hot_reload.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ContentHotReloader:
    """Watch content files and reload on change"""

    def __init__(self, content_loader):
        self.content_loader = content_loader
        self.observer = Observer()

    async def start(self):
        class ChangeHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if event.src_path.endswith('.yaml'):
                    print(f"🔄 Reloading {event.src_path}")
                    self.content_loader.load_all()
                    print("✅ Reload complete!")

        self.observer.schedule(ChangeHandler(), path="data", recursive=True)
        self.observer.start()
        print("🔥 Hot-reload enabled - edit YAML live!")

# Development mode
if config.environment == "development":
    hot_reloader = ContentHotReloader(content_loader)
    await hot_reloader.start()

# Now you can:
# 1. Edit data/monsters/goblin.yaml
# 2. Save
# 3. Changes appear immediately!
```

---

## 7. Phased Approach

### Phase 1 (Now): YAML + Expressions ✅

**Content:**
- Monsters, abilities, recipes: YAML
- Simple conditions: `simpleeval`
- No full scripting yet

**Good for:** 80% of content

```yaml
monster:
  id: goblin_shaman
  abilities:
    - id: heal_nearby
      condition: "nearby_allies_hurt() and mana >= 10"
```

### Phase 2 (Post-MVP): Add Lua 🤔

**Content:**
- Complex AI: Lua scripts
- Boss mechanics: Lua scripts
- Quest logic: Lua scripts

**Good for:** Complex behavior

```lua
function boss_ai(boss)
    if boss.hp_percent < 0.25 then
        boss:go_berserk()
    end
end
```

### Phase 3 (Future): Sandboxed Python 🚀

**Content:**
- Player houses: Sandboxed Python
- Custom game modes: Sandboxed Python
- Mods: Sandboxed Python

**Good for:** Player-created content

```python
def on_lever():
    if puzzle_solved():
        open_treasure_room()
```

---

## Summary

| Approach | Power | Safety | Ease | When |
|----------|-------|--------|------|------|
| **YAML** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Static content |
| **Expressions** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Simple conditions |
| **Lua** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Complex behavior |
| **Python** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Player content |

**Recommendation:**
1. **Start:** YAML + expressions (Phase 1)
2. **Add:** Lua for dev content (Phase 2)
3. **Consider:** Sandboxed Python for players (Phase 3)

---

## References

- [Pydantic Validation](https://docs.pydantic.dev/)
- [Lua Programming](https://www.lua.org/manual/5.4/)
- [Lupa (Python-Lua)](https://github.com/scoder/lupa)
- [simpleeval](https://github.com/danthedeckie/simpleeval)
- `VEINBORN_YAML_CONTENT_SYSTEM.md` - Full YAML examples

---

**Next Steps:**
1. Create content schemas (`veinborn/content/schemas.py`)
2. Implement ContentLoader (`veinborn/content/loader.py`)
3. Add hot-reload for development
4. Create example content (monsters, abilities)
5. Test with real game systems
