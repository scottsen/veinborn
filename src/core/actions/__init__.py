"""
Concrete action implementations.

All actions inherit from Action base class and follow the
event-ready pattern (return structured outcomes with events).
"""

from typing import Dict, Type

from ..base.action import Action
from .move_action import MoveAction
from .attack_action import AttackAction
from .mine_action import MineAction
from .survey_action import SurveyAction
from .descend_action import DescendAction
from .craft_action import CraftAction
from .equip_action import EquipAction
from .unequip_action import UnequipAction
from .pickup_action import PickupAction
from .wait_action import WaitAction
from .ability_action import AbilityAction
from .use_item_action import UseItemAction
from .drop_action import DropAction

__all__ = [
    'MoveAction',
    'AttackAction',
    'MineAction',
    'SurveyAction',
    'DescendAction',
    'CraftAction',
    'EquipAction',
    'UnequipAction',
    'PickupAction',
    'WaitAction',
    'AbilityAction',
    'UseItemAction',
    'DropAction',
    'ACTION_TYPES',
]

# VB-21: single source of truth for every action, by class name, for plain
# to_dict()/from_dict(action_type=ClassName). The wire carries intents, not
# actions (plan D3), so nothing deserializes client actions any more; the map
# stays the one list tests check every Action subclass against.
ACTION_TYPES: Dict[str, Type[Action]] = {
    'MoveAction': MoveAction,
    'AttackAction': AttackAction,
    'MineAction': MineAction,
    'SurveyAction': SurveyAction,
    'DescendAction': DescendAction,
    'CraftAction': CraftAction,
    'EquipAction': EquipAction,
    'UnequipAction': UnequipAction,
    'PickupAction': PickupAction,
    'WaitAction': WaitAction,
    'AbilityAction': AbilityAction,
    'UseItemAction': UseItemAction,
    'DropAction': DropAction,
}
