# Player Config & Character Classes Design

**Date**: 2025-10-25
**Session**: xogicuca-1025
**Status**: 🎨 **DESIGN PHASE**

---

## Overview

Design a comprehensive player configuration and character class system:
- NetHack-style config file (`~/.broguerc`)
- ENV VAR support for player name
- Character classes with unique starting stats/items
- Game start flow with identity/class selection

---

## Player Name Resolution

### Priority Order

```python
def get_player_name() -> str:
    """
    Resolve player name with priority:
    1. ENV VAR (BROGUE_PLAYER_NAME)
    2. Config file (~/.broguerc)
    3. Command-line argument (--name)
    4. Interactive prompt (if TTY)
    5. Default: "Anonymous"
    """

    # 1. Check environment variable
    if name := os.getenv('BROGUE_PLAYER_NAME'):
        return name

    # 2. Check config file
    config = ConfigManager.get_instance()
    if name := config.get('player.name'):
        return name

    # 3. Check CLI argument (parsed earlier)
    if name := args.name:
        return name

    # 4. Interactive prompt (if terminal)
    if sys.stdin.isatty():
        name = input("Enter your name: ").strip()
        if name:
            return name

    # 5. Default
    return "Anonymous"
```

### ENV VAR Examples

```bash
# Set player name globally
export BROGUE_PLAYER_NAME="Alice"
brogue

# One-off run
BROGUE_PLAYER_NAME="Bob" brogue

# In .bashrc or .zshrc
echo 'export BROGUE_PLAYER_NAME="YourName"' >> ~/.bashrc
```

---

## Config File System (NetHack-style)

### File Locations (Priority Order)

```python
CONFIG_PATHS = [
    Path.home() / ".broguerc",           # Classic Unix style
    Path.home() / ".config" / "brogue" / "config",  # XDG style
    Path("/etc/broguerc"),                # System-wide (read-only)
]
```

### Config Format (INI-style)

```ini
# ~/.broguerc - Brogue Configuration File
# Lines starting with # are comments

[player]
name = Alice
default_class = warrior

[game]
# Random seed for all games (leave empty for random)
default_seed =

# Autopickup settings
autopickup = true
autopickup_types = ore,food,weapon

[display]
# UI settings (future)
show_damage_numbers = true
color_scheme = classic

[keys]
# Keybindings (future)
# move_north = k
# move_south = j
```

### ConfigManager Implementation

```python
# src/core/config/user_config.py

from pathlib import Path
from typing import Optional, Any
import configparser
import logging
import os

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages user configuration (NetHack-style .broguerc).

    Features:
    - Multiple config file locations
    - ENV VAR overrides
    - INI format (human-readable)
    - Type-safe getters
    - Default values
    """

    _instance: Optional['ConfigManager'] = None

    CONFIG_PATHS = [
        Path.home() / ".broguerc",
        Path.home() / ".config" / "brogue" / "config",
        Path("/etc/broguerc"),
    ]

    def __init__(self):
        """Initialize config manager."""
        self.config = configparser.ConfigParser()
        self.config_file: Optional[Path] = None
        self.load()

    @classmethod
    def get_instance(cls) -> 'ConfigManager':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton (for testing)."""
        cls._instance = None

    def load(self) -> None:
        """Load config from first available file."""
        for path in self.CONFIG_PATHS:
            if path.exists():
                try:
                    self.config.read(path)
                    self.config_file = path
                    logger.info(f"Loaded config from {path}")
                    return
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

        logger.info("No config file found, using defaults")

    def get(self, key: str, default: Any = None) -> Optional[str]:
        """
        Get config value by dot-separated key.

        Args:
            key: Config key (e.g., 'player.name', 'game.default_seed')
            default: Default value if not found

        Returns:
            Config value or default

        Example:
            >>> config.get('player.name')
            'Alice'
            >>> config.get('player.name', 'Anonymous')
            'Alice' or 'Anonymous' if not set
        """
        # Check ENV VAR override first (convert key to ENV format)
        env_key = f"BROGUE_{key.upper().replace('.', '_')}"
        if env_value := os.getenv(env_key):
            return env_value

        # Parse section.key
        if '.' not in key:
            return default

        section, option = key.split('.', 1)

        if not self.config.has_section(section):
            return default

        if not self.config.has_option(section, option):
            return default

        return self.config.get(section, option) or default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean config value."""
        value = self.get(key)
        if value is None:
            return default
        return value.lower() in ('true', 'yes', '1', 'on')

    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer config value."""
        value = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Set config value (in-memory only, use save() to persist).

        Args:
            key: Config key (e.g., 'player.name')
            value: Value to set
        """
        section, option = key.split('.', 1)

        if not self.config.has_section(section):
            self.config.add_section(section)

        self.config.set(section, option, str(value))

    def save(self, path: Optional[Path] = None) -> None:
        """
        Save config to file.

        Args:
            path: File path (default: first writable path)
        """
        if path is None:
            # Use first writable path
            for p in self.CONFIG_PATHS[:2]:  # Skip /etc (read-only)
                try:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    path = p
                    break
                except PermissionError:
                    continue

        if path is None:
            logger.error("No writable config path found")
            return

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                self.config.write(f)
            logger.info(f"Saved config to {path}")
        except IOError as e:
            logger.error(f"Failed to save config: {e}")

    def create_default_config(self, path: Optional[Path] = None) -> None:
        """
        Create default config file with comments.

        Args:
            path: File path (default: ~/.broguerc)
        """
        if path is None:
            path = Path.home() / ".broguerc"

        default_config = """# Brogue Configuration File
# Lines starting with # are comments

[player]
# Your player name (appears in high scores)
name =

# Default character class (warrior, rogue, mage)
default_class =

[game]
# Default seed for all games (leave empty for random)
default_seed =

# Autopickup settings
autopickup = true
autopickup_types = ore,food,weapon

[display]
# Show damage numbers in combat
show_damage_numbers = true

# Color scheme (classic, modern, colorblind)
color_scheme = classic

[keys]
# Custom keybindings (future feature)
# move_north = k
# move_south = j
"""

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                f.write(default_config)
            logger.info(f"Created default config at {path}")
        except IOError as e:
            logger.error(f"Failed to create default config: {e}")
```

---

## Character Classes

### Class Design

```python
# src/core/character_class.py

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum


class CharacterClass(Enum):
    """Available character classes."""
    WARRIOR = "warrior"
    ROGUE = "rogue"
    MAGE = "mage"


@dataclass
class ClassTemplate:
    """
    Character class template with starting stats and items.

    Defines the initial state for each class.
    """

    name: str
    description: str

    # Starting stats
    hp: int
    attack: int
    defense: int

    # Starting items (future)
    starting_items: List[str]

    # Class-specific modifiers (future)
    hp_per_level: int
    attack_per_level: int
    defense_per_level: int

    # Special abilities (future)
    abilities: List[str]


# Class definitions
CLASS_TEMPLATES: Dict[CharacterClass, ClassTemplate] = {
    CharacterClass.WARRIOR: ClassTemplate(
        name="Warrior",
        description="Strong melee fighter with high HP and attack",
        hp=30,
        attack=5,
        defense=3,
        starting_items=["iron_sword", "leather_armor"],
        hp_per_level=5,
        attack_per_level=2,
        defense_per_level=1,
        abilities=["power_strike"],
    ),

    CharacterClass.ROGUE: ClassTemplate(
        name="Rogue",
        description="Agile explorer with high speed and critical hits",
        hp=20,
        attack=4,
        defense=2,
        starting_items=["dagger", "lockpick"],
        hp_per_level=3,
        attack_per_level=1,
        defense_per_level=1,
        abilities=["backstab", "dodge"],
    ),

    CharacterClass.MAGE: ClassTemplate(
        name="Mage",
        description="Arcane spellcaster with low HP but powerful magic",
        hp=15,
        attack=2,
        defense=1,
        starting_items=["wand", "spellbook"],
        hp_per_level=2,
        attack_per_level=1,
        defense_per_level=0,
        abilities=["fireball", "teleport"],
    ),
}


def get_class_template(class_type: CharacterClass) -> ClassTemplate:
    """Get class template by type."""
    return CLASS_TEMPLATES[class_type]


def create_player_from_class(
    class_type: CharacterClass,
    x: int,
    y: int,
    name: str
) -> 'Player':
    """
    Create player with class template.

    Args:
        class_type: Character class
        x, y: Starting position
        name: Player name

    Returns:
        Player instance with class stats
    """
    from .entities import Player

    template = get_class_template(class_type)

    player = Player(
        x=x,
        y=y,
        hp=template.hp,
        max_hp=template.hp,
        attack=template.attack,
        defense=template.defense,
    )

    # Set name and class
    player.stats['name'] = name
    player.stats['class'] = template.name
    player.stats['class_type'] = class_type.value

    # Future: Add starting items
    # for item_id in template.starting_items:
    #     item = create_item(item_id)
    #     player.inventory.append(item)

    return player
```

---

## Game Start Flow

### Terminal UI Flow

```
╔══════════════════════════════════════════════════════════════════╗
║                       WELCOME TO BROGUE                          ║
╚══════════════════════════════════════════════════════════════════╝

Enter your name [Alice]: █

(Loaded from ENV VAR or config, can override)

╔══════════════════════════════════════════════════════════════════╗
║                    CHOOSE YOUR CLASS                             ║
╚══════════════════════════════════════════════════════════════════╝

1. Warrior - Strong melee fighter
   HP: 30  Attack: 5  Defense: 3
   Abilities: Power Strike

2. Rogue - Agile explorer
   HP: 20  Attack: 4  Defense: 2
   Abilities: Backstab, Dodge

3. Mage - Arcane spellcaster
   HP: 15  Attack: 2  Defense: 1
   Abilities: Fireball, Teleport

Select class [1-3]: █

╔══════════════════════════════════════════════════════════════════╗
║                      OPTIONAL SETTINGS                           ║
╚══════════════════════════════════════════════════════════════════╝

Seed (leave empty for random): █
  Tip: Use same seed to replay exact same dungeon!

[Press Enter to Start Adventure]

Starting game...
  Player: Alice
  Class: Warrior
  Seed: random

Good luck, brave adventurer!
```

### Implementation

```python
# src/ui/game_start.py

from typing import Optional, Tuple
from ..core.config.user_config import ConfigManager
from ..core.character_class import CharacterClass, CLASS_TEMPLATES
import os
import sys


class GameStartUI:
    """
    Game start flow with player name and class selection.

    Handles:
    - Player name resolution (ENV > config > prompt)
    - Character class selection
    - Seed input (optional)
    - Config saving (if desired)
    """

    def __init__(self):
        self.config = ConfigManager.get_instance()

    def get_player_name(self, override: Optional[str] = None) -> str:
        """
        Get player name with priority resolution.

        Priority:
        1. Override (CLI argument)
        2. ENV VAR (BROGUE_PLAYER_NAME)
        3. Config file
        4. Interactive prompt
        5. Default: "Anonymous"
        """
        # 1. CLI override
        if override:
            return override

        # 2. ENV VAR
        if name := os.getenv('BROGUE_PLAYER_NAME'):
            return name

        # 3. Config file
        if name := self.config.get('player.name'):
            return name

        # 4. Interactive prompt (if TTY)
        if sys.stdin.isatty():
            print("╔" + "=" * 66 + "╗")
            print("║" + " " * 20 + "WELCOME TO BROGUE" + " " * 29 + "║")
            print("╚" + "=" * 66 + "╝")
            print()

            name = input("Enter your name: ").strip()
            if name:
                # Ask to save to config
                save = input("Save name to config? [Y/n]: ").strip().lower()
                if save != 'n':
                    self.config.set('player.name', name)
                    self.config.save()
                    print(f"✓ Saved to {self.config.config_file or '~/.broguerc'}")

                return name

        # 5. Default
        return "Anonymous"

    def select_character_class(self, override: Optional[str] = None) -> CharacterClass:
        """
        Select character class.

        Priority:
        1. Override (CLI argument --class)
        2. Config file default_class
        3. Interactive prompt
        4. Default: WARRIOR
        """
        # 1. CLI override
        if override:
            try:
                return CharacterClass(override.lower())
            except ValueError:
                pass

        # 2. Config file
        if default_class := self.config.get('player.default_class'):
            try:
                return CharacterClass(default_class.lower())
            except ValueError:
                pass

        # 3. Interactive prompt (if TTY)
        if sys.stdin.isatty():
            print()
            print("╔" + "=" * 66 + "╗")
            print("║" + " " * 21 + "CHOOSE YOUR CLASS" + " " * 28 + "║")
            print("╚" + "=" * 66 + "╝")
            print()

            for i, (class_type, template) in enumerate(CLASS_TEMPLATES.items(), 1):
                print(f"{i}. {template.name} - {template.description}")
                print(f"   HP: {template.hp}  Attack: {template.attack}  "
                      f"Defense: {template.defense}")
                print(f"   Abilities: {', '.join(template.abilities)}")
                print()

            while True:
                choice = input("Select class [1-3]: ").strip()
                if choice in ['1', '2', '3']:
                    class_list = list(CharacterClass)
                    selected = class_list[int(choice) - 1]

                    # Ask to save to config
                    save = input("Set as default class? [y/N]: ").strip().lower()
                    if save == 'y':
                        self.config.set('player.default_class', selected.value)
                        self.config.save()
                        print(f"✓ Saved to config")

                    return selected
                else:
                    print("Invalid choice. Please enter 1, 2, or 3.")

        # 4. Default
        return CharacterClass.WARRIOR

    def get_seed(self, override: Optional[str] = None) -> Optional[str]:
        """
        Get optional seed for game.

        Priority:
        1. Override (CLI argument --seed)
        2. Config file default_seed
        3. Interactive prompt
        4. None (random)
        """
        # 1. CLI override
        if override:
            return override

        # 2. Config file
        if seed := self.config.get('game.default_seed'):
            if seed:  # Not empty string
                return seed

        # 3. Interactive prompt (if TTY)
        if sys.stdin.isatty():
            print()
            print("╔" + "=" * 66 + "╗")
            print("║" + " " * 20 + "OPTIONAL SETTINGS" + " " * 29 + "║")
            print("╚" + "=" * 66 + "╝")
            print()
            print("Tip: Use same seed to replay exact same dungeon!")
            seed = input("Seed (leave empty for random): ").strip()
            return seed if seed else None

        # 4. None (random)
        return None

    def run_game_start(
        self,
        name_override: Optional[str] = None,
        class_override: Optional[str] = None,
        seed_override: Optional[str] = None,
    ) -> Tuple[str, CharacterClass, Optional[str]]:
        """
        Run full game start flow.

        Returns:
            (player_name, character_class, seed)
        """
        name = self.get_player_name(name_override)
        char_class = self.select_character_class(class_override)
        seed = self.get_seed(seed_override)

        # Display summary
        print()
        print("Starting game...")
        print(f"  Player: {name}")
        print(f"  Class: {CLASS_TEMPLATES[char_class].name}")
        print(f"  Seed: {seed or 'random'}")
        print()
        print("Good luck, brave adventurer!")
        print()

        return name, char_class, seed
```

---

## Integration with Game Class

```python
# src/core/game.py

from .character_class import CharacterClass, create_player_from_class
from .config.user_config import ConfigManager

class Game:
    # ... existing code ...

    def start_new_game(
        self,
        seed: Optional[Union[int, str]] = None,
        player_name: Optional[str] = None,
        character_class: Optional[CharacterClass] = None,
    ) -> None:
        """
        Initialize a new game.

        Args:
            seed: Optional seed for reproducibility
            player_name: Player name (for high scores)
            character_class: Character class (for stats/items)
        """
        # Initialize RNG with seed (Phase 4)
        rng = GameRNG.initialize(seed)
        logger.info(f"Starting new game with {rng.get_seed_display()}")

        # Create fresh map
        dungeon_map = Map(width=DEFAULT_MAP_WIDTH, height=DEFAULT_MAP_HEIGHT)

        # Get player starting position
        player_pos = dungeon_map.find_starting_position()

        # Create player based on class
        if character_class:
            player = create_player_from_class(
                character_class,
                x=player_pos[0],
                y=player_pos[1],
                name=player_name or "Anonymous"
            )
        else:
            # Default player (no class)
            player = Player(
                x=player_pos[0],
                y=player_pos[1],
                hp=PLAYER_STARTING_HP,
                max_hp=PLAYER_STARTING_HP,
                attack=PLAYER_STARTING_ATTACK,
                defense=PLAYER_STARTING_DEFENSE,
            )
            if player_name:
                player.stats['name'] = player_name

        # Create game state
        self.state = GameState(
            player=player,
            dungeon_map=dungeon_map,
            seed=rng.original_seed,
            player_name=player_name,
        )

        # ... rest of initialization ...
```

---

## CLI Arguments

```python
# brogue (main entry point)

import argparse

def main():
    parser = argparse.ArgumentParser(description="Brogue - A roguelike adventure")

    parser.add_argument('--name', type=str, help='Player name')
    parser.add_argument('--class', type=str, choices=['warrior', 'rogue', 'mage'],
                       help='Character class')
    parser.add_argument('--seed', type=str, help='Game seed')
    parser.add_argument('--config', type=str, help='Config file path')
    parser.add_argument('--create-config', action='store_true',
                       help='Create default config file and exit')

    args = parser.parse_args()

    # Create default config
    if args.create_config:
        from src.core.config.user_config import ConfigManager
        config = ConfigManager()
        config.create_default_config()
        print("Created default config at ~/.broguerc")
        return

    # Run game start flow
    from src.ui.game_start import GameStartUI
    ui = GameStartUI()

    player_name, char_class, seed = ui.run_game_start(
        name_override=args.name,
        class_override=args.class_,
        seed_override=args.seed,
    )

    # Start game
    game = Game()
    game.start_new_game(
        seed=seed,
        player_name=player_name,
        character_class=char_class,
    )

    # ... run game loop ...
```

---

## Example Usage

### ENV VAR Only

```bash
export BROGUE_PLAYER_NAME="Alice"
brogue
# Skips name prompt, uses "Alice"
```

### Config File

```bash
# Create default config
brogue --create-config

# Edit ~/.broguerc
nano ~/.broguerc

# Set player.name = Alice
# Set player.default_class = warrior

brogue
# Uses config settings, minimal prompts
```

### CLI Arguments

```bash
# Override everything
brogue --name Bob --class rogue --seed 12345

# Just name
brogue --name Charlie
# Still prompts for class (unless in config)
```

### Interactive (No Config)

```bash
brogue
# Prompts for:
# 1. Name
# 2. Class
# 3. Seed (optional)
# Offers to save to config
```

---

## Implementation Plan

### Phase 1: Config System

1. Create ConfigManager class
2. Support ~/.broguerc and XDG paths
3. ENV VAR overrides
4. Save/load functionality
5. Tests

### Phase 2: Character Classes

1. Define CharacterClass enum
2. Create ClassTemplate dataclass
3. Implement CLASS_TEMPLATES dict
4. create_player_from_class() function
5. Tests

### Phase 3: Game Start UI

1. Create GameStartUI class
2. Player name resolution
3. Class selection prompt
4. Seed input
5. Integration with Game class

### Phase 4: CLI Arguments

1. Add argparse to main entry point
2. --name, --class, --seed arguments
3. --create-config helper
4. --config custom path

### Phase 5: Integration

1. Update Game.start_new_game() signature
2. Update Player to store name/class
3. Update GameState to store player_name
4. Tests

---

## File Structure

```
data/
  highscores.json          # High scores

~/.broguerc                # User config (created by user)
~/.config/brogue/config    # Alternative XDG path

src/core/
  config/
    __init__.py
    user_config.py         # ConfigManager
  character_class.py       # Classes and templates

src/ui/
  game_start.py            # Game start flow

tests/unit/
  test_config.py           # Config tests
  test_character_class.py  # Class tests
```

---

## Next Steps

Ready to implement! Which part first?

1. **ConfigManager** - Foundation for everything
2. **Character Classes** - Core gameplay mechanics
3. **Game Start UI** - User-facing flow
4. **All at once** - Full integration

Your call! 🚀
