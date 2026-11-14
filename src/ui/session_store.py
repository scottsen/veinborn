"""Remembered multiplayer session: lets a restarted client get back into its game.

The server resumes an auth session from its token (plan D7, ruling 7: rejoin is for the
same identity), so the client keeps the last token and game id per server and name.
The file holds a credential for a game server only; it is private to the user (0600).
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def default_path() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "veinborn" / "multiplayer_session.json"


def _key(host: str, port: int, name: str) -> str:
    return f"{host}:{port}/{name}"


def _read(path: Path) -> Dict[str, dict]:
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def load(host: str, port: int, name: str, path: Optional[Path] = None) -> Dict[str, str]:
    """The saved {"auth_token", "game_id"} for this server and name (empty if none)."""
    entry = _read(path or default_path()).get(_key(host, port, name), {})
    return {k: v for k, v in entry.items() if k in ("auth_token", "game_id") and isinstance(v, str)}


def save(host: str, port: int, name: str, auth_token: Optional[str], game_id: Optional[str],
         path: Optional[Path] = None) -> None:
    """Remember the session; a failure to write is logged, never raised (play goes on)."""
    path = path or default_path()
    try:
        entries = _read(path)
        entries[_key(host, port, name)] = {
            k: v for k, v in (("auth_token", auth_token), ("game_id", game_id)) if v
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(entries, f)
        os.replace(tmp, path)
    except OSError:
        logger.warning("Could not save the multiplayer session to %s", path, exc_info=True)


def forget(host: str, port: int, name: str, path: Optional[Path] = None) -> None:
    """Drop the saved session (the game is over or was left on purpose)."""
    path = path or default_path()
    entries = _read(path)
    if entries.pop(_key(host, port, name), None) is not None:
        try:
            path.write_text(json.dumps(entries))
        except OSError:
            logger.warning("Could not update %s", path, exc_info=True)
