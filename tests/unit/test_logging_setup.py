"""core.logging_setup: extra= fields reach the log, files stay size-bounded (VB-122, VB-123)."""
import logging

import pytest

from core.logging_setup import FORMAT, ExtrasFormatter, roll_over, setup_logging

pytestmark = pytest.mark.unit


@pytest.fixture
def root_restored():
    """setup_logging replaces the root handlers (force); put pytest's back afterwards."""
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    for h in root.handlers[:]:
        if h not in handlers:
            h.close()
    root.handlers[:] = handlers
    root.setLevel(level)


def record(msg="Item used", exc_info=None, **extra):
    rec = logging.LogRecord('core.actions', logging.INFO, __file__, 1, msg, (), exc_info)
    for k, v in extra.items():
        setattr(rec, k, v)
    return rec


def test_extra_fields_are_appended_as_key_value():
    line = ExtrasFormatter(FORMAT).format(record(item_name='Potion', effect='heal'))
    assert line.endswith("Item used | item_name=Potion effect=heal")


def test_no_extras_means_the_plain_line():
    assert ExtrasFormatter(FORMAT).format(record()).endswith(" - INFO - Item used")


def test_long_values_are_cut():
    line = ExtrasFormatter(FORMAT).format(record(big='x' * 1000))
    assert line.endswith('...') and len(line) < 400


def test_a_traceback_stays_after_the_extras():
    try:
        raise ValueError("boom")
    except ValueError:
        import sys
        line = ExtrasFormatter(FORMAT).format(record("Crash", exc_info=sys.exc_info(), turn=7))
    first, rest = line.split('\n', 1)
    assert first.endswith("Crash | turn=7") and "ValueError: boom" in rest


def test_roll_over_only_past_the_limit(tmp_path):
    log = tmp_path / "bot.log"
    log.write_text("x" * 50)
    assert not roll_over(log, max_bytes=100)
    log.write_text("x" * 500)
    assert roll_over(log, max_bytes=100, backups=2)
    assert (tmp_path / "bot.log.1").read_text() == "x" * 500
    assert not log.exists() or log.stat().st_size == 0


def test_setup_logging_writes_extras_to_the_file(tmp_path, root_restored):
    log = tmp_path / "logs" / "veinborn.log"
    setup_logging(log, logging.INFO)
    logging.getLogger('core.actions.use_item_action').info("Item used", extra={'item_name': 'Potion'})
    for h in logging.getLogger().handlers:
        h.flush()
    assert "Item used | item_name=Potion" in log.read_text()


def test_startup_rotation_mode_rolls_a_big_file_first(tmp_path, root_restored):
    log = tmp_path / "bot_tests.log"
    log.write_text("old\n" * 100)
    setup_logging(log, logging.WARNING, rotate_while_running=False, max_bytes=50)
    assert (tmp_path / "bot_tests.log.1").exists()
    handlers = logging.getLogger().handlers
    assert any(type(h) is logging.FileHandler for h in handlers)      # plain: no mid-run rotation
