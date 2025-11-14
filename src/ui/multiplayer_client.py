"""WebSocket client for multiplayer game sessions."""

import asyncio
import logging
from typing import Optional, Callable, Dict
from dataclasses import dataclass, field

try:
    import websockets
except ImportError:
    websockets = None

from server.messages import Message

logger = logging.getLogger('brogue.multiplayer_client')


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
    chat_messages: list = field(default_factory=list)  # List of ChatMessage objects


class MultiplayerClient:
    """Client for connecting to Brogue multiplayer server."""

    def __init__(self, host: str = "localhost", port: int = 8765):
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

        # Callbacks
        self.on_chat_message: Optional[Callable[[ChatMessage], None]] = None
        self.on_system_message: Optional[Callable[[str], None]] = None
        self.on_state_update: Optional[Callable[[Dict], None]] = None

        # Background tasks
        self._listen_task: Optional[asyncio.Task] = None
        self._running = False

    async def connect(self, player_name: str) -> bool:
        """Connect to the multiplayer server and authenticate.

        Args:
            player_name: Name for this player

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
            auth_msg = Message.auth(player_name)
            await self.ws.send(auth_msg.to_json())
            logger.info(f"Sent authentication as '{player_name}'")

            # Wait for auth response
            response_str = await self.ws.recv()
            response = Message.from_json(response_str)

            if response.type == "auth_success":
                self.state.session_id = response.data["session_id"]
                self.state.player_id = response.data["player_id"]
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

    async def create_game(self, game_name: str, player_class: str = "warrior", max_players: int = 4):
        """Create a new multiplayer game.

        Args:
            game_name: Name for the game
            player_class: Character class (warrior, mage, rogue, healer)
            max_players: Maximum number of players (default 4)
        """
        if not self.ws or not self.state.is_connected:
            logger.warning("Cannot create game: not connected")
            return

        msg = Message.create_game(game_name, max_players=max_players, player_class=player_class)
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
            # Handle error message
            text = message.data.get("message", "")
            logger.error(f"Server error: {text}")

            if self.on_system_message:
                self.on_system_message(f"Error: {text}")

        elif msg_type == "state":
            # Handle full state update
            state = message.data.get("state", {})

            # Update game_id if we joined a game
            game_id = state.get("game_id")
            if game_id:
                self.state.game_id = game_id

            if self.on_state_update:
                self.on_state_update(state)

            logger.debug("Received full state update")

        elif msg_type == "delta":
            # Handle delta state update
            if self.on_state_update:
                self.on_state_update(message.data)

            logger.debug("Received delta state update")

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

    def get_chat_messages(self, limit: int = 50) -> list:
        """Get recent chat messages.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of ChatMessage objects (most recent first)
        """
        return list(reversed(self.state.chat_messages[-limit:]))
