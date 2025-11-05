"""
EntityLoader - loads entity definitions from YAML files.

Responsibilities:
- Load monster and ore definitions from data/entities/
- Create entity instances from YAML data
- Replace hardcoded factory methods
- Enable data-driven modding

Phase 3: Data-Driven Entities
This class eliminates hardcoded entity definitions and factory methods,
making the game fully moddable via YAML files.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

from .entities import Monster, OreVein
from .rng import GameRNG
from .exceptions import ContentValidationError

logger = logging.getLogger(__name__)


class EntityLoader:
    """
    Loads and creates entities from YAML definitions.

    Design principles:
    - Single responsibility (entity loading only)
    - Data-driven (no hardcoded entities)
    - Cache definitions for performance
    - Clear error handling for invalid YAML
    """

    def __init__(self, entities_path: Optional[str] = None):
        """
        Initialize entity loader.

        Args:
            entities_path: Path to entities directory (default: data/entities/)
        """
        if entities_path is None:
            # Default to data/entities/ relative to project root
            project_root = Path(__file__).parent.parent.parent
            entities_path = project_root / "data" / "entities"

        self.entities_path = Path(entities_path)

        # Load entity definitions
        self.monsters: Dict[str, Dict[str, Any]] = {}
        self.ores: Dict[str, Dict[str, Any]] = {}
        self.ore_generation_config: Dict[str, Any] = {}  # Cache generation data

        self._load_monsters()
        self._load_ores()

        logger.info(
            f"EntityLoader initialized: {len(self.monsters)} monsters, "
            f"{len(self.ores)} ore types"
        )

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """
        Load YAML file and return parsed data.

        Args:
            filename: YAML filename (e.g., "monsters.yaml")

        Returns:
            Parsed YAML data as dictionary

        Raises:
            ContentValidationError: If YAML file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        filepath = self.entities_path / filename

        if not filepath.exists():
            raise ContentValidationError(
                f"Entity definition file not found: {filepath}",
                filename=filename,
                path=str(filepath)
            )

        with open(filepath, 'r') as f:
            try:
                data = yaml.safe_load(f)
                logger.debug(f"Loaded {filename}: {len(data)} entries")
                return data
            except yaml.YAMLError as e:
                logger.error(f"Failed to parse {filename}: {e}")
                raise

    def _load_monsters(self) -> None:
        """Load monster definitions from monsters.yaml."""
        try:
            data = self._load_yaml("monsters.yaml")
            self.monsters = data.get("monsters", {})

            if not self.monsters:
                logger.warning("No monsters defined in monsters.yaml")
            else:
                logger.info(
                    f"Loaded {len(self.monsters)} monsters: "
                    f"{', '.join(self.monsters.keys())}"
                )
        except Exception as e:
            logger.error(f"Failed to load monsters: {e}")
            # Use empty dict so game doesn't crash
            self.monsters = {}

    def _load_ores(self) -> None:
        """Load ore definitions from ores.yaml."""
        try:
            data = self._load_yaml("ores.yaml")
            self.ores = data.get("ore_types", {})

            # PERFORMANCE: Cache generation config to avoid reloading YAML
            self.ore_generation_config = data.get("generation", {})

            if not self.ores:
                logger.warning("No ore types defined in ores.yaml")
            else:
                logger.info(
                    f"Loaded {len(self.ores)} ore types: "
                    f"{', '.join(self.ores.keys())}"
                )
        except Exception as e:
            logger.error(f"Failed to load ores: {e}")
            # Use empty dict so game doesn't crash
            self.ores = {}
            self.ore_generation_config = {}

    def create_monster(self, monster_id: str, x: int, y: int) -> Monster:
        """
        Create a monster instance from YAML definition.

        This replaces the hardcoded factory methods:
        - Monster.create_goblin()
        - Monster.create_orc()
        - Monster.create_troll()

        Args:
            monster_id: Monster ID (e.g., "goblin", "orc", "troll")
            x, y: Position coordinates

        Returns:
            Monster instance

        Raises:
            ContentValidationError: If monster_id is not defined
        """
        if monster_id not in self.monsters:
            available = ", ".join(self.monsters.keys())
            raise ContentValidationError(
                f"Unknown monster ID: '{monster_id}'. "
                f"Available monsters: {available}",
                monster_id=monster_id,
                available_monsters=list(self.monsters.keys())
            )

        # Get monster definition
        definition = self.monsters[monster_id]

        # Extract stats
        stats = definition.get("stats", {})
        hp = stats.get("hp", 10)
        attack = stats.get("attack", 5)
        defense = stats.get("defense", 1)
        xp_reward = stats.get("xp_reward", 10)

        # Get display name
        name = definition.get("name", monster_id.title())

        # Create monster instance
        monster = Monster(
            name=name,
            x=x,
            y=y,
            hp=hp,
            max_hp=hp,
            attack=attack,
            defense=defense,
            xp_reward=xp_reward,
            content_id=monster_id,
        )

        # Apply AI settings
        ai_config = definition.get("ai", {})
        ai_type = ai_config.get("type", "aggressive")
        monster.set_stat("ai_type", ai_type)

        logger.debug(
            f"Created {name} at ({x}, {y}) "
            f"[hp={hp}, atk={attack}, def={defense}, xp={xp_reward}]"
        )

        return monster

    def create_ore_vein(
        self,
        ore_type: str,
        x: int,
        y: int,
        floor: int = 1,
    ) -> OreVein:
        """
        Create an ore vein instance from YAML definition.

        This replaces OreVein.generate_random() with data-driven generation.

        Args:
            ore_type: Ore type ID (e.g., "copper", "iron", "mithril")
            x, y: Position coordinates
            floor: Floor number (used for jackpot calculation)

        Returns:
            OreVein instance with randomized properties

        Raises:
            ContentValidationError: If ore_type is not defined
        """
        if ore_type not in self.ores:
            available = ", ".join(self.ores.keys())
            raise ContentValidationError(
                f"Unknown ore type: '{ore_type}'. "
                f"Available ore types: {available}",
                ore_type=ore_type,
                available_ores=list(self.ores.keys())
            )

        # Get ore definition
        definition = self.ores[ore_type]

        # Get property ranges
        properties = definition.get("properties", {})

        # PERFORMANCE FIX: Use cached generation config instead of reloading YAML!
        # OLD CODE: generation_data = self._load_yaml("ores.yaml").get("generation", {})
        jackpot_config = self.ore_generation_config.get("jackpot", {})
        jackpot_chance = jackpot_config.get("chance", 0.05)
        rng = GameRNG.get_instance()
        is_jackpot = rng.random() < jackpot_chance

        if is_jackpot:
            # Jackpot: all properties 80-100
            jackpot_range = jackpot_config.get("quality_override", [80, 100])
            min_prop = jackpot_range[0]
            max_prop = jackpot_range[1]
            logger.debug(f"JACKPOT! {ore_type} ore with exceptional quality!")
        else:
            # Normal: use ore type's quality ranges
            quality = definition.get("quality", {})
            min_prop = quality.get("min", 20)
            max_prop = quality.get("max", 50)

        # Generate random properties
        hardness = rng.randint(min_prop, max_prop)
        conductivity = rng.randint(min_prop, max_prop)
        malleability = rng.randint(min_prop, max_prop)
        purity = rng.randint(min_prop, max_prop)
        density = rng.randint(min_prop, max_prop)

        # Create ore vein
        ore_vein = OreVein(
            ore_type=ore_type,
            x=x,
            y=y,
            hardness=hardness,
            conductivity=conductivity,
            malleability=malleability,
            purity=purity,
            density=density,
        )

        logger.debug(
            f"Created {ore_type} ore vein at ({x}, {y}) "
            f"[avg quality: {ore_vein.average_quality:.1f}, "
            f"jackpot: {is_jackpot}]"
        )

        return ore_vein

    def get_monster_ids(self) -> List[str]:
        """
        Get all available monster IDs.

        Returns:
            List of monster IDs (e.g., ["goblin", "orc", "troll"])
        """
        return list(self.monsters.keys())

    def get_ore_ids(self) -> List[str]:
        """
        Get all available ore type IDs.

        Returns:
            List of ore IDs (e.g., ["copper", "iron", "mithril", "adamantite"])
        """
        return list(self.ores.keys())

    def get_monster_definition(self, monster_id: str) -> Dict[str, Any]:
        """
        Get raw monster definition from YAML.

        Useful for UI, debugging, or advanced queries.

        Args:
            monster_id: Monster ID

        Returns:
            Monster definition dictionary

        Raises:
            ContentValidationError: If monster_id is not defined
        """
        if monster_id not in self.monsters:
            raise ContentValidationError(
                f"Unknown monster ID: '{monster_id}'",
                monster_id=monster_id
            )

        return self.monsters[monster_id].copy()

    def get_ore_definition(self, ore_type: str) -> Dict[str, Any]:
        """
        Get raw ore definition from YAML.

        Args:
            ore_type: Ore type ID

        Returns:
            Ore definition dictionary

        Raises:
            ContentValidationError: If ore_type is not defined
        """
        if ore_type not in self.ores:
            raise ContentValidationError(
                f"Unknown ore type: '{ore_type}'",
                ore_type=ore_type
            )

        return self.ores[ore_type].copy()

    def reload(self) -> None:
        """
        Reload entity definitions from YAML files.

        Useful for hot-reloading during development or modding.
        """
        logger.info("Reloading entity definitions...")
        self._load_monsters()
        self._load_ores()
        logger.info(
            f"Reload complete: {len(self.monsters)} monsters, "
            f"{len(self.ores)} ore types"
        )
