"""
Item listings: what the player carries and what lies under their feet.

Data and message text for every frontend (the TUI, a graphical or multiplayer
client), read from a `core.snapshot.Snapshot` so a remote client lists exactly
what a local one does, and none of them walks `state.entities` or formats the
lines itself. Pure functions: no state is changed.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ItemLine:
    """One listed item: its entity id, display name, item_type and, for ore, its quality."""
    entity_id: object
    name: str
    item_type: str
    detail: str = ""            # e.g. ore quality 'P85 H70 M55 C40 D50' (VB-111)

    @property
    def text(self) -> str:
        return f"{self.name} ({self.item_type})" + (f" {self.detail}" if self.detail else "")


def _line(view) -> ItemLine:
    from .crafting import ore_label, stats_label
    part = getattr(view, 'part', None)
    detail = stats_label(part['stats']) if part else ore_label(getattr(view, 'ore', None))
    return ItemLine(view.entity_id, view.name, view.item_type or 'unknown', detail)


def items_here(snapshot) -> List[ItemLine]:
    """Living items on the viewer's tile."""
    me = snapshot.player
    return [
        _line(e) for e in snapshot.entities
        if e.entity_type == 'item' and e.x == me.x and e.y == me.y and e.alive
    ]


def inventory_listing(player_view) -> List[ItemLine]:
    """Carried items in pack order."""
    return [_line(item) for item in player_view.inventory]


def ground_messages(lines: List[ItemLine]) -> List[str]:
    """Message-log text for a look at the ground."""
    if not lines:
        return ["There are no items on the ground here."]
    return (
        [f"=== Items on the ground ({len(lines)}) ==="]
        + [f"  - {line.text}" for line in lines]
        + ["=============================="]
    )


def inventory_messages(player_view) -> List[str]:
    """Message-log text for the full inventory of a snapshot's `PlayerView`."""
    lines = inventory_listing(player_view)
    if not lines:
        return ["Your inventory is empty."]
    capacity = player_view.inventory_capacity
    pack = len(player_view.pack)
    return (
        [f"=== Full Inventory ({pack}/{capacity} items, ore bag {len(player_view.bag)}/{player_view.ore_capacity}, "
         f"{player_view.gold} gold) ==="]
        + [f"  {i}. {line.text}" for i, line in enumerate(lines, 1)]
        + ["========================================"]
    )
