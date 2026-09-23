"""
Game bootstrap — builds the player, initial game state, initial entities,
and per-game subsystems for a Game instance.

Extracted from Game to separate "how do we stand up a game world" from
Game's role as the turn-orchestration/persistence facade. Used by both
Game.start_new_game() (fresh state) and Game.load_game() (restored state
still needs fresh subsystems).
"""
import logging
from typing import Dict, List, Optional, Tuple

from .actions.action_factory import ActionFactory
from .base.game_context import GameContext
from .entities import Player, OreVein
from .entity_loader import EntityLoader
from .floor_manager import FloorManager
from .game_state import GameState
from .spawning import EntitySpawner
from .turn_processor import TurnProcessor
from .world import Map

logger = logging.getLogger(__name__)


class GameBootstrapper:
    """Builds the player, initial entities, and per-game subsystems for a Game instance."""

    def __init__(self, config, entity_loader: EntityLoader):
        self.config = config
        self.entity_loader = entity_loader

    def create_player(
        self,
        player_pos: Tuple[int, int],
        player_name: Optional[str],
        character_class: Optional['CharacterClass'],
    ) -> Player:
        """Create player entity based on class or defaults."""
        if character_class:
            from .character_class import create_player_from_class
            player = create_player_from_class(
                character_class,
                x=player_pos[0],
                y=player_pos[1],
                name=player_name or "Anonymous"
            )
            logger.info(f"Created {character_class.value} player: {player_name}")
        else:
            # Get starting stats from config
            starting_stats = self.config.game_constants['player']['starting_stats']
            starting_hp = starting_stats['hp']
            starting_attack = starting_stats['attack']
            starting_defense = starting_stats['defense']

            player = Player(
                x=player_pos[0],
                y=player_pos[1],
                hp=starting_hp,
                max_hp=starting_hp,
                attack=starting_attack,
                defense=starting_defense,
            )
            if player_name:
                player.stats['name'] = player_name
                logger.info(f"Created default player: {player_name}")
        return player

    def initialize_game_state(
        self,
        player: Player,
        dungeon_map: Map,
        player_name: Optional[str],
        is_legacy_run: bool,
        seed,
    ) -> Tuple[GameState, GameContext]:
        """Build GameState and GameContext for a fresh game."""
        state = GameState(
            player=player,
            dungeon_map=dungeon_map,
            seed=seed,
            # VB-18: share the map's own RNG instance rather than defaulting
            # to the process-global singleton -- dungeon_map was already
            # constructed with the game's dedicated GameRNG.
            rng=dungeon_map.rng,
        )
        state.player_name = player_name or "Anonymous"
        state.run_type = "legacy" if is_legacy_run else "pure"
        context = GameContext(state)
        return state, context

    def add_legacy_ore(self, player: Player, withdrawn_ore: 'LegacyOre') -> None:
        """Add legacy ore from vault to player inventory."""
        legacy_ore_entity = OreVein(
            x=player.x,
            y=player.y,
            ore_type=withdrawn_ore.ore_type,
            hardness=withdrawn_ore.hardness,
            conductivity=withdrawn_ore.conductivity,
            malleability=withdrawn_ore.malleability,
            purity=withdrawn_ore.purity,
            density=withdrawn_ore.density,
        )
        legacy_ore_entity.stats['mining_turns_remaining'] = 0
        player.inventory.append(legacy_ore_entity)
        logger.info(
            f"Added legacy ore to inventory: {withdrawn_ore.ore_type} "
            f"(Purity: {withdrawn_ore.purity})"
        )

    def spawn_entities(
        self, spawner: EntitySpawner, floor: int, dungeon_map: Map
    ) -> Dict[str, List]:
        """Spawn all initial entities for the floor."""
        monsters = spawner.spawn_monsters_for_floor(floor, dungeon_map)
        ore_veins = spawner.spawn_ore_veins_for_floor(floor, dungeon_map)
        forges = spawner.spawn_forges_for_floor(floor, dungeon_map)

        # Spawn special room entities
        special_entities = spawner.spawn_special_room_entities(floor, dungeon_map)
        monsters.extend(special_entities['monsters'])
        ore_veins.extend(special_entities['ores'])

        return {'monsters': monsters, 'ore_veins': ore_veins, 'forges': forges}

    def display_welcome_messages(
        self, state: GameState, forges: list, withdrawn_ore: Optional['LegacyOre']
    ) -> None:
        """Display initial game messages."""
        state.add_message("Welcome to Veinborn! Mine ore and craft weapons.")
        state.add_message("Use arrow keys or HJKL to move. Bump into monsters to attack.")

        if forges:
            state.add_message(f"Find the {forges[0].name} to craft equipment!")

        if withdrawn_ore:
            state.add_message(
                f"You start with {withdrawn_ore.get_quality_tier()} "
                f"{withdrawn_ore.ore_type} ore from the Legacy Vault!"
            )
            state.add_message("This is a Legacy run. Good luck!")

    def initialize_subsystems(
        self, context: GameContext
    ) -> Tuple[EntitySpawner, TurnProcessor, FloorManager, ActionFactory]:
        """
        Build the per-game subsystems (spawner, turn processor, floor
        manager, action factory) once state/context exist.

        Used by both Game.start_new_game() (after creating new state) and
        Game.load_game() (after loading saved state).
        """
        spawner = EntitySpawner(self.config, self.entity_loader)

        hp_regen_config = self.config.game_constants['player']['health_regeneration']
        hp_regen_interval = hp_regen_config['interval_turns']
        hp_regen_amount = hp_regen_config['amount']

        turn_processor = TurnProcessor(context, hp_regen_interval, hp_regen_amount)
        floor_manager = FloorManager(context, spawner)
        action_factory = ActionFactory(context)

        return spawner, turn_processor, floor_manager, action_factory
