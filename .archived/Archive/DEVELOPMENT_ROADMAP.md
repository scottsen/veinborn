# Brogue Development Roadmap

## Project Status

**Current Phase**: Planning & Design Complete
**Next Phase**: MVP Implementation (v0.9)
**Target**: Playable core game loop

## Immediate Next Steps

### 1. Technical Setup
- [ ] Finalize Python project structure
- [ ] Set up development environment
- [ ] Configure blessed terminal library
- [ ] Establish testing framework
- [ ] Create build/run scripts

### 2. Core Architecture
- [ ] Implement basic game loop
- [ ] Create tile-based map system
- [ ] Build entity management system
- [ ] Develop input handling
- [ ] Set up message logging

### 3. MVP Features (v0.9)

#### Essential Systems
- [ ] **Movement System**
  - Player movement on grid
  - Collision detection
  - Turn-based mechanics

- [ ] **Map Generation**
  - BSP dungeon algorithm
  - Room and corridor creation
  - Basic room variety
  - Stair placement

- [ ] **Combat System**
  - Basic melee combat
  - Hit chance calculation
  - Damage resolution
  - Death handling

- [ ] **Entity System**
  - Player character
  - 3-5 basic enemy types
  - Basic AI (move toward player)
  - Entity spawning

- [ ] **UI System**
  - Map display
  - Status bar (HP, etc.)
  - Message log
  - Basic menus

- [ ] **Item System**
  - Basic inventory (3-5 slots)
  - Equipment slots (weapon, armor)
  - Health potions
  - Pick up/drop mechanics

#### Testing Criteria
1. ✅ Can player move around map?
2. ✅ Does combat work correctly?
3. ✅ Can player die and restart?
4. ✅ Are items usable?
5. ✅ Is game winnable/loseable?

## Post-MVP Development

### Phase 2: Memory System (v1.0)
- [ ] Memory-triggered skill unlocks
- [ ] Basic weapon growth tracking
- [ ] Combat stance system
- [ ] Environmental bonuses
- [ ] Brother's teachings narrative

### Phase 3: Deep Systems (v2.0)
- [ ] Complete essence collection
- [ ] Material mastery system
- [ ] Advanced weapon evolution
- [ ] Multi-level dungeons
- [ ] Full progression depth

## Technical Architecture

### Core Components
```
brogue/
├── src/
│   ├── core/
│   │   ├── game.py          # Main game loop
│   │   ├── entities.py      # Entity management
│   │   └── world.py         # Game world state
│   ├── systems/
│   │   ├── combat.py        # Combat mechanics
│   │   ├── movement.py      # Movement and collision
│   │   ├── inventory.py     # Item management
│   │   └── progression.py   # Memory/skill system
│   ├── generation/
│   │   ├── mapgen.py        # Map generation
│   │   ├── bsp.py           # BSP algorithm
│   │   └── spawning.py      # Entity/item spawning
│   ├── ui/
│   │   ├── display.py       # Screen rendering
│   │   ├── input.py         # Input handling
│   │   └── menus.py         # Menu systems
│   └── data/
│       ├── monsters.py      # Monster definitions
│       ├── items.py         # Item definitions
│       └── config.py        # Game configuration
```

### Dependencies
- **Python 3.8+**: Core language
- **Blessed**: Terminal UI library
- **Dataclasses**: Data structure management
- **Enum**: Type safety
- **JSON**: Save/load system

## Quality Assurance

### Testing Strategy
- Unit tests for core systems
- Integration tests for game flow
- Manual playtesting for fun factor
- Performance testing for responsiveness

### Code Quality
- Type hints throughout
- Comprehensive docstrings
- Consistent code style (Black/Flake8)
- Regular code reviews

## Risk Management

### Technical Risks
- **Terminal compatibility**: Test across different terminals
- **Performance**: Profile map generation and rendering
- **Save system**: Ensure robust save/load functionality

### Design Risks
- **Complexity creep**: Stay focused on MVP scope
- **Fun factor**: Regular playtesting throughout development
- **Scope management**: Clear phase boundaries

## Success Metrics

### MVP Success
- Game runs smoothly on target terminals
- Core loop is engaging for 15+ minutes
- Death feels fair and educational
- Restart is quick and motivating

### Long-term Success
- Players discover advanced mechanics naturally
- Memory system creates emotional connection
- Weapon evolution feels personal and meaningful
- Community forms around shared experiences

## Timeline Estimates

### MVP (v0.9): 4-6 weeks
- Week 1-2: Core architecture and basic systems
- Week 3-4: Map generation and combat
- Week 5-6: Polish, testing, and optimization

### Memory System (v1.0): 2-3 weeks additional
- Advanced progression mechanics
- Narrative integration
- Balance tuning

### Deep Systems (v2.0): 4-6 weeks additional
- Complete material/essence systems
- Multi-level dungeons
- Advanced mechanics

## Next Actions

1. **Set up development environment**
2. **Create basic project structure**
3. **Implement core game loop**
4. **Begin with movement and map display**
5. **Add basic combat system**

The goal is to have a playable, engaging MVP that captures the core essence of Brogue while providing a solid foundation for the deeper systems that make it unique.