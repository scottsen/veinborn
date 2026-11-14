"""
Render snapshot: one plain-data description of the game for any frontend.

`build_snapshot(state)` turns live domain objects (GameState, Entity, Map) into
serializable views. The Textual widgets render from it and the multiplayer
server can send it, so no frontend reads domain objects or re-derives totals
(gear-inclusive attack/defense, xp to next level, ability cooldowns).

Pure: building a snapshot changes nothing. It shows what the single-player TUI
shows today (every entity on the floor); `viewer` is the hook where fog of war
or a second player's point of view will filter, and is None for "the player".
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from .base.entity import EntityType
from . import fog
from .equipment import gear_bonus, gear_slot, gear_total


@dataclass
class ItemView:
    entity_id: object
    content_id: Optional[str]
    name: str
    item_type: str
    slot: Optional[str] = None  # 'weapon' | 'armor' | 'shield' | 'ring' if it can be worn (core.equipment.gear_slot)
    bonus: int = 0              # its bonus in that slot (attack for weapons, defense otherwise)
    usable: bool = False        # a built effect: the pack screen offers Use (potion, food, later scrolls)
    ore: Optional[Dict[str, int]] = None   # raw ore only: the properties recipes read (VB-111)
    part: Optional[Dict] = None            # a crafted part only: {'slot', 'ore', 'stats'} (VB-116)

    @property
    def in_ore_bag(self) -> bool:
        """Raw ore and boss materials count against the ore bag, not the pack (Player.uses_ore_bag)."""
        return self.ore is not None or self.item_type == 'material'
    stats: Dict[str, int] = field(default_factory=dict)   # wearable gear: every core stat it has (VB-126)


@dataclass
class EntityView:
    """Anything standing on the map that is not the viewer: monsters, ore, items, forges, NPCs."""
    entity_id: object
    entity_type: str            # EntityType value, e.g. 'monster'
    content_id: Optional[str]
    name: str
    x: int
    y: int
    hp: int
    max_hp: int
    symbol: str                 # terminal default; VB-79 maps entity_type + content_id instead
    color: str
    alive: bool = True
    item_type: Optional[str] = None   # items on the map only
    info: Dict = field(default_factory=dict)   # examine facts (VB-129): survey numbers, a monster's attack/defense, an item's stats


@dataclass
class AbilityView:
    name: str
    cooldown_remaining: int     # turns until ready; 0 = ready
    aimed: bool = False         # takes a target (a bolt); heal and the like do not
    targets: List[object] = field(default_factory=list)   # aimed: every hostile it could hit now (range + sight)

    @property
    def ready(self) -> bool:
        return self.cooldown_remaining <= 0


@dataclass
class EffectView:
    name: str
    label: str
    turns_left: int
    magnitude: int
    per_turn: bool = False      # the magnitude applies every turn (regeneration), not for the whole duration


@dataclass
class RecipeView:
    """One craftable recipe as the viewer stands at a forge (VB-109): what it needs, whether the
    pack covers it, and the stats a craft now would give."""
    recipe_id: str
    name: str
    slot: str                   # 'weapon' | 'armor' | ...
    requires: str               # e.g. '3x copper ore'
    craftable: bool
    reason: Optional[str] = None            # why not, when not craftable
    stats: Dict[str, int] = field(default_factory=dict)   # preview, only when craftable
    ore_count: int = 0                                  # how many ore a craft spends
    ore_ids: List[object] = field(default_factory=list)      # the ore it spends by default (best)
    ore_choices: List[object] = field(default_factory=list)  # every carried ore it could use
    # Crafting v2 (VB-116). kind 'part' spends ore like any recipe (ore_* above); 'assembly'
    # spends carried parts instead: one per required slot, optionally a gem.
    kind: str = 'item'                                       # 'item' | 'part' | 'assembly'
    required_slots: List[str] = field(default_factory=list)  # assembly: slots a craft must fill
    optional_slots: List[str] = field(default_factory=list)  # assembly: slots that may stay empty
    part_ids: List[object] = field(default_factory=list)     # assembly: the parts it spends by default (best per required slot)
    part_choices: Dict[str, List[object]] = field(default_factory=dict)   # assembly: carried parts by slot


@dataclass
class PlayerView:
    entity_id: object
    name: str
    x: int
    y: int
    hp: int
    max_hp: int
    attack: int                 # totals, include equipped gear
    defense: int
    level: int
    xp: int
    xp_next: Optional[int]
    weapon: Optional[ItemView]
    armor: Optional[ItemView]
    shield: Optional[ItemView]
    ring: Optional[ItemView]
    inventory: List[ItemView]
    inventory_capacity: int
    abilities: List[AbilityView]
    symbol: str
    color: str
    alive: bool = True          # False for a dead viewer who is spectating
    effects: List[EffectView] = field(default_factory=list)   # active status effects (VB-107)
    forge_id: Optional[object] = None    # a forge within reach (adjacent or underfoot), else None
    recipes: List[RecipeView] = field(default_factory=list)   # filled only while forge_id is set
    accuracy: int = 0           # to-hit bonus from worn gear (VB-126)
    spell_power: int = 0        # direct-damage spell bonus from worn gear
    gold: int = 0               # a counter (VB-74), no longer pack items
    ore_capacity: int = 30      # the ore bag's size (VB-131): ore and materials do not use pack slots

    @property
    def bag(self) -> List[ItemView]:
        """Ore and boss materials carried (the ore bag), in pickup order."""
        return [i for i in self.inventory if i.in_ore_bag]

    @property
    def pack(self) -> List[ItemView]:
        """Everything carried that is not in the ore bag."""
        return [i for i in self.inventory if not i.in_ore_bag]


@dataclass
class PartyMemberView:
    """One seat in a multiplayer party (empty party in single-player)."""
    player_id: str
    name: str
    player_class: str
    entity_id: object
    alive: bool = True
    connected: bool = True
    grace_left: Optional[int] = None   # seconds until a disconnected seat is dropped (None: not in grace)


@dataclass
class RoundView:
    """Where the current round stands (multiplayer): who has acted, who is still owed."""
    number: int
    waiting_on: List[str] = field(default_factory=list)   # entity ids still owed an action
    acted: List[str] = field(default_factory=list)        # entity ids that have acted


@dataclass
class MapView:
    width: int
    height: int
    tiles: List[str]            # row-major, one TileType value char per tile (same as Map.to_dict);
                                # fog:UNSEEN (' ') where the viewer has never seen the tile
    lit: List[str] = field(default_factory=list)   # fog: '1' where the tile is in sight now,
                                                   # '0' remembered; empty when the map is revealed


@dataclass
class Snapshot:
    turn: int
    floor: int
    game_over: bool
    victory: bool
    player: PlayerView
    entities: List[EntityView]
    map: MapView
    messages: List[str] = field(default_factory=list)
    message_count: int = 0      # lines ever logged (monotonic): a client tells new lines from repeats
    party: List[PartyMemberView] = field(default_factory=list)
    round: Optional[RoundView] = None
    reveal_map: bool = False    # dev switch on: no fog, the sidebar says so

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Snapshot':
        """Rebuild a snapshot from `to_dict()` output (after a JSON round trip)."""
        return cls(
            turn=data['turn'],
            floor=data['floor'],
            game_over=data['game_over'],
            victory=data['victory'],
            player=_player_from_dict(data['player']),
            entities=[EntityView(**e) for e in data['entities']],
            map=MapView(**data['map']),
            messages=list(data.get('messages', [])),
            message_count=data.get('message_count', 0),
            party=[PartyMemberView(**m) for m in data.get('party', [])],
            round=RoundView(**data['round']) if data.get('round') else None,
            reveal_map=data.get('reveal_map', False),
        )

    def entity_at(self, x: int, y: int, entity_type: str) -> Optional[EntityView]:
        for e in self.entities:
            if e.entity_type == entity_type and e.x == x and e.y == y:
                return e
        return None


def _item_from_dict(data) -> Optional[ItemView]:
    return ItemView(**data) if data else None


def _player_from_dict(data: Dict) -> PlayerView:
    fields = dict(data)
    for slot in ('weapon', 'armor', 'shield', 'ring'):
        fields[slot] = _item_from_dict(fields.get(slot))
    fields['inventory'] = [_item_from_dict(i) for i in fields.get('inventory', [])]
    fields['abilities'] = [AbilityView(**a) for a in fields.get('abilities', [])]
    fields['effects'] = [EffectView(**e) for e in fields.get('effects', [])]
    fields['recipes'] = [RecipeView(**r) for r in fields.get('recipes', [])]
    return PlayerView(**fields)


def _item(item) -> Optional[ItemView]:
    if item is None:
        return None
    from .actions.use_item_action import usable_effect
    from .crafting import ore_properties, part_info
    from .equipment import core_stats
    slot = gear_slot(item)
    ore = ore_properties(item)
    return ItemView(
        item.entity_id, item.content_id, item.name, _item_type(item),
        slot=slot, bonus=gear_bonus(item, slot) if slot else 0,
        usable=usable_effect(item) is not None,
        ore=ore,
        part=part_info(item),
        stats=core_stats(item) if slot else {},
    )


def _item_type(item) -> str:
    """Mined ore carries no item_type stat (autopickup reads it, so it stays unset); it
    still lists as 'ore', not 'unknown'."""
    from .crafting import is_ore_item
    return item.get_stat('item_type', None) or ('ore' if is_ore_item(item) else 'unknown')


def _entity_info(e) -> Dict:
    """What examine can say about an entity beyond its name (see core.examine)."""
    kind = e.entity_type
    if kind == EntityType.ORE_VEIN:
        if not e.get_stat('surveyed'):
            return {'surveyed': False}
        from .crafting import ORE_PROPERTIES
        return {'surveyed': True, 'mining_turns': e.get_stat('mining_turns'),
                'ore': {name: int(e.get_stat(name, 50)) for name in ORE_PROPERTIES}}
    if kind == EntityType.MONSTER:
        return {'attack': getattr(e, 'attack', 0), 'defense': getattr(e, 'defense', 0),
                'xp': e.get_stat('xp_reward', 0), 'ai': e.get_stat('ai_type', '')}
    if kind == EntityType.ITEM:
        from .crafting import part_info
        from .equipment import core_stats
        return {'part': part_info(e), 'stats': core_stats(e)}
    return {}


def _etype(entity) -> str:
    t = entity.entity_type
    return t.value if hasattr(t, 'value') else str(t)


def _abilities(player, turn: int, state=None) -> List[AbilityView]:
    from .extensions import abilities as registry
    cooldowns = player.get_stat('cooldowns', {})
    views = []
    for name in player.get_stat('abilities', []):
        if name not in registry:
            continue
        view = AbilityView(name, max(0, cooldowns.get(name, 0) - turn))
        reach = getattr(registry.get(name), 'aim_range', None)
        if reach is not None and state is not None:
            view.aimed = True
            view.targets = _ability_targets(state, player, name, reach)
        views.append(view)
    return views


def _ability_targets(state, player, name: str, default_range: int) -> List[object]:
    """Ids of the hostiles `name` could hit now, nearest first: the same rule the cast uses."""
    from .base.game_context import GameContext
    from .config.config_loader import ConfigLoader
    from .geometry import chebyshev
    from .targeting import valid_target
    try:
        reach = ConfigLoader.get_config().get_ability_config(name).get('range', default_range)
    except KeyError:
        reach = default_range
    context = GameContext(state)
    hits = [e for e in context.hostiles_of(player) if valid_target(context, player, e, reach)]
    return [e.entity_id for e in sorted(hits, key=lambda e: chebyshev(player.x, player.y, e.x, e.y))]


def _effects(player) -> List[EffectView]:
    from .extensions import status_effects
    return [
        EffectView(e['name'], getattr(status_effects.get(e['name']), 'label', e['name']),
                   e['turns_left'], e['magnitude'],
                   getattr(status_effects.get(e['name']), 'per_turn', False))
        for e in (player.stats.get('effects') or [])
    ]


def _forge_in_reach(state, player):
    """The forge a craft would use (CraftAction needs one adjacent), else None."""
    return next((e for e in state.entities.values()
                 if e.entity_type == EntityType.FORGE and player.is_adjacent(e)), None)


def _recipe_requires(manager, recipe, inventory=()) -> str:
    """What a craft needs, in a line: '2x metal ore', '1x mithril/adamantite ore', or an
    assembly's parts ('Blade + Hilt (+ Focus Gem)'); a boss material adds ' + <id>'."""
    if recipe.kind == 'assembly':
        names = [manager.get_recipe(pid).display_name for pid in recipe.assembly_parts.values()]
        requires = " + ".join(names)
        if recipe.optional_slots:
            gems = [r.display_name for r in manager.get_all_recipes()
                    if r.kind == 'part' and r.part_slot in recipe.optional_slots]
            requires += f" (+ {' / '.join(gems)})"
    else:
        types = recipe.accepted_ore_types()
        kinds = 'metal' if types == list(manager.METALS) else "/".join(types)
        requires = f"{recipe.get_required_ore_count()}x {kinds} ore"
    special = recipe.get_special_requirement()
    if not special:
        return requires
    from .crafting import material_name
    have = any(getattr(i, 'content_id', None) == special for i in inventory)
    return f"{requires} + {material_name(special)} ({'carried' if have else 'missing'})"


def _recipes(player, floor: int) -> List[RecipeView]:
    """Every recipe, craftable ones first (then by name), judged against the viewer's pack."""
    from .actions.craft_action import CraftAction
    manager = CraftAction.get_recipe_manager()
    views = []
    for recipe in manager.get_all_recipes():
        ok, reason = manager.can_craft(recipe.recipe_id, player.inventory, floor)
        view = RecipeView(
            recipe.recipe_id, recipe.display_name, recipe.equipment_slot,
            _recipe_requires(manager, recipe, player.inventory), ok, reason,
            manager.preview_stats(recipe.recipe_id, player.inventory) or {} if ok else {},
            kind=recipe.kind,
        )
        if recipe.kind == 'assembly':
            view.required_slots = list(recipe.assembly_parts)
            view.optional_slots = list(recipe.optional_slots)
            view.part_choices = {slot: [i.entity_id for i in items] for slot, items
                                 in manager.part_choices(recipe, player.inventory).items()}
            if ok:
                view.part_ids = [i.entity_id for i in manager.parts_for(recipe, player.inventory)]
        else:
            best = manager.ore_for(recipe, player.inventory) if ok else []
            view.ore_count = recipe.get_required_ore_count()
            view.ore_ids = [i.entity_id for i in best]
            view.ore_choices = [i.entity_id for i in manager.ore_choices(recipe, player.inventory)]
        views.append(view)
    return sorted(views, key=lambda r: (not r.craftable, r.name))


def _player_view(player, turn: int, state=None) -> PlayerView:
    next_xp = player.xp_for_next_level() if hasattr(player, 'xp_for_next_level') else None
    return PlayerView(
        entity_id=player.entity_id,
        name=player.name,
        x=player.x, y=player.y,
        hp=player.hp, max_hp=player.max_hp,
        attack=player.get_total_attack() if hasattr(player, 'get_total_attack') else player.attack,
        defense=player.get_total_defense() if hasattr(player, 'get_total_defense') else player.defense,
        level=player.get_stat('level', 1),
        xp=player.get_stat('xp', 0),
        xp_next=next_xp or None,
        weapon=_item(getattr(player, 'equipped_weapon', None)),
        armor=_item(getattr(player, 'equipped_armor', None)),
        shield=_item(getattr(player, 'equipped_shield', None)),
        ring=_item(getattr(player, 'equipped_ring', None)),
        inventory=[_item(i) for i in player.inventory],
        inventory_capacity=player.get_stat('inventory_capacity', getattr(player, 'MAX_INVENTORY', 20)),
        abilities=_abilities(player, turn, state),
        symbol=player.display_symbol,
        color=player.display_color,
        alive=player.is_alive,
        effects=_effects(player),
        accuracy=gear_total(player, 'accuracy'),
        spell_power=gear_total(player, 'spell_power'),
        gold=getattr(player, 'gold', 0),
        ore_capacity=getattr(player, 'MAX_ORE_BAG', 30),
    )


def build_snapshot(state, viewer=None, message_count: int = 20) -> Snapshot:
    """Snapshot of `state` as seen by `viewer` (default: state.player).

    Fog of war (VB-105): unless `state.reveal_map` is on, the viewer gets only the terrain
    they have seen, monsters and items only while in sight, and ore veins and forges where
    they remember the tile. Other players are always shown (the party).
    """
    viewer = viewer or state.player
    game_map = state.dungeon_map
    reveal = state.reveal_map
    explored = lit = None
    if not reveal:
        lit = fog.observe(game_map, viewer.entity_id, viewer.x, viewer.y)
        explored = game_map.explored_by[viewer.entity_id]

    def shown(e) -> bool:
        if reveal or e.entity_type == EntityType.PLAYER:
            return True
        if e.entity_type in (EntityType.ORE_VEIN, EntityType.FORGE):
            return (e.x, e.y) in explored
        return (e.x, e.y) in lit

    entities = [
        EntityView(
            entity_id=e.entity_id, entity_type=_etype(e), content_id=e.content_id,
            name=e.name, x=e.x, y=e.y, hp=e.hp, max_hp=e.max_hp,
            symbol=e.display_symbol, color=e.display_color, alive=e.is_alive,
            item_type=_item_type(e) if e.entity_type == EntityType.ITEM else None,
            info=_entity_info(e),
        )
        for e in state.entities.values()
        if e.entity_id != viewer.entity_id and shown(e)
    ]
    player_view = _player_view(viewer, state.turn_count, state)
    forge = _forge_in_reach(state, viewer)
    if forge is not None:
        player_view.forge_id = forge.entity_id
        player_view.recipes = _recipes(viewer, state.current_floor)
    tiles = game_map.to_dict()['tiles']
    lit_rows = []
    if not reveal:
        tiles = [
            ''.join(c if (x, y) in explored else fog.UNSEEN for x, c in enumerate(row))
            for y, row in enumerate(tiles)
        ]
        lit_rows = [
            ''.join('1' if (x, y) in lit else '0' for x in range(game_map.width))
            for y in range(game_map.height)
        ]
    return Snapshot(
        turn=state.turn_count,
        floor=state.current_floor,
        game_over=state.game_over,
        victory=state.victory,
        player=player_view,
        entities=entities,
        map=MapView(game_map.width, game_map.height, tiles, lit_rows),
        messages=state.get_recent_messages(message_count),
        message_count=state.message_count,
        reveal_map=reveal,
    )
