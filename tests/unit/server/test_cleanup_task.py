"""VB-27: the server cleanup task must never busy-loop when a pass keeps failing."""

import asyncio

import pytest

from server.websocket_server import VeinbornServer


def test_delay_is_base_interval_when_healthy():
    assert VeinbornServer._cleanup_delay(0) == VeinbornServer.CLEANUP_INTERVAL_SECONDS


def test_delay_backs_off_exponentially_and_caps():
    base = VeinbornServer.CLEANUP_INTERVAL_SECONDS
    delays = [VeinbornServer._cleanup_delay(n) for n in range(1, 12)]
    assert delays[0] == base * 2
    assert delays[1] == base * 4
    assert delays == sorted(delays)
    assert max(delays) == VeinbornServer.CLEANUP_MAX_BACKOFF_SECONDS


@pytest.mark.asyncio
async def test_failing_pass_still_sleeps_with_growing_backoff(monkeypatch):
    server = VeinbornServer()
    server.is_running = True
    passes = 0
    sleeps = []

    async def always_fails():
        nonlocal passes
        passes += 1
        assert passes < 50, "cleanup_task is spinning without sleeping"
        raise RuntimeError("boom")

    async def fake_sleep(delay):
        sleeps.append(delay)
        if len(sleeps) == 4:
            server.is_running = False

    server._cleanup_once = always_fails
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await server.cleanup_task()

    assert passes == 4
    assert sleeps == [VeinbornServer._cleanup_delay(n) for n in (1, 2, 3, 4)]


@pytest.mark.asyncio
async def test_success_resets_backoff(monkeypatch):
    server = VeinbornServer()
    server.is_running = True
    outcomes = iter([RuntimeError("boom"), None, None])
    sleeps = []

    async def flaky():
        result = next(outcomes)
        if result:
            raise result

    async def fake_sleep(delay):
        sleeps.append(delay)
        if len(sleeps) == 3:
            server.is_running = False

    server._cleanup_once = flaky
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    await server.cleanup_task()

    base = VeinbornServer.CLEANUP_INTERVAL_SECONDS
    assert sleeps == [base * 2, base, base]


@pytest.mark.asyncio
async def test_cleanup_once_removes_expired_players():
    from server.game_session import GameSession

    server = VeinbornServer()
    game = GameSession("game1", "Test Game")
    await game.add_player("player1", "Alice", "warrior")
    await game.disconnect_player("player1")
    game.players["player1"].reconnect_timeout_seconds = 0
    server.game_manager._games["game1"] = game

    async def noop(*args, **kwargs):
        pass

    server.broadcast_to_game = noop
    server.broadcast_game_state = noop

    await server._cleanup_once()

    assert "player1" not in game.players


@pytest.mark.asyncio
async def test_cancellation_is_not_swallowed():
    server = VeinbornServer()
    server.is_running = True
    started = asyncio.Event()

    async def hang():
        started.set()
        await asyncio.sleep(3600)

    server._cleanup_once = hang
    task = asyncio.create_task(server.cleanup_task())
    await started.wait()
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
