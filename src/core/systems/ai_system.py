"""
AISystem - handles monster AI behavior.

Responsibilities:
- Run AI for all monsters each turn
- Look up each monster's behaviour by name (monsters.yaml `ai: type:`)
- Provide the toolkit behaviours are written against

Behaviours are not defined here: they live in core/content/ai/ and register
with @ai_behavior (see core.extensions, docs/EXTENDING.md). The public methods
below (nearest_player, distance, in_sight, attack, move_towards, flee_from,
wander, summon) are the toolkit a behaviour calls.

Each monster's parameters are resolved per turn (params_for): the universal
`defaults` and the behaviour's section of ai_behaviors.yaml, overridden by the
monster's `ai:` block in monsters.yaml (looked up by content_id, so YAML tuning
reaches saved games), overridden by an optional per-instance `ai_params` stat.
Monster AI data is validated when the system is built (validate_monster_ai).

Speed: a monster acts move_speed times per round on average (an energy
counter; update). Morale runs before every behaviour: below its flee_threshold of max HP, a
monster flees whatever it perceives instead of acting (0 = never flees).

Perception (perceive) decides which player a monster knows about: one it can see
within aggro_range, or one it saw or was attacked by within memory_turns.
Being attacked is recorded from ATTACK_RESOLVED events on the event bus, in core
so it works in single-player and multiplayer alike. Design:
docs/architecture/AI_ARCHITECTURE.md (ADR-019).
"""

import logging
from functools import partial
from typing import Optional, Dict, Any, Iterable, List
from ..base.system import System
from ..base.entity import EntityType
from ..actions.move_action import MoveAction
from ..actions.attack_action import AttackAction
from ..actions.ability_action import AbilityAction
from ..pathfinding import get_direction
from ..config.config_loader import ConfigLoader
from ..exceptions import ContentValidationError
from ..events import GameEventType
from ..extensions import abilities, ai_behaviors
from ..geometry import chebyshev, has_line_of_sight
from .ai_behavior_registry import AIBehaviorRegistry

logger = logging.getLogger(__name__)

# ai: keys that describe the monster rather than tune its behaviour
_NOT_PARAMS = frozenset({'type', 'description'})
# ability config keys that are bookkeeping, not tuning
_NOT_ABILITY_CONFIG = frozenset({'enabled', 'description'})


def validate_monster_ai(
    monsters: Dict[str, Dict[str, Any]],
    behavior_configs: Dict[str, Dict[str, Any]],
    behavior_names: Iterable[str],
    ability_names: Iterable[str],
    universal_keys: Iterable[str] = (),
) -> List[str]:
    """Problems in monster AI data, as readable strings (empty list = valid).

    Checks every monster's `ai:` block and `abilities:` block:
    - ai.type names a registered @ai_behavior
    - every ai key is type/description, a universal key (ai_behaviors.yaml
      `defaults`), or a key of that behaviour's section
    - an ability with enabled: true, or one a behaviour brings
      (`abilities` in its section), has a registered @ability
    """
    behavior_names, ability_names = set(behavior_names), set(ability_names)
    universal = _NOT_PARAMS | set(universal_keys)
    problems = []
    for monster_id, definition in monsters.items():
        ai = definition.get('ai') or {}
        ai_type = ai.get('type', 'aggressive')
        if ai_type not in behavior_names:
            problems.append(f"{monster_id}: ai.type '{ai_type}' is not a registered AI behaviour")
        allowed = (universal | set(behavior_configs.get(ai_type, {}))) - {'abilities'}
        for key in sorted(set(ai) - allowed):
            problems.append(f"{monster_id}: ai.{key} is not a parameter of '{ai_type}' or a universal AI key")
        for name, config in (definition.get('abilities') or {}).items():
            if isinstance(config, dict) and config.get('enabled') and name not in ability_names:
                problems.append(f"{monster_id}: ability '{name}' is enabled but no @ability('{name}') exists")
    for ai_type, section in behavior_configs.items():
        for name in (section or {}).get('abilities') or {}:
            if name not in ability_names:
                problems.append(f"behaviour '{ai_type}' brings ability '{name}' but no @ability('{name}') exists")
    return problems


class AISystem(System):
    """
    AI system: runs each monster's behaviour and provides the toolkit.

    Behaviours (core/content/ai/): aggressive, defensive, neutral, coward,
    guard, berserker, sniper, summoner.
    """

    def __init__(self, context, entity_loader=None, event_bus=None):
        """
        Initialize AI system with config and behavior registry.

        Args:
            context: GameContext instance
            entity_loader: Monster definitions (params, summon); created on
                first use if not given
            event_bus: The game's EventBus; monsters learn who attacked them
                from its ATTACK_RESOLVED events. Call detach() before
                replacing this system.
        """
        super().__init__(context)
        self.config = ConfigLoader.get_config()
        self.registry = AIBehaviorRegistry()
        self._entity_loader = entity_loader
        self._register_behaviors()
        self._validate_monster_data()
        self._event_bus = event_bus
        if event_bus is not None:
            event_bus.subscribe(GameEventType.ATTACK_RESOLVED, self._on_attack, 'AISystem.provocation')

    def detach(self) -> None:
        """Stop listening to the event bus (before this system is replaced)."""
        if self._event_bus is not None:
            self._event_bus.unsubscribe(GameEventType.ATTACK_RESOLVED, self._on_attack)
            self._event_bus = None

    def _on_attack(self, event) -> None:
        """Provocation: a monster that is attacked remembers its attacker as its target."""
        defender = self.context.get_entity(event.data.get('defender_id'))
        attacker_id = event.data.get('attacker_id')
        if defender is None or defender.entity_type != EntityType.MONSTER or attacker_id == defender.entity_id:
            return
        defender.set_stat('provoked_by', attacker_id)
        defender.set_stat('provoked_turn', self.context.get_turn_count())
        self._remember(defender, attacker_id)

    def _remember(self, monster, target_id: str) -> None:
        monster.set_stat('target_id', target_id)
        monster.set_stat('target_seen_turn', self.context.get_turn_count())

    def _forget(self, monster) -> None:
        monster.set_stat('target_id', None)

    def perceive(self, monster, params: Dict[str, Any]) -> Optional['Entity']:
        """The player this monster knows about, or None.

        Sees: a living player within params['aggro_range'] and in line of sight
        (the current target wins ties, else the nearest). Remembers: the player
        it last saw or was attacked by, for params['memory_turns'] turns, even
        out of sight (it pathfinds to them). Behaviours use this, not
        nearest_player, so ranges, walls and being attacked all count.
        """
        current = monster.get_stat('target_id', None)
        reach = params.get('aggro_range', 8)
        visible = [
            p for p in self.context.get_alive_players()
            if p.x is not None and self.distance(monster, p) <= reach and self.in_sight(monster, p)
        ]
        if visible:
            target = min(visible, key=lambda p: (p.entity_id != current, self.distance(monster, p)))
            self._remember(monster, target.entity_id)
            return target

        if current is not None:
            target = self.context.get_entity(current)
            since = self.context.get_turn_count() - monster.get_stat('target_seen_turn', 0)
            if target is not None and target.is_alive and target.x is not None \
                    and since <= params.get('memory_turns', 10):
                return target
            self._forget(monster)
        return None

    def provoked_by(self, monster, params: Dict[str, Any]) -> Optional['Entity']:
        """Whoever attacked this monster within memory_turns and is still alive, or None."""
        attacker_id = monster.get_stat('provoked_by', None)
        if attacker_id is None:
            return None
        if self.context.get_turn_count() - monster.get_stat('provoked_turn', 0) > params.get('memory_turns', 10):
            return None
        attacker = self.context.get_entity(attacker_id)
        if attacker is None or not attacker.is_alive or attacker.x is None:
            return None
        return attacker

    @property
    def entity_loader(self):
        """Monster definitions (shared with the game when it passed one in)."""
        if self._entity_loader is None:
            from ..entity_loader import EntityLoader
            self._entity_loader = EntityLoader()
        return self._entity_loader

    def _validate_monster_data(self) -> None:
        """Refuse to run on monster AI data the engine would silently misread."""
        problems = validate_monster_ai(
            self.entity_loader.monsters,
            self.config.ai_behaviors.get('behaviors', {}),
            self.registry.list_behaviors(),
            abilities.names(),
            universal_keys=self.config.ai_behaviors.get('defaults', {}),
        )
        if problems:
            raise ContentValidationError(
                "Invalid monster AI data:\n  " + "\n  ".join(problems), problems=problems
            )

    def params_for(self, monster) -> Dict[str, Any]:
        """This monster's AI parameters: defaults <- behaviour <- its ai: block <- ai_params stat."""
        ai_type = monster.get_stat('ai_type', 'aggressive')
        params = dict(self.config.ai_behaviors.get('defaults', {}))
        params.update(self.config.get_ai_behavior_config(ai_type))
        params.pop('description', None)
        params.pop('abilities', None)  # see abilities_for
        definition = self.entity_loader.monsters.get(getattr(monster, 'content_id', None)) or {}
        for key, value in (definition.get('ai') or {}).items():
            if key not in _NOT_PARAMS:
                params[key] = value
        params.update(monster.get_stat('ai_params', None) or {})
        return params

    def _register_behaviors(self) -> None:
        """Register every @ai_behavior from core.content, bound to this system."""
        for name, fn in ai_behaviors.items():
            self.registry.register_python_behavior(name, partial(fn, self))
        logger.debug(f"Registered {len(self.registry.list_behaviors())} AI behaviors")

    def update(self, delta_time: float = 0) -> None:
        """Run one round of AI for all monsters (called once per game turn / MP round).

        Speed: each round a monster gains move_speed energy and takes one action
        per whole point (energy stat, carried between rounds). Speed 1.0 acts
        every round, 1.5 three times per two rounds, 0.6 three times per five.
        """
        monsters = list(self.context.get_entities_by_type(EntityType.MONSTER))

        for monster in monsters:
            if not monster.is_alive:
                continue

            # Remember where the monster started (guards leash to this point)
            if 'spawn_x' not in monster.stats:
                monster.set_stat('spawn_x', monster.x)
                monster.set_stat('spawn_y', monster.y)

            params = self.params_for(monster)
            energy = monster.get_stat('energy', 0.0) + max(0.0, params.get('move_speed', 1.0))
            while energy >= 1 and monster.is_alive:
                energy -= 1
                self._act(monster, params)
            monster.set_stat('energy', round(energy, 6))  # no float drift across many rounds

    def _act(self, monster, params: Dict[str, Any]) -> None:
        """One action: morale, else a ready and worthwhile ability, else the behaviour."""
        if self._morale_breaks(monster, params):
            return
        if self._use_ability(monster, params):
            return
        self._execute_behavior(monster, monster.get_stat('ai_type', 'aggressive'), params)

    def abilities_for(self, monster) -> Dict[str, Dict[str, Any]]:
        """This monster's usable abilities and their config, resolved live (ADR-019).

        Per ability: formulas.yaml `abilities.<name>` (shared tuning, e.g. force_bolt)
        <- what its behaviour brings (`abilities` in its ai_behaviors.yaml section)
        <- its own monsters.yaml `abilities.<name>`. A monsters.yaml entry with
        enabled: false removes one; enabled: true adds one.
        """
        ai_type = monster.get_stat('ai_type', 'aggressive')
        brought = (self.config.get_ai_behavior_config(ai_type) or {}).get('abilities') or {}
        definition = self.entity_loader.monsters.get(getattr(monster, 'content_id', None)) or {}
        own = definition.get('abilities') or {}
        shared = self.config.formulas.get('abilities', {})

        resolved = {}
        for name in list(brought) + [n for n in own if n not in brought]:
            mine = own.get(name)
            if isinstance(mine, dict) and 'enabled' in mine and not mine['enabled']:
                continue
            if name not in brought and not (isinstance(mine, dict) and mine.get('enabled')):
                continue
            config = dict(shared.get(name, {}))
            config.update(brought.get(name) or {})
            config.update({k: v for k, v in (mine or {}).items() if k not in _NOT_ABILITY_CONFIG})
            resolved[name] = config
        return resolved

    def _use_ability(self, monster, params: Dict[str, Any]) -> bool:
        """Use the first ready ability whose should_use says yes against what it perceives."""
        usable = self.abilities_for(monster)
        if not usable:
            return False
        target = self.perceive(monster, params)
        if target is None:
            return False
        turn = self.context.get_turn_count()
        cooldowns = monster.get_stat('cooldowns', {}) or {}
        for name, config in usable.items():
            effect = abilities.get(name)
            should_use = getattr(effect, 'should_use', None)
            if effect is None or should_use is None or cooldowns.get(name, 0) > turn:
                continue
            if not should_use(self.context, monster, config, target):
                continue
            outcome = AbilityAction(monster.entity_id, name, target.entity_id, config).execute(self.context)
            if outcome.is_success:
                self._apply_outcome(outcome)
                return True
        return False

    def _morale_breaks(self, monster, params: Dict[str, Any]) -> bool:
        """Morale, for every behaviour: below flee_threshold of max HP, flee what it perceives.

        Returns True if the monster fled (its behaviour does not run this turn).
        flee_threshold 0 (the default) never flees.
        """
        threshold = params.get('flee_threshold', 0.0)
        if threshold <= 0 or monster.hp / monster.max_hp >= threshold:
            return False
        target = self.perceive(monster, params)
        if target is None:
            return False
        self.flee_from(monster, target)
        return True

    @staticmethod
    def distance(a, b) -> int:
        """Range between two entities (or anything with x, y): 8-way steps (Chebyshev)."""
        return chebyshev(a.x, a.y, b.x, b.y)

    def in_sight(self, a, b) -> bool:
        """True if no wall blocks the straight line between a and b."""
        game_map = self.context.get_map()
        return has_line_of_sight(a.x, a.y, b.x, b.y, game_map.is_transparent)

    def nearest_player(self, monster) -> Optional['Entity']:
        """
        Get the nearest alive player to a monster, ignoring perception (range,
        walls, memory). Behaviours should use perceive() instead.

        Args:
            monster: Monster entity

        Returns:
            Nearest alive player entity, or None if no players alive
        """
        alive_players = self.context.get_alive_players()

        if not alive_players:
            return None

        # Find the nearest player (ties: first in the player list)
        nearest_player = None
        nearest_distance = float('inf')

        for player in alive_players:
            distance = self.distance(monster, player)
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_player = player

        return nearest_player

    def _execute_behavior(
        self,
        monster,
        ai_type: str,
        behavior_config: Dict[str, Any]
    ) -> None:
        """
        Execute AI behavior based on type.

        Behaviors come from the registry and act on the world directly.
        """
        # Get behavior from registry
        behavior_fn = self.registry.get_behavior(ai_type)

        if not behavior_fn:
            logger.warning(f"Unknown AI type: {ai_type}, using aggressive")
            behavior_fn = self.registry.get_behavior("aggressive")

        try:
            behavior_fn(monster, behavior_config)
        except Exception:
            # Content is pluggable: one buggy behaviour must not stop the turn.
            logger.exception(
                f"AI behavior '{ai_type}' failed for {monster.name}; monster skipped this turn"
            )

    def attack(self, monster, target, ranged: bool = False) -> None:
        """Attack a target (adjacent, or from range when ranged=True)."""
        action = AttackAction(monster.entity_id, target.entity_id, ranged=ranged)
        outcome = action.execute(self.context)
        self._apply_outcome(outcome)

        logger.debug(
            f"Monster {monster.name} attacked {target.name}",
            extra={'damage': outcome.events}
        )

    def _apply_outcome(self, outcome) -> None:
        """Log a monster action's messages and publish its events (ATTACK_RESOLVED,
        ENTITY_DIED), like a player action's, so telemetry and content see them (VB-66)."""
        for msg in outcome.messages:
            self.context.add_message(msg)
        if self._event_bus is not None and outcome.events:
            self._event_bus.publish_all(outcome.events)

    def flee_from(self, monster, target) -> None:
        """
        Move to the neighbouring tile that is farthest from target.

        Only steps that increase the distance are taken. A cornered monster
        (no such step) fights back if the target is adjacent, else holds still.
        """
        game_map = self.context.get_map()

        def dist2(x, y):
            return (x - target.x) ** 2 + (y - target.y) ** 2

        best, best_d = None, dist2(monster.x, monster.y)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = monster.x + dx, monster.y + dy
                if not game_map.is_walkable(nx, ny) or self.context.get_entity_at(nx, ny):
                    continue
                d = dist2(nx, ny)
                if d > best_d:
                    action = MoveAction(monster.entity_id, dx, dy)
                    if action.validate(self.context):
                        best, best_d = action, d

        if best:
            best.execute(self.context)
        elif monster.is_adjacent(target):
            self.attack(monster, target)  # cornered: bite back

    def _obstacle_tiles(self):
        """Tiles blocked by ore veins and forges (walkable terrain, solid entity)."""
        return {
            (e.x, e.y)
            for entity_type in (EntityType.ORE_VEIN, EntityType.FORGE)
            for e in self.context.get_entities_by_type(entity_type)
        }

    def move_towards(self, monster, target, leash=None) -> None:
        """
        Move toward target using pathfinding, routing around ore veins and forges.

        Args:
            leash: Optional (x, y, radius). The monster will not step to a tile
                farther than `radius` (Chebyshev) from (x, y).
        """
        game_map = self.context.get_map()
        direction = get_direction(
            game_map,
            start=(monster.x, monster.y),
            goal=(target.x, target.y),
            allow_diagonals=True,
            blocked=self._obstacle_tiles(),
        )

        if direction:
            dx, dy = direction

            if leash is not None:
                lx, ly, radius = leash
                if chebyshev(monster.x + dx, monster.y + dy, lx, ly) > radius:
                    return  # Next step leaves the leash: hold position

            action = MoveAction(monster.entity_id, dx, dy)

            if action.validate(self.context):
                outcome = action.execute(self.context)

                # Only log if movement failed (unexpected)
                if outcome.result.value != 'success':
                    logger.debug(
                        f"Monster {monster.name} failed to move",
                        extra={'reason': outcome.messages}
                    )

    def wander(self, monster) -> None:
        """Random movement onto a free tile (never a bump attack on whoever stands there)."""
        rng = self.context.get_rng()

        # 50% chance to stand still (monsters don't always move)
        if rng.random() < 0.5:
            return

        # Pick random direction
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        rng.shuffle(directions)

        game_map = self.context.get_map()
        for dx, dy in directions:
            new_x = monster.x + dx
            new_y = monster.y + dy

            if game_map.is_walkable(new_x, new_y) and not self.context.get_entity_at(new_x, new_y):
                action = MoveAction(monster.entity_id, dx, dy)
                if action.validate(self.context):
                    action.execute(self.context)
                    return

    def summon(self, monster, monster_id: str):
        """Create `monster_id` on a free tile next to `monster`; None if there is none.

        Used by behaviours that call for help. The new monster is added to the
        world and acts from the next turn.
        """
        from ..spawning.entity_spawner import EntitySpawner

        minion = self.entity_loader.create_monster(
            monster_id, monster.x, monster.y, floor=self.context.get_floor()
        )
        occupied = {
            (e.x, e.y) for e in self.context.game_state.entities.values() if e.x is not None
        }
        if not EntitySpawner._claim_free_tile(
            minion, occupied, self.context.get_map(), max_radius=3
        ):
            return None
        self.context.add_entity(minion)
        return minion
