"""core.actions.ACTION_TYPES lists every Action (VB-21).

Every action is a dataclass that round-trips through to_dict/from_dict via this
map; a class missing from it once made PickupAction and WaitAction unusable in
multiplayer while they worked in single-player.
"""

from core.actions import ACTION_TYPES
from core.actions.pickup_action import PickupAction
from core.actions.wait_action import WaitAction
from core.base.action import Action


def test_every_action_subclass_is_in_action_types():
    # Add a class here only with a reason it cannot be listed.
    excluded = set()

    all_action_classes = {cls.__name__ for cls in Action.__subclasses__()}
    unaccounted = all_action_classes - set(ACTION_TYPES.keys()) - excluded

    assert not unaccounted, (
        f"Action subclass(es) {unaccounted} exist but aren't in "
        f"core.actions.ACTION_TYPES -- add them or explicitly exclude them "
        f"with a reason in `excluded` above."
    )


def test_pickup_and_wait_round_trip():
    for action in (PickupAction(actor_id="player-1"), WaitAction(actor_id="player-1")):
        back = ACTION_TYPES[type(action).__name__].from_dict(action.to_dict())
        assert type(back) is type(action) and back.actor_id == "player-1"
