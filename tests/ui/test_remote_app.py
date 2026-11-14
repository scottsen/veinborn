"""The TUI plays a server's game through a RemoteDriver (plan phase 4c, VB-101).

Real server, real websocket client, real Textual app: the screen draws the
server's snapshot, keys go over the wire as intents, and nothing runs locally.
"""
import asyncio

import pytest

from server.websocket_server import VeinbornServer
from ui.driver import RemoteDriver
from ui.multiplayer_client import MultiplayerClient
from ui.textual.app import VeinbornApp

pytestmark = pytest.mark.unit

STEP_KEYS = {"h": (-1, 0), "l": (1, 0), "k": (0, -1), "j": (0, 1)}


async def until(predicate, pilot, timeout=3.0):
    loop = asyncio.get_running_loop()
    end = loop.time() + timeout
    while not predicate():
        if loop.time() > end:
            raise AssertionError("condition not reached")
        await pilot.pause(0.05)


def free_step(server, game_id, entity_id):
    """A vi key whose target tile is walkable and empty, read from the server's state."""
    game = server.game_manager._games[game_id]
    state = game.mp_game_state.game_state
    me = state.entities[entity_id]
    blocked = {(e.x, e.y) for e in state.entities.values() if e is not me and e.blocks_movement}
    for key, (dx, dy) in STEP_KEYS.items():
        x, y = me.x + dx, me.y + dy
        if state.dungeon_map.is_walkable(x, y) and (x, y) not in blocked:
            return key, (x, y)
    pytest.skip("no free neighbour on this seed")


def test_lobby_ready_move_and_refusal_through_the_app():
    async def scenario():
        server = VeinbornServer("127.0.0.1", 0)
        await server.start()
        port = server.server.sockets[0].getsockname()[1]
        client = MultiplayerClient(host="127.0.0.1", port=port)

        async def setup(c):
            return await c.connect("Alice") and (await c.create_game("Remote", player_class="warrior") or True)

        app = VeinbornApp(multiplayer_client=client, multiplayer_setup=setup)
        assert isinstance(app.driver, RemoteDriver) and not hasattr(app.driver, 'game')
        try:
            async with app.run_test() as pilot:
                # Lobby: no snapshot yet, the status bar says how to start
                await until(lambda: client.lobby.get("players"), pilot)
                await pilot.pause()
                lobby_line = app.status_bar.render().plain
                assert "Lobby 'Remote'" in lobby_line and client.state.game_id in lobby_line
                assert "Alice (warrior)" in lobby_line and "R: ready" in lobby_line
                await pilot.press("l")                       # no game yet: nothing is sent
                await pilot.pause()

                await pilot.press("R")
                await until(lambda: app.driver.snapshot() is not None, pilot)
                await pilot.pause()
                snap = app.driver.snapshot()
                assert app.status_bar.render().plain.startswith(f"HP: {snap.player.hp}/{snap.player.max_hp}")
                assert "Round 0" in app.status_bar.render().plain
                assert (app.map_widget.snapshot.player.x, app.map_widget.snapshot.player.y) == (snap.player.x, snap.player.y)

                # A move key moves this seat on the server, and the screen follows
                key, target = free_step(server, client.state.game_id, snap.player.entity_id)
                await pilot.press(key)
                await until(lambda: (app.driver.snapshot().player.x, app.driver.snapshot().player.y) == target, pilot)
                await pilot.pause()
                assert (app.map_widget.snapshot.player.x, app.map_widget.snapshot.player.y) == target

                # A refused intent: its reason reaches this player's log
                game = server.game_manager._games[client.state.game_id]
                alice = game.mp_game_state.get_player_entity(client.state.player_id)
                alice.inventory.clear()
                await pilot.press("d")
                await until(lambda: "You have nothing to drop." in app.message_log.render().plain, pilot)

                # Listings are local notes, merged into the server's log
                await pilot.press("i")
                await pilot.pause()
                assert "Your inventory is empty." in app.message_log.render().plain

                # Save/load/restart do not exist for a server's game
                await pilot.press("S")
                await pilot.pause()
                assert "Saving is only available in single-player." in app.message_log.render().plain
        finally:
            await server.stop()

    asyncio.run(scenario())


def test_remote_driver_merges_new_server_lines_with_notes_in_order():
    """New server lines are told apart by message_count, so a repeated line is not shown twice."""
    from core.snapshot import Snapshot

    class StubClient:
        snapshot = None
        lobby = {}
        on_snapshot = on_lobby = None

    def snap(lines, count):
        base = Snapshot.__new__(Snapshot)
        base.__dict__.update(turn=0, floor=1, game_over=False, victory=False, player=None, entities=[],
                             map=None, messages=list(lines), message_count=count, party=[], round=None)
        return base

    client = StubClient()
    driver = RemoteDriver(client)
    client.on_snapshot(snap(["a", "b"], 2))
    driver.note("note-1")
    client.on_snapshot(snap(["a", "b", "c"], 3))        # one new line
    client.on_snapshot(snap(["a", "b", "c"], 3))        # nothing new (another player's snapshot)
    client.on_snapshot(snap(["b", "c", "d", "d"], 5))   # two new, one a repeat of the text before
    assert driver.snapshot().messages == ["a", "b", "note-1", "c", "d", "d"]
