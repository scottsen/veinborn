"""WebSocket client for multiplayer game sessions."""

import asyncio
import logging
from typing import Optional, Callable, Dict, List, Tuple
from dataclasses import dataclass, field

try:
    import websockets
except ImportError:
    websockets = None

from protocol import PROTOCOL_VERSION
from protocol.messages import Message
from core.snapshot import Snapshot

logger = logging.getLogger('veinborn.multiplayer_client')


@dataclass
class ChatMessage:
    """Represents a chat message."""
    player_name: str
    message: str
    player_id: str = ""


@dataclass
class MultiplayerState:
    """State for multiplayer session."""
    is_connected: bool = False
    session_id: Optional[str] = None
    player_id: Optional[str] = None
    player_name: Optional[str] = None
    game_id: Optional[str] = None
    auth_token: Optional[str] = None
    errors: list = field(default_factory=list)        # error texts the server sent, newest last
    chat_messages: list = field(default_factory=list)  # List of ChatMessage objects


class MultiplayerClient:
    """Client for connecting to Veinborn multiplayer server."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        # Called when the auth token or game id changes (a restarted client resumes from them)
        self.on_session: Optional[Callable[[], None]] = None
        # Set while a join from a saved session is in flight: if the server refuses it
        # (game gone) the saved game id is dropped so the next start is not stuck on it
        self.resume_game_id: Optional[str] = None
        """Initialize the multiplayer client.

        Args:
            host: WebSocket server host
            port: WebSocket server port
        """
        if websockets is None:
            raise ImportError("websockets library not installed. Install with: pip install websockets")

        self.host = host
        self.port = port
        self.ws = None
        self.state = MultiplayerState()

        # What the server last told us. A snapshot is this player's whole view, so there
        # is nothing to merge: keep the newest (highest seq), drop anything older.
        self.snapshot: Optional[Snapshot] = None
        self.game_info: Dict = {}      # game id/name/started/finished beside the snapshot
        self.lobby: Dict = {}          # the game before it starts
        self.last_seq = 0

        # Callbacks
        self.on_chat_message: Optional[Callable[[ChatMessage], None]] = None
        self.on_system_message: Optional[Callable[[str], None]] = None
        self.on_snapshot: Optional[Callable[[Snapshot], None]] = None
        self.on_lobby: Optional[Callable[[Dict], None]] = None

        # Background tasks
        self._listen_task: Optional[asyncio.Task] = None
        self._running = False

        # Intents awaiting their intent_result, by request id
        self._next_rid = 0
        self._pending: Dict[int, asyncio.Future] = {}

    async def connect(self, player_name: str, auth_token: Optional[str] = None) -> bool:
        """Connect to the multiplayer server and authenticate.

        Args:
            player_name: Name for this player
            auth_token: Previously issued token to resume a session (reconnect)
                instead of minting a new one. Ignored if not recognized by
                the server.

        Returns:
            True if connection and authentication succeeded
        """
        uri = f"ws://{self.host}:{self.port}"
        logger.info(f"Connecting to multiplayer server at {uri}...")

        try:
            self.ws = await websockets.connect(uri)
            logger.info("Connected to server")

            # Send authentication
            self.state.player_name = player_name
            auth_msg = Message.auth(player_name, auth_token=auth_token)
            await self.ws.send(auth_msg.to_json())
            logger.info(f"Sent authentication as '{player_name}'")

            # Wait for auth response
            response_str = await self.ws.recv()
            response = Message.from_json(response_str)

            if response.v != PROTOCOL_VERSION:
                logger.error(f"Protocol version mismatch: server {response.v}, client {PROTOCOL_VERSION}")
                return False

            if response.type == "auth_success":
                self.state.session_id = response.data["session_id"]
                self.state.player_id = response.data["player_id"]
                self.state.auth_token = response.data.get("auth_token", auth_token)
                self.state.is_connected = True
                logger.info(f"Authenticated successfully as {player_name}")
                logger.info(f"Session ID: {self.state.session_id}")
                logger.info(f"Player ID: {self.state.player_id}")

                # Start listening for messages
                self._running = True
                self._listen_task = asyncio.create_task(self._listen())

                return True
            else:
                logger.error(f"Authentication failed: {response.data}")
                return False

        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    async def reconnect(self) -> bool:
        """Reconnect using the session's stored auth_token and, if the
        session was previously in a game, resume that game.

        Returns:
            True if reconnection (and game resume, if applicable) succeeded
        """
        if not self.state.auth_token or not self.state.player_name:
            logger.warning("Cannot reconnect: no prior session to resume")
            return False

        was_in_game = self.state.game_id is not None

        connected = await self.connect(self.state.player_name, auth_token=self.state.auth_token)
        if not connected:
            return False

        if was_in_game:
            reconnect_msg = Message.reconnect(self.state.session_id)
            await self.ws.send(reconnect_msg.to_json())
            logger.info(f"Sent reconnect request for game {self.state.game_id}")

        return True

    async def disconnect(self):
        """Disconnect from the server."""
        self._running = False

        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None

        if self.ws:
            await self.ws.close()
            self.ws = None

        self.state.is_connected = False
        logger.info("Disconnected from multiplayer server")

    async def send_chat(self, message: str):
        """Send a chat message to all players in the game.

        Args:
            message: Chat message text
        """
        if not self.ws or not self.state.is_connected:
            logger.warning("Cannot send chat: not connected")
            return

        if not self.state.game_id:
            logger.warning("Cannot send chat: not in a game")
            return

        msg = Message(type="chat", data={"message": message})
        await self.ws.send(msg.to_json())
        logger.debug(f"Sent chat message: {message}")

    async def create_game(self, game_name: str, player_class: str = "warrior", max_players: int = 4,
                          reveal_map: bool = False):
        """Create a new multiplayer game.

        Args:
            game_name: Name for the game
            player_class: Character class (warrior, mage, rogue, healer)
            max_players: Maximum number of players (default 4)
            reveal_map: Dev game with no fog of war (VB-105)
        """
        if not self.ws or not self.state.is_connected:
            logger.warning("Cannot create game: not connected")
            return

        msg = Message.create_game(game_name, max_players=max_players, player_class=player_class,
                                     reveal_map=reveal_map)
        await self.ws.send(msg.to_json())
        logger.info(f"Sent create game request: '{game_name}'")

    async def join_game(self, game_id: str, player_class: str = "warrior"):
        """Join an existing game.

        Args:
            game_id: Game ID to join
            player_class: Character class (warrior, mage, rogue, healer)
        """
        if not self.ws or not self.state.is_connected:
            logger.warning("Cannot join game: not connected")
            return

        msg = Message.join_game(game_id, player_class=player_class)
        await self.ws.send(msg.to_json())
        logger.info(f"Sent join game request: {game_id}")

    async def submit(self, intent: str, **args) -> bool:
        """Send a player intent (e.g. ``submit('move', dx=1, dy=0)``).

        The server decides who acts from this session's seat, so no actor id is
        sent. Returns False if not connected.
        """
        if not self.ws or not self.state.is_connected:
            logger.warning(f"Cannot submit {intent!r}: not connected")
            return False

        await self.ws.send(Message.intent(intent, **args).to_json())
        return True

    async def act(self, intent: str, timeout: float = 5.0, **args) -> Tuple[bool, List[str]]:
        """Send an intent and wait for the server's answer to it.

        Returns (accepted, lines): lines say why a refused intent was refused. An
        accepted intent's state has already arrived as a snapshot when this returns.
        """
        if not self.ws or not self.state.is_connected:
            return False, ["Not connected to the server."]
        self._next_rid += 1
        rid = self._next_rid
        future = asyncio.get_running_loop().create_future()
        self._pending[rid] = future
        try:
            await self.ws.send(Message.intent(intent, rid=rid, **args).to_json())
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            logger.warning(f"No intent_result for {intent!r} (rid {rid}) within {timeout}s")
            return False, ["No answer from the server."]
        finally:
            self._pending.pop(rid, None)

    async def request_snapshot(self) -> bool:
        """Ask the server for the current state (after a gap, or on joining late)."""
        if not self.ws or not self.state.is_connected:
            return False
        await self.ws.send(Message.get_snapshot().to_json())
        return True

    async def send_ready(self):
        """Send ready status to start the game."""
        if not self.ws or not self.state.is_connected:
            logger.warning("Cannot send ready: not connected")
            return

        msg = Message(type="ready", data={"ready": True})
        await self.ws.send(msg.to_json())
        logger.info("Sent ready status")

    async def _listen(self):
        """Listen for messages from the server (background task)."""
        if not self.ws:
            return

        try:
            async for message_str in self.ws:
                if not self._running:
                    break

                try:
                    message = Message.from_json(message_str)
                    await self._handle_message(message)
                except Exception as e:
                    logger.error(f"Error handling message: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by server")
            self.state.is_connected = False
        except Exception as e:
            logger.error(f"Listen error: {e}")
            self.state.is_connected = False

    async def _handle_message(self, message: Message):
        """Handle a message from the server.

        Args:
            message: Received message
        """
        msg_type = message.type

        if msg_type == "chat_message":
            # Handle incoming chat message
            player_name = message.data.get("player_name", "Unknown")
            player_id = message.data.get("player_id", "")
            text = message.data.get("message", "")

            chat_msg = ChatMessage(
                player_name=player_name,
                player_id=player_id,
                message=text
            )

            # Store in history
            self.state.chat_messages.append(chat_msg)

            # Keep only last 100 messages
            if len(self.state.chat_messages) > 100:
                self.state.chat_messages = self.state.chat_messages[-100:]

            # Call callback
            if self.on_chat_message:
                self.on_chat_message(chat_msg)

            logger.debug(f"Chat from {player_name}: {text}")

        elif msg_type == "system":
            # Handle system message
            text = message.data.get("message", "")
            level = message.data.get("level", "info")

            if self.on_system_message:
                self.on_system_message(text)

            logger.info(f"System message ({level}): {text}")

        elif msg_type == "error":
            self._refused(message.data.get("message", ""))
            if self.resume_game_id and self.state.game_id is None:
                logger.info(f"Saved game {self.resume_game_id} is gone: forgetting it")
                self.resume_game_id = None
                if self.on_session:
                    self.on_session()    # saves the current state, which has no game id

        elif msg_type == "intent_result":
            ok = bool(message.data.get("ok"))
            lines = list(message.data.get("messages") or [])
            if not ok:
                for text in lines or ["Action refused"]:
                    self._refused(text)
            future = self._pending.get(message.data.get("rid"))
            if future is not None and not future.done():
                future.set_result((ok, lines))

        elif msg_type == "snapshot":
            if message.seq is not None and message.seq <= self.last_seq:
                logger.debug(f"Ignoring stale snapshot (seq {message.seq} <= {self.last_seq})")
                return
            self.last_seq = message.seq or self.last_seq
            self.snapshot = Snapshot.from_dict(message.data["snapshot"])
            self.game_info = message.data.get("game", {})
            self.lobby = {}
            if self.game_info.get("game_id"):
                self._set_game_id(self.game_info["game_id"])

            if self.on_snapshot:
                self.on_snapshot(self.snapshot)

        elif msg_type == "lobby":
            self.lobby = message.data
            self.game_info = {k: v for k, v in message.data.items() if k != "players"}
            if self.lobby.get("game_id"):
                self._set_game_id(self.lobby["game_id"])

            if self.on_lobby:
                self.on_lobby(self.lobby)

        elif msg_type == "player_joined":
            name = message.data.get("player_name", "Unknown")
            text = f"{name} joined the game"

            if self.on_system_message:
                self.on_system_message(text)

            logger.info(text)

        elif msg_type == "player_left":
            name = message.data.get("player_name", "Unknown")
            text = f"{name} left the game"

            if self.on_system_message:
                self.on_system_message(text)

            logger.info(text)

        elif msg_type == "game_start":
            players = message.data.get("players", [])
            text = f"Game started with {len(players)} players!"

            if self.on_system_message:
                self.on_system_message(text)

            logger.info(text)

        else:
            logger.debug(f"Received message type: {msg_type}")

    def _set_game_id(self, game_id: str) -> None:
        changed = game_id != self.state.game_id
        self.state.game_id = game_id
        self.resume_game_id = None
        if changed and self.on_session:
            self.on_session()

    def _refused(self, text: str) -> None:
        """The server said no (an error, or a refused intent): keep it and tell the UI."""
        logger.warning(f"Server refused: {text}")
        self.state.errors.append(text)
        if self.on_system_message:
            self.on_system_message(f"Error: {text}")

    def get_chat_messages(self, limit: int = 50) -> list:
        """Get recent chat messages.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of ChatMessage objects (most recent first)
        """
        return list(reversed(self.state.chat_messages[-limit:]))
