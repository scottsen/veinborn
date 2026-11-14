"""The multiplayer TUI connects from inside Textual's event loop (VB-44 note #2).

run_multiplayer used to ``asyncio.run`` the connect, so MultiplayerClient._listen
(a task of that loop) was cancelled the moment it returned.
"""

import asyncio

from server.websocket_server import VeinbornServer
from ui.multiplayer_client import MultiplayerClient
from ui.textual.app import VeinbornApp


def test_setup_runs_in_the_app_loop_and_the_listener_survives():
    async def scenario():
        server = VeinbornServer("127.0.0.1", 0)
        await server.start()
        port = server.server.sockets[0].getsockname()[1]
        client = MultiplayerClient(host="127.0.0.1", port=port)
        seen = {}

        async def setup(c):
            seen["loop"] = asyncio.get_running_loop()
            return await c.connect("Tester")

        app = VeinbornApp(seed=5, multiplayer_client=client, multiplayer_setup=setup)
        try:
            async with app.run_test() as pilot:
                await pilot.pause(0.2)
                assert seen["loop"] is asyncio.get_running_loop()
                assert client.state.is_connected
                assert client._listen_task is not None and not client._listen_task.done()
                assert await client.submit("move", dx=1, dy=0)
        finally:
            await server.stop()
        # on_unmount closed the connection in the same loop
        assert not client.state.is_connected

    asyncio.run(scenario())


def test_submit_when_disconnected_returns_false():
    client = MultiplayerClient()
    assert asyncio.run(client.submit("move", dx=1, dy=0)) is False


def test_act_when_disconnected_says_so():
    client = MultiplayerClient()
    assert asyncio.run(client.act("move", dx=1, dy=0)) == (False, ["Not connected to the server."])
