"""
AttackAction - attack another entity.

Handles:
- Combat damage calculation
- Death detection
- XP rewards
- Loot drops (NetHack-style)
- Event-ready pattern for combat log
"""

import logging
from dataclasses import dataclass
from typing import Optional
from simpleeval import simple_eval
from ..base.action import Action, ActionOutcome, ActionResult
from ..base.game_context import GameContext
from ..base.entity import EntityType
from ..loot import LootGenerator
from ..events import create_attack_event, create_entity_died_event
from ..config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


@dataclass
class AttackAction(Action):
    """Attack another entity."""

    actor_id: str
    target_id: str
    loot_generator: Optional[LootGenerator] = None  # For dependency injection

    def validate(self, context: GameContext) -> bool:
        """Check if attack is valid."""
        # Use base class helper for actor validation
        actor = self._get_and_validate_actor(context)
        if not actor:
            return False

        # Validate target (must be monster or player, alive, adjacent)
        # Note: _validate_entity now supports sets of types for flexible validation
        attackable_types = {EntityType.MONSTER, EntityType.PLAYER}
        target = self._validate_entity(
            context, self.target_id, attackable_types,
            entity_name="target", require_adjacency=True, require_alive=True
        )
        if not target:
            return False

        self._log_validation_success(
            "validated successfully",
            actor_name=actor.name,
            target_id=self.target_id,
            target_name=target.name
        )
        return True

    def execute(self, context: GameContext) -> ActionOutcome:
        """Execute attack."""
        if not self.validate(context):
            logger.error(
                f"AttackAction execution failed validation",
                extra={'actor_id': self.actor_id, 'target_id': self.target_id}
            )
            return ActionOutcome.failure("Cannot attack")

        actor, target = self._get_attacker_and_target(context)
        self._log_attack_start(actor, target)

        # Calculate and apply damage
        actual_damage = self._calculate_and_apply_damage(actor, target)
        self._log_damage(actor, target, actual_damage)

        # Build outcome with damage message
        outcome = self._build_combat_outcome(actor, target, actual_damage)

        # Handle target death if killed
        if not target.is_alive:
            self._handle_target_death(context, actor, target, outcome)

        return outcome

    def _get_attacker_and_target(self, context: GameContext):
        """Get attacker and target entities."""
        actor = context.get_entity(self.actor_id) or context.get_player()
        target = context.get_entity(self.target_id) or context.get_player()
        return actor, target

    def _log_attack_start(self, actor, target):
        """Log attack initiation."""
        logger.info(
            f"AttackAction started",
            extra={
                'actor_id': self.actor_id,
                'actor_name': actor.name,
                'actor_hp': actor.hp,
                'actor_attack': actor.attack,
                'target_id': self.target_id,
                'target_name': target.name,
                'target_hp': target.hp,
                'target_defense': target.defense,
            }
        )

    def _calculate_and_apply_damage(self, actor, target) -> int:
        """Calculate damage and apply to target using configured formula."""
        # Import Player locally to avoid circular imports
        from ..entities import Player

        # Get attack value (including equipment bonuses for Players)
        if isinstance(actor, Player):
            actor_attack = actor.get_total_attack()
        else:
            actor_attack = actor.attack

        # Get defense value (including equipment bonuses for Players)
        if isinstance(target, Player):
            target_defense = target.get_total_defense()
        else:
            target_defense = target.defense

        # Get damage formula from config
        config = ConfigLoader.get_config()
        formula = config.get_damage_formula()
        min_damage = config.get_min_damage()

        # Evaluate formula
        try:
            damage = simple_eval(
                formula,
                names={
                    'attacker_attack': actor_attack,
                    'defender_defense': target_defense,
                    'max': max,
                    'min': min,
                }
            )
        except Exception as e:
            logger.error(f"Formula evaluation failed: {e}, using fallback")
            damage = max(1, actor_attack - target_defense)

        return target.take_damage(int(damage))

    def _log_damage(self, actor, target, actual_damage: int):
        """Log damage dealt."""
        logger.info(
            f"AttackAction damage dealt",
            extra={
                'actor_id': self.actor_id,
                'actor_name': actor.name,
                'target_id': self.target_id,
                'target_name': target.name,
                'damage': actual_damage,
                'target_hp_remaining': target.hp,
            }
        )

    def _build_combat_outcome(self, actor, target, actual_damage: int) -> ActionOutcome:
        """Build outcome with damage message and event."""
        outcome = ActionOutcome.success(took_turn=True)
        outcome.messages.append(
            f"{actor.name} hits {target.name} for {actual_damage} damage!"
        )
        # Use event builder helper for type-safe event creation
        outcome.events.append(create_attack_event(
            attacker_id=self.actor_id,
            defender_id=self.target_id,
            damage=actual_damage,
            killed=not target.is_alive,
        ))
        return outcome

    def _handle_target_death(self, context: GameContext, actor, target, outcome: ActionOutcome):
        """Handle target death, XP rewards, and loot drops."""
        self._log_target_death(actor, target)

        outcome.messages.append(f"{target.name} died!")
        # Use event builder helper for type-safe event creation
        outcome.events.append(create_entity_died_event(
            entity_id=self.target_id,
            entity_name=target.name,
            killer_id=self.actor_id,
            cause="combat",
        ))

        # Award XP if player killed monster
        if actor.entity_type == EntityType.PLAYER:
            self._award_xp(actor, target, outcome)

        # Generate loot drops if target is a monster
        if target.entity_type == EntityType.MONSTER:
            self._generate_loot_drops(context, target, outcome)

    def _log_target_death(self, actor, target):
        """Log target death."""
        logger.info(
            f"AttackAction killed target",
            extra={
                'actor_id': self.actor_id,
                'actor_name': actor.name,
                'target_id': self.target_id,
                'target_name': target.name,
            }
        )

    def _award_xp(self, actor, target, outcome: ActionOutcome):
        """Award XP to player for killing target."""
        xp_reward = target.get_stat('xp_reward', 0)
        if xp_reward <= 0:
            return

        from ..entities import Player
        if not isinstance(actor, Player):
            return

        leveled_up = actor.gain_xp(xp_reward)
        logger.info(
            f"XP awarded",
            extra={
                'player_id': self.actor_id,
                'xp_reward': xp_reward,
                'leveled_up': leveled_up,
            }
        )
        outcome.messages.append(f"Gained {xp_reward} XP!")
        if leveled_up:
            outcome.messages.append(f"Level up! Now level {actor.get_stat('level')}!")

    def _generate_loot_drops(self, context: GameContext, target, outcome: ActionOutcome):
        """Generate and drop loot from killed monster."""
        if self.loot_generator is None:
            self.loot_generator = LootGenerator.get_instance()

        monster_type = self._get_monster_type(target)
        if not monster_type:
            return

        # Check if multiplayer mode (more than one player total, regardless of alive status)
        all_players = context.get_all_players()
        is_multiplayer = len(all_players) > 1

        if is_multiplayer:
            # Multiplayer: Generate personal loot for each alive player
            alive_players = context.get_alive_players()
            self._generate_personal_loot(context, target, monster_type, alive_players, outcome)
        else:
            # Single-player: Drop loot on ground (existing behavior)
            self._generate_shared_loot(context, target, monster_type, outcome)

    def _generate_personal_loot(self, context: GameContext, target, monster_type: str,
                                alive_players: list, outcome: ActionOutcome):
        """
        Generate personal loot for each alive player (multiplayer mode).

        Each player gets their own independent loot roll added directly to inventory.
        """
        floor_number = context.get_floor()
        total_items_generated = 0
        player_loot_map = {}  # Track which items each player received

        for player in alive_players:
            # Generate loot for this specific player
            items = self.loot_generator.generate_loot(monster_type, floor_number=floor_number)

            if not items:
                continue

            # Add items to player's inventory
            items_added = []
            items_dropped = []

            for item in items:
                if player.add_to_inventory(item):
                    items_added.append(item)
                else:
                    # Inventory full - drop on ground at player's position
                    item.x = player.x
                    item.y = player.y
                    context.add_entity(item)
                    items_dropped.append(item)

            # Track loot for this player
            if items_added or items_dropped:
                player_loot_map[player.entity_id] = {
                    'player_name': player.name,
                    'items_added': items_added,
                    'items_dropped': items_dropped
                }
                total_items_generated += len(items_added) + len(items_dropped)

        # Add messages and events
        if total_items_generated > 0:
            self._add_personal_loot_messages(outcome, target, player_loot_map)
            self._add_personal_loot_event(outcome, target, monster_type, player_loot_map)

            logger.info(f"Personal loot distributed from {target.name}",
                       extra={'monster_type': monster_type, 'num_players': len(player_loot_map),
                             'total_items': total_items_generated})
        else:
            logger.debug(f"No personal loot generated for any player from {target.name}",
                        extra={'monster_type': monster_type})

    def _generate_shared_loot(self, context: GameContext, target, monster_type: str,
                             outcome: ActionOutcome):
        """
        Generate shared loot placed on ground (single-player mode).

        This is the original behavior where items are placed at monster's position.
        """
        floor_number = context.get_floor()

        # Generate loot items
        dropped_items = self.loot_generator.generate_loot(monster_type, floor_number=floor_number)
        if not dropped_items:
            logger.debug(f"No loot dropped from {target.name}", extra={'monster_type': monster_type})
            return

        # Place items and update outcome
        self._place_loot_items(context, target, dropped_items)
        self._add_loot_messages(outcome, target, dropped_items)
        self._add_loot_event(outcome, target, monster_type, dropped_items)

        logger.info(f"Loot dropped from {target.name}",
                   extra={'monster_type': monster_type, 'num_items': len(dropped_items),
                         'items': [item.content_id for item in dropped_items]})

    def _get_monster_type(self, target) -> str:
        """Get monster type from target, with validation."""
        monster_type = target.content_id
        if not monster_type:
            logger.warning("Cannot generate loot: monster has no content_id",
                          extra={'target_id': self.target_id, 'target_name': target.name})
        return monster_type

    def _place_loot_items(self, context: GameContext, target, dropped_items: list):
        """Place loot items on ground at monster's position."""
        for item in dropped_items:
            item.x = target.x
            item.y = target.y
            context.add_entity(item)

    def _add_loot_messages(self, outcome: ActionOutcome, target, dropped_items: list):
        """Add loot drop messages to outcome."""
        if len(dropped_items) == 1:
            outcome.messages.append(f"{target.name} dropped: {dropped_items[0].name}")
        elif len(dropped_items) > 1:
            item_names = ', '.join(item.name for item in dropped_items)
            outcome.messages.append(f"{target.name} dropped {len(dropped_items)} items: {item_names}")

    def _add_loot_event(self, outcome: ActionOutcome, target, monster_type: str, dropped_items: list):
        """Add loot drop event with item details."""
        outcome.events.append({
            'type': 'loot_dropped',
            'monster_id': self.target_id,
            'monster_type': monster_type,
            'position': (target.x, target.y),
            'items': [
                {'entity_id': item.entity_id, 'item_id': item.content_id, 'name': item.name}
                for item in dropped_items
            ],
        })

    def _add_personal_loot_messages(self, outcome: ActionOutcome, target, player_loot_map: dict):
        """Add personal loot messages for multiplayer."""
        for player_id, loot_info in player_loot_map.items():
            player_name = loot_info['player_name']
            items_added = loot_info['items_added']
            items_dropped = loot_info['items_dropped']

            # Message for items added to inventory
            if items_added:
                if len(items_added) == 1:
                    outcome.messages.append(
                        f"{player_name} received: {items_added[0].name}"
                    )
                else:
                    item_names = ', '.join(item.name for item in items_added)
                    outcome.messages.append(
                        f"{player_name} received {len(items_added)} items: {item_names}"
                    )

            # Message for items dropped (inventory full)
            if items_dropped:
                if len(items_dropped) == 1:
                    outcome.messages.append(
                        f"{player_name}'s inventory full! {items_dropped[0].name} dropped on ground"
                    )
                else:
                    outcome.messages.append(
                        f"{player_name}'s inventory full! {len(items_dropped)} items dropped on ground"
                    )

    def _add_personal_loot_event(self, outcome: ActionOutcome, target, monster_type: str,
                                 player_loot_map: dict):
        """Add personal loot event for multiplayer."""
        outcome.events.append({
            'type': 'personal_loot_dropped',
            'monster_id': self.target_id,
            'monster_type': monster_type,
            'position': (target.x, target.y),
            'player_loot': {
                player_id: {
                    'player_name': loot_info['player_name'],
                    'items_added': [
                        {'entity_id': item.entity_id, 'item_id': item.content_id, 'name': item.name}
                        for item in loot_info['items_added']
                    ],
                    'items_dropped': [
                        {'entity_id': item.entity_id, 'item_id': item.content_id, 'name': item.name}
                        for item in loot_info['items_dropped']
                    ]
                }
                for player_id, loot_info in player_loot_map.items()
            },
        })

    def to_dict(self) -> dict:
        return {
            'action_type': 'AttackAction',
            'actor_id': self.actor_id,
            'target_id': self.target_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AttackAction':
        return cls(
            actor_id=data['actor_id'],
            target_id=data['target_id'],
        )
