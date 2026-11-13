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


@dataclass
class ItemView:
    entity_id: object
    content_id: Optional[str]
    name: str
    item_type: str


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


@dataclass
class MapView:
    width: int
    height: int
    tiles: List[str]            # row-major, one TileType value char per tile (same as Map.to_dict)


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

    def to_dict(self) -> Dict:
        return asdict(self)

    def entity_at(self, x: int, y: int, entity_type: str) -> Optional[EntityView]:
        for e in self.entities:
            if e.entity_type == entity_type and e.x == x and e.y == y:
                return e
        return None


def _item(item) -> Optional[ItemView]:
    if item is None:
        return None
    return ItemView(item.entity_id, item.content_id, item.name, item.get_stat('item_type', 'unknown'))


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
    )


def build_snapshot(state, viewer=None, message_count: int = 20) -> Snapshot:
    """Snapshot of `state` as seen by `viewer` (default: state.player)."""
    viewer = viewer or state.player
    entities = [
        EntityView(
            entity_id=e.entity_id, entity_type=_etype(e), content_id=e.content_id,
            name=e.name, x=e.x, y=e.y, hp=e.hp, max_hp=e.max_hp,
            symbol=e.display_symbol, color=e.display_color, alive=e.is_alive,
        )
        for e in state.entities.values()
        if e.entity_id != viewer.entity_id
    ]
    game_map = state.dungeon_map
    return Snapshot(
        turn=state.turn_count,
        floor=state.current_floor,
        game_over=state.game_over,
        victory=state.victory,
        player=_player_view(viewer, state.turn_count),
        entities=entities,
        map=MapView(game_map.width, game_map.height, game_map.to_dict()['tiles']),
        messages=state.get_recent_messages(message_count),
    )
