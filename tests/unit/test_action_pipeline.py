"""Tests for the post-action pipeline shared by single-player and multiplayer (VB-24)."""

from unittest.mock import Mock

from core.action_pipeline import process_action_outcome
from core.base.action import ActionOutcome


def _run(outcome, event_bus=None):
    messages, descents = [], []
    took_turn = process_action_outcome(
        outcome,
        "test",
        add_message=messages.append,
        on_descend_floor=lambda: descents.append(1),
        event_bus=event_bus,
    )
    return took_turn, messages, descents


def test_success_records_messages_and_reports_took_turn():
    outcome = ActionOutcome.success(took_turn=True, message="You mine ore.")
    took_turn, messages, descents = _run(outcome)
    assert took_turn is True
    assert messages == ["You mine ore."]
    assert descents == []


def test_free_action_reports_no_turn_taken():
    outcome = ActionOutcome.success(took_turn=False, message="Inventory full.")
    took_turn, messages, _ = _run(outcome)
    assert took_turn is False
    assert messages == ["Inventory full."]


def test_failure_records_message_and_takes_no_turn():
    took_turn, messages, _ = _run(ActionOutcome.failure("Too far away."))
    assert took_turn is False
    assert messages == ["Too far away."]


def test_events_are_published_to_bus():
    outcome = ActionOutcome.success()
    outcome.events.append({'type': 'entity_moved'})
    bus = Mock()
    _run(outcome, event_bus=bus)
    bus.publish_all.assert_called_once_with(outcome.events)


def test_no_bus_and_no_events_is_fine():
    outcome = ActionOutcome.success()
    bus = Mock()
    _run(outcome)
    _run(outcome, event_bus=bus)
    bus.publish_all.assert_not_called()


def test_each_descend_event_triggers_descent():
    outcome = ActionOutcome.success()
    outcome.events.append({'type': 'entity_moved'})
    outcome.events.append({'type': 'descend_floor'})
    _, _, descents = _run(outcome)
    assert descents == [1]
