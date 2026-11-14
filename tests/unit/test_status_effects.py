"""Timed status effects: the registry, add/refresh/tick, turn-loop ticking, saves, snapshot (VB-107)."""

import json

import pytest

from core.base.entity import EntityType
from core.extensions import status_effect, status_effects
from core.game import Game
from core.snapshot import Snapshot, build_snapshot
from core.status_effects import add_effect, effects_of, has_effect, remove_effect, tick_effects


@pytest.fixture
def game():
    g = Game()
    g.start_new_game(seed=3)
    for e in list(g.state.entities.values()):
        if e.entity_type == EntityType.MONSTER:
            g.context.remove_entity(e.entity_id)
    p = g.state.player
    p.max_hp, p.hp = 100, 20
    return g


def test_regeneration_is_registered_with_a_label():
    assert 'regeneration' in status_effects
    assert status_effects.get('regeneration').label == "Regeneration"


def test_an_unknown_effect_is_refused(game):
    with pytest.raises(KeyError):
        add_effect(game.state.player, 'no_such_effect', 3)


def test_ticking_heals_counts_down_and_ends_with_a_message(game):
    p = game.state.player
    add_effect(p, 'regeneration', 2, 4)
    assert tick_effects(game.context, p) == []
    assert p.hp == 24 and effects_of(p)[0]['turns_left'] == 1
    messages = tick_effects(game.context, p)
    assert p.hp == 28 and messages == ["Player: Regeneration fades."]
    assert effects_of(p) == [] and not has_effect(p, 'regeneration')


def test_reapplying_refreshes_to_the_longer_and_stronger_never_stacks(game):
    p = game.state.player
    add_effect(p, 'regeneration', 5, 2)
    add_effect(p, 'regeneration', 3, 4)
    add_effect(p, 'regeneration', 9, 1)
    assert effects_of(p) == [{'name': 'regeneration', 'turns_left': 9, 'magnitude': 4}]


def test_remove_effect(game):
    p = game.state.player
    add_effect(p, 'regeneration', 5)
    remove_effect(p, 'regeneration')
    assert effects_of(p) == []


def test_a_broken_effect_is_skipped_but_still_counts_down(game):
    @status_effect("boom_test", replace=True)
    def boom(context, actor, effect):
        raise RuntimeError("boom")
    try:
        p = game.state.player
        add_effect(p, 'boom_test', 2)
        tick_effects(game.context, p)
        assert effects_of(p)[0]['turns_left'] == 1
        tick_effects(game.context, p)
        assert effects_of(p) == []
    finally:
        status_effects.unregister("boom_test")


def test_the_turn_loop_ticks_every_actor(game):
    p = game.state.player
    add_effect(p, 'regeneration', 3, 2)
    for _ in range(3):
        game.engine.tick()
    assert p.hp >= 26 and effects_of(p) == []
    assert any("Regeneration fades" in m for m in game.state.messages)


def test_effects_are_saved_with_the_game(game, tmp_path):
    from core.save_load import SaveSystem
    p = game.state.player
    add_effect(p, 'regeneration', 7, 3)
    system = SaveSystem(save_dir=tmp_path)
    system.save_game(game.state, "fx")
    loaded = system.load_game("fx")
    assert effects_of(loaded.player) == [{'name': 'regeneration', 'turns_left': 7, 'magnitude': 3}]


def test_the_snapshot_shows_effects_and_round_trips(game):
    add_effect(game.state.player, 'regeneration', 7, 3)
    snap = build_snapshot(game.state)
    [view] = snap.player.effects
    assert (view.name, view.label, view.turns_left, view.magnitude) == ('regeneration', 'Regeneration', 7, 3)
    back = Snapshot.from_dict(json.loads(json.dumps(snap.to_dict())))
    assert back.player.effects == snap.player.effects


def test_the_sidebar_lists_active_effects(game):
    from ui.textual.widgets.sidebar import Sidebar
    add_effect(game.state.player, 'regeneration', 7, 3)
    text = Sidebar(build_snapshot(game.state)).render_content().plain
    assert "Regeneration +3/turn (7t)" in text
