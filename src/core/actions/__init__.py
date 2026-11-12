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
    'PickupAction',
    'WaitAction',
    'AbilityAction',
    'UseItemAction',
    'DropAction',
    'ACTION_TYPES',
]

# VB-21: single source of truth for actions that can be (de)serialized over
# the wire via plain to_dict()/from_dict(action_type=ClassName). The server's
# ActionRegistry (server/action_handler.py) registers directly from this map
# instead of hand-maintaining its own import list, which is how PickupAction
# and WaitAction silently ended up unusable in multiplayer despite working
# fine in single-player.
ACTION_TYPES: Dict[str, Type[Action]] = {
    'MoveAction': MoveAction,
    'AttackAction': AttackAction,
    'MineAction': MineAction,
    'SurveyAction': SurveyAction,
    'DescendAction': DescendAction,
    'CraftAction': CraftAction,
    'EquipAction': EquipAction,
    'PickupAction': PickupAction,
    'WaitAction': WaitAction,
    'AbilityAction': AbilityAction,
    'UseItemAction': UseItemAction,
    'DropAction': DropAction,
}
