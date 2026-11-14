"""Scrolls (VB-128 follow-up): enchant a worn weapon or armor, teleport, identify nearby ore.

Each is a one-use ``item_effect`` named by the item's ``effect`` stat in items.yaml; having an
effect is what makes an item usable (pack screen Enter, quick key e only drinks and eats).
A scroll that cannot do anything now (no weapon worn) fails without being used up or
spending a turn.
"""
from ...base.action import ActionOutcome
from ...base.entity import EntityType
from ...equipment import SLOT_ATTR
from ...extensions import item_effect
from ...geometry import chebyshev

IDENTIFY_RADIUS = 8


def _enchant(slot, stat, noun):
    def effect(context, actor, item) -> ActionOutcome:
        worn = getattr(actor, SLOT_ATTR[slot], None)
        if worn is None:
            return ActionOutcome.failure(f"You wear no {noun} to enchant.")
        bonus = int(item.get_stat('enchant_bonus', 1))
        worn.set_stat(stat, worn.get_stat(stat, 0) + bonus)
        outcome = ActionOutcome.success(took_turn=True)
        outcome.messages.append(f"The {item.name} flares: your {worn.name} gains +{bonus} {noun}.")
        return outcome
    return effect


item_effect("enchant_weapon")(_enchant('weapon', 'attack_bonus', 'attack'))
item_effect("enchant_armor")(_enchant('armor', 'defense_bonus', 'defense'))


@item_effect("teleport")
def teleport(context, actor, item) -> ActionOutcome:
    """Jump to a random free walkable tile of the floor (the game's own seeded RNG)."""
    game_map = context.get_map()
    free = [(x, y) for y in range(game_map.height) for x in range(game_map.width)
            if game_map.is_walkable(x, y) and context.get_entity_at(x, y) is None
            and (x, y) != (actor.x, actor.y)]
    if not free:
        return ActionOutcome.failure("The scroll fizzles: there is nowhere to go.")
    actor.x, actor.y = context.get_rng().choice(free)
    outcome = ActionOutcome.success(took_turn=True)
    outcome.messages.append(f"The {item.name} whisks {actor.name} away!")
    return outcome


@item_effect("identify")
def identify(context, actor, item) -> ActionOutcome:
    """Survey every ore vein within IDENTIFY_RADIUS (their numbers then show under x)."""
    veins = [v for v in context.get_entities_by_type(EntityType.ORE_VEIN)
             if not v.get_stat('surveyed')
             and chebyshev(actor.x, actor.y, v.x, v.y) <= IDENTIFY_RADIUS]
    if not veins:
        return ActionOutcome.failure("There is no unsurveyed ore nearby to identify.")
    for vein in veins:
        vein.set_stat('surveyed', True)
        if actor.entity_type == EntityType.PLAYER:
            actor.increment_stat('ore_surveyed')
    outcome = ActionOutcome.success(took_turn=True)
    outcome.messages.append(f"The {item.name} reveals {len(veins)} nearby ore vein"
                            f"{'s' if len(veins) != 1 else ''}: press x to read them.")
    return outcome
