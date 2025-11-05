# Brogue MVP Roadmap

**Last Updated:** 2025-10-23
**Status:** Single-Player MVP - Pre-Multiplayer Phase
**Goal:** Feature-complete single-player game with mining/crafting systems

---

## Current Status

### ✅ COMPLETED (Phase 0 - Foundation)

**Core Game Loop:**
- ✅ 8-direction grid movement (arrows, HJKL, YUBN)
- ✅ Turn-based combat (bump to attack)
- ✅ Monster AI (pathfind toward player, attack when adjacent)
- ✅ Death and game over detection
- ✅ Game restart flow

**Map Generation:**
- ✅ BSP (Binary Space Partitioning) dungeon algorithm
- ✅ Rooms + corridors
- ✅ Multiple walkable areas
- ✅ Player spawn (first room center)
- ✅ Monster spawn (random rooms)

**UI Framework:**
- ✅ Textual terminal UI
- ✅ Map viewport (60×20) centered on player
- ✅ Status bar (HP, turn count, position)
- ✅ Message log (game events)
- ✅ Sidebar (player stats, monster list)
- ✅ Full keyboard controls

**Code Structure:**
- ✅ GameState management (`src/core/game.py`)
- ✅ Entity system (`src/core/entities.py`)
- ✅ World/map system (`src/core/world.py`)
- ✅ Widget composition (`src/ui/textual/`)

---

## 🎯 MVP Phase 1: Mining & Crafting (4-6 weeks)

**Goal:** Add the SWG-style mining and crafting systems that make Brogue unique.

---

## 🏗️ Architectural Foundation

**IMPORTANT**: Week 1-2 is the ideal time to implement base class architecture.

**Why Now?**
- Mining system needs OreVein entities (perfect Entity base class use case)
- Clean refactor before complexity grows
- Lua-ready architecture with zero extra cost
- Multiplayer-ready patterns with no overhead

**See**: `docs/architecture/BASE_CLASS_ARCHITECTURE.md` (complete design)

**Recommended Approach**:
1. Start with `Entity` base class (2-3 hours)
2. Refactor Player, Monster to inherit (1 hour)
3. Create OreVein as Entity subclass (30 min)
4. Implement Action pattern during mining actions (2 hours)

**Outcome**: Clean architecture + mining system implemented together

**Optional**: See `docs/architecture/LUA_INTEGRATION_STRATEGY.md` for future-proofing decisions

---

### Week 1-2: Mining System

#### Task 1.1: Ore Vein Generation
**Priority:** HIGH
**Files to modify:**
- `src/core/base/entity.py` - **NEW: Create Entity base class**
- `src/core/entities.py` - Refactor to use Entity base, add OreVein
- `src/core/world.py` - Add ore vein spawning

**Architecture Note**: This task is perfect for implementing Entity base class pattern.

**Recommended Implementation Path**:
1. ✅ Create `src/core/base/entity.py` (Entity base class)
2. ✅ Refactor Player, Monster → inherit from Entity
3. ✅ Create OreVein class (extends Entity)
4. ✅ Add ore vein spawning to world generation

**See**: `docs/architecture/BASE_CLASS_ARCHITECTURE.md` for complete Entity design.

**Implementation:**
```python
# Using Entity base class (see architecture docs)
class OreVein(Entity):
    def __init__(self, ore_type: str, x: int, y: int, properties: dict):
        super().__init__(
            entity_type=EntityType.ORE_VEIN,
            name=f"{ore_type.title()} Ore Vein",
            x=x,
            y=y,
            stats=properties  # hardness, conductivity, etc.
        )
        self.ore_type = ore_type  # "copper", "iron", "mithril", "adamantite"
        self.mining_turns = 3 + (properties.get('hardness', 50) // 25)
```

**Ore Spawning Rules:**
- Copper (Floors 1-3): Properties 20-50
- Iron (Floors 4-6): Properties 40-70
- Mithril (Floors 7-9): Properties 60-90
- Adamantite (Floor 10+): Properties 80-100
- 5% chance for "jackpot" (2-3 tiers above normal, 80-100 stats)

**5 Properties (0-100 scale):**
1. Hardness → Weapon damage / Armor defense
2. Conductivity → Magic power / Spell efficiency
3. Malleability → Durability / Repair ease
4. Purity → Quality multiplier (affects all stats)
5. Density → Weight / Encumbrance

**Acceptance Criteria:**
- [ ] Ore veins spawn in dungeon walls
- [ ] Render as `◆` character (distinct from walls)
- [ ] Each ore has 5 properties rolled independently
- [ ] Ore type determined by floor depth
- [ ] Jackpot spawns occur ~5% of the time

#### Task 1.2: Survey Action
**Priority:** HIGH
**Files to modify:**
- `src/core/game.py` - Add survey action to game loop
- `src/ui/textual/widgets/ore_widget.py` - NEW: Ore display widget

**Implementation:**
- Press 's' when adjacent to ore vein
- Takes 1 turn
- Displays ore properties in sidebar
- Shows mining time (3-5 turns based on hardness)

**UI Mockup:**
```
═══════════════════════════════════
  Iron Ore Vein
═══════════════════════════════════
  Hardness:      78  ████████░░
  Conductivity:  23  ██░░░░░░░░
  Malleability:  65  ██████░░░░
  Purity:        82  ████████░░
  Density:       45  █████░░░░░
═══════════════════════════════════
  Mining Time: 4 turns
  [M]ine  [L]eave
```

**Acceptance Criteria:**
- [ ] Survey action available when adjacent to ore
- [ ] Properties displayed with visual bars
- [ ] Mining time calculated from hardness
- [ ] Clear UI showing ore quality

#### Task 1.3: Mining Action
**Priority:** HIGH
**Files to modify:**
- `src/core/game.py` - Multi-turn mining action
- `src/core/entities.py` - Ore inventory

**Implementation:**
- Press 'm' to start mining
- Takes 3-5 turns (you're vulnerable!)
- Cannot move or attack while mining
- Monsters can attack you during mining
- Can cancel mining (but lose progress)
- Ore added to inventory when complete

**Risk/Reward Mechanic:**
- Mining leaves you vulnerable (can't dodge)
- High-quality ore takes longer to mine
- Must decide: mine now (risky) or come back later (safer)

**Acceptance Criteria:**
- [ ] Mining is multi-turn action
- [ ] Player is vulnerable during mining
- [ ] Mining can be interrupted (cancel or take damage)
- [ ] Ore added to inventory on completion
- [ ] Ore vein removed from map after mining
- [ ] Message log shows mining progress

### Week 3: Crafting System

#### Task 2.1: Recipe System
**Priority:** HIGH
**Files to create:**
- `data/recipes/` - YAML recipe definitions
- `src/core/recipes.py` - Recipe loader and validator

**Recipe Format (YAML):**
```yaml
simple_sword:
  name: "Simple Sword"
  type: weapon
  tier: basic
  required_ore: 1
  ore_types: [copper, iron]
  base_damage: 3
  stat_formula: "base_damage + (hardness * purity / 100)"
  crafting_time: 2  # turns
  requires_forge: false

longsword:
  name: "Longsword"
  type: weapon
  tier: advanced
  required_ore: 2
  ore_types: [iron, mithril]
  base_damage: 6
  stat_formula: "base_damage + (hardness * purity / 100 * 1.5)"
  crafting_time: 4
  requires_forge: true
```

**Recipe Tiers:**
- **Basic** (start with): Simple Sword, Staff, Bow
- **Advanced** (find in dungeon): Longsword, Battle Staff, Composite Bow
- **Legendary** (boss drops): Flaming Sword, Arcane Staff, Dragon Bow

**Acceptance Criteria:**
- [ ] Recipe YAML schema defined
- [ ] Recipe loader validates YAML
- [ ] Basic recipes available at start
- [ ] Advanced/Legendary recipes discoverable
- [ ] Stat calculation from ore properties

#### Task 2.2: Crafting Interface
**Priority:** HIGH
**Files to modify:**
- `src/core/game.py` - Crafting mode
- `src/ui/textual/widgets/crafting_widget.py` - NEW: Crafting UI

**Implementation:**
- Press 'c' to open crafting menu
- Show available recipes (based on what you've discovered)
- Show required materials
- Select recipe → select ore from inventory → craft
- Takes N turns based on recipe
- Can craft at forge OR with portable kit (class ability)

**UI Mockup:**
```
╔══════════════════════════════════════════════════════════╗
║ CRAFTING                                                 ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║ [1] Simple Sword      (1 copper/iron ore)               ║
║     Damage: 3 + (hardness × purity / 100)               ║
║     Time: 2 turns                                       ║
║                                                          ║
║ [2] Longsword         (2 iron/mithril ore) 🔒 FORGE     ║
║     Damage: 6 + (hardness × purity / 100 × 1.5)         ║
║     Time: 4 turns                                       ║
║                                                          ║
║ [3] ??? (Undiscovered)                                   ║
║                                                          ║
╠══════════════════════════════════════════════════════════╣
║ Inventory: 3 Iron Ore, 1 Mithril Ore                    ║
╚══════════════════════════════════════════════════════════╝
```

**Acceptance Criteria:**
- [ ] Crafting menu accessible via 'c' key
- [ ] Shows available recipes
- [ ] Shows required materials vs inventory
- [ ] Crafting takes multiple turns
- [ ] Crafted item added to inventory with calculated stats
- [ ] Message log shows crafting progress

#### Task 2.3: Forge Locations
**Priority:** MEDIUM
**Files to modify:**
- `src/core/world.py` - Add forge room type

**Implementation:**
- Special room type (5-10% chance per floor)
- Render forge as `▓` tiles
- Required for advanced/legendary recipes
- Multiple forges per level (not bottleneck)

**Acceptance Criteria:**
- [ ] Forge rooms generate in dungeon
- [ ] Forges visually distinct
- [ ] Advanced recipes only craftable at forge
- [ ] Message indicates when forge required

### Week 4: Meta-Progression & Persistence

#### Task 3.1: Legacy Vault System
**Priority:** HIGH
**Files to create:**
- `src/core/legacy.py` - Legacy Vault management
- `data/legacy_vault.json` - Persistent storage

**Implementation:**
- When you die, rare ore (80+ purity) saved to Legacy Vault
- Max 10 ores in vault (FIFO)
- At run start, can withdraw 1 ore from vault
- "Pure Victory" track (no Legacy gear) vs "Legacy Victory"
- Vault persists across runs

**Legacy Vault Rules:**
- Only ores with Purity ≥ 80 are saved
- Max 10 ores (oldest removed when full)
- Can withdraw 1 ore per run at start
- Withdrawing ore marks run as "Legacy Run" (no Pure Victory credit)

**Acceptance Criteria:**
- [ ] Rare ore saved on death
- [ ] Vault UI shows stored ores
- [ ] Can withdraw 1 ore at run start
- [ ] Run flagged as Legacy vs Pure
- [ ] Vault persists to JSON file

#### Task 3.2: Save/Load System
**Priority:** HIGH
**Files to create:**
- `src/core/save.py` - Save/load game state
- `data/saves/` - Save file directory

**Implementation:**
- Save game state to JSON
- Load game state from JSON
- Support multiple save slots (3)
- Auto-save on quit
- Quick-save keybind (Ctrl+S)

**Save Data:**
```json
{
  "player": {...},
  "map": {...},
  "monsters": [...],
  "inventory": [...],
  "floor": 5,
  "turn": 234,
  "run_type": "pure",
  "timestamp": "2025-10-23T15:30:00Z"
}
```

**Acceptance Criteria:**
- [ ] Game state serializable to JSON
- [ ] Save/load preserves all game state
- [ ] Multiple save slots
- [ ] Auto-save on quit
- [ ] Load game from main menu

#### Task 3.3: Statistics Tracking
**Priority:** MEDIUM
**Files to create:**
- `src/core/stats.py` - Stats tracking
- `data/player_stats.json` - Persistent stats

**Implementation:**
- Track runs, deaths, victories
- Track deepest floor reached
- Track Pure Victories vs Legacy Victories
- Track ores mined, items crafted
- Display stats in main menu

**Stats to Track:**
```json
{
  "total_runs": 42,
  "total_deaths": 40,
  "pure_victories": 2,
  "legacy_victories": 0,
  "deepest_floor": 12,
  "ores_mined": 234,
  "items_crafted": 87,
  "monsters_killed": 456
}
```

**Acceptance Criteria:**
- [ ] Stats tracked across runs
- [ ] Stats displayed in menu
- [ ] Pure vs Legacy victories separate
- [ ] Stats persist to JSON

---

## 🎯 MVP Phase 2: Polish & Content (2-3 weeks)

### Week 5: Content Expansion

#### Task 4.1: More Monster Types
**Priority:** MEDIUM
**Current:** 3 monster types (goblin, rat, orc)
**Target:** 15-20 monster types across all floors

**Monster Types by Floor:**
- Floors 1-3: Rat, Goblin, Kobold, Giant Bat
- Floors 4-6: Orc, Troll, Dark Elf, Warg
- Floors 7-9: Ogre, Wyvern, Shadow Beast, Mimic
- Floor 10+: Dragon, Lich, Demon, Ancient Horror

**Monster Abilities:**
- Basic: Just attack
- Advanced: Ranged, AOE, status effects
- Special: Steal ore, destroy equipment, summon allies

#### Task 4.2: Dungeon Features
**Priority:** MEDIUM

**Room Types:**
- Treasure room (high-quality loot)
- Monster den (extra monsters, boss)
- Ore chamber (multiple veins)
- Shrine (healing, buffs)
- Trap room (pressure plates, arrows)

**Hazards:**
- Spike traps
- Fire pits
- Poison gas
- Collapsing floors

#### Task 4.3: Items & Consumables
**Priority:** MEDIUM

**Consumables:**
- Health potions (instant heal)
- Mana potions (restore magic)
- Scrolls (teleport, identify, enchant)
- Food (hunger system)

**Equipment:**
- Weapons (swords, axes, bows, staves)
- Armor (chest, helm, gloves, boots)
- Accessories (rings, amulets)

### Week 6: Balance & Testing

#### Task 5.1: Combat Balance
- Tune monster HP/damage
- Tune player progression
- Ore quality curves
- Crafting stat formulas

#### Task 5.2: Playtest & Iterate
- Internal playtesting
- Balance adjustments
- Bug fixes
- Performance optimization

#### Task 5.3: Tutorial & Onboarding
- Tutorial messages on first run
- Help screen (H key)
- Keybind reference
- New player guidance

---

## 📦 MVP Deliverables

### Minimum Viable Product (MVP) Checklist

**Core Systems:**
- [x] Movement and combat
- [x] Map generation
- [x] UI framework
- [ ] Mining system (survey, mine ore)
- [ ] Crafting system (recipes, forging)
- [ ] Meta-progression (Legacy Vault)
- [ ] Save/load system

**Content:**
- [x] Basic monsters (3 types) → [ ] 15-20 types
- [ ] Multiple floor progression (stairs)
- [ ] Boss encounters
- [ ] Recipe discovery system
- [ ] Forge locations

**Polish:**
- [ ] Statistics tracking
- [ ] Tutorial/help system
- [ ] Balance pass
- [ ] Performance optimization
- [ ] Bug fixes

**MVP Success Criteria:**
- ✅ Game is playable start to finish
- ✅ Mining/crafting loop is fun
- ✅ Meta-progression encourages replay
- ✅ "One more run" factor is strong
- ✅ No major bugs or crashes

---

## 🚀 Post-MVP: Multiplayer Phase

**See:** `/docs/future-multiplayer/` for complete multiplayer design

**High-Level Multiplayer Roadmap:**
1. Network infrastructure (NATS, WebSockets)
2. Messaging architecture (Pydantic messages)
3. 4-action turn system
4. 4-player classes (Warrior, Mage, Healer, Rogue)
5. Party system
6. Shared Legacy Vault
7. Boss fights (4-player mechanics)

**Estimated Timeline:** 8-12 weeks after MVP complete

---

## 🛠️ Development Workflow

### Getting Started
```bash
cd /home/scottsen/src/tia/projects/brogue

# Run the game
python3 run_textual.py

# Run with debug logging
python3 scripts/run_debug.py

# Run tests
python3 -m pytest tests/
```

### Project Structure
```
projects/brogue/
├── src/
│   ├── core/           # Game logic
│   │   ├── game.py     # Game loop, state management
│   │   ├── entities.py # Player, monsters, items
│   │   ├── world.py    # Map generation
│   │   ├── recipes.py  # Crafting system (TODO)
│   │   ├── legacy.py   # Legacy Vault (TODO)
│   │   └── save.py     # Save/load (TODO)
│   └── ui/
│       └── textual/    # Textual UI widgets
│
├── data/
│   ├── recipes/        # Recipe YAML files (TODO)
│   ├── saves/          # Save games (TODO)
│   └── legacy_vault.json (TODO)
│
├── docs/
│   ├── BROGUE_CONSOLIDATED_DESIGN.md  # Master design
│   ├── MVP_ROADMAP.md                 # This file
│   ├── architecture/                  # Phase 2 architecture
│   └── future-multiplayer/            # Phase 2 design docs
│
└── tests/              # Test files
```

### Code Style
- Python 3.10+ with type hints
- Follow existing patterns in `src/core/`
- Use Pydantic for data models
- Write tests for new systems
- Document complex logic

---

## 📝 Notes for Implementers

### Preserve Working Code
The following code is **functional and should not be broken**:
- `src/core/game.py` - Game loop works perfectly
- `src/core/world.py` - BSP map generation works
- `src/ui/textual/` - UI framework integrated

### Architecture Alignment
- MVP uses **direct function calls** (not message-based)
- Multiplayer phase will **refactor to event-driven** (see `/docs/architecture/`)
- Build systems in a way that can be refactored later
- Use clean interfaces (will help with Phase 2 refactor)

### Testing Strategy
- Unit tests for game logic (`game.py`, `entities.py`)
- Integration tests for crafting workflow
- Playtest each feature as you build
- Balance testing (is mining/crafting fun?)

### Performance Considerations
- Map generation should be < 100ms
- Game loop should handle 60+ FPS
- Save/load should be < 500ms
- No memory leaks (long play sessions)

---

## 🎯 Success Metrics

### Phase 1 Success (Mining/Crafting):
- [ ] Player can mine ore (3-5 turns, vulnerable)
- [ ] Player can survey ore (see properties)
- [ ] Player can craft items from ore
- [ ] Crafted items have calculated stats
- [ ] Legacy Vault saves rare ore on death
- [ ] Game saves/loads properly

### MVP Success (Complete Game):
- [ ] 15-20 monster types
- [ ] 10+ floors with progression
- [ ] Boss encounters
- [ ] Meta-progression encourages replay
- [ ] No critical bugs
- [ ] Playable for 30+ hours

### Ready for Multiplayer:
- [ ] All MVP features complete
- [ ] Code is clean and documented
- [ ] Performance is good (60 FPS)
- [ ] Save system robust
- [ ] Balance feels good

---

**Next Step:** Start Week 1 - Implement ore vein generation and survey action!

🎮 Let's build something awesome.
