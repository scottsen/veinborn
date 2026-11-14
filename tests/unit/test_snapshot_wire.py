"""A snapshot survives JSON unchanged: the form it takes on the wire (VB-96)."""

import asyncio
import json

from core.game import Game
from core.loot import LootGenerator
from core.snapshot import PartyMemberView, RoundView, Snapshot
from server.game_session import GameSession


def _over_the_wire(snap: Snapshot) -> Snapshot:
    return Snapshot.from_dict(json.loads(json.dumps(snap.to_dict())))


def _geared_game():
    game = Game()
    game.start_new_game(seed=5, player_name="Solo")
    player = game.state.player
    for item_id in ("long_sword", "chainmail", "potion_healing"):
        assert player.add_to_inventory(LootGenerator.get_instance().create_item(item_id))
    game.handle_player_action('equip', item_id=player.inventory[0].entity_id)
    game.handle_player_action('equip', item_id=player.inventory[0].entity_id)
    return game


def test_single_player_snapshot_round_trips():
    game = Game()
    game.start_new_game(seed=5, player_name="Solo")
    snap = game.engine.snapshot()

    assert snap.party == [] and snap.round is None
    assert _over_the_wire(snap) == snap


def test_gear_and_inventory_survive_the_wire():
    snap = _geared_game().engine.snapshot()
    assert snap.player.weapon is not None and snap.player.armor is not None
    assert snap.player.inventory  # the potion

    back = _over_the_wire(snap)

    assert back == snap
    assert back.player.weapon.name == snap.player.weapon.name
    assert [i.content_id for i in back.player.inventory] == [i.content_id for i in snap.player.inventory]


async def _party_session():
    game = GameSession("g", "t", max_players=4)
    for i, cls in enumerate(["warrior", "mage", "rogue"]):
        await game.add_player(f"p{i}", f"P{i}", cls)
    await game.start_game(seed=3)
    return game


def test_party_snapshot_with_party_and_round_round_trips():
    game = asyncio.run(_party_session())
    mp = game.mp_game_state
    viewer = mp.player_slots["p1"].player_entity
    snap = game.engine.snapshot(viewer)
    snap.party = [
        PartyMemberView(s.player_id, s.player_name, "warrior", s.entity_id, s.is_alive, True)
        for s in mp.player_slots.values()
    ]
    snap.round = RoundView(number=2, waiting_on=[viewer.entity_id], acted=["player"])

    back = _over_the_wire(snap)

    assert back == snap
    assert back.player.entity_id == viewer.entity_id
    # the other two players are entities in this viewer's world, the viewer is not
    others = [e for e in back.entities if e.entity_type == "player"]
    assert len(others) == 2 and viewer.entity_id not in {e.entity_id for e in others}


def test_a_dead_viewer_still_gets_a_snapshot_after_being_purged():
    game = asyncio.run(_party_session())
    mp = game.mp_game_state
    dead = mp.player_slots["p2"].player_entity
    dead.take_damage(dead.hp)
    mp.game_state.cleanup_dead_entities()  # a dead guest leaves state.entities (VB-16)
    assert dead.entity_id not in mp.game_state.entities

    snap = game.engine.snapshot(dead)

    assert snap.player.entity_id == dead.entity_id and snap.player.alive is False
    assert _over_the_wire(snap) == snap


def test_engine_snapshot_accepts_an_entity_id():
    game = asyncio.run(_party_session())
    other = game.mp_game_state.player_slots["p1"].player_entity
    assert game.engine.snapshot(other.entity_id).player.entity_id == other.entity_id
