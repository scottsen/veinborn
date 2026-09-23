"""VB-33: every event an action emits must be deliverable through the EventBus."""

import glob
import logging
import re

import pytest

from core.events import EventBus, GameEvent, GameEventType

pytestmark = pytest.mark.unit


def test_from_dict_accepts_flat_action_events():
    """Actions emit flat dicts ({'type': ..., 'actor_id': ...}), not {'data': {...}}."""
    event = GameEvent.from_dict({'type': 'entity_moved', 'entity_id': 'p', 'to': (1, 2)})

    assert event.event_type == GameEventType.ENTITY_MOVED
    assert event.data == {'entity_id': 'p', 'to': (1, 2)}


def test_from_dict_prefers_explicit_data():
    event = GameEvent.from_dict({
        'type': 'attack_resolved', 'data': {'damage': 3}, 'turn': 5, 'timestamp': 1.0,
    })
    assert event.data == {'damage': 3}
    assert (event.turn, event.timestamp) == (5, 1.0)


def test_flat_event_reaches_subscribers():
    bus = EventBus()
    seen = []
    bus.subscribe(GameEventType.ITEM_PICKED_UP, seen.append)

    bus.publish_dict({'type': 'item_picked_up', 'actor_id': 'p', 'item_name': 'Ring'})

    assert len(seen) == 1
    assert seen[0].data['item_name'] == 'Ring'


def test_every_type_emitted_by_actions_is_a_known_event_type():
    valid = {e.value for e in GameEventType}
    emitted = set()
    for path in glob.glob('src/core/actions/*.py'):
        emitted |= set(re.findall(r"'type':\s*'([a-z_]+)'", open(path).read()))
    emitted.add('mining_progress')  # chosen conditionally in MineAction

    assert emitted - valid == set()


def test_publishing_action_events_does_not_log_errors(caplog):
    bus = EventBus()
    bus.enable_history = True
    events = [
        {'type': 'actor_waited', 'actor_id': 'p', 'position': (1, 1)},
        {'type': 'descend_floor', 'actor_id': 'p'},
        {'type': 'mining_progress', 'actor_id': 'p'},
    ]

    with caplog.at_level(logging.ERROR, logger='core.events.events'):
        bus.publish_all(events)

    assert [r for r in caplog.records if r.levelno >= logging.ERROR] == []
    assert len(bus.event_history) == 3


def test_malformed_event_is_still_reported_not_raised(caplog):
    bus = EventBus()
    with caplog.at_level(logging.ERROR, logger='core.events.events'):
        bus.publish_dict({'no_type_here': True})
    assert any(r.levelno >= logging.ERROR for r in caplog.records)
