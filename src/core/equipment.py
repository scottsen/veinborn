"""
Equipment view: what the player wears and which carried gear could be worn.

One answer for every frontend (the TUI equipment screen today, a graphical or
multiplayer client later), so none of them re-derives "equippable" from the
inventory. `equipment_listing` reads a snapshot's `PlayerView` (whose items
already carry their slot and bonus), so it works the same on a remote client.
The actions (`equip`, `unequip`) change state; `gear_slot`/`gear_bonus` are the
rules on live items that the snapshot and those actions share.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

GEAR_SLOTS = ('weapon', 'armor', 'shield')


def gear_slot(item) -> Optional[str]:
    """'weapon', 'armor' or 'shield' if the item can be equipped (EquipAction's rule), else None."""
    slot = item.get_stat('equipment_slot') or item.get_stat('item_type')
    return slot if slot in GEAR_SLOTS else None


def gear_bonus(item, slot) -> int:
    """The bonus that makes gear better in its slot: attack for weapons, defense for armor."""
    return item.get_stat('attack_bonus' if slot == 'weapon' else 'defense_bonus', 0)


SLOT_ATTR = {'weapon': 'equipped_weapon', 'armor': 'equipped_armor', 'shield': 'equipped_shield'}
SLOT_STAT = {'weapon': 'attack', 'armor': 'defense', 'shield': 'defense'}
SLOT_LABEL = {'weapon': 'Weapon', 'armor': 'Armor', 'shield': 'Shield'}


def worn_item(player, slot: str):
    """The item worn in `slot`, or None."""
    return getattr(player, SLOT_ATTR[slot], None)


@dataclass(frozen=True)
class GearLine:
    """One row of the equipment list."""
    slot: str                 # 'weapon' | 'armor' | 'shield'
    item: Optional[object]    # an ItemView; None only for an empty worn slot
    worn: bool                # True: worn now (remove it); False: carried (wear it)
    bonus: int                # the item's bonus in its slot's stat
    change: int               # carried gear: bonus minus what is worn in the slot; worn: 0

    @property
    def stat(self) -> str:
        return SLOT_STAT[self.slot]

    @property
    def item_id(self):
        return self.item.entity_id if self.item is not None else None

    def text(self) -> str:
        """e.g. 'Weapon: Iron Sword (+4 attack)' / '2. Mithril Sword (weapon, +7 attack, +3 better)'."""
        if self.item is None:
            return f"{SLOT_LABEL[self.slot]}: (nothing)"
        if self.worn:
            return f"{SLOT_LABEL[self.slot]}: {self.item.name} (+{self.bonus} {self.stat})"
        verdict = "same" if self.change == 0 else f"{self.change:+d} vs worn"
        return f"{self.item.name} ({self.slot}, +{self.bonus} {self.stat}, {verdict})"


def equipment_listing(player_view) -> Tuple[List[GearLine], List[GearLine]]:
    """(worn, carried) for a snapshot `PlayerView`: `worn` has one line per slot,
    empty slots included; `carried` has every pack item that can be worn, in pack order."""
    worn_items = {slot: getattr(player_view, slot) for slot in GEAR_SLOTS}
    worn = [
        GearLine(slot, item, True, item.bonus if item else 0, 0)
        for slot, item in worn_items.items()
    ]
    carried = []
    for item in player_view.inventory:
        if item.slot not in GEAR_SLOTS:
            continue
        current = worn_items[item.slot]
        carried.append(GearLine(item.slot, item, False, item.bonus,
                                item.bonus - (current.bonus if current else 0)))
    return worn, carried
