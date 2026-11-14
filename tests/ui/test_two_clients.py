"""Two TUI clients play one server's game (plan phase 4d, VB-102).

Alice creates, Bob joins with the id from Alice's lobby line, both ready up.
Each sees the other on the map, the round waits for both, and a second move
before the partner has acted is refused with the reason in the player's log.
"""
import asyncio

import pytest

from server.websocket_server import VeinbornServer
from ui.multiplayer_client import MultiplayerClient
from ui.textual.app import VeinbornApp

pytestmark = pytest.mark.unit

STEP_KEYS = {"h": (-1, 0), "l": (1, 0), "k": (0, -1), "j": (0, 1)}


async def until(predicate, pilots, timeout=4.0):
    loop = asyncio.get_running_loop()
    end = loop.time() + timeout
    while not predicate():
        if loop.time() > end:
            raise AssertionError("condition not reached")
        for pilot in pilots:
            await pilot.pause(0.02)


def free_step(game, entity_id):
    """A vi key whose target is walkable and empty on the server, or None."""
    state = game.mp_game_state.game_state
    me = state.entities[entity_id]
    blocked = {(e.x, e.y) for e in state.entities.values() if e is not me and e.blocks_movement}
    for key, (dx, dy) in STEP_KEYS.items():
        x, y = me.x + dx, me.y + dy
        if state.dungeon_map.is_walkable(x, y) and (x, y) not in blocked:
            return key, (x, y)
    return None


def pos(app):
    snap = app.driver.snapshot()
    return (snap.player.x, snap.player.y)


def cell_text(app, x, y):
    return app.map_widget._render_cell(x, y, app.map_widget.snapshot).text


def test_two_apps_share_a_game_and_the_round_waits_for_both():
    async def scenario():
        server = VeinbornServer("127.0.0.1", 0)
        await server.start()
        port = server.server.sockets[0].getsockname()[1]
        a_client = MultiplayerClient(host="127.0.0.1", port=port)
        b_client = MultiplayerClient(host="127.0.0.1", port=port)

        async def alice_setup(c):
            return await c.connect("Alice") and (await c.create_game("Duo", player_class="warrior") or True)

        game_id = {}

        async def bob_setup(c):
            ok = await c.connect("Bob")
            await c.join_game(game_id["id"], player_class="mage")
            return ok

        alice = VeinbornApp(multiplayer_client=a_client, multiplayer_setup=alice_setup)
        bob = VeinbornApp(multiplayer_client=b_client, multiplayer_setup=bob_setup)
        try:
            async with alice.run_test() as pa:
                await until(lambda: a_client.lobby.get("game_id"), [pa])
                await pa.pause()
                # Bob would read the id off Alice's status bar
                line = alice.status_bar.render().plain
                game_id["id"] = a_client.lobby["game_id"]
                assert game_id["id"] in line

                async with bob.run_test() as pb:
                    pilots = [pa, pb]
                    await until(lambda: len(a_client.lobby.get("players", [])) == 2, pilots)
                    await pa.pause()
                    assert "Bob (mage)" in alice.status_bar.render().plain

                    await pa.press("R")
                    await until(lambda: any(p.get("is_ready") for p in b_client.lobby.get("players", [])), pilots)
                    assert alice.driver.snapshot() is None          # Bob is not ready yet
                    await pb.press("R")
                    await until(lambda: alice.driver.snapshot() and bob.driver.snapshot(), pilots)
                    for p in pilots:
                        await p.pause()

                    game = await server.game_manager.get_game(game_id["id"])
                    a_snap, b_snap = alice.driver.snapshot(), bob.driver.snapshot()
                    assert [m.name for m in a_snap.party] == ["Alice", "Bob"]

                    # Each sees the other, drawn as an ally
                    bx, by = pos(bob)
                    ax, ay = pos(alice)
                    assert cell_text(alice, bx, by) == "@" and cell_text(bob, ax, ay) == "@"
                    assert "waiting on Alice, Bob" in alice.status_bar.render().plain

                    # Alice moves; the round now waits on Bob only
                    step = free_step(game, a_snap.player.entity_id)
                    assert step, "no free tile next to Alice on this seed"
                    key, target = step
                    await pa.press(key)
                    await until(lambda: pos(alice) == target, pilots)
                    await until(lambda: "waiting on Bob" in alice.status_bar.render().plain, pilots)
                    # Bob's screen shows Alice where she went
                    await until(lambda: cell_text(bob, *target) == "@", pilots)

                    # A second move before Bob acts is refused, with the reason in Alice's log
                    await pa.press("." )
                    await until(lambda: "Waiting for the party: Bob" in alice.message_log.render().plain, pilots)
                    assert pos(alice) == target and game.mp_game_state.round_number == 0

                    # Bob acts: the round rolls over and both are owed again
                    await pb.press(".")
                    await until(lambda: game.mp_game_state.round_number == 1, pilots)
                    await until(lambda: "Round 1: waiting on Alice, Bob" in bob.status_bar.render().plain, pilots)
        finally:
            await server.stop()

    asyncio.run(scenario())
