"""Examine: what a player can learn about the things around them (VB-129, VB-110).

Pure functions over a `core.snapshot.Snapshot`, so the TUI, a graphical client and a remote
client list the same facts. A surveyed ore vein keeps its numbers here (the survey message
scrolls away), a monster shows what a fight against it will be, an item shows its stats.
"""

from dataclasses import dataclass
from typing import List

from .crafting import ORE_LEGEND, ore_label, stats_label
from .geometry import chebyshev

KINDS = ('monster', 'ore_vein', 'item', 'forge')     # what examine lists; other players are not
_ORDER = {kind: n for n, kind in enumerate(KINDS)}


@dataclass
class ExamineLine:
    entity_id: object
    kind: str
    distance: int
    text: str       # one row: 'Goblin  3 away  hp 8/8'
    detail: str     # what the selected row says underneath (may span lines)


def _monster(e) -> str:
    info = e.info or {}
    bits = [f"hp {e.hp}/{e.max_hp}"]
    if 'attack' in info:
        bits.append(f"attack {info['attack']}  defense {info['defense']}")
    return "  ".join(bits)


def _vein_detail(e) -> str:
    info = e.info or {}
    if not info.get('surveyed'):
        return "Not surveyed: stand next to it and press s to learn its properties."
    turns = info.get('mining_turns')
    mining = f"   mining takes {turns} turns" if turns else ""
    return f"{ore_label(info.get('ore'))}{mining}\n{ORE_LEGEND}"


def _detail(e) -> str:
    info = e.info or {}
    if e.entity_type == 'monster':
        more = f"\nworth {info['xp']} XP, {info.get('ai', '?')} AI" if 'xp' in info else ""
        return _monster(e) + more
    if e.entity_type == 'ore_vein':
        return _vein_detail(e)
    if e.entity_type == 'item':
        part = info.get('part')
        stats = stats_label(part['stats']) if part else stats_label(info.get('stats'))
        return stats or (e.item_type or "an item")
    return "A forge: stand next to it and press f to craft."


def _label(e) -> str:
    if e.entity_type == 'ore_vein':
        return f"{e.name} ({'surveyed' if (e.info or {}).get('surveyed') else 'not surveyed'})"
    if e.entity_type == 'monster':
        return f"{e.name} {e.hp}/{e.max_hp}"
    return e.name


def examine_listing(snapshot) -> List[ExamineLine]:
    """Everything the viewer can see or remember, nearest first (monsters before ore at a tie)."""
    me = snapshot.player
    lines = []
    for e in snapshot.entities:
        if e.entity_type not in KINDS or not e.alive:
            continue
        dist = chebyshev(me.x, me.y, e.x, e.y)
        lines.append(ExamineLine(e.entity_id, e.entity_type, dist,
                                 f"{_label(e):<30} {dist} away", _detail(e)))
    return sorted(lines, key=lambda l: (l.distance, _ORDER[l.kind], l.text))
