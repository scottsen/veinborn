"""Rogue backstab (passive): the first hit on an unhurt monster does extra damage."""

from ...base.entity import EntityType
from ...config.config_loader import ConfigLoader
from ...extensions import damage_modifier


@damage_modifier("backstab")
def backstab(actor, target, damage):
    if target.entity_type != EntityType.MONSTER or target.hp < target.max_hp:
        return None
    multiplier = ConfigLoader.get_config().get_ability_config('backstab')['damage_multiplier']
    return damage * multiplier, "backstabs"
