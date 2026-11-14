"""ui.session_store: the remembered token and game id of a multiplayer client (VB-103)."""

import stat

import pytest

from ui import session_store

pytestmark = pytest.mark.unit


def test_a_saved_session_is_loaded_back_per_server_and_name(tmp_path):
    path = tmp_path / "s" / "session.json"
    session_store.save("h", 1, "Alice", "tok-a", "game-1", path=path)
    session_store.save("h", 1, "Bob", "tok-b", None, path=path)

    assert session_store.load("h", 1, "Alice", path=path) == {"auth_token": "tok-a", "game_id": "game-1"}
    assert session_store.load("h", 1, "Bob", path=path) == {"auth_token": "tok-b"}
    assert session_store.load("h", 2, "Alice", path=path) == {}      # another server
    assert stat.S_IMODE(path.stat().st_mode) == 0o600                # it holds a credential


def test_forget_drops_only_that_entry(tmp_path):
    path = tmp_path / "session.json"
    session_store.save("h", 1, "Alice", "a", "g", path=path)
    session_store.save("h", 1, "Bob", "b", "g", path=path)

    session_store.forget("h", 1, "Alice", path=path)

    assert session_store.load("h", 1, "Alice", path=path) == {}
    assert session_store.load("h", 1, "Bob", path=path) == {"auth_token": "b", "game_id": "g"}


def test_a_missing_or_corrupt_file_loads_as_empty_and_saving_replaces_it(tmp_path):
    path = tmp_path / "session.json"
    assert session_store.load("h", 1, "Alice", path=path) == {}
    path.write_text("{not json")
    assert session_store.load("h", 1, "Alice", path=path) == {}

    session_store.save("h", 1, "Alice", "t", None, path=path)
    assert session_store.load("h", 1, "Alice", path=path) == {"auth_token": "t"}


def test_a_failed_write_is_not_an_error(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    session_store.save("h", 1, "Alice", "t", "g", path=blocker / "session.json")   # parent is a file
