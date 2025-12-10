# Veinborn System Interactions

**Last Updated:** 2025-11-05
**For:** Developers understanding how systems connect

---

## Overview

Veinborn has **11 interconnected systems** working together. This document maps how they interact, what data flows between them, and where to look when debugging.

---

## 🗺️ High-Level Architecture Map

```
┌─────────────────────────────────────────────────────────────┐
│                         User Input                           │
│                      (Keyboard/Mouse)                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                     Textual UI (app.py)                      │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────┐  │
│  │ Map      │ │ Status   │ │ Message   │ │   Sidebar    │  │
│  │ Widget   │ │ Bar      │ │ Log       │ │   (Stats)    │  │
│  └──────────┘ └──────────┘ └───────────┘ └──────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │ Key event → Action
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    ActionFactory                             │
│              (Creates appropriate action)                    │
│  'h' → MoveAction, 'm' → MineAction, 'c' → CraftAction      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   Action.perform()                           │
│              (Modifies game state)                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      GameContext                             │
│        (Safe API for accessing/modifying state)              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              GameState (central state)                 │ │
│  │  ┌─────────┐ ┌─────────┐ ┌──────┐ ┌──────────────┐   │ │
│  │  │ Player  │ │Monsters │ │ Map  │ │  Inventory   │   │ │
│  │  └─────────┘ └─────────┘ └──────┘ └──────────────┘   │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Systems Process                           │
│  ┌──────────┐ ┌─────────────┐ ┌─────────────────────────┐  │
│  │   AI     │ │    Turn     │ │       Floor             │  │
│  │  System  │ │  Processor  │ │      Manager            │  │
│  └──────────┘ └─────────────┘ └─────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    UI Refresh                                │
│            (Display updated state)                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Core Game Loop

```python
# Simplified game loop
while player.is_alive:
    # 1. Get player input
    key = ui.get_key()

    # 2. Create action from input
    action = action_factory.create(key, context)

    # 3. Validate and perform action
    if action.can_perform(context):
        result = action.perform(context)

    # 4. Process monster turns
    for monster in state.monsters:
        ai_system.process_monster(monster, context)

    # 5. Update systems
    turn_processor.process_turn(context)

    # 6. Refresh UI
    ui.refresh(state)
```

---

## 📦 System Interactions by Flow

### Player Movement Flow

```
User presses 'h' (move left)
    │
    ▼
ActionFactory creates MoveAction(dx=-1, dy=0)
    │
    ▼
MoveAction.can_perform(context)
    ├─> Check if target tile is walkable
    ├─> Check if monster is there
    └─> Return (True, "") or (False, "Reason")
    │
    ▼
MoveAction.perform(context)
    ├─> If monster at target: Convert to AttackAction
    ├─> Else: Update player position
    ├─> Add message to log
    └─> Return ActionResult
    │
    ▼
AISystem processes all monsters
    ├─> Each monster pathfinds toward player
    ├─> Move or attack if adjacent
    └─> Update monster positions
    │
    ▼
TurnProcessor increments turn count
    │
    ▼
UI refreshes (shows new positions)
```

### Mining Flow

```
User presses 's' (survey ore)
    │
    ▼
ActionFactory creates SurveyAction
    │
    ▼
SurveyAction.can_perform()
    ├─> Check if adjacent to ore vein
    └─> Return (True/False)
    │
    ▼
SurveyAction.perform()
    ├─> Get ore vein properties from GameState
    ├─> Display in sidebar (hardness, purity, etc.)
    └─> Add message "You survey the ore..."
    │
    ▼
User sees ore properties, decides to mine
    │
    ▼
User presses 'm' (mine)
    │
    ▼
ActionFactory creates MineAction
    │
    ▼
MineAction.can_perform()
    ├─> Check if adjacent to ore
    ├─> Check if already mining
    └─> Return (True/False)
    │
    ▼
MineAction.perform() [Turn 1]
    ├─> Set player.mining_target = ore_vein
    ├─> Set player.mining_progress = 0
    ├─> Calculate total_turns (based on hardness)
    └─> Add message "You start mining... (0/5)"
    │
    ▼
AISystem processes monsters (player is vulnerable!)
    ├─> Monsters can attack player while mining
    │
    ▼
User presses 'm' again [Turn 2]
    │
    ▼
MineAction.perform() [Turn 2]
    ├─> Increment mining_progress
    ├─> Check if complete (progress >= total_turns)
    ├─> If complete:
    │   ├─> Add ore to inventory
    │   ├─> Remove ore vein from map
    │   ├─> Clear mining_target
    │   └─> Add message "Mining complete!"
    └─> Else: Add message "Mining... (2/5)"
```

### Crafting Flow

```
User arrives at forge, presses 'c' (craft)
    │
    ▼
ActionFactory creates CraftAction (opens menu)
    │
    ▼
CraftAction shows crafting UI
    ├─> Load recipes from recipes.yaml
    ├─> Filter by discovered recipes
    ├─> Show required materials vs inventory
    │
    ▼
User selects recipe "Iron Sword"
    │
    ▼
CraftAction.can_perform()
    ├─> Check inventory has 2 iron ore
    ├─> Check at forge (if required)
    └─> Return (True/False)
    │
    ▼
CraftAction.perform()
    ├─> Read ore properties from inventory
    │   (hardness=78, conductivity=30, purity=82)
    ├─> Evaluate stat formula:
    │   attack = hardness * 0.1 + purity * 0.05
    │   attack = 78 * 0.1 + 82 * 0.05 = 7.8 + 4.1 = 11.9 → 12
    ├─> Create item with calculated stats
    ├─> Remove ore from inventory
    ├─> Add crafted item to inventory
    └─> Add message "You crafted an Iron Sword (+12 attack)!"
```

### Combat Flow

```
Player moves into monster tile
    │
    ▼
MoveAction detects monster at target
    │
    ▼
MoveAction converts to AttackAction
    │
    ▼
AttackAction.perform()
    ├─> Get attacker stats (player.attack + weapon bonus)
    ├─> Get defender stats (monster.defense)
    ├─> Calculate damage:
    │   base_damage = player.attack (5)
    │   equipment_bonus = weapon.attack_bonus (12)
    │   total_attack = 5 + 12 = 17
    │   defense_reduction = monster.defense * 0.5 = 2 * 0.5 = 1
    │   final_damage = max(1, 17 - 1) = 16
    ├─> Apply damage: monster.take_damage(16)
    ├─> Check if monster dead:
    │   ├─> If dead: award XP, drop loot
    │   └─> Else: continue
    └─> Add message "You hit goblin for 16 damage!"
    │
    ▼
Monster's turn (if still alive)
    │
    ▼
AISystem processes monster
    ├─> Check if adjacent to player
    ├─> Create AttackAction (monster → player)
    ├─> Calculate damage (same formula)
    ├─> Apply damage to player
    └─> Check if player dead (game over)
```

### Save/Load Flow

```
User presses 'S' (save game)
    │
    ▼
SaveSystem.save_game()
    ├─> Serialize GameState to dict
    │   ├─> Player → JSON
    │   ├─> Monsters → JSON array
    │   ├─> Map → JSON (tiles, entities)
    │   ├─> Inventory → JSON array
    │   └─> RNG state → Seed value
    ├─> Write to ~/.veinborn/saves/save_001.json
    └─> Add message "Game saved!"
    │
    ▼
[Later] User loads game
    │
    ▼
SaveSystem.load_game("save_001")
    ├─> Read JSON from file
    ├─> Deserialize to GameState
    │   ├─> Create Player from JSON
    │   ├─> Create Monsters from JSON
    │   ├─> Recreate Map
    │   └─> Restore RNG state
    ├─> Return GameState
    └─> Game continues exactly where it left off
```

### Floor Progression Flow

```
Player reaches stairs, presses '>' (descend)
    │
    ▼
ActionFactory creates DescendAction
    │
    ▼
DescendAction.can_perform()
    ├─> Check if standing on stairs tile
    └─> Return (True/False)
    │
    ▼
DescendAction.perform()
    ├─> Increment floor number
    ├─> Add message "You descend to floor 2..."
    │
    ▼
FloorManager.generate_new_floor(floor_num=2)
    ├─> Generate new map (BSP algorithm)
    ├─> Calculate monster count:
    │   count = base_count + (floor // 3)
    │   count = 2 + (2 // 3) = 2 monsters
    ├─> Spawn monsters using monster_spawns.yaml
    │   (Floor 2 → goblins, orcs weighted spawn)
    ├─> Calculate ore vein count:
    │   count = base_count + (floor // 5)
    │   count = 5 + (2 // 5) = 5 veins
    ├─> Spawn ore veins with floor-appropriate quality
    ├─> Place stairs (up and down)
    └─> Spawn player on up-stairs
    │
    ▼
UI refreshes (shows new floor)
```

---

## 📊 System Dependencies

### What Depends on What

```
GameState (central dependency)
    │
    ├──> Actions (modify state)
    ├──> Systems (read/modify state)
    ├──> UI (reads state)
    └──> SaveSystem (serializes state)

ActionFactory
    ├──> Depends on: GameContext
    └──> Used by: UI (key handler)

AISystem
    ├──> Depends on: GameContext, Pathfinding
    └──> Used by: Game loop (monster turns)

FloorManager
    ├──> Depends on: WorldGenerator, EntitySpawner, GameContext
    └──> Used by: DescendAction, Game initialization

CraftingSystem
    ├──> Depends on: Recipes (YAML), GameContext
    └──> Used by: CraftAction

LootSystem
    ├──> Depends on: LootTables (YAML), GameRNG
    └──> Used by: Monster death (combat)
```

---

## 🔍 Data Flow Examples

### Example 1: Ore Properties → Crafted Item Stats

```
1. Player mines Iron Ore
   └─> Ore properties generated by GameRNG:
       hardness: 78
       conductivity: 30
       malleability: 65
       purity: 82
       density: 50

2. Ore stored in inventory (keeps properties)

3. Player crafts "Iron Sword" (requires 2 iron ore)
   └─> Recipe formula: "hardness * 0.1 + purity * 0.05"

4. CraftingSystem evaluates formula:
   attack_bonus = 78 * 0.1 + 82 * 0.05
   attack_bonus = 7.8 + 4.1
   attack_bonus = 11.9 → 12 (rounded)

5. Item created with stats:
   {
     "name": "Iron Sword",
     "attack_bonus": 12,
     "source_ore": {"hardness": 78, "purity": 82}
   }

6. Item added to inventory

7. Player equips sword
   └─> EquipAction adds attack_bonus to player.attack
```

### Example 2: Floor Number → Monster Difficulty

```
1. Player descends to floor 7

2. FloorManager.generate_new_floor(7)

3. EntitySpawner.spawn_monsters()
   ├─> Calculate count: 2 + (7 // 3) = 2 + 2 = 4 monsters
   ├─> Load monster_spawns.yaml for floor 7
   │   floor_7_9:
   │     orc: 30%
   │     ogre: 30%
   │     troll: 25%
   │     skeleton: 15%
   └─> Roll RNG for each monster:
       Spawn: orc, troll, ogre, orc

4. Each monster loaded from monsters.yaml
   └─> Orc: HP=12, Attack=5, Defense=2
       Troll: HP=30, Attack=12, Defense=5
       Ogre: HP=25, Attack=10, Defense=4

5. Monsters placed on map

6. Player encounters troll (12 attack vs player's 5+12=17)
   └─> Challenging but winnable with crafted gear
```

### Example 3: RNG Seed → Reproducible Gameplay

```
1. Player starts new game with seed "12345"

2. GameRNG.initialize("12345")
   └─> Sets internal RNG state

3. Map generation uses RNG:
   ├─> BSP split points: deterministic from seed
   ├─> Room sizes: deterministic
   └─> Corridor paths: deterministic

4. Ore spawning uses RNG:
   ├─> Ore locations: same every time
   ├─> Ore properties: same every time
   └─> Floor 1, position (10, 5) always has:
       Iron Ore (hardness: 78, purity: 82)

5. Monster spawning uses RNG:
   └─> Floor 1 always spawns same monsters at same positions

6. Combat uses RNG:
   └─> Critical hits (if implemented) deterministic

7. Result: Players can share seeds for identical runs
   └─> "Try seed 12345, amazing iron spawn at (10, 5)!"
```

---

## 🐛 Debugging Guide

### "Player can't mine ore"

**Check:**
1. Is player adjacent to ore? (`MineAction.can_perform()`)
2. Is ore vein entity on map? (`state.map.get_entity_at(pos)`)
3. Is player already mining? (`player.mining_target`)

**Files to check:**
- `src/core/actions/mine_action.py` - Mining logic
- `src/core/entities.py` - OreVein entity
- `src/core/world.py` - Ore vein spawning

### "Crafted item has wrong stats"

**Check:**
1. Ore properties in inventory (`player.inventory`)
2. Recipe formula in `data/balance/recipes.yaml`
3. Formula evaluation in `src/core/crafting.py`

**Debug:**
```python
# Add to crafting.py
print(f"Ore properties: {ore.properties}")
print(f"Formula: {recipe.stat_formulas['attack_bonus']}")
print(f"Result: {calculated_attack}")
```

### "Monsters not spawning on floor 5"

**Check:**
1. Floor range in `data/balance/monster_spawns.yaml`
2. Spawn count calculation in `src/core/spawning.py`
3. Monster spawn calls in `src/core/floor_manager.py`

**Debug:**
```bash
# Run with debug logging
python3 scripts/run_debug.py

# Check logs
tail -f logs/veinborn.log | grep "spawn"
```

### "Save file doesn't restore correctly"

**Check:**
1. Serialization in `src/core/save_load.py`
2. Entity `to_dict()` and `from_dict()` methods
3. RNG state restoration

**Debug:**
```python
# Compare saved vs loaded state
saved_state = state.to_dict()
loaded_state = SaveSystem.load_game("save_001")
print(json.dumps(saved_state, indent=2))
```

---

## 📚 Related Documentation

- **BASE_CLASS_ARCHITECTURE.md** - Entity and Action patterns
- **00_ARCHITECTURE_OVERVIEW.md** - High-level architecture
- **ACTION_FACTORY_COMPLETE.md** - Action creation pattern
- **CONTENT_SYSTEM.md** - YAML-driven content

---

## 💡 Key Takeaways

1. **GameState is central** - All systems read/modify it through GameContext
2. **Actions drive changes** - All state modifications go through Action.perform()
3. **Systems are processors** - They read state, apply logic, update state
4. **UI is read-only** - Never modifies state directly, only displays it
5. **Data flows one direction** - User → Action → State → Systems → UI

---

**Understanding these interactions makes debugging and feature addition much easier!**
