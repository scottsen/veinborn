# Brogue: Project Overview

## Game Vision

**Brogue** is a memory-driven roguelike that tells the story of a young protagonist following in the footsteps of their missing older sibling. It combines deep mechanical systems with emotional storytelling, where progression comes through remembering teachings and developing a personal relationship with evolving equipment.

## Core Differentiators

### 1. Memory-Based Progression
- Skills unlock through emotional memory triggers
- "Remember when Big Bro showed you how to..."
- Growth feels personal and earned
- Each run builds on previous knowledge

### 2. Growing Weapon System
- Weapons evolve based on combat history
- Develop "memories" of battles and environments
- Create unique, personal equipment stories
- Multiple growth paths (Specialized, Adaptive, Chaotic)

### 3. Essence & Material Mastery
- Deep crafting system without complexity
- Materials have distinct "personalities"
- Essence collection and combination
- Systems interact meaningfully

### 4. Tactical Combat
- Position-based advantages
- Multiple combat stances
- Environmental interactions
- Status effects and combos

## Development Phases

### Phase 1: MVP (v0.9)
**Goal**: Playable core game loop

**Must Have**:
- Basic movement and turn system
- Simple combat with 3-5 enemy types
- BSP dungeon generation (single level)
- Basic inventory and equipment
- Core UI with Textual framework
- Death/restart cycle

**Success Criteria**:
- Player can explore, fight, and die meaningfully
- Game feels like a complete (if simple) roguelike
- Core mechanics are solid foundation for expansion

### Phase 2: Memory System
**Goal**: Implement unique progression

**Features**:
- Memory-triggered skill unlocks
- Basic weapon growth system
- Simple essence collection
- Improved combat with stances

### Phase 3: Deep Systems
**Goal**: Full vision implementation

**Features**:
- Complete material mastery system
- Complex essence interactions
- Advanced weapon evolution
- Multiple dungeon levels
- Full progression depth

## Technical Architecture

### Core Components
```
Game Engine:
- Python 3.8+
- Textual for terminal UI (cross-platform TUI framework)
- Turn-based architecture
- Modular system design

Map Generation:
- BSP-based dungeon creation
- Room-corridor connectivity
- Environmental variety
- Expandable level types

Combat System:
- Tactical turn-based combat
- Position-based modifiers
- Status effect management
- Scalable complexity

Data Management:
- Save/load system
- Configuration management
- Progress tracking
- Session persistence
```

### File Structure
```
brogue/
├── src/
│   ├── core/          # Game engine
│   ├── systems/       # Core systems (combat, progression)
│   ├── generation/    # Map and content generation
│   ├── ui/           # User interface
│   └── data/         # Game data and configuration
├── tests/            # Test suites
├── docs/             # Design documentation
└── assets/           # Game assets (if any)
```

## Key Design Principles

1. **Meaningful Every Turn**: Each decision matters
2. **Personal Growth**: Progression feels earned and emotional
3. **Simple Rules, Complex Emergence**: Easy to learn, deep to master
4. **No Meaningless Choices**: Every option has purpose
5. **Story Through Gameplay**: Narrative emerges from mechanics
6. **Respectful of Player Time**: Quick restart, clear feedback
7. **Always Something New**: Discovery drives engagement

## Target Experience

Players should feel:
- **Connected** to their character and equipment
- **Clever** when remembering and applying teachings
- **Proud** of personal growth and weapon evolution
- **Curious** about new combinations and discoveries
- **Engaged** by meaningful tactical decisions
- **Motivated** to try "just one more run"

## Success Metrics

### Engagement
- Average session length
- Return rate after death
- Progression through content
- Discovery of advanced mechanics

### Emotional Connection
- Player attachment to weapons
- Memory system engagement
- Story completion rate
- Community sharing of experiences

### Mechanical Depth
- Build variety in player approaches
- Advanced technique adoption
- Mastery system progression
- Strategic depth utilization

## Next Steps

1. **Complete MVP Planning**: Define exact scope for v0.9
2. **Technical Architecture**: Finalize code structure and dependencies
3. **Core Implementation**: Build basic game loop and systems
4. **Playtesting Framework**: Establish feedback and iteration process
5. **Community Building**: Share progress and gather input

The goal is to create not just another roguelike, but a game that feels personally meaningful to each player through its unique blend of mechanical depth and emotional resonance.