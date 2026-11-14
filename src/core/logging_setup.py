"""One logging setup for every entry point (TUI, server, fuzz bots): VB-122, VB-123.

- `ExtrasFormatter` appends a record's ``extra=`` fields as ``key=value``. The old format
  string printed only the message, so ``logger.info("Item used", extra={'item_name': ...})``
  reached the file as a bare "Item used" and most of the context the code logs was lost.
- Log files are size-bounded: a single process (TUI, server) rotates while running; a
  multi-process run (bots with ``--jobs``) rotates once at startup, before workers fork, since
  a rotating handler shared across processes renames the file under the others' feet.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
MAX_BYTES = 10 * 1024 * 1024
BACKUPS = 3
_VALUE_LIMIT = 200

# Attributes every LogRecord has; anything else on a record came from ``extra=``
_STANDARD = set(vars(logging.LogRecord('', 0, '', 0, '', (), None))) | {
    'message', 'asctime', 'taskName'}


def _short(value) -> str:
    text = value if isinstance(value, str) else repr(value)
    return text if len(text) <= _VALUE_LIMIT else text[:_VALUE_LIMIT - 3] + '...'


class ExtrasFormatter(logging.Formatter):
    """The standard format plus `` | key=value ...`` for the record's extra fields (before any
    traceback, so a multi-line exception stays at the end)."""

    def formatMessage(self, record: logging.LogRecord) -> str:
        line = super().formatMessage(record)
        extras = [(k, v) for k, v in record.__dict__.items()
                  if k not in _STANDARD and not k.startswith('_')]
        if extras:
            line += ' | ' + ' '.join(f'{k}={_short(v)}' for k, v in extras)
        return line


def roll_over(path: Path, max_bytes: int = MAX_BYTES, backups: int = BACKUPS) -> bool:
    """Rotate `path` now if it is over `max_bytes` (path -> path.1 -> ... -> path.<backups>).
    Returns whether it rotated."""
    if not path.exists() or path.stat().st_size <= max_bytes:
        return False
    handler = logging.handlers.RotatingFileHandler(path, maxBytes=1, backupCount=backups,
                                                   delay=True)
    handler.doRollover()
    handler.close()
    return True


def setup_logging(path: Optional[Path], level: int, *, console: bool = False,
                  rotate_while_running: bool = True, max_bytes: int = MAX_BYTES,
                  backups: int = BACKUPS) -> None:
    """Configure the root logger: an optional size-bounded file and an optional console, both
    with `ExtrasFormatter`. Replaces handlers set up before (``force``)."""
    formatter = ExtrasFormatter(FORMAT)
    handlers: list = []
    if path is not None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if rotate_while_running:
            handlers.append(logging.handlers.RotatingFileHandler(
                path, maxBytes=max_bytes, backupCount=backups))
        else:
            roll_over(path, max_bytes, backups)
            handlers.append(logging.FileHandler(path))
    if console:
        handlers.append(logging.StreamHandler())
    for handler in handlers:
        handler.setFormatter(formatter)
    logging.basicConfig(level=level, handlers=handlers, force=True)

