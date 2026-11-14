"""Sidebar shows what the player actually has: gear-inclusive stats, gear, ability status."""

import pytest

from core.character_class import CharacterClass
from core.game import Game
from core.snapshot import build_snapshot
from ui.textual.widgets.sidebar import Sidebar

pytestmark = pytest.mark.unit


def render(cls):
    game = Game()
    game.start_new_game(seed=7, character_class=cls)
    return game, Sidebar(build_snapshot(game.state)).render_content().plain


def test_warrior_sees_attack_and_defense_including_starting_gear():
    _, text = render(CharacterClass.WARRIOR)
    assert "Attack: 5" in text and "Defense: 3" in text
    assert "Weapon: Short Sword" in text and "Armor: Leather Armor" in text


def test_mage_with_no_gear_shows_dashes_and_the_ability():
    _, text = render(CharacterClass.MAGE)
    assert "Weapon: -" in text and "Armor: -" in text
    assert "Z: Force bolt (ready)" in text


def test_warrior_has_no_ability_line():
    _, text = render(CharacterClass.WARRIOR)
    assert "Z:" not in text


def test_ability_line_counts_down_the_cooldown():
    game, _ = render(CharacterClass.HEALER)
    player = game.state.player
    player.hp = 5
    game.handle_player_action('ability')
    text = Sidebar(build_snapshot(game.state)).render_content().plain
    assert "Z: Heal (" in text and "(ready)" not in text


def test_sidebar_marks_a_revealed_map_only():
    """VB-105: the dev switch shows in the sidebar; normal play does not."""
    game, plain = render(CharacterClass.WARRIOR)
    assert "MAP REVEALED" not in plain
    game.state.reveal_map = True
    assert "MAP REVEALED" in Sidebar(build_snapshot(game.state)).render_content().plain
