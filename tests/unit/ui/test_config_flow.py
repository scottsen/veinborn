"""Class and seed resolution order in the game start flow (ui/textual/config_flow.py)."""
from types import SimpleNamespace

import pytest

from core.character_class import CharacterClass
from ui.textual import config_flow


class FakeConfig:
    def __init__(self, **values):
        self.values = dict(values)
        self.saved = False

    def get(self, key, default=None):
        return self.values.get(key, default)

    def set(self, key, value):
        self.values[key] = value

    def save(self):
        self.saved = True


def args(char_class=None, seed=None):
    return SimpleNamespace(char_class=char_class, seed=seed)


@pytest.fixture
def tty(monkeypatch):
    """Pretend stdin is a terminal and feed `answers` to input()."""
    def setup(*answers):
        monkeypatch.setattr(config_flow.sys.stdin, 'isatty', lambda: True, raising=False)
        queue = list(answers)

        def fake_input(_prompt=''):
            if not queue:
                raise EOFError
            return queue.pop(0)
        monkeypatch.setattr('builtins.input', fake_input)
    return setup


@pytest.fixture
def no_tty(monkeypatch):
    monkeypatch.setattr(config_flow.sys.stdin, 'isatty', lambda: False, raising=False)

    def fail(_prompt=''):
        raise AssertionError("must not prompt without a terminal")
    monkeypatch.setattr('builtins.input', fail)


class TestChooseClass:
    def test_cli_wins_over_config(self, no_tty):
        config = FakeConfig(**{'player.default_class': 'warrior'})
        assert config_flow.choose_class(args('mage'), config) == CharacterClass.MAGE

    def test_invalid_cli_falls_back_to_config(self, no_tty):
        config = FakeConfig(**{'player.default_class': 'rogue'})
        assert config_flow.choose_class(args('bard'), config) == CharacterClass.ROGUE

    def test_invalid_config_and_no_tty_is_warrior(self, no_tty):
        config = FakeConfig(**{'player.default_class': 'bard'})
        assert config_flow.choose_class(args(), config) == CharacterClass.WARRIOR

    def test_prompt_retries_until_valid_and_does_not_save_on_no(self, tty):
        tty('9', 'x', '2', 'n')
        config = FakeConfig()
        chosen = config_flow.choose_class(args(), config)
        assert chosen == config_flow.get_class_from_choice(2)
        assert not config.saved and 'player.default_class' not in config.values

    def test_prompt_saves_default_on_yes(self, tty):
        tty('3', 'y')
        config = FakeConfig()
        chosen = config_flow.choose_class(args(), config)
        assert config.saved
        assert config.values['player.default_class'] == chosen.value

    def test_every_class_is_selectable_by_its_menu_number(self, tty):
        """The menu numbers CLASS_TEMPLATES; the prompt must accept all of them (Healer was unreachable)."""
        from core.character_class import CLASS_TEMPLATES
        for number, class_type in enumerate(CLASS_TEMPLATES, start=1):
            tty(str(number), 'n')
            assert config_flow.choose_class(args(), FakeConfig()) == class_type

    def test_eof_at_class_prompt_is_warrior(self, tty):
        tty()
        assert config_flow.choose_class(args(), FakeConfig()) == CharacterClass.WARRIOR

    def test_eof_at_save_prompt_is_warrior(self, tty):
        """Matches the original flow: an interrupt anywhere in the prompt means Warrior."""
        tty('2')
        assert config_flow.choose_class(args(), FakeConfig()) == CharacterClass.WARRIOR


class TestChooseSeed:
    def test_cli_wins_over_config(self, no_tty):
        config = FakeConfig(**{'game.default_seed': 'cfg'})
        assert config_flow.choose_seed(args(seed='cli'), config) == 'cli'

    def test_config_used_without_cli(self, no_tty):
        config = FakeConfig(**{'game.default_seed': 'cfg'})
        assert config_flow.choose_seed(args(), config) == 'cfg'

    def test_no_tty_no_seed_is_random(self, no_tty):
        assert config_flow.choose_seed(args(), FakeConfig()) is None

    def test_prompt_value_used(self, tty):
        tty('  abc  ')
        assert config_flow.choose_seed(args(), FakeConfig()) == 'abc'

    def test_prompt_empty_is_random(self, tty):
        tty('   ')
        assert config_flow.choose_seed(args(), FakeConfig()) is None

    def test_prompt_eof_is_random(self, tty):
        tty()
        assert config_flow.choose_seed(args(), FakeConfig()) is None
