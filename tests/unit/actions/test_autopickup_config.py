"""Autopickup follows user preferences, and tests/bots run on the built-in ones (VB-76).

The autouse default_user_config fixture (tests/conftest.py) installs
ConfigManager.use_defaults(), so a developer's ~/.veinbornrc cannot change these results.
"""
import pytest

from core.base.entity import EntityType
from core.config.user_config import ConfigManager
from core.game import Game
from core.loot import LootGenerator

pytestmark = pytest.mark.unit


def gold_one_step_away():
    """A fresh game with gold on a free tile beside the player; returns (game, gold, step)."""
    game = Game()
    game.start_new_game(seed=11)
    p, m = game.state.player, game.state.dungeon_map
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        x, y = p.x + dx, p.y + dy
        if m.is_walkable(x, y) and not any(e.x == x and e.y == y for e in game.state.entities.values()):
            gold = LootGenerator.get_instance().create_item('gold_pile_small')
            gold.x, gold.y = x, y
            game.context.add_entity(gold)
            return game, gold, (dx, dy)
    pytest.skip("no free tile beside the player")


def test_use_defaults_ignores_the_config_file(tmp_path, monkeypatch):
    rc = tmp_path / ".veinbornrc"
    rc.write_text("[game]\nautopickup_types = gold\n")
    monkeypatch.setattr(ConfigManager, 'CONFIG_PATHS', [rc])

    assert ConfigManager().get('game.autopickup_types') == 'gold'      # positive control
    assert ConfigManager.use_defaults().get('game.autopickup_types') is None
    assert ConfigManager.get_instance().config_file is None


def test_default_autopickup_takes_gold():
    game, gold, (dx, dy) = gold_one_step_away()
    game.handle_player_action('move', dx=dx, dy=dy)
    assert gold in game.state.player.inventory


def test_autopickup_types_preference_can_leave_gold(monkeypatch):
    monkeypatch.setenv('VEINBORN_GAME_AUTOPICKUP_TYPES', 'ore,food,weapon')
    game, gold, (dx, dy) = gold_one_step_away()
    game.handle_player_action('move', dx=dx, dy=dy)
    assert gold not in game.state.player.inventory


def test_default_config_file_writes_the_code_default(tmp_path):
    from core.config.user_config import DEFAULT_AUTOPICKUP_TYPES
    rc = tmp_path / ".veinbornrc"
    ConfigManager.use_defaults().create_default_config(rc)
    assert f"autopickup_types = {DEFAULT_AUTOPICKUP_TYPES}\n" in rc.read_text()
