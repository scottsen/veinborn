# Core Mechanics & MVP Guide

## What Makes Roguelikes Fun

### Core "Fun" Elements

#### 1. Meaningful Decisions
- Each turn matters
- Resource management (HP, potions, scrolls)
- Risk vs reward choices
- No obvious "best" choice
- Example: Use last healing potion now or save it?

#### 2. Discovery & Learning
- Procedural generation keeps it fresh
- Item identification system
- Learning enemy patterns
- Hidden mechanics to master
- Example: NetHack's complex item interactions

#### 3. Permadeath & Consequences
- Stakes feel real
- Each run is a story
- Learning from failures
- "Just one more try" factor

#### 4. Progressive Knowledge
Player knowledge grows in layers:
1. Basic mechanics
2. Enemy behaviors
3. Item combinations
4. Advanced strategies
5. Secret interactions

## Key Design Elements

### Information Clarity
- Clear feedback on actions
- Visible consequences
- Understanding why you died
- No "unfair" deaths

### Depth vs Complexity
**Good**: Deep systems with simple rules
**Bad**: Complex systems that feel arbitrary
**Example**: Brogue's simple systems creating complex gameplay

### Pacing
- Quiet exploration
- Tense decisions
- Dramatic moments
- Emergency options
- Example: Finding stairs with low HP

### Power Progression
- Finding better items
- Learning new abilities
- Character advancement
- BUT maintaining challenge

## Common Pitfalls to Avoid

### Tedium
- Too much backtracking
- Grinding
- Repetitive actions
- Slow early game

### Unfair Challenge
- Unavoidable deaths
- Hidden critical information
- Too much RNG dependency
- Unsignaled dangers

### Lack of Agency
- Too linear
- Forced choices
- Limited strategies
- No creative solutions

## Design Tips by Game Phase

### Early Game
- Quick to start
- Clear initial goals
- Early interesting choices
- Fast restart after death

### Middle Game
- Multiple viable strategies
- Interesting item combinations
- Risk/reward opportunities
- Character specialization

### Late Game
- New challenges
- Power fantasy payoff
- Strategic depth
- Optional harder content

## Elements that Keep Players Coming Back
1. "What if I try..." moments
2. Discoverable secrets
3. Multiple viable builds
4. Emergent gameplay
5. Achievement milestones
6. Meta-progression (if any)
7. Community knowledge sharing

## V0.9 MVP Priority

### Must Have Core Features
```
1. Basic Game Loop
   - Movement
   - Turn system
   - Combat basics
   - Death/restart

2. Map Generation
   - BSP dungeon generation
   - Rooms and corridors
   - Single level (multi-level nice but not required)
   - Basic room variety

3. Character
   - Simple stats (HP, attack, defense)
   - Basic inventory (3-5 slots)
   - Simple equipment (weapon, armor)

4. Minimal Enemies
   - 3-5 enemy types
   - Basic AI (move toward player)
   - Different stats/behavior

5. Core UI (blessed)
   - Map display
   - Status line (HP, etc)
   - Message log
   - Basic menus
```

### Essential Systems
```
1. Combat
   - Melee attacks
   - Hit chance
   - Damage calculation
   - Death handling

2. Field of View
   - Basic line of sight
   - Memory of seen tiles
   - Fog of war

3. Basic Items
   - Health potions
   - Better weapon/armor
   - Pick up/drop
```

### Nice to Have But Can Wait
- Ranged combat
- Magic system
- Complex items
- Multiple levels
- Character progression
- Advanced AI
- Sound effects
- Save/load

### Minimum Viable Data
```python
class GameState:
    def __init__(self):
        self.map = Map()
        self.player = Player()
        self.entities = []
        self.messages = MessageLog()

class Player:
    def __init__(self):
        self.hp = 10
        self.max_hp = 10
        self.attack = 2
        self.defense = 1
        self.inventory = []

class Map:
    def __init__(self, width=80, height=24):
        self.tiles = [[Tile() for y in range(height)]
                     for x in range(width)]
```

### Core Game Loop
```python
def game_loop():
    while True:
        display.draw(game_state)
        action = input_handler.get_action()
        if action:
            player.take_action(action)
            for entity in entities:
                entity.take_turn()
        check_game_over()
```

### Testing Priority
1. Can player move around map?
2. Does combat work?
3. Can player die/restart?
4. Are items usable?
5. Is game winnable?

This gives you a playable game with core roguelike elements while leaving room for expansion.