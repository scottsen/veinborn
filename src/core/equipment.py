"""
Equipment view: what the player wears and which carried gear could be worn.

One answer for every frontend (the TUI equipment screen today, a graphical or
multiplayer client later), so none of them re-derives "equippable" from the
inventory. Pure data in, pure data out; the actions (`equip`, `unequip`) change
state.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

GEAR_SLOTS = ('weapon', 'armor')


def gear_slot(item) -> Optional[str]:
    """'weapon' or 'armor' if the item can be equipped (EquipAction's rule), else None."""
    slot = item.get_stat('equipment_slot') or item.get_stat('item_type')
    return slot if slot in GEAR_SLOTS else None


def gear_bonus(item, slot) -> int:
    """The bonus that makes gear better in its slot: attack for weapons, defense for armor."""
    return item.get_stat('attack_bonus' if slot == 'weapon' else 'defense_bonus', 0)


SLOT_ATTR = {'weapon': 'equipped_weapon', 'armor': 'equipped_armor'}
SLOT_STAT = {'weapon': 'attack', 'armor': 'defense'}
SLOT_LABEL = {'weapon': 'Weapon', 'armor': 'Armor'}


def worn_item(player, slot: str):
    """The item worn in `slot`, or None."""
    return getattr(player, SLOT_ATTR[slot], None)


@dataclass(frozen=True)
class GearLine:
    """One row of the equipment list."""
    slot: str                 # 'weapon' | 'armor'
    item: Optional[object]    # None only for an empty worn slot
    worn: bool                # True: worn now (remove it); False: carried (wear it)
    bonus: int                # the item's bonus in its slot's stat
    change: int               # carried gear: bonus minus what is worn in the slot; worn: 0

    @property
    def stat(self) -> str:
        return SLOT_STAT[self.slot]

    def text(self) -> str:
        """e.g. 'Weapon: Iron Sword (+4 attack)' / '2. Mithril Sword (weapon, +7 attack, +3 better)'."""
        if self.item is None:
            return f"{SLOT_LABEL[self.slot]}: (nothing)"
        if self.worn:
            return f"{SLOT_LABEL[self.slot]}: {self.item.name} (+{self.bonus} {self.stat})"
        verdict = "same" if self.change == 0 else f"{self.change:+d} vs worn"
        return f"{self.item.name} ({self.slot}, +{self.bonus} {self.stat}, {verdict})"


def equipment_listing(player) -> Tuple[List[GearLine], List[GearLine]]:
    """(worn, carried): `worn` has one line per slot, empty slots included;
    `carried` has every pack item that can be worn, in pack order."""
    worn = []
    for slot in GEAR_SLOTS:
        item = worn_item(player, slot)
        worn.append(GearLine(slot, item, True, gear_bonus(item, slot) if item else 0, 0))

    carried = []
    for item in player.inventory:
        slot = gear_slot(item)
        if slot is None:
            continue
        current = worn_item(player, slot)
        bonus = gear_bonus(item, slot)
        carried.append(GearLine(slot, item, False, bonus,
                                bonus - (gear_bonus(current, slot) if current else 0)))
    return worn, carried
