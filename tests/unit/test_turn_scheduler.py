"""RoundScheduler: one action per living player per round (MP plan D2 / VB-90)."""

from core.turn_scheduler import RoundScheduler


def test_party_of_one_ticks_after_every_turn_taking_action():
    s = RoundScheduler(["a"])
    for expected_round in (1, 2, 3):
        assert s.after_action("a", True, ["a"]) is True
        s.next_round(["a"])
        assert s.round_number == expected_round


def test_round_waits_until_every_living_player_has_acted():
    s = RoundScheduler(["a", "b", "c"])
    assert s.after_action("a", True, ["a", "b", "c"]) is False
    assert s.waiting_on() == ["b", "c"]
    assert s.after_action("c", True, ["a", "b", "c"]) is False
    assert s.after_action("b", True, ["a", "b", "c"]) is True


def test_a_second_action_in_the_same_round_is_refused_until_the_next_round():
    s = RoundScheduler(["a", "b"])
    s.after_action("a", True, ["a", "b"])
    assert not s.can_act("a") and s.can_act("b")
    s.after_action("b", True, ["a", "b"])
    s.next_round(["a", "b"])
    assert s.can_act("a")


def test_free_actions_never_count():
    s = RoundScheduler(["a", "b"])
    assert s.after_action("a", False, ["a", "b"]) is False
    assert s.can_act("a") and s.waiting_on() == ["a", "b"]


def test_a_dead_player_stops_the_round_waiting_for_them():
    s = RoundScheduler(["a", "b"])
    s.after_action("a", True, ["a", "b"])
    # b dies before acting; only a is left alive, so the round is complete
    assert s.after_action("a", False, ["a"]) is True
    assert s.waiting_on() == []


def test_death_of_the_last_owed_player_completes_the_round_on_the_next_turn_action():
    s = RoundScheduler(["a", "b", "c"])
    s.after_action("a", True, ["a", "b", "c"])
    s.after_action("b", True, ["a", "b", "c"])
    # c, the only one still owed, dies; the next turn-taking action by a living seat ticks
    assert s.after_action("a", True, ["a", "b"]) is True


def test_dropping_the_last_owed_seat_completes_a_round_someone_acted_in():
    s = RoundScheduler(["a", "b"])
    s.after_action("a", True, ["a", "b"])
    assert s.drop("b") is True
    s2 = RoundScheduler(["a", "b"])
    assert s2.drop("b") is False  # nobody acted yet: nothing to tick
