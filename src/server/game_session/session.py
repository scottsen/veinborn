"""GameSession — manages a single multiplayer game instance."""

import asyncio
import time
import logging
from typing import Dict, List, Optional

from core.base.action import Action
from core.base.game_context import GameContext
from core.events import EventBus, GameEventType, create_game_started_event
from core.snapshot import PartyMemberView, RoundView, Snapshot
from protocol.messages import Message
from core.engine import Engine
from core.highscore import HighScoreEntry, HighScoreManager
from server.multiplayer_game_state import MultiplayerGameState, Seat

from .player_info import PlayerInfo

logger = logging.getLogger(__name__)


class GameSession:
    """Manages a single multiplayer game instance."""

    def __init__(
        self,
        game_id: str,
        game_name: str,
        max_players: int = 4,
        high_scores: Optional[HighScoreManager] = None,
        reveal_map: bool = False,
    ):
        self.game_id = game_id
        self.reveal_map = reveal_map      # dev game: no fog of war (VB-105)
        self.game_name = game_name
        self.max_players = max_players

        # Player management
        self.players: Dict[str, PlayerInfo] = {}
        self.player_order: List[str] = []

        # Game state (multiplayer-aware)
        self.mp_game_state: Optional[MultiplayerGameState] = None
        self.is_started = False
        self.is_finished = False
        self.created_at = time.time()

        # Game context and systems (initialized when game starts)
        self.game_context: Optional[GameContext] = None
        self.engine: Optional[Engine] = None
        self.event_bus = EventBus()

        # Turn management (rounds live in mp_game_state.scheduler)
        self.pending_actions: asyncio.Queue = asyncio.Queue()

        # Sequence number of state messages sent for this game
        self._seq = 0

        # Co-op scores live on their own leaderboard, one entry per player
        # (resolved lazily so tests and the server can inject a manager).
        self._high_scores = high_scores
        self._scored_player_ids: set = set()

        # Locks
        self._lock = asyncio.Lock()

    # The engine's parts, under the names callers and tests have used
    ai_system = property(lambda self: self.engine.ai_system if self.engine else None)
    turn_processor = property(lambda self: self.engine.turn_processor if self.engine else None)
    floor_manager = property(lambda self: self.engine.floor_manager if self.engine else None)
    event_handlers = property(lambda self: self.engine.event_handlers if self.engine else [])

    def can_join(self) -> bool:
        """Check if the game can accept more players."""
        return (
            len(self.players) < self.max_players
            and not self.is_started
            and not self.is_finished
        )

    async def add_player(
        self, player_id: str, player_name: str, player_class: str = "warrior"
    ) -> bool:
        """Add a player to the game session.

        Args:
            player_id: Unique player ID
            player_name: Player display name
            player_class: Character class (warrior, mage, rogue, healer)

        Returns:
            True if player was added, False otherwise
        """
        async with self._lock:
            if not self.can_join():
                return False

            if player_id in self.players:
                return False

            player_info = PlayerInfo(
                player_id=player_id,
                player_name=player_name,
                player_class=player_class,
            )
            self.players[player_id] = player_info
            self.player_order.append(player_id)

            return True

    async def remove_player(self, player_id: str) -> bool:
        """Remove a player from the game session.

        Args:
            player_id: Player ID to remove

        Returns:
            True if player was removed, False otherwise
        """
        async with self._lock:
            return self._remove_player_locked(player_id)

    def _remove_player_locked(self, player_id: str) -> bool:
        """Remove a player — caller must already hold self._lock."""
        if player_id not in self.players:
            return False

        del self.players[player_id]
        if player_id in self.player_order:
            self.player_order.remove(player_id)
        self._drop_seat_locked(player_id)

        # If game is running and no connected/disconnected players left, mark as finished
        connected_count = sum(
            1 for p in self.players.values()
            if not p.has_left()
        )
        if self.is_started and connected_count == 0:
            self.is_finished = True

        return True

    async def disconnect_player(self, player_id: str) -> bool:
        """Mark a player as disconnected but keep them in the game.

        Args:
            player_id: Player ID to disconnect

        Returns:
            True if player was marked as disconnected, False otherwise
        """
        async with self._lock:
            if player_id not in self.players:
                return False

            player_info = self.players[player_id]
            player_info.mark_disconnected()

            logger.info(
                f"Player {player_info.player_name} disconnected from game {self.game_id}. "
                f"Will be removed in {player_info.reconnect_timeout_seconds}s if not reconnected."
            )

            return True

    async def reconnect_player(self, player_id: str) -> tuple[bool, Optional[str]]:
        """Reconnect a previously disconnected player.

        Args:
            player_id: Player ID to reconnect

        Returns:
            Tuple of (success, error_message)
        """
        async with self._lock:
            if player_id not in self.players:
                return False, "Player not in game"

            player_info = self.players[player_id]

            if not player_info.is_disconnected():
                if player_info.has_left():
                    return False, "Player has left the game"
                else:
                    return False, "Player is already connected"

            # Check if reconnect timeout has expired
            if player_info.is_reconnect_timeout_expired():
                return False, "Reconnection timeout expired"

            # Mark player as reconnected
            player_info.mark_reconnected()

            logger.info(
                f"Player {player_info.player_name} reconnected to game {self.game_id}"
            )

            return True, None

    async def leave_player(self, player_id: str) -> bool:
        """Mark a player as having voluntarily left the game.

        Args:
            player_id: Player ID

        Returns:
            True if successful, False otherwise
        """
        async with self._lock:
            if player_id not in self.players:
                return False

            player_info = self.players[player_id]
            player_info.mark_left()
            self._drop_seat_locked(player_id)

            logger.info(
                f"Player {player_info.player_name} left game {self.game_id}"
            )

            self._finish_if_everyone_left()

            return True

    def _finish_if_everyone_left(self) -> None:
        """The run ends when every seat has left (plan D7)."""
        if all(p.has_left() for p in self.players.values()):
            self.is_finished = True

    def _dropped_seat_for(self, player_id: str, player_name: str) -> tuple[Optional[str], Optional[str]]:
        """Which dropped seat this player takes back: (seat's player_id, error).

        Same identity (plan ruling 7): the seat of this player id, which an auth token
        resumes; with no seat under that id, a name match, but only while exactly one
        dropped seat has that name.
        """
        dropped = {slot.player_id for slot in self.mp_game_state.dropped_seats()}
        if player_id in self.players:
            if player_id in dropped:
                return player_id, None
            return None, "Your seat is already in the game"
        named = [pid for pid in dropped if self.players[pid].player_name == player_name]
        if len(named) == 1:
            return named[0], None
        if not named:
            return None, f"No dropped seat for {player_name} in this game"
        return None, f"Several dropped seats are named {player_name}: rejoin with your original session"

    async def rejoin_player(self, player_id: str, player_name: str) -> tuple[bool, Optional[str]]:
        """A player takes back a seat that left or timed out in the running game (plan D7).

        The character returns with its state intact, near the party on the current
        floor, owed an action from the next round. Under a new player id (a name
        match) the seat is re-keyed to it.

        Returns:
            Tuple of (success, error_message)
        """
        async with self._lock:
            mp = self.mp_game_state
            if not self.is_started or mp is None:
                return False, "Game has not started"
            if self.is_finished:
                return False, "Game is finished"
            old_id, error = self._dropped_seat_for(player_id, player_name)
            if old_id is None:
                return False, error

            if old_id != player_id:
                self._rekey_player(old_id, player_id)
            mp.rejoin_seat(player_id)
            self.players[player_id].mark_reconnected()
            logger.info(f"Player {player_name} rejoined game {self.game_id}")
            return True, None

    def _rekey_player(self, old_id: str, new_id: str) -> None:
        """A dropped seat now belongs to a new player id (same name, fresh session)."""
        info = self.players[old_id]
        info.player_id = new_id
        self.players = {(new_id if pid == old_id else pid): p for pid, p in self.players.items()}
        self.player_order = [new_id if pid == old_id else pid for pid in self.player_order]
        self.mp_game_state.rekey_seat(old_id, new_id)
        if old_id in self._scored_player_ids:
            self._scored_player_ids.discard(old_id)
            self._scored_player_ids.add(new_id)

    async def cleanup_expired_disconnections(self) -> List[str]:
        """Remove players whose reconnection timeout has expired.

        Returns:
            List of player IDs that were removed
        """
        removed_players = []

        async with self._lock:
            for player_id, player_info in list(self.players.items()):
                if not player_info.is_reconnect_timeout_expired():
                    continue

                logger.info(
                    f"Removing player {player_info.player_name} from game {self.game_id} "
                    f"due to reconnection timeout"
                )
                if self.is_started:
                    # A running game keeps the record: the seat is dropped and can rejoin
                    player_info.mark_left()
                    self._drop_seat_locked(player_id)
                    self._finish_if_everyone_left()
                    removed_players.append(player_id)
                elif self._remove_player_locked(player_id):
                    removed_players.append(player_id)

        return removed_players

    async def set_player_ready(self, player_id: str, ready: bool = True) -> bool:
        """Set a player's ready status.

        Args:
            player_id: Player ID
            ready: Ready status

        Returns:
            True if status was updated, False otherwise
        """
        async with self._lock:
            if player_id not in self.players:
                return False

            self.players[player_id].is_ready = ready
            return True

    def all_players_ready(self) -> bool:
        """Check if all players are ready to start."""
        if len(self.players) == 0:
            return False
        return all(p.is_ready for p in self.players.values())

    async def start_game(self, seed: Optional[int] = None) -> bool:
        """Start the game session.

        Args:
            seed: Optional random seed for dungeon generation

        Returns:
            True if game was started, False otherwise
        """
        async with self._lock:
            if self.is_started or self.is_finished:
                return False

            if len(self.players) == 0:
                return False

            # One run for every seated player, built at once (plan D1)
            self.mp_game_state = MultiplayerGameState(
                [Seat(pid, info.player_name, info.player_class) for pid, info in self.players.items()],
                seed=seed,
                max_players=self.max_players,
            )
            self.mp_game_state.game_state.reveal_map = self.reveal_map
            for player_id, player_info in self.players.items():
                player_info.entity_id = self.mp_game_state.get_player_entity_id(player_id)

            self.game_context = GameContext(self.mp_game_state.game_state)
            # The same engine single-player runs on: actions, world tick, floors, AI,
            # content handlers (achievements, quests, kill streaks)
            self.engine = Engine(
                self.game_context,
                self.mp_game_state.config,
                self.event_bus,
                spawner=self.mp_game_state.spawner,
                log_failures=False,  # a refused action is reported to its sender only
                defeat_message="All players have died. Game over!",
            )
            # Co-op scores are recorded per player as they die, survivors when the run ends
            self.event_bus.subscribe(GameEventType.PLAYER_DIED, self._on_player_died)
            self.event_bus.subscribe(GameEventType.RUN_ENDED, self._on_run_ended)
            living = self.mp_game_state.living_entity_ids()
            self.mp_game_state.scheduler.start(living)

            self.is_started = True
            self.event_bus.publish_dict(create_game_started_event(
                living[0], self.mp_game_state.game_state.current_floor,
            ))
            logger.info(f"Game {self.game_id} started with {len(self.players)} players")

            return True

    def _finish_action(self, entity_id: str, took_turn: bool) -> None:
        """Book a successful action with the round scheduler and tick the world if due.

        The scheduler decides when the round is complete (every living player has
        taken a turn-consuming action); the tick is the same TurnProcessor
        single-player uses, so multiplayer gets wanderers and regen from one place.
        Also updates alive status and propagates game-over into session state so
        the session stops accepting actions and can be cleaned up.
        """
        mp = self.mp_game_state
        if mp.scheduler.after_action(entity_id, took_turn, mp.living_entity_ids()):
            self._world_tick()
            mp.scheduler.next_round(mp.living_entity_ids())

        # Deaths and the end of the run are announced by the engine; scoring subscribes
        mp.update_player_alive_status()
        self.engine.after_action()

        if mp.game_state.game_over:
            self.is_finished = True

    def _drop_seat_locked(self, player_id: str) -> None:
        """A running game stops waiting for a seat that left or timed out (plan D7, drop half).

        If that seat was the last one the round owed, the world ticks now, as it would
        have after their action. Rejoining a dropped seat is plan phase 5.
        """
        mp = self.mp_game_state
        if not self.is_started or mp is None or self.engine is None:
            return
        if mp.drop_seat(player_id):
            self._world_tick()
            mp.scheduler.next_round(mp.living_entity_ids())
            mp.update_player_alive_status()
            self.engine.after_action()
            if mp.game_state.game_over:
                self.is_finished = True

    def _slot_for_entity(self, entity_id):
        player_id = self.mp_game_state.entity_to_player.get(entity_id)
        return self.mp_game_state.player_slots.get(player_id)

    def _on_player_died(self, event) -> None:
        slot = self._slot_for_entity(event.data.get('entity_id'))
        if slot:
            self._record_scores([slot])

    def _on_run_ended(self, event) -> None:
        self._record_scores(self.mp_game_state.player_slots.values())

    def _world_tick(self) -> None:
        """Monsters act, time passes. Errors are logged so a bad tick cannot wedge the session."""
        try:
            self.engine.tick()
        except Exception as e:
            logger.error(f"Error processing world turn: {e}", exc_info=True)

    def _record_scores(self, slots) -> None:
        """Record each given player's run on the multiplayer leaderboard, once.

        Players are scored the moment they die, survivors when the game ends.
        Never raises: a leaderboard failure must not break the game.
        """
        game_state = self.mp_game_state.game_state
        for slot in slots:
            if slot.player_id in self._scored_player_ids or not slot.player_entity:
                continue
            self._scored_player_ids.add(slot.player_id)

            try:
                hsm = self._high_scores or HighScoreManager.get_multiplayer_instance()
                entry = HighScoreEntry.from_game_state(
                    game_state, slot.player_name, player=slot.player_entity
                )
                rank = hsm.add_score(entry)

                if rank > 0:
                    self.mp_game_state.add_message(
                        f"{slot.player_name}'s final score: {entry.score} "
                        f"(co-op rank #{rank})"
                    )
                logger.info(
                    f"Co-op high score recorded: {slot.player_name} scored "
                    f"{entry.score} (rank #{rank}) in game {self.game_id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to record co-op high score for {slot.player_name}: {e}",
                    exc_info=True,
                )

    async def process_intent(
        self, player_id: str, intent: str, args: Optional[dict] = None
    ) -> tuple[bool, Optional[str]]:
        """Build the action for an intent and run it for this player's seat.

        The actor is always the seat's entity (never taken from the client), and
        the action is built by the same ActionFactory single-player uses.
        """
        args = dict(args or {})
        args.pop("actor_id", None)  # never accept an actor from the wire
        if not self.engine or not self.mp_game_state or not self.mp_game_state.game_state:
            return False, "Game state not initialized"
        entity_id = self.mp_game_state.get_player_entity_id(player_id)
        if not entity_id:
            return False, "Player not in game"
        slot = self.mp_game_state.player_slots[player_id]
        if not slot.is_alive:
            # Say why before the factory refuses a dead actor with a bare "Cannot <intent>"
            return False, "You are dead - spectating until the run ends"

        # No await between building and handing over: factory reads state synchronously
        state = self.mp_game_state.game_state
        before = state.message_count
        action = self.engine.make_action(intent, actor_id=entity_id, **args)
        if action is None:
            added = state.message_count - before
            return False, (state.messages[-1] if added > 0 else f"Cannot {intent}")
        return await self.process_action(player_id, action)

    async def process_action(
        self, player_id: str, action: Action
    ) -> tuple[bool, Optional[str]]:
        """Process a player action.

        Args:
            player_id: Player performing the action
            action: Action to process

        Returns:
            Tuple of (success, error_message)
        """
        async with self._lock:
            if not self.is_started or self.is_finished:
                return False, "Game is not active"

            if player_id not in self.players:
                return False, "Player not in game"

            # Check if player is disconnected - reject action from disconnected players
            player_info = self.players[player_id]
            if player_info.is_disconnected():
                return False, "You are disconnected - reconnect to act"

            if not self.mp_game_state or not self.mp_game_state.game_state:
                return False, "Game state not initialized"

            # Dead players spectate until the run ends (the party plays on while anyone lives)
            slot = self.mp_game_state.player_slots.get(player_id)
            if slot and not slot.is_alive:
                return False, "You are dead - spectating until the run ends"

            # Validate action belongs to player
            if player_info.entity_id and action.actor_id != player_info.entity_id:
                return False, "Action actor does not match player entity"

            # One turn-consuming action per living player per round
            if not action.free and not self.mp_game_state.scheduler.can_act(action.actor_id):
                waiting = [
                    self.players[pid].player_name
                    for pid in self.mp_game_state.waiting_on() if pid in self.players
                ]
                return False, "Waiting for the party" + (f": {', '.join(waiting)}" if waiting else "")

            # Execute through the engine (same pipeline as single-player)
            try:
                result = self.engine.execute(action, action.get_action_type())
                if not result.outcome.is_success:
                    return False, "; ".join(result.outcome.messages) or "Action failed"

                took_turn = result.took_turn
                self._finish_action(action.actor_id, took_turn)

                return True, None

            except Exception as e:
                logger.error(f"Action execution error: {e}", exc_info=True)
                return False, f"Action execution failed: {str(e)}"

    def rejoinable_names(self) -> List[str]:
        """Names of the dropped seats of a running game (what a lobby list offers to rejoin)."""
        if not self.is_started or self.is_finished or self.mp_game_state is None:
            return []
        return [
            slot.player_name for slot in self.mp_game_state.dropped_seats()
            if slot.player_id in self.players
        ]

    def get_disconnected_players(self) -> List[str]:
        """Get list of disconnected player IDs.

        Returns:
            List of player IDs who are disconnected
        """
        return [
            player_id
            for player_id, player_info in self.players.items()
            if player_info.is_disconnected() and player_info.is_alive
        ]

    def game_info(self) -> Dict:
        """The game-level facts that sit beside a snapshot on the wire."""
        return {
            "game_id": self.game_id,
            "game_name": self.game_name,
            "is_started": self.is_started,
            "is_finished": self.is_finished,
            "max_players": self.max_players,
        }

    def lobby_dict(self) -> Dict:
        """The game before it starts."""
        return {
            **self.game_info(),
            "players": [
                {
                    "player_id": p.player_id,
                    "player_name": p.player_name,
                    "player_class": p.player_class,
                    "is_ready": p.is_ready,
                }
                for p in self.players.values()
            ],
        }

    def snapshot_for(self, player_id: str) -> Snapshot:
        """What this player's seat sees, with the party and the round filled in.

        A dead player gets the view from their own (possibly purged) character, so
        they can spectate until the run ends.
        """
        mp = self.mp_game_state
        slot = mp.player_slots[player_id]
        snap = self.engine.snapshot(slot.player_entity)
        snap.party = [
            PartyMemberView(
                player_id=s.player_id,
                name=s.player_name,
                player_class=s.player_entity.stats.get('class_type', 'warrior'),
                entity_id=s.entity_id,
                alive=s.is_alive,
                # Dropped (left, timed out) or in its reconnect grace: not connected
                connected=s.is_active and s.player_id in self.players
                and not self.players[s.player_id].is_disconnected(),
                grace_left=(self.players[s.player_id].grace_seconds_left()
                            if s.player_id in self.players else None),
            )
            for s in mp.player_slots.values()
        ]
        seats = [s.entity_id for s in mp.player_slots.values()]   # seat order: what players read
        snap.round = RoundView(
            number=mp.round_number,
            waiting_on=[e for e in seats if e in mp.scheduler.owed],
            acted=[e for e in seats if e in mp.scheduler.acted],
        )
        return snap

    def state_messages(self) -> Dict[str, Message]:
        """One state message per seated player, built together so they share a `seq`.

        Before the game starts that is the lobby (the same for everyone); after, each
        player's own snapshot. Built synchronously: nothing can change the game between
        two recipients' views, and a slow send can never reorder them.
        """
        if not self.is_started or not self.engine:
            lobby = Message.lobby(self.lobby_dict())
            return {pid: lobby for pid in self.players}
        self._seq += 1
        info = self.game_info()
        return {
            pid: Message.snapshot(self._seq, info, self.snapshot_for(pid).to_dict())
            for pid in self.players if pid in self.mp_game_state.player_slots
        }

    def get_player_count(self) -> int:
        """Get the number of players in the game."""
        return len(self.players)

    def get_player_names(self) -> List[str]:
        """Get list of player names."""
        return [p.player_name for p in self.players.values()]

