#!/usr/bin/env python3
"""Monte Carlo duels: each class vs each monster, both sides played by the real game.

The monster is driven by the real AISystem (perception, line of sight, memory,
provocation, morale, speed, abilities), on a real Map with an EventBus, so the
numbers move with data/balance/ai_behaviors.yaml, formulas.yaml and the
monsters.yaml `abilities:` blocks. The player plays the way a sensible player
would: heal below half HP, force-bolt the nearest monster when ready, otherwise
walk up and melee (rogue backstab is automatic on the first swing). A fight is
won when every monster (summons included) is dead.

Monster abilities (VB-64): --abilities picks which ones are on.
    off      as shipped (monsters.yaml enabled: false stays off)
    on       every built ability on every monster that declares it
    both     off and on side by side (default)
    lich.death_bolt,imp.fire_bolt    only these, plus the shipped variant
--set overrides one ability number, e.g. --set lich.death_bolt.damage=8
(applies to every variant that has that ability on).

--gear equips items through the real EquipAction before each fight: items.yaml
weapon/armor ids (long_sword,chainmail) or recipes.yaml recipe ids, crafted by the real
RecipeManager from ore whose properties all equal QUALITY (recipe@QUALITY, default 70),
e.g. --gear mithril_sword@80,mithril_chestplate@80. Without it the player has starting
gear only, which understates a player who has been crafting and looting.

Usage:
    python3 scripts/sim_duels.py                              # early monsters, level 1, shipped
    python3 scripts/sim_duels.py --monsters lich,imp --levels 4,8 --abilities both
    python3 scripts/sim_duels.py --monsters lich --levels 6 --set lich.death_bolt.damage=8
    python3 scripts/sim_duels.py --abilities both --json /tmp/duels.json
    python3 scripts/sim_duels.py --monsters wyvern,lich --levels 8 --gear long_sword,chainmail

Columns: win% / timeout% (max rounds, nobody died) / HP lost on a win (% of max) /
avg rounds / where the player's damage came from (monster melee, monster
abilities, summoned minions) / abilities the monsters used per fight.
"""
import argparse
import copy
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.actions.ability_action import AbilityAction  # noqa: E402
from core.actions.attack_action import AttackAction  # noqa: E402
from core.actions.craft_action import CraftAction  # noqa: E402
from core.actions.equip_action import EquipAction  # noqa: E402
from core.base.entity import Entity  # noqa: E402
from core.actions.move_action import MoveAction  # noqa: E402
from core.base.entity import EntityType  # noqa: E402
from core.base.game_context import GameContext  # noqa: E402
from core.character_class import CharacterClass, create_player_from_class  # noqa: E402
from core.config.config_loader import ConfigLoader  # noqa: E402
from core.entity_loader import EntityLoader  # noqa: E402
from core.events import EventBus  # noqa: E402
from core.extensions import abilities  # noqa: E402
from core.game_state import GameState  # noqa: E402
from core.geometry import chebyshev  # noqa: E402
from core.loot import LootGenerator  # noqa: E402
from core.pathfinding import get_direction  # noqa: E402
from core.rng import GameRNG  # noqa: E402
from core.systems.ai_system import AISystem  # noqa: E402
from core.world import Map, Tile, TileType  # noqa: E402

EARLY = "bat,goblin,spider,wolf,skeleton,imp,orc,mimic,ogre,troll"
ARENA_W, ARENA_H = 40, 21
PLAYER_X, PLAYER_Y = 5, 10


def open_arena() -> Map:
    """A walled rectangle of open floor: nothing blocks sight or movement."""
    m = Map(ARENA_W, ARENA_H)
    for x in range(ARENA_W):
        for y in range(ARENA_H):
            border = x in (0, ARENA_W - 1) or y in (0, ARENA_H - 1)
            m.tiles[x][y] = Tile(TileType.WALL if border else TileType.FLOOR)
    return m


def built_abilities():
    """Ability names the AI can use: registered and carrying a should_use hint."""
    return {n for n in abilities.names() if getattr(abilities.get(n), 'should_use', None)}


def monster_defs(base, spec, overrides):
    """A copy of the monster definitions with the abilities in `spec` switched on.

    spec: 'off', 'on', or a set of 'monster.ability' names.
    overrides: {(monster, ability): {key: value}} applied to switched-on abilities.
    """
    defs = copy.deepcopy(base)
    if spec == 'off':
        return defs
    built = built_abilities()
    for monster_id, definition in defs.items():
        for name, config in (definition.get('abilities') or {}).items():
            if name not in built or not isinstance(config, dict):
                continue
            if spec == 'on' or f"{monster_id}.{name}" in spec:
                config['enabled'] = True
                config.update(overrides.get((monster_id, name), {}))
    return defs


class TrackedAI(AISystem):
    """AISystem that records how much of the player's HP each monster action took."""

    def __init__(self, *args, duelist_id, player, **kwargs):
        super().__init__(*args, **kwargs)
        self.duelist_id = duelist_id
        self.player = player
        self.damage = {'melee': 0, 'ability': 0, 'minion': 0}
        self.ability_uses = {}  # ability name -> times used
        self._used_ability = False

    def _use_ability(self, monster, params):
        cooldowns_before = dict(monster.get_stat('cooldowns', {}) or {})
        self._used_ability = super()._use_ability(monster, params)
        if self._used_ability:
            # The ability that fired is the one whose cooldown just moved
            after = monster.get_stat('cooldowns', {}) or {}
            fired = [n for n in after if after[n] != cooldowns_before.get(n)] or ['?']
            prefix = '' if monster.entity_id == self.duelist_id else 'minion:'
            for name in fired:
                key = prefix + name
                self.ability_uses[key] = self.ability_uses.get(key, 0) + 1
        return self._used_ability

    def _act(self, monster, params):
        before = self.player.hp
        self._used_ability = False
        super()._act(monster, params)
        lost = max(0, before - self.player.hp)
        if monster.entity_id != self.duelist_id:
            self.damage['minion'] += lost
        elif self._used_ability:
            self.damage['ability'] += lost
        else:
            self.damage['melee'] += lost


def make_player(cls, level):
    p = create_player_from_class(cls, PLAYER_X, PLAYER_Y, name=cls.value)
    if level > 1:
        p.gain_xp(ConfigLoader.get_config().get_xp_for_level(level))
        p.hp = p.max_hp
    return p


def player_turn(ctx, bus, player, game_map):
    """One sensible-player action against the nearest living monster."""
    monsters = [m for m in ctx.get_entities_by_type(EntityType.MONSTER) if m.is_alive]
    if not monsters:
        return
    target = min(monsters, key=lambda m: chebyshev(player.x, player.y, m.x, m.y))
    known = player.get_stat('abilities', [])

    def run(action):
        outcome = action.execute(ctx)
        if outcome.is_success and outcome.events:
            bus.publish_all(outcome.events)  # provocation: monsters learn who hit them
        return outcome.is_success

    if 'heal' in known and player.hp * 2 <= player.max_hp:
        if run(AbilityAction(player.entity_id, 'heal')):
            return
    if 'force_bolt' in known:
        if run(AbilityAction(player.entity_id, 'force_bolt')):
            return
    if chebyshev(player.x, player.y, target.x, target.y) <= 1:
        run(AttackAction(player.entity_id, target.entity_id))
        return
    blocked = {(m.x, m.y) for m in monsters if m is not target}
    step = get_direction(game_map, start=(player.x, player.y), goal=(target.x, target.y),
                         allow_diagonals=True, blocked=blocked)
    if step:
        run(MoveAction(player.entity_id, *step))


@dataclass
class Fight:
    won: bool
    timeout: bool
    hp_lost: float  # fraction of max HP
    rounds: int
    damage: dict = field(default_factory=dict)
    ability_uses: dict = field(default_factory=dict)


ORE_PROPERTIES = ('hardness', 'conductivity', 'malleability', 'purity', 'density')
DEFAULT_QUALITY = 70


def make_gear(spec):
    """An item from an items.yaml id, or crafted from a recipe id ('recipe@quality')."""
    name, _, quality = spec.partition('@')
    if LootGenerator.get_instance().get_item_info(name) is not None and not quality:
        return LootGenerator.get_instance().create_item(name)
    manager = CraftAction.get_recipe_manager()
    recipe = manager.get_recipe(name)
    if recipe is None:
        return None
    q = int(quality) if quality else DEFAULT_QUALITY
    ore = []
    for _ in range(recipe.get_required_ore_count()):
        o = Entity(name="ore")
        o.set_stat('ore_type', recipe.get_required_ore_type())
        for prop in ORE_PROPERTIES:
            o.set_stat(prop, q)
        ore.append(o)
    return manager.create_equipment(name, ore)


def equip(ctx, player, gear):
    """Put each gear spec on the player through the real EquipAction (later ones replace earlier)."""
    for spec in gear:
        item = make_gear(spec)
        item_id = spec
        player.add_to_inventory(item)
        action = EquipAction(player.entity_id, item.entity_id)
        if not action.validate(ctx):
            raise SystemExit(f"--gear {item_id}: not equippable (not weapon, armor or shield gear)")
        action.execute(ctx)


def duel(cls, level, monster_id, loader, game_map, max_rounds=500, start_distance=1, gear=(), floor=1):
    player = make_player(cls, level)
    monster = loader.create_monster(monster_id, PLAYER_X + start_distance, PLAYER_Y, floor=floor)
    state = GameState(player=player)
    state.dungeon_map = game_map
    state.entities[player.entity_id] = player
    state.entities[monster.entity_id] = monster
    ctx = GameContext(state)
    equip(ctx, player, gear)
    bus = EventBus()
    ai = TrackedAI(ctx, entity_loader=loader, event_bus=bus,
                   duelist_id=monster.entity_id, player=player)
    ctx.register_system('ai', ai)  # summon abilities find the AI through the context
    try:
        for rounds in range(1, max_rounds + 1):
            state.turn_count += 1
            player_turn(ctx, bus, player, game_map)
            if not any(m.is_alive for m in ctx.get_entities_by_type(EntityType.MONSTER)):
                return Fight(True, False, 1 - player.hp / player.max_hp, rounds,
                             ai.damage, ai.ability_uses)
            ai.update()
            if not player.is_alive:
                return Fight(False, False, 1.0, rounds, ai.damage, ai.ability_uses)
        return Fight(False, True, 1 - player.hp / player.max_hp, max_rounds,
                     ai.damage, ai.ability_uses)
    finally:
        ai.detach()


@dataclass
class Cell:
    variant: str
    monster: str
    character_class: str
    level: int
    fights: int
    win_pct: float
    timeout_pct: float
    hp_lost_on_win_pct: float
    avg_rounds: float
    damage_melee_pct: float
    damage_ability_pct: float
    damage_minion_pct: float
    ability_uses_per_fight: dict


def summarise(variant, monster, cls, level, fights):
    n = len(fights)
    wins = [f for f in fights if f.won]
    totals = {k: sum(f.damage.get(k, 0) for f in fights) for k in ('melee', 'ability', 'minion')}
    all_damage = sum(totals.values()) or 1
    return Cell(
        variant=variant, monster=monster, character_class=cls.value, level=level, fights=n,
        win_pct=100 * len(wins) / n,
        timeout_pct=100 * sum(f.timeout for f in fights) / n,
        hp_lost_on_win_pct=100 * sum(f.hp_lost for f in wins) / len(wins) if wins else 0.0,
        avg_rounds=sum(f.rounds for f in fights) / n,
        damage_melee_pct=100 * totals['melee'] / all_damage,
        damage_ability_pct=100 * totals['ability'] / all_damage,
        damage_minion_pct=100 * totals['minion'] / all_damage,
        ability_uses_per_fight={
            name: round(sum(f.ability_uses.get(name, 0) for f in fights) / n, 2)
            for name in sorted({k for f in fights for k in f.ability_uses})
        },
    )


def parse_overrides(items):
    """['lich.death_bolt.damage=8'] -> {('lich', 'death_bolt'): {'damage': 8}}"""
    out = {}
    for item in items:
        path, _, raw = item.partition('=')
        parts = path.split('.')
        if len(parts) != 3 or not raw:
            raise SystemExit(f"--set wants monster.ability.key=value, got {item!r}")
        try:
            value = int(raw)
        except ValueError:
            try:
                value = float(raw)
            except ValueError:
                value = raw
        out.setdefault((parts[0], parts[1]), {})[parts[2]] = value
    return out


def variants_for(arg):
    if arg == 'both':
        return [('off', 'off'), ('on', 'on')]
    if arg in ('off', 'on'):
        return [(arg, arg)]
    chosen = set(arg.split(','))
    return [('off', 'off'), ('+' + arg, chosen)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fights", type=int, default=500, help="fights per cell (default 500)")
    ap.add_argument("--levels", default="1", help="comma-separated player levels (default 1)")
    ap.add_argument("--level", type=int, help="single level (same as --levels N)")
    ap.add_argument("--monsters", default=None,
                    help=f"comma-separated monster ids (default: {EARLY}; with abilities on, "
                         "the monsters that have a built ability)")
    ap.add_argument("--classes", default=None, help="comma-separated classes (default all)")
    ap.add_argument("--abilities", default=None, help="off | on | both | monster.ability,... (see top)")
    ap.add_argument("--set", action="append", default=[], metavar="MONSTER.ABILITY.KEY=VALUE")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--floor", type=int, default=1,
                    help="floor the monster appears on: its stats scale per monster_spawns.yaml floor_scaling (default 1)")
    ap.add_argument("--max-rounds", type=int, default=500)
    ap.add_argument("--start-distance", type=int, default=1,
                    help="tiles between player and monster at the start (1 = adjacent); farther "
                         "gives ranged monsters and the mage's bolt free turns")
    ap.add_argument("--gear", default="",
                    help="comma-separated items.yaml ids or recipe[@quality] to equip, "
                         "e.g. long_sword,chainmail or mithril_sword@80")
    ap.add_argument("--json", help="also write every cell to this JSON file")
    args = ap.parse_args()

    import logging
    logging.disable(logging.CRITICAL)
    GameRNG.initialize(args.seed)
    loader = EntityLoader()
    base_defs = loader.monsters
    built = built_abilities()

    ability_arg = args.abilities or 'off'
    if args.monsters:
        monsters = args.monsters.split(",")
    elif ability_arg == 'off':
        monsters = EARLY.split(",")
    else:
        monsters = [m for m, d in base_defs.items() if any(n in built for n in (d.get('abilities') or {}))]
    unknown = [m for m in monsters if m not in base_defs]
    if unknown:
        raise SystemExit(f"unknown monster(s): {', '.join(unknown)}")
    levels = [args.level] if args.level else [int(x) for x in args.levels.split(",")]
    classes = [CharacterClass(c) for c in args.classes.split(",")] if args.classes else list(CharacterClass)
    overrides = parse_overrides(args.set)
    gear = [g for g in args.gear.split(",") if g]
    unknown_gear = [g for g in gear if make_gear(g) is None]
    if unknown_gear:
        raise SystemExit(f"unknown item or recipe for --gear: {', '.join(unknown_gear)}")
    game_map = open_arena()

    cells = []
    print(f"{args.fights} fights per cell, start distance {args.start_distance}, seed {args.seed}"
          f"{', gear ' + '+'.join(gear) if gear else ''}")
    header = (f"{'monster':15} {'variant':>16} {'class':8} {'lvl':>3} {'win%':>5} {'tmo%':>5} "
              f"{'hpLost':>6} {'rounds':>6}  {'melee/abil/minion dmg%':>22}  abilities used per fight")
    print(header)
    print("-" * len(header))
    for monster_id in monsters:
        for label, spec in variants_for(ability_arg):
            loader.monsters = monster_defs(base_defs, spec, overrides)
            for level in levels:
                for cls in classes:
                    fights = [duel(cls, level, monster_id, loader, game_map,
                                   max_rounds=args.max_rounds, start_distance=args.start_distance, floor=args.floor,
                                   gear=gear)
                              for _ in range(args.fights)]
                    c = summarise(label, monster_id, cls, level, fights)
                    cells.append(c)
                    uses = " ".join(f"{k}={v}" for k, v in c.ability_uses_per_fight.items()) or "-"
                    split = f"{c.damage_melee_pct:3.0f}/{c.damage_ability_pct:3.0f}/{c.damage_minion_pct:3.0f}"
                    print(f"{monster_id:15} {label[:16]:>16} {c.character_class:8} {level:>3} "
                          f"{c.win_pct:5.0f} {c.timeout_pct:5.0f} {c.hp_lost_on_win_pct:6.0f} "
                          f"{c.avg_rounds:6.1f}  {split:>22}  {uses}")
        print()
    loader.monsters = base_defs

    if args.json:
        Path(args.json).write_text(json.dumps({
            'args': vars(args), 'cells': [asdict(c) for c in cells]}, indent=2))
        print(f"wrote {len(cells)} cells to {args.json}")


if __name__ == "__main__":
    main()
