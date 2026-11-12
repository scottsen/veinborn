# Veinborn Architecture Overview

**Document Type:** Architecture Overview
**Audience:** Developers working on the codebase
**Status:** Current as of 2026-04-17 (pajuzopo-0417 trust-restore)
**Last Updated:** 2026-04-17

---

## What Veinborn Is Today

A terminal roguelike (NetHack-style) in Python with:
- **Single-player core** — mining, crafting, dungeon exploration (working, playable)
- **Textual UI** — the live client (`src/ui/textual/app.py`)
- **Multiplayer (in-progress)** — WebSocket-based server (`src/server/`) with `GameSession`, reconnection, chat; design in `docs/design/MULTIPLAYER_DESIGN_2025.md`
- **Python content system** — AI behaviours, abilities and event handlers registered from `src/core/content/` (`src/core/extensions.py`); see `docs/EXTENDING.md`
- **YAML-driven content** — recipes, monsters, ores

**Verified test state (2026-09-23):** 1170 passing / 0 failing / 0 skipped (`python3 -m pytest tests/ -q`).

## Key Subsystems

| Area | Home | Notes |
|------|------|-------|
| Game loop / turn engine | `src/core/game.py` | Owns event bus, content event handlers, telemetry, floor manager, save-load; assembled by `GameBootstrapper` (`game_bootstrap.py`) and the content registries (`extensions.py`) |
| Post-action pipeline | `src/core/action_pipeline.py` | `process_action_outcome()` — log failures, publish events, react to `descend_floor`, record messages. Shared by single-player `Game` and multiplayer `GameSession` |
| Turn processing | `src/core/turn_processor.py` | Single-player: monster AI, cleanup, game over / high score. `apply_hp_regeneration()` is shared with multiplayer |
| Floors | `src/core/floor_manager.py` + `EntitySpawner.spawn_all_for_floor` | Shared helpers (`generate_floor_map`, `get_victory_floor`, `GameState.clear_floor_entities`) are used by both modes |
| Actions | `src/core/actions/` | `Action.validate(ctx) / execute(ctx) → ActionOutcome` — always passed a `GameContext`, not raw `GameState` |
| Game state | `src/core/game_state.py` + `GameContext` facade | Actions see `GameContext`; `GameState` is the underlying store |
| UI | `src/ui/textual/` | Bindings live in `app.py` — source of truth for keybinds |
| Multiplayer server | `src/server/` | `GameSession`, `WebSocketServer`, reconnection, chat |
| Content / extension points | `src/core/extensions.py` + `src/core/content/` | Decorator registries for AI behaviours, abilities, damage modifiers and event handlers; content modules are auto-imported. See `docs/EXTENDING.md` |
| Content | `data/` + `src/core/entity_loader.py` | Monsters, ores, recipes |

## Canonical Design Docs

- **Multiplayer:** `docs/design/MULTIPLAYER_DESIGN_2025.md`
- **Testing patterns:** `docs/architecture/MVP_TESTING_GUIDE.md`
- **Development guidelines:** `docs/architecture/MVP_DEVELOPMENT_GUIDELINES.md`
- **Decision log:** `docs/architecture/DECISIONS.md`
- **Recent audit:** `docs/PROJECT_REVIEW_2026-04-17.md`

## Historical Context

Earlier phases framed this as "MVP single-player only, multiplayer is future work." That framing is obsolete: multiplayer code is integrated and partially working. The section below retains original MVP-era descriptions of the core loop — still broadly accurate for the single-player path but predates the server layer, Lua runtime, and event bus that now ship in `Game`.

---

**Technology Stack:**
- Python 3.10+ (type hints, dataclasses)
- Textual (terminal UI framework)
- websockets (multiplayer transport)
- PyYAML (content loading)
- pytest + pytest-asyncio (testing)

---

## Core Architecture

### Current Game Loop

The loop is driven by the UI; `Game` owns no input loop of its own. One player action flows like this:

```python
# src/core/game.py (simplified)
def handle_player_action(self, action_type, **kwargs) -> bool:
    action = self.action_factory.create(action_type, **kwargs)
    outcome = action.execute(self.context)          # GameContext, not raw GameState
    took_turn = process_action_outcome(             # src/core/action_pipeline.py
        outcome, action_type,
        add_message=self.state.add_message,
        on_descend_floor=self.descend_floor,        # -> FloorManager
        event_bus=self.event_bus,
    )
    if took_turn:
        self.turn_processor.process_turn()          # HP regen, monster AI, cleanup, game over
    return took_turn
```

Multiplayer (`src/server/game_session/session.py`) runs the same `process_action_outcome()` per action, but
counts turn-taking actions toward a per-round quota and runs monsters once per round instead of after every
action. HP regen is the shared `apply_hp_regeneration()`. Multiplayer game over differs on purpose: the party plays on while any player is alive, and each player is scored on the co-op leaderboard (`HighScoreManager.get_multiplayer_instance()`, `data/highscores_multiplayer.json`) at death, survivors at game end.

**Key Characteristics:**
- ✅ Simple and direct
- ✅ Easy to understand
- ✅ Easy to debug
- ✅ No network complexity
- ✅ Works perfectly for single-player

---

## Project Structure

```
projects/veinborn/
├── src/
│   ├── core/                  # Game logic (no UI, no network)
│   │   ├── game.py            # Game facade: wires subsystems, handles player actions
│   │   ├── game_bootstrap.py  # Subsystem construction
│   │   ├── action_pipeline.py # Post-action handling shared with multiplayer
│   │   ├── turn_processor.py  # Per-turn regen / AI / game over (single-player)
│   │   ├── floor_manager.py   # Descent, victory, shared floor helpers
│   │   ├── game_state.py      # State store (entities is the single entity store)
│   │   ├── entities.py        # Player, monsters, ore veins, forges
│   │   ├── world.py           # Map generation (BSP algorithm)
│   │   ├── actions/           # Move, mine, attack, craft, pickup, ...
│   │   ├── events/            # EventBus and event types
│   │   ├── extensions.py      # Registries + decorators for content
│   │   ├── content/           # ai/, abilities/, events/ content modules
│   │   ├── spawning/          # EntitySpawner
│   │   ├── systems/           # AI system and behaviours
│   │   ├── crafting.py, loot.py, legacy.py, highscore.py, save_load.py
│   │   └── config/            # YAML config loading
│   │
│   ├── server/                # WebSocket multiplayer (GameSession, state deltas, auth)
│   └── ui/
│       ├── textual/           # Textual UI (app.py, widgets/)
│       └── multiplayer_client.py
│
├── data/
│   ├── entities/              # Monster/ore/item YAML definitions
│   ├── balance/               # Balance tuning
│   └── ui/                    # UI layouts
│
├── tests/                     # pytest tests (unit/, integration/, fuzz/)
│
├── run_textual.py             # Single-player entry point
└── run_multiplayer.py         # Multiplayer entry point
```

---

## Core Systems

### 1. Game State Management

**File:** `src/core/game.py`

```python
@dataclass
class GameState:
    """Complete game state (can be serialized for save/load)"""
    player: Player
    monsters: list[Monster]
    map: Map
    inventory: list[Item]
    turn_count: int
    floor: int

    def to_dict(self) -> dict:
        """Serialize for saving"""
        return {
            'player': self.player.to_dict(),
            'monsters': [m.to_dict() for m in self.monsters],
            # ...
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GameState':
        """Deserialize from save file"""
        # ...
```

**Why simple state management:**
- Easy to save/load (just serialize to JSON)
- Easy to test (create GameState, test logic)
- Easy to understand (no hidden state)
- Can refactor to message-based later (Phase 2)

### 2. Entity System

**File:** `src/core/entities.py`

```python
class Player:
    """Player character"""
    hp: int
    max_hp: int
    attack: int
    defense: int
    x: int
    y: int
    inventory: list[Item]

    def move(self, dx: int, dy: int):
        self.x += dx
        self.y += dy

    def take_damage(self, amount: int):
        self.hp -= amount

class Monster:
    """Enemy monsters"""
    name: str
    hp: int
    attack: int
    defense: int
    x: int
    y: int

    def move_toward(self, target_x: int, target_y: int):
        # Simple pathfinding
```

**Current state:** ✅ Working
**Next step:** Add OreVein class for mining system

**Future:** Could refactor to use Entity base class (see `BASE_CLASS_ARCHITECTURE.md`) but not required for MVP.

### 3. Map Generation

**File:** `src/core/world.py`

**Algorithm:** Binary Space Partitioning (BSP)

```python
def generate_dungeon(width: int, height: int) -> Map:
    """Generate dungeon using BSP algorithm"""
    # 1. Partition space recursively
    root = Leaf(0, 0, width, height)
    root.split_recursive()

    # 2. Create rooms in leaf nodes
    rooms = []
    for leaf in root.get_leaves():
        room = create_room(leaf)
        rooms.append(room)

    # 3. Connect rooms with corridors
    connect_rooms(rooms)

    return Map(rooms)
```

**Current state:** ✅ Working perfectly
**Next step:** Add ore vein spawning (Week 1-2)

### 4. UI Framework

**Framework:** Textual (terminal UI)

**Widgets:**
- MapWidget: Dungeon viewport
- StatusBar: HP, turn count, position
- MessageLog: Game events
- Sidebar: Player stats, nearby monsters

**Current state:** ✅ Working perfectly
**Next step:** Add crafting widget, ore survey widget

---

## Adding New Systems (MVP Phase 1)

### Week 1-2: Mining System

**New classes:**
```python
# src/core/entities.py
class OreVein:
    """Ore vein that can be mined"""
    ore_type: str  # "copper", "iron", "mithril", "adamantite"
    x: int
    y: int
    properties: dict  # hardness, conductivity, malleability, purity, density
    mining_turns_required: int
```

**New actions:**
```python
# src/core/game.py
def handle_survey_action(self, target_x: int, target_y: int):
    """Survey ore vein (takes 1 turn)"""
    ore = self.map.get_ore_at(target_x, target_y)
    self.ui.show_ore_properties(ore)

def handle_mining_action(self, target_x: int, target_y: int):
    """Mine ore (takes 3-5 turns, player vulnerable)"""
    ore = self.map.get_ore_at(target_x, target_y)
    self.player.start_mining(ore)
    # Player can't move/attack while mining
    # Mining progresses over multiple turns
```

### Week 3: Crafting System

**New files:**
- `data/recipes/*.yaml` - Recipe definitions
- `src/core/recipes.py` - Recipe loader

**Recipe format:**
```yaml
# data/recipes/simple_sword.yaml
name: "Simple Sword"
type: weapon
required_ore: 1
ore_types: [copper, iron]
base_damage: 3
stat_formula: "base_damage + (ore.hardness * ore.purity / 100)"
crafting_time: 2
```

**Integration:**
```python
# src/core/game.py
def handle_craft_action(self, recipe_id: str, ore_id: str):
    """Craft item from recipe + ore"""
    recipe = self.recipes.get(recipe_id)
    ore = self.player.inventory.get_ore(ore_id)

    item = craft_item(recipe, ore)
    self.player.inventory.add(item)
```

### Week 4: Meta-Progression

**New files:**
- `src/core/legacy.py` - Legacy Vault
- `src/core/save.py` - Save/load system

**Legacy Vault:**
```python
class LegacyVault:
    """Persistent storage for rare ore (survives death)"""
    max_ores: int = 10
    ores: list[Ore]

    def save_ore_on_death(self, player_inventory: list[Ore]):
        """Save rare ore (purity >= 80) to vault"""
        rare_ores = [ore for ore in player_inventory if ore.purity >= 80]
        for ore in rare_ores:
            if len(self.ores) < self.max_ores:
                self.ores.append(ore)

    def withdraw_ore(self) -> Optional[Ore]:
        """Withdraw 1 ore at run start"""
        if self.ores:
            return self.ores.pop(0)
        return None
```

**Save/Load:**
```python
def save_game(state: GameState, slot: int):
    """Save game to JSON file"""
    data = state.to_dict()
    with open(f'data/saves/save_{slot}.json', 'w') as f:
        json.dump(data, f, indent=2)

def load_game(slot: int) -> GameState:
    """Load game from JSON file"""
    with open(f'data/saves/save_{slot}.json', 'r') as f:
        data = json.load(f)
    return GameState.from_dict(data)
```

---

## Testing Strategy (MVP)

### Unit Tests

**Test game logic in isolation:**

```python
# tests/test_entities.py
def test_player_takes_damage():
    player = Player(hp=100, max_hp=100)
    player.take_damage(30)
    assert player.hp == 70

def test_monster_pathfinding():
    monster = Monster(x=0, y=0)
    monster.move_toward(target_x=5, target_y=5)
    # Assert monster moved closer to target
```

**Test crafting:**
```python
# tests/test_recipes.py
def test_craft_sword_from_ore():
    ore = Ore(ore_type="iron", hardness=78, purity=82)
    recipe = load_recipe("simple_sword")

    sword = craft_item(recipe, ore)

    # base_damage + (hardness * purity / 100)
    # 3 + (78 * 0.82) = 3 + 63.96 = ~67 damage
    assert sword.damage == pytest.approx(67, abs=1)
```

### Integration Tests

**Test multiple systems together:**

```python
# tests/test_mining_workflow.py
def test_full_mining_workflow():
    game = Game()
    ore_vein = game.map.get_ore_at(10, 10)

    # Survey ore
    game.handle_survey_action(10, 10)
    assert ore_vein.is_surveyed

    # Mine ore (takes 4 turns)
    for _ in range(4):
        game.handle_mining_action(10, 10)

    # Ore added to inventory
    assert len(game.player.inventory.ores) == 1
    assert ore_vein.is_mined
```

### Manual Testing

**Playtest the game:**
1. Run `python3 run_textual.py`
2. Test each feature as you build it
3. Check edge cases (what if player dies while mining?)
4. Verify UI updates correctly

**Goal:** Every feature should be playable and fun before moving to next feature.

---

## Content System (YAML-Based)

### Why YAML?

- ✅ Human-readable
- ✅ Easy for non-programmers to edit
- ✅ Safe (no code execution)
- ✅ Git-friendly (version control works)
- ✅ Can be loaded at runtime (no recompile)

### Example: Monster Definitions

```yaml
# data/monsters/goblin.yaml
id: goblin
name: "Goblin"
glyph: "g"
color: green
stats:
  hp: 6
  attack: 3
  defense: 1
loot:
  gold: [1, 5]  # 1-5 gold
  chance: 1.0   # 100% drop rate
```

**Loading:**
```python
# src/core/content.py
def load_monster_data(monster_id: str) -> dict:
    with open(f'data/monsters/{monster_id}.yaml') as f:
        return yaml.safe_load(f)

def spawn_monster(monster_id: str, x: int, y: int) -> Monster:
    data = load_monster_data(monster_id)
    return Monster(
        name=data['name'],
        hp=data['stats']['hp'],
        attack=data['stats']['attack'],
        # ...
    )
```

---

## Development Workflow

### Adding a New Feature

1. **Read the design:** `docs/VEINBORN_CONSOLIDATED_DESIGN.md`
2. **Check the roadmap:** `docs/MVP_ROADMAP.md`
3. **Understand existing code:** Read relevant files in `src/core/`
4. **Write tests first** (TDD): Create test file in `tests/`
5. **Implement:** Add code to make tests pass
6. **Manual test:** Play the game, verify it works
7. **Document:** Update docs if needed

### Code Style

- Python 3.10+ with type hints
- Use dataclasses for data structures
- Keep functions small and focused
- Comment complex logic
- Write docstrings for public APIs

### Running Tests

```bash
# Run all tests
python3 -m pytest tests/

# Run specific test file
python3 -m pytest tests/test_entities.py

# Run with coverage
python3 -m pytest --cov=src tests/
```

---

## Future Refactoring (Phase 2)

**When MVP is complete**, we'll refactor to support multiplayer:

### Changes for Phase 2:
1. **Replace direct function calls** → Event-driven messages (NATS)
2. **Extract game logic** → GameStateService (microservice)
3. **Add network layer** → ConnectionService (WebSocket gateway)
4. **Add persistence** → PersistenceService (PostgreSQL)
5. **Extend via content modules** → `src/core/content/` (already in place; see `docs/EXTENDING.md`)

**But for MVP:** Keep it simple! Direct function calls work perfectly for single-player.

**Complete Phase 2 architecture:** See `docs/design/MULTIPLAYER_DESIGN_2025.md` (the original `/docs/future-multiplayer/` directory is archived, not in this repo — see `docs/INDEX.md`)

---

## Key Architecture Documents

### For MVP Implementation (Read These)
- `START_HERE.md` - Onboarding guide
- `MVP_ROADMAP.md` - What to build, week by week
- `00_ARCHITECTURE_OVERVIEW.md` (this doc) - How it works
- `BASE_CLASS_ARCHITECTURE.md` - Optional: Clean base classes
- `CONTENT_SYSTEM.md` - YAML content loading
- `DEVELOPMENT_GUIDELINES.md` - Code style, testing

### For Future Planning (Don't Build Yet)
- `docs/design/MULTIPLAYER_DESIGN_2025.md` - Multiplayer architecture (Phase 2 complete; the original `future-multiplayer/` directory is archived, not in this repo)
- `LOGGING_OBSERVABILITY.md` - Phase 2 monitoring

---

## Common Questions

### Q: Why not use the Phase 2 architecture from the start?

**A:** YAGNI (You Ain't Gonna Need It)

Phase 2 architecture adds:
- NATS message bus (complex setup)
- Microservices (deployment complexity)
- WebSocket protocol (network complexity)
- Event-driven design (harder to debug)

**For MVP:** None of this is needed! Simple Python game loop works perfectly.

**When to refactor:** After MVP is complete and we're ready for multiplayer.

### Q: Should I use Entity base class?

**A:** Optional, but recommended

See `BASE_CLASS_ARCHITECTURE.md` for complete design. Main benefits:
- Less code duplication (Player and Monster share code)
- Easier to add OreVein class (just extend Entity)
- Easier to test (uniform interface)
- Makes Phase 2 refactor easier (but works without it)

**Time cost:** 2-3 hours to refactor
**Benefit:** Cleaner code, easier mining implementation

### Q: What about scripting (Lua)?

**A:** Tried and removed (2026-11-11, ADR-018 in `DECISIONS.md`).

All game logic is Python and content is YAML plus small Python content modules
registered with decorators (`docs/EXTENDING.md`). That gives hot-spot extensibility
without a second language to bridge, test and sandbox.

---

## Success Criteria

**MVP is complete when:**
- ✅ Player can mine ore (survey properties, mine over multiple turns)
- ✅ Player can craft items from ore (recipes loaded from YAML)
- ✅ Crafted items have calculated stats (ore properties × recipe formula)
- ✅ Legacy Vault saves rare ore on death
- ✅ Game can save/load
- ✅ 15-20 monster types across 10+ floors
- ✅ Boss encounters
- ✅ Game is fun and replayable

**Ready for Phase 2 when:**
- ✅ All MVP features complete
- ✅ Code is clean and tested
- ✅ Performance is good (60 FPS)
- ✅ No critical bugs

---

## References

- [START_HERE.md](../START_HERE.md) - Start here if new to project
- [MVP_ROADMAP.md](../MVP_ROADMAP.md) - Implementation tasks
- [VEINBORN_CONSOLIDATED_DESIGN.md](../VEINBORN_CONSOLIDATED_DESIGN.md) - Game design
- [MULTIPLAYER_DESIGN_2025.md](../design/MULTIPLAYER_DESIGN_2025.md) - Multiplayer architecture (the original future-multiplayer/ directory is archived, not in this repo)
- [BASE_CLASS_ARCHITECTURE.md](./BASE_CLASS_ARCHITECTURE.md) - Optional: Clean base classes
- [CONTENT_SYSTEM.md](./CONTENT_SYSTEM.md) - YAML content system
- [DEVELOPMENT_GUIDELINES.md](./DEVELOPMENT_GUIDELINES.md) - Code style

---

**Next Step:** Read `MVP_ROADMAP.md` and pick a task!

🎮 Let's build something awesome (and keep it simple for MVP).
