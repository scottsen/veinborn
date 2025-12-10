#!/usr/bin/env python3
"""
Veinborn Automated Testing Bot (Fuzzer)

Plays the game automatically to find bugs. Supports multiple play styles:
- Random: Chaotic random actions (stress testing)
- Strategic: Actually tries to win (realistic gameplay)
- Hybrid: Mix of both (50/50 split)

Features:
- Intelligent perception (find monsters, threats, opportunities)
- Tactical decision-making (fight vs flee, when to heal)
- Strategic action selection (pursuit, retreat, mining)
- Game state validation (invariants)
- Crash detection and logging
- Statistical analysis (games played, avg turns survived, win rate)
- Can run overnight unattended

Usage:
    python tests/fuzz/veinborn_bot.py                    # 100 games, strategic
    python tests/fuzz/veinborn_bot.py --mode random      # Random chaos mode
    python tests/fuzz/veinborn_bot.py --mode hybrid      # Mix of both
    python tests/fuzz/veinborn_bot.py --games 1000 -v    # Verbose 1000 games
"""

try:
    import pytest
    pytestmark = pytest.mark.fuzz
except ImportError:
    # pytest not available - bot can still run standalone
    pytestmark = None


import sys
from pathlib import Path
import random
import time
import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
import traceback

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.game import Game
from core.entities import EntityType, OreVein
from core.base.entity import Entity
from core.entity_loader import EntityLoader
from core.pathfinding import get_direction, find_path

# Phase 3: Import extracted services
# Use relative imports since we're in tests/fuzz
import sys
from pathlib import Path
# Add tests directory to path for service imports
tests_path = Path(__file__).parent.parent
sys.path.insert(0, str(tests_path))

from fuzz.services.perception_service import PerceptionService
from fuzz.services.tactical_decision_service import (
    TacticalDecisionService, CombatConfig, MiningConfig
)
from fuzz.services.action_planner import ActionPlanner


@dataclass
class GameResult:
    """Per-game statistics for histogram analysis."""
    game_number: int
    character_class: str
    turns_survived: int
    floor_reached: int
    player_level: int
    monsters_killed: int
    damage_dealt: int
    damage_taken: int
    final_score: int
    ore_mined: int
    ore_surveyed: int
    jackpot_ore: int
    death_cause: str
    completed: bool
    timestamp: str


@dataclass
class BotStats:
    """Statistics from bot gameplay."""
    games_played: int = 0
    games_completed: int = 0
    crashes: int = 0
    errors: int = 0
    total_turns: int = 0
    max_turns_survived: int = 0
    max_level_reached: int = 1
    max_floor_reached: int = 1
    total_floors_descended: int = 0
    total_monsters_killed: int = 0

    # Mining statistics
    total_ore_surveyed: int = 0
    total_ore_mined: int = 0
    jackpot_ore_found: int = 0
    legacy_ore_mined: int = 0  # 80+ purity
    best_purity_found: int = 0
    ore_by_type: Dict[str, int] = None  # Counted after init

    # Crafting & Equipment statistics
    total_equipment_crafted: int = 0
    total_equipment_equipped: int = 0
    weapons_crafted: int = 0
    armor_crafted: int = 0

    # Per-game results for analysis
    game_results: List[GameResult] = None

    def __post_init__(self):
        if self.ore_by_type is None:
            self.ore_by_type = {}
        if self.game_results is None:
            self.game_results = []

    @property
    def avg_turns_per_game(self) -> float:
        return self.total_turns / max(1, self.games_played)

    @property
    def crash_rate(self) -> float:
        return self.crashes / max(1, self.games_played)


class VeinbornBot:
    """Automated game-playing bot for testing."""

    def __init__(self, verbose: bool = False, mode: str = 'strategic', player_name: str = 'Bot',
                 combat_config: Optional[CombatConfig] = None, mining_config: Optional[MiningConfig] = None):
        """
        Initialize bot.

        Args:
            verbose: Print detailed logs
            mode: Play style - 'random', 'strategic', or 'hybrid'
            player_name: Player name for high scores (default: 'Bot')
            combat_config: Combat behavior configuration (uses defaults if None)
            mining_config: Mining behavior configuration (uses defaults if None)
        """
        self.verbose = verbose
        self.mode = mode
        self.player_name = player_name
        self.stats = BotStats()
        self.error_log: List[Dict] = []

        # Phase 3: Load entity intelligence from YAML
        self.entity_loader = EntityLoader()
        self.threat_rankings = self._build_threat_rankings()

        # Phase 3: Wire up extracted services
        self.perception = PerceptionService(verbose=verbose)
        self.decisions = TacticalDecisionService(
            self.perception,
            combat_config=combat_config or CombatConfig(),
            mining_config=mining_config or MiningConfig(),
            verbose=verbose
        )
        self.planner = ActionPlanner(self.perception, self.decisions, verbose=verbose)

        if verbose:
            print(f"[BOT] Entity loader initialized:")
            print(f"  Monsters: {', '.join(self.entity_loader.get_monster_ids())}")
            print(f"  Ore types: {', '.join(self.entity_loader.get_ore_ids())}")
            print(f"  Threat rankings: {self.threat_rankings}")
            print(f"[BOT] Services initialized:")
            print(f"  PerceptionService: {self.perception}")
            print(f"  TacticalDecisionService: {self.decisions}")
            print(f"  ActionPlanner: {self.planner}")

    def log(self, message: str) -> None:
        """Log message if verbose."""
        if self.verbose:
            print(f"[BOT] {message}")

    def log_error(self, error: str, game_state: Optional[Dict] = None) -> None:
        """Log error with context."""
        self.error_log.append({
            'error': error,
            'game_state': game_state,
            'timestamp': time.time(),
        })
        print(f"[ERROR] {error}")

    def validate_game_state(self, game: Game) -> List[str]:
        """
        Validate game state invariants.

        Returns list of violations (empty if valid).
        """
        violations = []

        # Check player invariants
        if game.state.player.hp < 0:
            violations.append(f"Player HP negative: {game.state.player.hp}")

        if game.state.player.hp > game.state.player.max_hp:
            violations.append(
                f"Player HP exceeds max: {game.state.player.hp} > {game.state.player.max_hp}"
            )

        if game.state.player.hp == 0 and game.state.player.is_alive:
            violations.append("Player at 0 HP but marked alive")

        if game.state.player.hp > 0 and not game.state.player.is_alive:
            violations.append("Player has HP but marked dead")

        # Check entity invariants
        for entity in game.state.entities.values():
            if entity.hp < 0:
                violations.append(f"Entity {entity.name} has negative HP: {entity.hp}")

            if entity.hp > entity.max_hp and entity.max_hp > 0:
                violations.append(
                    f"Entity {entity.name} HP exceeds max: {entity.hp} > {entity.max_hp}"
                )

        # Check position invariants
        if game.state.player.x is not None and game.state.player.y is not None:
            if not game.state.dungeon_map.in_bounds(game.state.player.x, game.state.player.y):
                violations.append(
                    f"Player out of bounds: ({game.state.player.x}, {game.state.player.y})"
                )

        # Check inventory invariants (if player has inventory)
        if hasattr(game.state.player, 'inventory'):
            if len(game.state.player.inventory) > 20:
                violations.append(f"Inventory exceeds max: {len(game.state.player.inventory)}")

        return violations

    # ========================================================================
    # PERCEPTION LAYER - Delegated to PerceptionService
    # ========================================================================
    # Methods removed: find_monsters, find_nearest_monster, monster_in_view,
    # is_adjacent_to_monster, find_level_exit, on_stairs
    # Use: self.perception.method_name(game)

    # ========================================================================
    # ENTITY INTELLIGENCE - Phase 3 YAML-based knowledge
    # ========================================================================

    def _build_threat_rankings(self) -> Dict[str, float]:
        """
        Build threat ranking from YAML entity definitions.

        Returns dict of monster_id -> threat_score.
        """
        rankings = {}
        for monster_id in self.entity_loader.get_monster_ids():
            definition = self.entity_loader.get_monster_definition(monster_id)
            stats = definition['stats']

            # Calculate threat score (hp * attack / defense ratio)
            threat = (stats['hp'] * stats['attack']) / max(1, stats['defense'])
            rankings[monster_id] = threat

        return rankings

    def get_monster_threat_level(self, monster: Entity) -> str:
        """
        Get threat classification: 'trivial', 'manageable', 'dangerous', 'deadly'.

        Uses YAML-loaded monster stats for perfect information.
        """
        if not monster.content_id:
            return 'unknown'

        threat_score = self.threat_rankings.get(monster.content_id, 0)

        if threat_score < 30:
            return 'trivial'   # Goblins (6*3/1 = 18)
        elif threat_score < 100:
            return 'manageable'  # Orcs (12*5/2 = 30)
        elif threat_score < 200:
            return 'dangerous'  # Trolls (20*7/3 = 46.7)
        else:
            return 'deadly'     # Future boss monsters

    # Ore perception methods removed - delegated to PerceptionService
    # Methods: find_ore_veins, find_valuable_ore, find_jackpot_ore
    # Use: self.perception.method_name(game)

    # ========================================================================
    # CRAFTING & EQUIPMENT - Delegated to services
    # ========================================================================
    # Perception methods removed: find_forges, find_nearest_forge, has_craftable_ore, has_unequipped_gear
    # Decision methods removed: should_craft, should_survey_ore
    # Use: self.perception.method_name(game) or self.decisions.method_name(game)

    # ========================================================================
    # TACTICAL LAYER - Delegated to TacticalDecisionService
    # ========================================================================
    # Methods removed: can_win_fight, should_fight, should_flee, should_descend
    # Also removed: is_low_health, should_mine_strategically, should_craft, should_survey_ore
    # Use: self.decisions.method_name(game)

    # ========================================================================
    # STRATEGIC LAYER - Delegated to ActionPlanner
    # ========================================================================
    # Methods removed: move_towards, flee_from, get_smart_action, get_random_action
    # Use: self.planner.method_name(game)

    def play_one_game(self, max_turns: int = 100000) -> Dict:
        """
        Play one complete game until win or death.

        Args:
            max_turns: Safety limit to prevent infinite loops (default: 100000)

        Returns game statistics.
        """
        self.log("Starting new game...")

        try:
            game = Game()
            # Use character class if bot has one (specialized bots)
            character_class = getattr(self, 'character_class', None)
            game.start_new_game(player_name=self.player_name, character_class=character_class)

            turn = 0
            game_stats = {
                'turns': 0,
                'level': 1,
                'floor': 1,
                'monsters_killed': 0,
                'completed': False,
                'death_reason': None,
            }

            # Stuck detection
            last_position = None
            stuck_counter = 0
            stuck_threshold = 5  # Consider stuck after 5 turns in same spot

            while not game.state.game_over and turn < max_turns:
                turn += 1

                # Invalidate perception cache for new turn (performance optimization)
                self.perception.start_turn(turn)

                # Check if stuck (same position for multiple turns)
                current_position = (game.state.player.x, game.state.player.y)
                is_stuck = False
                if current_position == last_position:
                    stuck_counter += 1
                    if stuck_counter >= stuck_threshold:
                        is_stuck = True
                        self.log(f"⚠️  STUCK DETECTED at {current_position} for {stuck_counter} turns - trying random action!")
                else:
                    if stuck_counter > 0:
                        stuck_counter = 0  # Reset when position changes
                last_position = current_position

                # Validate state before action
                violations = self.validate_game_state(game)
                if violations:
                    self.log_error(
                        f"State violations on turn {turn}: {violations}",
                        game_state={
                            'turn': turn,
                            'player_hp': game.state.player.hp,
                            'player_pos': (game.state.player.x, game.state.player.y),
                        }
                    )
                    self.stats.errors += 1

                # Choose action based on mode (force random if stuck)
                if is_stuck:
                    # Try multiple random actions, validating each one
                    action_type, kwargs = None, None
                    for attempt in range(10):
                        candidate_action, candidate_kwargs = self.planner.get_random_action(game)

                        # Validate move actions (check walkability)
                        if candidate_action == 'move':
                            dx = candidate_kwargs.get('dx', 0)
                            dy = candidate_kwargs.get('dy', 0)
                            new_x = game.state.player.x + dx
                            new_y = game.state.player.y + dy
                            if game.state.dungeon_map.is_walkable(new_x, new_y):
                                action_type, kwargs = candidate_action, candidate_kwargs
                                break
                        else:
                            # Non-move actions (wait, survey, mine) - accept
                            action_type, kwargs = candidate_action, candidate_kwargs
                            break

                    # If all random attempts failed, just wait
                    if action_type is None:
                        action_type, kwargs = ('wait', {})
                        self.log("⚠️  All random actions blocked - waiting instead")

                else:
                    # Use ActionPlanner.plan_next_action which handles all modes
                    action_type, kwargs = self.planner.plan_next_action(game, mode=self.mode)

                # Execute action - keep executing instant actions until one takes a turn
                # This ensures crafted items are equipped immediately (equip is instant)
                try:
                    # Helper to track a single action's statistics
                    def track_action_stats(act_type, act_kwargs):
                        """Track statistics for a specific action."""
                        if act_type == 'survey':
                            self.stats.total_ore_surveyed += 1

                        elif act_type == 'mine':
                            # Check if we mined successfully (safely handle missing inventory)
                            if hasattr(game.state.player, 'inventory'):
                                # Ore items have ore_type in stats, not as attribute
                                ore_in_inventory = [item for item in game.state.player.inventory
                                                  if item.get_stat('ore_type') is not None]
                                prev_count = game_stats.get('prev_ore_count', 0)
                                curr_count = len(ore_in_inventory)
                                if curr_count > prev_count:
                                    ore_item = ore_in_inventory[-1]  # Most recent
                                    self.stats.total_ore_mined += 1

                                    # Track purity
                                    purity = ore_item.get_stat('purity', 0)
                                    if purity > self.stats.best_purity_found:
                                        self.stats.best_purity_found = purity

                                    # Track Legacy Vault quality
                                    if purity >= 80:
                                        self.stats.legacy_ore_mined += 1

                                    # Track by ore type
                                    ore_type = ore_item.get_stat('ore_type', 'unknown')
                                    self.stats.ore_by_type[ore_type] = self.stats.ore_by_type.get(ore_type, 0) + 1

                                game_stats['prev_ore_count'] = len(ore_in_inventory)
                            else:
                                # Player missing inventory attribute - shouldn't happen, but be defensive
                                game_stats['prev_ore_count'] = 0

                        elif act_type == 'craft':
                            # Track crafting statistics
                            if hasattr(game.state.player, 'inventory'):
                                equipment_in_inventory = [item for item in game.state.player.inventory
                                                        if item.get_stat('equipment_slot') is not None]
                                prev_equip_count = game_stats.get('prev_equipment_count', 0)
                                curr_equip_count = len(equipment_in_inventory)
                                if curr_equip_count > prev_equip_count:
                                    equipment = equipment_in_inventory[-1]  # Most recent
                                    self.stats.total_equipment_crafted += 1

                                    # Track by equipment type
                                    equipment_slot = equipment.get_stat('equipment_slot')
                                    if equipment_slot == 'weapon':
                                        self.stats.weapons_crafted += 1
                                    elif equipment_slot == 'armor':
                                        self.stats.armor_crafted += 1

                                game_stats['prev_equipment_count'] = len(equipment_in_inventory)
                            else:
                                game_stats['prev_equipment_count'] = 0

                        elif act_type == 'equip':
                            # Track equipping statistics
                            self.stats.total_equipment_equipped += 1
                            # ADD DETAILED LOGGING: Track what's being equipped with upgrade info
                            equipped_item_id = act_kwargs.get('item_id', 'unknown')
                            equipped_item = [item for item in game.state.player.inventory
                                           if item.entity_id == equipped_item_id]
                            if equipped_item:
                                item = equipped_item[0]
                                slot = item.get_stat('equipment_slot')

                                # Track upgrade vs sidegrade vs downgrade
                                is_upgrade = False
                                stat_diff = 0

                                if slot == 'weapon':
                                    new_attack = item.get_stat('attack_bonus', 0)
                                    if hasattr(game.state.player, 'equipped_weapon') and game.state.player.equipped_weapon:
                                        old_attack = game.state.player.equipped_weapon.get_stat('attack_bonus', 0)
                                        stat_diff = new_attack - old_attack
                                        is_upgrade = stat_diff > 0
                                elif slot == 'armor':
                                    new_defense = item.get_stat('defense_bonus', 0)
                                    if hasattr(game.state.player, 'equipped_armor') and game.state.player.equipped_armor:
                                        old_defense = game.state.player.equipped_armor.get_stat('defense_bonus', 0)
                                        stat_diff = new_defense - old_defense
                                        is_upgrade = stat_diff > 0

                                upgrade_type = "UPGRADE" if is_upgrade else "FIRST" if stat_diff == 0 else "DOWNGRADE"
                                self.log(f"   🎽 Equipped: {item.name} ({upgrade_type} {stat_diff:+d} | slot: {slot})")

                    # Execute first action
                    action_took_turn = game.handle_player_action(action_type, **kwargs)
                    track_action_stats(action_type, kwargs)

                    if not action_took_turn:
                        self.log(f"   ⚡ Instant action: {action_type} (no turn consumed)")

                    # Track successful instant actions for this turn
                    instant_actions_count = 0
                    max_instant_actions = 10  # Safety limit to prevent infinite loops

                    # Keep executing actions while they're instant (don't consume a turn)
                    while not action_took_turn and instant_actions_count < max_instant_actions:
                        instant_actions_count += 1

                        # Plan next action
                        action_type, kwargs = self.planner.plan_next_action(game, mode=self.mode)

                        # Execute it
                        action_took_turn = game.handle_player_action(action_type, **kwargs)
                        track_action_stats(action_type, kwargs)

                        if not action_took_turn:
                            self.log(f"   ⚡ Instant action #{instant_actions_count}: {action_type}")

                    if instant_actions_count >= max_instant_actions:
                        self.log(f"   ⚠️  Hit max instant actions limit ({max_instant_actions})!")

                except Exception as e:
                    self.log_error(
                        f"Action failed on turn {turn}: {action_type} {kwargs}",
                        game_state={
                            'error': str(e),
                            'traceback': traceback.format_exc(),
                        }
                    )
                    self.stats.errors += 1

                # Track stats
                current_level = game.state.player.get_stat('level', 1)
                if current_level > game_stats['level']:
                    self.log(f"Leveled up to {current_level}!")
                    game_stats['level'] = current_level

                current_floor = game.state.current_floor
                if current_floor > game_stats.get('floor', 1):
                    self.log(f"⬇️  Descended to floor {current_floor}!")
                    game_stats['floor'] = current_floor

                if turn % 10 == 0:
                    monster_count = len(self.perception.find_monsters(game))
                    player = game.state.player
                    nearest = self.perception.find_nearest_monster(game)
                    if nearest:
                        dx = nearest.x - player.x
                        dy = nearest.y - player.y
                        dist = (dx*dx + dy*dy) ** 0.5
                        nearest_info = f"@ ({nearest.x},{nearest.y}), dist={dist:.1f}"
                    else:
                        nearest_info = "None"
                    self.log(
                        f"Turn {turn}: Player @ ({player.x},{player.y}), HP={player.hp}/{player.max_hp}, "
                        f"Floor={game.state.current_floor}, Level={current_level}, Monsters={monster_count}, Nearest={nearest_info}"
                    )

            # Game ended
            game_stats['turns'] = turn
            game_stats['completed'] = not game.state.game_over

            if game.state.game_over:
                game_stats['death_reason'] = 'player_died'
                self.log(f"Game over on turn {turn}")
            else:
                self.log(f"Reached max turns ({max_turns})")

            return game_stats

        except Exception as e:
            self.log_error(
                f"Game crashed!",
                game_state={
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                }
            )
            self.stats.crashes += 1
            return {
                'turns': 0,
                'level': 1,
                'monsters_killed': 0,
                'completed': False,
                'death_reason': 'crash',
            }

    def run(self, num_games: int = 100, max_turns_per_game: int = 100000) -> None:
        """
        Run multiple games and collect statistics.

        Args:
            num_games: Number of games to play
            max_turns_per_game: Safety limit to prevent infinite loops (default: 100000)
        """
        print(f"\n{'='*60}")
        print(f"Veinborn Automated Testing Bot")
        print(f"{'='*60}")
        print(f"Player Name: {self.player_name}")
        print(f"Mode: {self.mode.upper()}")
        print(f"Games to play: {num_games}")
        print(f"Max turns per game: {max_turns_per_game}")
        print(f"Verbose: {self.verbose}")
        print(f"{'='*60}\n")

        start_time = time.time()

        for i in range(num_games):
            print(f"\n[Game {i+1}/{num_games}]")
            game_stats = self.play_one_game(max_turns=max_turns_per_game)

            # Update overall stats
            self.stats.games_played += 1
            self.stats.total_turns += game_stats['turns']
            self.stats.max_turns_survived = max(
                self.stats.max_turns_survived,
                game_stats['turns']
            )
            self.stats.max_level_reached = max(
                self.stats.max_level_reached,
                game_stats['level']
            )
            self.stats.max_floor_reached = max(
                self.stats.max_floor_reached,
                game_stats.get('floor', 1)
            )
            if game_stats.get('floor', 1) > 1:
                self.stats.total_floors_descended += (game_stats['floor'] - 1)

            if game_stats['completed']:
                self.stats.games_completed += 1

            # Record per-game result for histogram analysis
            character_class = getattr(self, 'character_class', None)
            class_name = character_class.value if character_class else 'unknown'

            game_result = GameResult(
                game_number=i + 1,
                character_class=class_name,
                turns_survived=game_stats['turns'],
                floor_reached=game_stats.get('floor', 1),
                player_level=game_stats.get('level', 1),
                monsters_killed=game_stats.get('monsters_killed', 0),
                damage_dealt=game_stats.get('damage_dealt', 0),
                damage_taken=game_stats.get('damage_taken', 0),
                final_score=game_stats.get('final_score', 0),
                ore_mined=game_stats.get('ore_mined', 0),
                ore_surveyed=game_stats.get('ore_surveyed', 0),
                jackpot_ore=game_stats.get('jackpot_ore', 0),
                death_cause=game_stats.get('death_reason', 'unknown'),
                completed=game_stats['completed'],
                timestamp=datetime.now().isoformat()
            )
            self.stats.game_results.append(game_result)

            # Progress update
            if (i + 1) % 10 == 0:
                self.print_progress()

        elapsed = time.time() - start_time

        # Final report
        print(f"\n{'='*60}")
        print(f"FINAL RESULTS")
        print(f"{'='*60}")
        self.print_final_report(elapsed)

        # Save per-game results to JSON for histogram analysis
        self.save_game_results()

    def print_progress(self) -> None:
        """Print progress update."""
        print(f"\nProgress: {self.stats.games_played} games")
        print(f"  Crashes: {self.stats.crashes}")
        print(f"  Errors: {self.stats.errors}")
        print(f"  Avg turns: {self.stats.avg_turns_per_game:.1f}")

    def print_final_report(self, elapsed_seconds: float) -> None:
        """Print final statistics report."""
        print(f"\nGames Played: {self.stats.games_played}")
        print(f"Games Completed: {self.stats.games_completed}")
        print(f"Crashes: {self.stats.crashes} ({self.stats.crash_rate*100:.1f}%)")
        print(f"Errors: {self.stats.errors}")
        print(f"\nTotal Turns: {self.stats.total_turns}")
        print(f"Avg Turns/Game: {self.stats.avg_turns_per_game:.1f}")
        print(f"Max Turns Survived: {self.stats.max_turns_survived}")
        print(f"Max Level Reached: {self.stats.max_level_reached}")
        print(f"Max Floor Reached: {self.stats.max_floor_reached}")
        print(f"Total Floors Descended: {self.stats.total_floors_descended}")

        # Phase 3: Mining statistics
        print(f"\n{'='*60}")
        print(f"MINING STATISTICS (Phase 3)")
        print(f"{'='*60}")
        print(f"Ore Surveyed: {self.stats.total_ore_surveyed}")
        print(f"Ore Mined: {self.stats.total_ore_mined}")
        print(f"💎 Jackpot Ore Found: {self.stats.jackpot_ore_found}")
        print(f"🏆 Legacy Vault Ore (80+): {self.stats.legacy_ore_mined}")
        print(f"Best Purity Found: {self.stats.best_purity_found}")

        if self.stats.ore_by_type:
            print(f"\nOre Mined by Type:")
            for ore_type, count in sorted(self.stats.ore_by_type.items()):
                print(f"  {ore_type}: {count}")

        # Crafting & Equipment statistics
        print(f"\n{'='*60}")
        print(f"CRAFTING & EQUIPMENT STATISTICS")
        print(f"{'='*60}")
        print(f"🔨 Equipment Crafted: {self.stats.total_equipment_crafted}")
        print(f"  ⚔️  Weapons Crafted: {self.stats.weapons_crafted}")
        print(f"  🛡️  Armor Crafted: {self.stats.armor_crafted}")
        print(f"🎽 Equipment Equipped: {self.stats.total_equipment_equipped}")

        print(f"\nTime Elapsed: {elapsed_seconds:.1f}s")
        print(f"Games/Second: {self.stats.games_played / elapsed_seconds:.2f}")

        if self.error_log:
            print(f"\n{'='*60}")
            print(f"ERRORS FOUND ({len(self.error_log)} total)")
            print(f"{'='*60}")
            for i, error in enumerate(self.error_log[:10], 1):  # Show first 10
                print(f"\n{i}. {error['error']}")
                if error['game_state']:
                    print(f"   State: {error['game_state']}")

            if len(self.error_log) > 10:
                print(f"\n... and {len(self.error_log) - 10} more errors")

        # Success message
        if self.stats.crashes == 0 and self.stats.errors == 0:
            print(f"\n🎉 NO BUGS FOUND! Game is stable!")
        else:
            print(f"\n🐛 BUGS FOUND - See errors above")

    def save_game_results(self) -> None:
        """Save per-game results to JSON for histogram analysis."""
        if not self.stats.game_results:
            return

        # Create logs directory if it doesn't exist
        logs_dir = Path(__file__).parent.parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)

        # Generate filename with timestamp and character class
        character_class = getattr(self, 'character_class', None)
        class_name = character_class.value if character_class else 'bot'
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bot_results_{class_name}_{timestamp}.json"
        filepath = logs_dir / filename

        # Convert game results to dicts
        results_data = {
            'metadata': {
                'character_class': class_name,
                'player_name': self.player_name,
                'mode': self.mode,
                'games_played': self.stats.games_played,
                'timestamp': timestamp,
            },
            'games': [asdict(result) for result in self.stats.game_results]
        }

        # Save to JSON
        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2)

        print(f"\n📊 Per-game results saved to: {filepath}")
        print(f"   {len(self.stats.game_results)} game records for histogram analysis")


def main(bot_class=None, default_class=None):
    """
    Main entry point.

    Args:
        bot_class: Custom bot class to use (default: VeinbornBot)
        default_class: Default character class for the bot (optional)
    """
    import argparse
    import logging

    parser = argparse.ArgumentParser(
        description='Veinborn automated testing bot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Play Modes:
  random      Random chaos - stress test the game with random actions
  strategic   Smart play - bot tries to win using tactics (default)
  hybrid      Mix of both - 50% smart, 50% random

Logging Levels:
  (default)   WARNING - only errors/warnings (fast performance)
  -v          INFO    - show action details (debugging gameplay)
  --debug     DEBUG   - show everything (trace level)

Examples:
  python tests/fuzz/veinborn_bot.py                    # 100 strategic games (fast)
  python tests/fuzz/veinborn_bot.py --mode random      # Random chaos
  python tests/fuzz/veinborn_bot.py --games 1000       # 1000 games (production)
  python tests/fuzz/veinborn_bot.py --games 10 -v      # 10 games with action logs
  python tests/fuzz/veinborn_bot.py --games 1 --debug  # 1 game with full trace
        """
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['random', 'strategic', 'hybrid'],
        default='strategic',
        help='Bot play mode (default: strategic)'
    )
    parser.add_argument(
        '--games',
        type=int,
        default=100,
        help='Number of games to play (default: 100)'
    )
    parser.add_argument(
        '--max-turns',
        type=int,
        default=100000,
        help='Safety limit to prevent infinite loops (default: 100000)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output (show INFO level logs - action details)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Debug output (show DEBUG level logs - full trace)'
    )
    parser.add_argument(
        '--name',
        type=str,
        default=None,
        help='Player name for high scores (default: bot-specific name)'
    )

    args = parser.parse_args()

    # Setup logging for bot tests
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Logging levels:
    # - Default (production): WARNING - only warnings/errors (fast)
    # - --verbose: INFO - show action details (debugging)
    # - --debug: DEBUG - show everything (trace)
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'bot_tests.log'),
            logging.StreamHandler()  # Also print to console
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Bot test logging initialized - mode: {args.mode}, games: {args.games}")
    logger.info(f"Log file: {log_dir / 'bot_tests.log'}")

    # Use custom bot class if provided, otherwise default VeinbornBot
    if bot_class is None:
        bot_class = VeinbornBot

    # Create bot instance
    # For specialized bots that don't use mode parameter
    if bot_class == VeinbornBot:
        bot = bot_class(verbose=args.verbose, mode=args.mode, player_name=args.name or 'Bot')
    else:
        # Specialized bots (Warrior, Rogue, Mage, Healer) handle their own defaults
        bot = bot_class(verbose=args.verbose)
        # Override name if specified
        if args.name:
            bot.player_name = args.name

    bot.run(num_games=args.games, max_turns_per_game=args.max_turns)


if __name__ == '__main__':
    main()
