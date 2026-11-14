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
from .equipment import gear_bonus, gear_slot


@dataclass
class ItemView:
    entity_id: object
    content_id: Optional[str]
    name: str
    item_type: str
    slot: Optional[str] = None  # 'weapon' | 'armor' | 'shield' if it can be worn (core.equipment.gear_slot)
    bonus: int = 0              # its bonus in that slot (attack for weapons, defense otherwise)


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


@dataclass
class AbilityView:
    name: str
    cooldown_remaining: int     # turns until ready; 0 = ready

    @property
    def ready(self) -> bool:
        return self.cooldown_remaining <= 0


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
    inventory: List[ItemView]
    inventory_capacity: int
    abilities: List[AbilityView]
    symbol: str
    color: str
    alive: bool = True          # False for a dead viewer who is spectating


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
    for slot in ('weapon', 'armor', 'shield'):
        fields[slot] = _item_from_dict(fields.get(slot))
    fields['inventory'] = [_item_from_dict(i) for i in fields.get('inventory', [])]
    fields['abilities'] = [AbilityView(**a) for a in fields.get('abilities', [])]
    return PlayerView(**fields)


def _item(item) -> Optional[ItemView]:
    if item is None:
        return None
    slot = gear_slot(item)
    return ItemView(
        item.entity_id, item.content_id, item.name, item.get_stat('item_type', 'unknown'),
        slot=slot, bonus=gear_bonus(item, slot) if slot else 0,
    )


def _etype(entity) -> str:
    t = entity.entity_type
    return t.value if hasattr(t, 'value') else str(t)


def _abilities(player, turn: int) -> List[AbilityView]:
    from .extensions import abilities as registry
    cooldowns = player.get_stat('cooldowns', {})
    return [
        AbilityView(name, max(0, cooldowns.get(name, 0) - turn))
        for name in player.get_stat('abilities', []) if name in registry
    ]


def _player_view(player, turn: int) -> PlayerView:
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
        inventory=[_item(i) for i in player.inventory],
        inventory_capacity=player.get_stat('inventory_capacity', 20),
        abilities=_abilities(player, turn),
        symbol=player.display_symbol,
        color=player.display_color,
        alive=player.is_alive,
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
            item_type=e.get_stat('item_type', 'unknown') if e.entity_type == EntityType.ITEM else None,
        )
        for e in state.entities.values()
        if e.entity_id != viewer.entity_id and shown(e)
    ]
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
        player=_player_view(viewer, state.turn_count),
        entities=entities,
        map=MapView(game_map.width, game_map.height, tiles, lit_rows),
        messages=state.get_recent_messages(message_count),
        message_count=state.message_count,
        reveal_map=reveal,
    )
