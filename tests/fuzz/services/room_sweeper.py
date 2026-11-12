"""
RoomSweeper - visit every room on a floor, clearing monsters, then leave.

Why it exists: the class bots used to head for the stairs only when the floor
was empty of monsters (or of monsters they could see). With wandering spawns
(VB-52) the floor is never empty, so the bots stopped descending. The sweeper
gives them a finite goal instead: each room visited and clear is done, and when
every room is done (or the floor's turn budget runs out) the floor is done.

Per floor it remembers which rooms are finished. Each step it returns what to
walk toward next:

    ('monster', entity)   a fightable monster inside the room we are in
    ('room', (x, y))      the centre of the nearest unfinished room
    ('stairs', (x, y))    every room finished: go down
    None                  nothing to do (e.g. already standing on the stairs)

`fight` is a predicate (monster -> bool) that carries each class's temperament:
a warrior fights anything it judges winnable, a rogue only easy targets, a mage
nothing (it still visits rooms, it just doesn't hunt).
"""

import logging
from typing import Callable, Optional, Tuple

logger = logging.getLogger(__name__)

MAX_FLOOR_TURNS = 1500   # leave after this many game turns on a floor, cleared or not
GIVE_UP_TURNS = 60       # turns spent walking to one room before it is written off


class RoomSweeper:
    def __init__(self, perception, max_floor_turns: int = MAX_FLOOR_TURNS,
                 give_up_turns: int = GIVE_UP_TURNS):
        self.perception = perception
        self.max_floor_turns = max_floor_turns
        self.give_up_turns = give_up_turns
        self._map = None          # held (not just id'd) so an address can't be reused
        self._start_turn = 0
        self._finished = set()
        self._target = None
        self._target_turns = 0

    # --- state ------------------------------------------------------------

    def _sync(self, game) -> None:
        """Start fresh whenever the floor (its map object) changes."""
        game_map = game.state.dungeon_map
        if game_map is not self._map:
            self._map = game_map
            self._start_turn = game.state.turn_count
            self._finished = set()
            self._target = None
            self._target_turns = 0

    @staticmethod
    def _contains(room, x: int, y: int) -> bool:
        return room.x <= x < room.x + room.width and room.y <= y < room.y + room.height

    def _room_at(self, game, x: int, y: int) -> Optional[int]:
        for index, room in enumerate(game.state.dungeon_map.rooms):
            if self._contains(room, x, y):
                return index
        return None

    # --- queries ----------------------------------------------------------

    def done(self, game) -> bool:
        """Every room finished, or the floor's turn budget spent."""
        self._sync(game)
        if game.state.turn_count - self._start_turn >= self.max_floor_turns:
            return True
        return len(self._finished) >= len(game.state.dungeon_map.rooms)

    def ready_to_leave(self, game) -> bool:
        """May the bot take the stairs now? Also true when no monster is left."""
        return self.done(game) or not self.perception.find_monsters(game)

    # --- planning ---------------------------------------------------------

    def next_step(self, game, fight: Optional[Callable] = None) -> Optional[Tuple[str, object]]:
        self._sync(game)
        player = game.state.player
        game_map = game.state.dungeon_map

        if self.done(game):
            stairs = self.perception.find_level_exit(game)
            if stairs and (player.x, player.y) != tuple(stairs):
                return ('stairs', tuple(stairs))
            return None

        here = self._room_at(game, player.x, player.y)
        if here is not None and here not in self._finished:
            room = game_map.rooms[here]
            targets = [
                m for m in self.perception.find_monsters(game)
                if self._contains(room, m.x, m.y) and fight is not None and fight(m)
            ]
            if targets:
                nearest = min(targets, key=lambda m: abs(m.x - player.x) + abs(m.y - player.y))
                return ('monster', nearest)
            self._finish(here)

        index = self._pick_room(game)
        if index is None:
            return self.next_step(game, fight) if self.done(game) else None

        if index != self._target:
            self._target, self._target_turns = index, 0
        self._target_turns += 1
        if self._target_turns > self.give_up_turns:
            logger.debug(f"RoomSweeper: giving up on room {index} (unreachable or blocked)")
            self._finish(index)
            return self.next_step(game, fight)
        return ('room', game_map.rooms[index].center)

    def _finish(self, index: int) -> None:
        self._finished.add(index)
        if self._target == index:
            self._target, self._target_turns = None, 0

    def _pick_room(self, game) -> Optional[int]:
        player = game.state.player
        remaining = [
            (abs(room.center[0] - player.x) + abs(room.center[1] - player.y), index)
            for index, room in enumerate(game.state.dungeon_map.rooms)
            if index not in self._finished
        ]
        return min(remaining)[1] if remaining else None
