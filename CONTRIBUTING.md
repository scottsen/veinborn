# Contributing to Brogue

Thank you for your interest in contributing to Brogue! This guide will help you get started.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Getting Help](#getting-help)

---

## Quick Start

**New to the project?** Start here:

1. **Read the docs** (15 minutes):
   - [`docs/START_HERE.md`](docs/START_HERE.md) - New developer guide
   - [`docs/MVP_ROADMAP.md`](docs/MVP_ROADMAP.md) - What to build next
   - [`README.md`](README.md) - Project overview

2. **Run the game** (5 minutes):
   ```bash
   python3 run_textual.py
   ```
   Play around, understand the mechanics.

3. **Pick a task**:
   - Check [`docs/MVP_ROADMAP.md`](docs/MVP_ROADMAP.md) for open tasks
   - Look for "Good First Issue" items

---

## Development Setup

### Prerequisites

- **Python 3.10+**
- **pip** (Python package manager)
- **Git**

### Installation

```bash
# Clone the repository
git clone https://github.com/scottsen/brogue.git
cd brogue

# Install dependencies
pip install -r requirements.txt

# Run the game
python3 run_textual.py
```

### Verify Setup

```bash
# Run tests
pytest

# Run with debug logging
python3 scripts/run_debug.py

# Check code coverage (if available)
pytest --cov=src
```

---

## Project Structure

```
brogue/
├── src/              # Source code
│   ├── core/         # Game logic (entities, world, combat)
│   └── ui/           # User interface (Textual UI)
├── tests/            # Test files
├── data/             # Game data (YAML configs)
├── docs/             # Documentation
├── scripts/          # Utility scripts
└── examples/         # Example code/configs
```

**Key Files:**
- `src/core/game.py` - Main game loop
- `src/core/entities.py` - Player, monsters, items
- `src/core/world.py` - Map generation (BSP algorithm)
- `src/ui/textual/` - Terminal UI components

**Documentation:**
- [`docs/README.md`](docs/README.md) - Master documentation index
- [`docs/development/`](docs/development/) - Testing, debugging, code standards
- [`docs/architecture/`](docs/architecture/) - Technical design

---

## Development Workflow

### 1. Choose a Task

- **From the roadmap:** [`docs/MVP_ROADMAP.md`](docs/MVP_ROADMAP.md)
- **Good first tasks:**
  - Add new monster types
  - Improve UI feedback
  - Add tests for existing systems
  - Fix bugs in issue tracker

### 2. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

### 3. Make Changes

- Follow existing code patterns (see [Code Standards](#code-standards))
- Write clear, descriptive code
- Add comments for complex logic
- Test your changes thoroughly

### 4. Test Your Changes

```bash
# Play the game
python3 run_textual.py

# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Test specific file
pytest tests/unit/test_combat.py
```

### 5. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a clear message
git commit -m "Add new goblin champion enemy type

- Added GoblinChampion class with enhanced stats
- Increased spawn rate on floors 3+
- Added unique attack pattern"
```

**Good commit messages:**
- Start with a verb (Add, Fix, Update, Refactor)
- First line is a brief summary (50 chars or less)
- Add details in the body if needed
- Reference issues: "Fixes #123"

### 6. Push and Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create a pull request on GitHub
# Describe your changes, link to relevant issues
```

---

## Code Standards

### Python Style

- **Python 3.10+** with type hints
- **PEP 8** style guide (mostly)
- **4 spaces** for indentation (no tabs)
- **Line length:** 100 characters (soft limit)

### Type Hints

```python
# Use type hints for function signatures
def calculate_damage(
    attacker: Entity,
    defender: Entity,
    weapon: Optional[Weapon] = None
) -> int:
    """Calculate damage dealt by attacker to defender.

    Args:
        attacker: The attacking entity
        defender: The defending entity
        weapon: Optional weapon being used

    Returns:
        Total damage dealt
    """
    # Implementation...
```

### Code Organization

**Follow existing patterns:**

```python
# Good: Clear, documented, type-hinted
class Monster(Entity):
    """A hostile creature in the dungeon."""

    def __init__(self, name: str, hp: int, attack: int):
        super().__init__(name, hp)
        self.attack = attack

    def take_turn(self, game_state: GameState) -> None:
        """Execute monster's turn logic."""
        # Implementation...

# Avoid: Unclear, no types, no docs
class Monster:
    def __init__(self, n, h, a):
        self.n = n
        self.h = h
        self.a = a
```

### Design Principles

1. **Keep it simple** - Don't over-engineer
2. **Follow existing patterns** - Consistency matters
3. **Meaningful names** - Code should be self-documenting
4. **Small functions** - One thing, do it well
5. **Test by playing** - Manual testing is important for games

### Detailed Standards

See [`docs/development/CODE_REVIEW_STANDARDS.md`](docs/development/CODE_REVIEW_STANDARDS.md) for complete guidelines.

---

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_combat.py

# Specific test
pytest tests/unit/test_combat.py::test_melee_attack

# With coverage
pytest --cov=src --cov-report=html

# Verbose output
pytest -v
```

### Writing Tests

**Example test:**

```python
def test_player_takes_damage():
    """Test that player HP decreases when damaged."""
    player = Player(name="Test", hp=10)
    player.take_damage(3)
    assert player.hp == 7

def test_player_death():
    """Test that player dies when HP reaches 0."""
    player = Player(name="Test", hp=5)
    player.take_damage(10)
    assert player.hp == 0
    assert not player.is_alive
```

**Testing guidelines:**
- Test one thing per test
- Clear test names describe what's tested
- Use fixtures for common setup
- Test edge cases (0 HP, negative values, etc.)

### Manual Testing

**Always test by playing the game!**
- Does it feel right?
- Are there edge cases?
- Is the UI clear?
- Is it fun?

See [`docs/development/TESTING_ACTION_FACTORY.md`](docs/development/TESTING_ACTION_FACTORY.md) for more guidance.

---

## Submitting Changes

### Pull Request Checklist

Before submitting:

- [ ] Code follows project standards
- [ ] Tests added/updated and passing
- [ ] Documentation updated if needed
- [ ] Played the game to verify changes
- [ ] Commit messages are clear
- [ ] No debug code or commented-out code
- [ ] Branch is up to date with main

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Refactoring
- [ ] Documentation
- [ ] Tests

## Testing
How did you test this?
- [ ] Unit tests added/updated
- [ ] Manual testing (played the game)
- [ ] Integration tests

## Related Issues
Fixes #123
Related to #456

## Screenshots (if UI changes)
[Add screenshots if applicable]
```

### Code Review Process

1. **Submit PR** - Create pull request with clear description
2. **Automated checks** - Tests must pass
3. **Review** - Maintainers will review your code
4. **Address feedback** - Make requested changes
5. **Approval** - Once approved, PR will be merged

**Review focus:**
- Code quality and style
- Test coverage
- Design patterns
- Performance impact
- Documentation

---

## Getting Help

### Resources

- **Documentation:** [`docs/`](docs/)
- **Start Here:** [`docs/START_HERE.md`](docs/START_HERE.md)
- **Roadmap:** [`docs/MVP_ROADMAP.md`](docs/MVP_ROADMAP.md)
- **Architecture:** [`docs/architecture/`](docs/architecture/)
- **Development Guides:** [`docs/development/`](docs/development/)

### Questions?

- **Check existing docs** - Most questions are answered in docs/
- **Search issues** - Someone may have asked before
- **Ask maintainers** - Open an issue with your question
- **Debug guides:** [`docs/development/DEBUG_INSTRUCTIONS.md`](docs/development/DEBUG_INSTRUCTIONS.md)

### Common Issues

**Game won't start:**
```bash
# Check dependencies
pip install -r requirements.txt

# Try safe mode
python3 scripts/run_safe.py
```

**Terminal issues:**
```bash
# Reset terminal
./scripts/fix_terminal.sh

# Or manually
reset
```

**Import errors:**
```bash
# Make sure you're in the project root
cd /path/to/brogue
python3 run_textual.py
```

---

## Project Philosophy

### Design Principles

1. **Mechanical over narrative** - Gameplay first
2. **Simple rules, complex emergence** - Depth through interaction
3. **Accessibility + Mastery** - Easy to start, hard to master
4. **Social play** - Built for playing with friends

### Development Values

- **Quality over speed** - Take time to do it right
- **Consistency** - Follow existing patterns
- **Clarity** - Code should be understandable
- **Testing** - Verify your changes work
- **Fun** - Make the game enjoyable!

### Current Phase: MVP (Single-Player)

We're building the single-player foundation. Multiplayer comes later in Phase 2.

**Focus now:**
- Core mechanics (mining, crafting)
- Polish and balance
- Test coverage
- Documentation

**Not now:**
- Multiplayer systems
- Advanced meta-progression
- Lua scripting

See [`docs/MVP_ROADMAP.md`](docs/MVP_ROADMAP.md) for current priorities.

---

## Thank You!

Thank you for contributing to Brogue! Every contribution helps make this game better.

**Questions?** Open an issue or check the docs.

**Ready to code?** Pick a task from [`docs/MVP_ROADMAP.md`](docs/MVP_ROADMAP.md)!

---

## Quick Links

- [README.md](README.md) - Project overview
- [docs/START_HERE.md](docs/START_HERE.md) - New developer guide
- [docs/MVP_ROADMAP.md](docs/MVP_ROADMAP.md) - Current tasks
- [docs/README.md](docs/README.md) - Documentation index
- [docs/development/CODE_REVIEW_STANDARDS.md](docs/development/CODE_REVIEW_STANDARDS.md) - Detailed code standards
