"""StatusBar shows who the round waits on, with a disconnected seat's grace running down (VB-103)."""

import time

import pytest

from core.snapshot import PartyMemberView, RoundView, Snapshot
from ui.textual.widgets.status_bar import StatusBar

pytestmark = pytest.mark.unit


def _snapshot(grace_left):
    party = [
        PartyMemberView("p-a", "Alice", "warrior", "e-a", True, True),
        PartyMemberView("p-b", "Bob", "mage", "e-b", True, False, grace_left),
    ]
    snap = Snapshot.__new__(Snapshot)
    snap.__dict__.update(
        turn=3, game_over=False, party=party,
        round=RoundView(number=2, waiting_on=["e-b"], acted=["e-a"]),
        player=type("P", (), {"hp": 10, "max_hp": 10, "x": 1, "y": 2, "alive": True})(),
    )
    return snap


def _text(bar):
    return bar.render().plain


def test_a_seat_in_grace_shows_a_countdown_that_runs_down():
    bar = StatusBar()
    bar.refresh = lambda *a, **k: None
    bar.show(_snapshot(105))
    assert "waiting on Bob (disconnected, 1:45)" in _text(bar)

    bar._shown_at -= 10                                  # ten seconds later, same snapshot
    assert "Bob (disconnected, 1:35)" in _text(bar)
    bar.show(_snapshot(105))                             # a local redraw: the clock keeps running
    assert "Bob (disconnected, 1:35)" in _text(bar)

    bar.show(_snapshot(90))                              # a fresh snapshot restarts from the server's value
    assert "Bob (disconnected, 1:30)" in _text(bar)


def test_a_dropped_seat_without_grace_says_disconnected():
    bar = StatusBar()
    bar.refresh = lambda *a, **k: None
    bar.show(_snapshot(None))
    assert "waiting on Bob (disconnected)" in _text(bar)
