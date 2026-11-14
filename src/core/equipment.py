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
# The stats worn gear can carry that the game reads (crafting v2 D1, VB-113/VB-114)
CORE_GEAR_STATS = ('attack_bonus', 'defense_bonus', 'accuracy', 'max_hp_bonus', 'spell_power',
                   'fire_damage')


def core_stats(item) -> dict:
    """The item's nonzero core gear stats, e.g. {'attack_bonus': 6, 'accuracy': 2}."""
    return {k: item.get_stat(k, 0) for k in CORE_GEAR_STATS if item.get_stat(k, 0)}


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


def gear_total(entity, stat: str) -> int:
    """Sum of `stat` over everything `entity` wears; 0 for anything without gear (monsters)."""
    total = 0
    for slot in GEAR_SLOTS:
        item = getattr(entity, SLOT_ATTR[slot], None)
        if item is not None:
            total += int(item.get_stat(stat, 0) or 0)
    return total


def wear(actor, slot: str, item) -> None:
    """Put `item` (or None: take off) in `slot`, applying what worn gear grants while worn.

    The one place a worn slot changes during play (EquipAction, UnequipAction), so a bonus
    is added and removed exactly once. `max_hp_bonus` (crafting v2, VB-114): max HP rises
    and falls with the gear; current HP is not topped up, and falls only as far as the new
    maximum (never below 1). Saves store max HP with the bonus in it, so loading does not
    call this.
    """
    old = getattr(actor, SLOT_ATTR[slot], None)
    delta = ((item.get_stat('max_hp_bonus', 0) if item is not None else 0)
             - (old.get_stat('max_hp_bonus', 0) if old is not None else 0))
    setattr(actor, SLOT_ATTR[slot], item)
    if delta:
        actor.max_hp = max(1, actor.max_hp + delta)
        actor.hp = max(1, min(actor.hp, actor.max_hp))


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
