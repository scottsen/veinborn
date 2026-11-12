"""Tests for ActionRegistry (VB-21: server/core action registry parity)."""

import pytest

from core.actions import ACTION_TYPES
from core.actions.pickup_action import PickupAction
from core.actions.wait_action import WaitAction
from server.action_handler import ActionRegistry


def test_registry_matches_core_action_types():
    """VB-21: the server registry must be sourced from core.actions.ACTION_TYPES,
    not a separately hand-maintained list -- that drift is exactly how
    PickupAction and WaitAction ended up silently unusable in multiplayer
    despite working fine in single-player."""
    registry = ActionRegistry()

    assert registry._action_types == ACTION_TYPES


def test_registry_includes_every_standard_action_subclass():
    """Guards against a new Action subclass being added to core/actions/
    without also being added to ACTION_TYPES -- the actual root cause of
    VB-21 (a class existed and worked in single-player, but no one
    remembered to register it for the network protocol too)."""
    from core.base.action import Action

    # Add a class here only with a reason it can't travel over the wire.
    excluded = set()

    all_action_classes = {cls.__name__ for cls in Action.__subclasses__()}
    unaccounted = all_action_classes - set(ACTION_TYPES.keys()) - excluded

    assert not unaccounted, (
        f"Action subclass(es) {unaccounted} exist but aren't in "
        f"core.actions.ACTION_TYPES -- add them or explicitly exclude them "
        f"with a reason in `excluded` above."
    )


def test_registry_deserializes_pickup_action():
    registry = ActionRegistry()
    action = PickupAction(actor_id="player-1")

    deserialized = registry.deserialize(action.to_dict())

    assert isinstance(deserialized, PickupAction)
    assert deserialized.actor_id == "player-1"


def test_registry_deserializes_wait_action():
    registry = ActionRegistry()
    action = WaitAction(actor_id="player-1")

    deserialized = registry.deserialize(action.to_dict())

    assert isinstance(deserialized, WaitAction)
    assert deserialized.actor_id == "player-1"
