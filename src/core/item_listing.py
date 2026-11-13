"""
Item listings: what the player carries and what lies under their feet.

Data and message text for every frontend (the TUI today, a graphical or
multiplayer client later), so none of them walks `state.entities` or formats
the lines itself. Pure functions: no state is changed.
"""

from dataclasses import dataclass
from typing import List

from .base.entity import EntityType


@dataclass
class ItemLine:
    """One listed item: its entity id, display name and item_type."""
    entity_id: object
    name: str
    item_type: str

    @property
    def text(self) -> str:
        return f"{self.name} ({self.item_type})"


def _line(item) -> ItemLine:
    return ItemLine(item.entity_id, item.name, item.get_stat('item_type', 'unknown'))


def items_here(state, player=None) -> List[ItemLine]:
    """Living item entities on the player's tile."""
    player = player or state.player
    return [
        _line(e) for e in state.entities.values()
        if e.entity_type == EntityType.ITEM and e.x == player.x and e.y == player.y and e.is_alive
    ]


def inventory_listing(player) -> List[ItemLine]:
    """Carried items in pack order."""
    return [_line(item) for item in player.inventory]


def ground_messages(lines: List[ItemLine]) -> List[str]:
    """Message-log text for a look at the ground."""
    if not lines:
        return ["There are no items on the ground here."]
    return (
        [f"=== Items on the ground ({len(lines)}) ==="]
        + [f"  - {line.text}" for line in lines]
        + ["=============================="]
    )


def inventory_messages(player) -> List[str]:
    """Message-log text for the full inventory."""
    lines = inventory_listing(player)
    if not lines:
        return ["Your inventory is empty."]
    capacity = player.get_stat('inventory_capacity', 20)
    return (
        [f"=== Full Inventory ({len(lines)}/{capacity} items) ==="]
        + [f"  {i}. {line.text}" for i, line in enumerate(lines, 1)]
        + ["========================================"]
    )
