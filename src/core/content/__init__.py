"""
Game content, auto-discovered.

Every module under this package (ai/, abilities/, events/, or anything you add)
is imported once, on the first registry lookup. Importing a module runs its
decorators (see core.extensions), which is what registers its content. So to add
content: drop a file in the right subfolder; nothing else needs editing.

A module that raises on import is logged and skipped, so one broken piece of
content cannot stop the game from starting.
"""

import importlib
import logging
import pkgutil

logger = logging.getLogger(__name__)

_loaded = False
_loading = False
failed_modules = {}


def load_content() -> None:
    """Import every content module. Safe to call repeatedly."""
    global _loaded, _loading
    if _loaded or _loading:
        return
    _loading = True
    try:
        for info in pkgutil.walk_packages(__path__, prefix=__name__ + "."):
            if info.ispkg:
                continue
            try:
                importlib.import_module(info.name)
            except Exception as exc:
                failed_modules[info.name] = exc
                logger.exception(f"Content module {info.name} failed to load; skipped")
        _loaded = True
    finally:
        _loading = False
