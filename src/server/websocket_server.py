"""WebSocket server for Veinborn multiplayer."""

import asyncio
import json
import logging
from typing import Dict

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    # websockets not installed yet
    websockets = None
    WebSocketServerProtocol = None

from server.auth import AuthManager, Session
from server.config import config
from server.game_session import GameSessionManager
from server.messages import Message, MessageType
from server.action_handler import action_registry


logger = logging.getLogger(__name__)


class VeinbornServer:
    """Main WebSocket server for Veinborn multiplayer."""

    def __init__(self, host: str = None, port: int = None):
        self.host = host or config.host
        self.port = port if port is not None else config.port  # 0 = OS-assigned (tests)

        # Managers
        self.auth_manager = AuthManager()
        self.game_manager = GameSessionManager()

        # Connection tracking
        self.connections: Dict[str, WebSocketServerProtocol] = {}  # session_id -> websocket
        self.session_to_player: Dict[str, str] = {}  # session_id -> player_id

        # Server state
        self.is_running = False
        self.server = None
        self._cleanup_task_handle = None

    async def start(self):
        """Start the WebSocket server."""
        if websockets is None:
            raise RuntimeError(
                "websockets library not installed. "
                "Install with: pip install websockets"
            )

        logger.info(f"Starting Veinborn multiplayer server on {self.host}:{self.port}")

        self.is_running = True
        self.server = await websockets.serve(
            self.handle_connection,
            self.host,
            self.port,
            max_size=config.max_message_size,
        )

        logger.info("Server started successfully")

        # Start background tasks
        self._cleanup_task_handle = asyncio.create_task(self.cleanup_task())

    async def stop(self):
        """Stop the WebSocket server."""
        logger.info("Stopping server...")
        self.is_running = False

        if self._cleanup_task_handle:
            self._cleanup_task_handle.cancel()
            self._cleanup_task_handle = None

        # Close all connections
        if self.connections:
            close_tasks = [
                self.disconnect_client(session_id, "Server shutting down")
                for session_id in list(self.connections.keys())
            ]
            await asyncio.gather(*close_tasks, return_exceptions=True)

        # Stop server
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        logger.info("Server stopped")

    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str = None):
        """Handle a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            path: Connection path. Only websockets < 13 (legacy API) passes it; the
                current asyncio API calls the handler with the connection alone.
        """
        session_id = None
        try:
            logger.info(f"New connection from {websocket.remote_address}")

            # Wait for authentication
            session_id = await self.authenticate_connection(websocket)
            if not session_id:
                await websocket.close(1008, "Authentication failed")
                return

            # Register connection
            self.connections[session_id] = websocket
            session = self.auth_manager.get_session(session_id)

            if session:
                self.session_to_player[session_id] = session.player_id
                logger.info(
                    f"Player {session.player_name} authenticated (session: {session_id})"
                )

            # Handle messages
            await self.message_loop(websocket, session_id)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed: {session_id}")
        except Exception as e:
            logger.error(f"Error handling connection: {e}", exc_info=True)
        finally:
            # Cleanup. Pass this socket's own identity so disconnect_client can
            # detect a fast reconnect that already replaced it in self.connections
            # (VB-22) and skip tearing down the live connection.
            if session_id:
                await self.disconnect_client(session_id, "Connection closed", websocket=websocket)

    async def authenticate_connection(
        self, websocket: WebSocketServerProtocol
    ) -> str | None:
        """Authenticate a new connection.

        Args:
            websocket: WebSocket connection

        Returns:
            Session ID if successful, None otherwise
        """
        try:
            # Wait for auth message with timeout
            message_str = await asyncio.wait_for(
                websocket.recv(), timeout=config.connection_timeout
            )

            message = Message.from_json(message_str)

            # Check message type
            if message.type != MessageType.AUTH.value:
                await self.send_message(
                    websocket,
                    Message.auth_failure("Expected authentication message"),
                )
                return None

            # Get player name
            player_name = message.data.get("player_name")
            if not player_name or not isinstance(player_name, str):
                await self.send_message(
                    websocket,
                    Message.auth_failure("Invalid player name"),
                )
                return None

            # Resume an existing session if a valid auth_token was sent
            # (reconnect flow); otherwise mint a new session.
            auth_token = message.data.get("auth_token")
            session = self.auth_manager.verify_token(auth_token) if auth_token else None
            if session:
                session.mark_active()
            else:
                auth_token, session = self.auth_manager.create_session(player_name)

            # Send success response
            await self.send_message(
                websocket,
                Message.auth_success(session.session_id, session.player_id, auth_token),
            )

            return session.session_id

        except asyncio.TimeoutError:
            await self.send_message(
                websocket,
                Message.auth_failure("Authentication timeout"),
            )
            return None
        except json.JSONDecodeError:
            await self.send_message(
                websocket,
                Message.auth_failure("Invalid message format"),
            )
            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    async def message_loop(self, websocket: WebSocketServerProtocol, session_id: str):
        """Main message processing loop for a connection.

        Args:
            websocket: WebSocket connection
            session_id: Session ID
        """
        try:
            async for message_str in websocket:
                try:
                    message = Message.from_json(message_str)
                    await self.handle_message(session_id, message)
                except json.JSONDecodeError:
                    await self.send_error(session_id, "Invalid message format")
                except Exception as e:
                    logger.error(f"Error handling message: {e}", exc_info=True)
                    await self.send_error(session_id, f"Error processing message: {e}")

        except websockets.exceptions.ConnectionClosed:
            pass

    async def handle_message(self, session_id: str, message: Message):
        """Handle a message from a client.

        Args:
            session_id: Session ID
            message: Received message
        """
        session = self.auth_manager.get_session(session_id)
        if not session:
            await self.send_error(session_id, "Invalid session")
            return

        # Update activity
        session.update_activity()

        # Route message based on type
        msg_type = message.type

        if msg_type == MessageType.CREATE_GAME.value:
            await self.handle_create_game(session_id, session, message)
        elif msg_type == MessageType.JOIN_GAME.value:
            await self.handle_join_game(session_id, session, message)
        elif msg_type == MessageType.LEAVE_GAME.value:
            await self.handle_leave_game(session_id, session, message)
        elif msg_type == MessageType.RECONNECT.value:
            await self.handle_reconnect(session_id, session, message)
        elif msg_type == MessageType.READY.value:
            await self.handle_ready(session_id, session, message)
        elif msg_type == MessageType.ACTION.value:
            await self.handle_action(session_id, session, message)
        elif msg_type == MessageType.INTENT.value:
            await self.handle_intent(session_id, session, message)
        elif msg_type == MessageType.CHAT.value:
            await self.handle_chat(session_id, session, message)
        else:
            await self.send_error(session_id, f"Unknown message type: {msg_type}")

    async def handle_create_game(
        self, session_id: str, session: Session, message: Message
    ):
        """Handle create game request."""
        game_name = message.data.get("game_name", "Unnamed Game")
        max_players = message.data.get("max_players", 4)
        player_class = message.data.get("player_class", "warrior")

        game = await self.game_manager.create_game(
            game_name=game_name,
            max_players=max_players,
        )

        # Auto-join creator with their selected class
        success, error = await self.game_manager.join_game(
            game.game_id, session.player_id, session.player_name, player_class
        )

        if success:
            session.game_id = game.game_id
            await self.send_message_to_session(
                session_id,
                Message.system(
                    f"Created game '{game_name}' as {player_class} (ID: {game.game_id})", "success"
                ),
            )
            await self.broadcast_game_state(game.game_id)
        else:
            await self.send_error(session_id, error or "Failed to create game")

    async def handle_join_game(
        self, session_id: str, session: Session, message: Message
    ):
        """Handle join game request."""
        game_id = message.data.get("game_id")
        if not game_id:
            await self.send_error(session_id, "Missing game_id")
            return

        player_class = message.data.get("player_class", "warrior")

        success, error = await self.game_manager.join_game(
            game_id, session.player_id, session.player_name, player_class
        )

        if success:
            session.game_id = game_id
            await self.send_message_to_session(
                session_id,
                Message.system(f"Joined game {game_id} as {player_class}", "success"),
            )
            # Notify all players in game
            await self.broadcast_to_game(
                game_id,
                Message.player_joined(session.player_id, session.player_name, player_class),
            )
            await self.broadcast_game_state(game_id)
        else:
            await self.send_error(session_id, error or "Failed to join game")

    async def handle_leave_game(
        self, session_id: str, session: Session, message: Message
    ):
        """Handle leave game request (intentional departure)."""
        if not session.game_id:
            await self.send_error(session_id, "Not in a game")
            return

        game_id = session.game_id
        game = await self.game_manager.get_game(game_id)

        if not game:
            await self.send_error(session_id, "Game not found")
            return

        # Mark player as having left (preserves record in game.players,
        # cleans up manager's player→game mapping)
        success, error = await self.game_manager.mark_player_left(session.player_id)

        if success:
            session.game_id = None
            await self.send_message_to_session(
                session_id,
                Message.system("Left game", "info"),
            )
            # Notify remaining players
            await self.broadcast_to_game(
                game_id,
                Message.player_left(session.player_id, session.player_name),
            )
            await self.broadcast_game_state(game_id)
        else:
            await self.send_error(session_id, error or "Failed to leave game")

    async def handle_reconnect(
        self, session_id: str, session: Session, message: Message
    ):
        """Handle reconnection request."""
        if not session.game_id:
            await self.send_error(session_id, "Not in a game to reconnect to")
            return

        game = await self.game_manager.get_game(session.game_id)
        if not game:
            await self.send_error(session_id, "Game not found")
            return

        # Attempt to reconnect player
        success, error = await game.reconnect_player(session.player_id)

        if not success:
            await self.send_error(session_id, error or "Failed to reconnect")
            return

        # Reconnection successful
        session.mark_active()
        self.connections[session_id] = self.connections.get(session_id)

        await self.send_message_to_session(
            session_id,
            Message.system("Reconnected successfully", "success"),
        )

        # Notify other players
        await self.broadcast_to_game(
            session.game_id,
            Message.player_reconnected(session.player_id, session.player_name),
        )

        # Send full game state to reconnecting player
        await self.broadcast_game_state(session.game_id, force_full_state=True)

    async def handle_ready(self, session_id: str, session: Session, message: Message):
        """Handle player ready status."""
        if not session.game_id:
            await self.send_error(session_id, "Not in a game")
            return

        ready = message.data.get("ready", True)
        game = await self.game_manager.get_game(session.game_id)

        if not game:
            await self.send_error(session_id, "Game not found")
            return

        await game.set_player_ready(session.player_id, ready)

        # Check if all players ready
        if game.all_players_ready() and not game.is_started:
            # Start game
            await game.start_game()
            await self.broadcast_to_game(
                session.game_id,
                Message.game_start(
                    game.game_id,
                    [
                        {"player_id": p.player_id, "player_name": p.player_name}
                        for p in game.players.values()
                    ],
                ),
            )

        await self.broadcast_game_state(session.game_id)

    async def handle_intent(self, session_id: str, session: Session, message: Message):
        """Handle a player intent. The actor comes from the session's seat, not the payload."""
        if not session.game_id:
            await self.send_error(session_id, "Not in a game")
            return

        game = await self.game_manager.get_game(session.game_id)
        if not game or not game.is_started:
            await self.send_error(session_id, "Game not active")
            return

        intent = message.data.get("intent")
        args = message.data.get("args") or {}
        if not isinstance(intent, str) or not intent or not isinstance(args, dict):
            await self.send_error(session_id, "Invalid intent")
            return

        success, error = await game.process_intent(session.player_id, intent, args)
        if not success:
            await self.send_error(session_id, error or "Action failed")
        else:
            await self.broadcast_game_state(session.game_id)

    async def handle_action(self, session_id: str, session: Session, message: Message):
        """Handle player action."""
        if not session.game_id:
            await self.send_error(session_id, "Not in a game")
            return

        game = await self.game_manager.get_game(session.game_id)
        if not game or not game.is_started:
            await self.send_error(session_id, "Game not active")
            return

        # Deserialize action
        action_data = message.data.get("action_data")
        if not action_data:
            await self.send_error(session_id, "Missing action_data")
            return

        action = action_registry.deserialize(action_data)
        if not action:
            await self.send_error(session_id, "Invalid action data")
            return

        # Validate action belongs to this player
        player_entity_id = None
        if game.mp_game_state:
            player_entity_id = game.mp_game_state.get_player_entity_id(session.player_id)

        if player_entity_id and action.actor_id != player_entity_id:
            await self.send_error(session_id, "Action actor does not match player")
            return

        # Execute action
        success, error = await game.process_action(session.player_id, action)

        if not success:
            await self.send_error(session_id, error or "Action failed")
        else:
            # Broadcast updated state to all players
            await self.broadcast_game_state(session.game_id)

    async def handle_chat(self, session_id: str, session: Session, message: Message):
        """Handle chat message."""
        if not session.game_id:
            await self.send_error(session_id, "Not in a game")
            return

        chat_text = message.data.get("message", "")
        if not chat_text:
            return

        # Broadcast to all players in game
        await self.broadcast_to_game(
            session.game_id,
            Message.chat_message(session.player_id, session.player_name, chat_text),
        )

    async def disconnect_client(
        self,
        session_id: str,
        reason: str = "Disconnected",
        preserve_session: bool = True,
        websocket: WebSocketServerProtocol | None = None,
    ):
        """Disconnect a client and optionally preserve session for reconnection.

        Args:
            session_id: Session to disconnect
            reason: Disconnect reason
            preserve_session: If True, preserve session for reconnection; if False, clean up completely
            websocket: The specific socket that closed, if known (passed by
                handle_connection's finally block). A fast reconnect can reuse
                session_id and overwrite self.connections[session_id] with a new,
                live socket before the old socket's finally block runs. When given,
                this call is a no-op unless it's still the socket currently
                registered for session_id -- otherwise it would tear down the
                connection the reconnect just established (VB-22).
        """
        if websocket is not None and self.connections.get(session_id) is not websocket:
            logger.info(
                f"Ignoring stale disconnect for session {session_id}: connection "
                f"already replaced by a reconnect ({reason})"
            )
            return

        session = self.auth_manager.get_session(session_id)

        if session and session.game_id:
            game = await self.game_manager.get_game(session.game_id)

            if game and preserve_session:
                # Mark player as disconnected but keep them in the game
                await game.disconnect_player(session.player_id)

                # Mark session as inactive but don't invalidate
                session.mark_inactive()

                # Notify other players
                await self.broadcast_to_game(
                    session.game_id,
                    Message.player_disconnected(session.player_id, session.player_name),
                )

                logger.info(
                    f"Player {session.player_name} disconnected from game {session.game_id}. "
                    f"Session preserved for reconnection. ({reason})"
                )
            else:
                # Permanently remove from game
                await self.game_manager.leave_game(session.player_id)

        # Close WebSocket. If a specific socket was given, only remove it from
        # self.connections if it's still the one registered -- the awaits above
        # (disconnect_player, broadcast_to_game) give a concurrent reconnect a
        # window to have already replaced it with a new live socket.
        if websocket is not None:
            if self.connections.get(session_id) is websocket:
                self.connections.pop(session_id, None)
            dead_socket = websocket
        else:
            dead_socket = self.connections.pop(session_id, None)

        if dead_socket and not self._is_closed(dead_socket):
            try:
                await dead_socket.close(1000, reason)
            except Exception:
                logger.warning(f"Error closing websocket for session {session_id}", exc_info=True)

        # Clean up connection tracking
        self.session_to_player.pop(session_id, None)

        if not preserve_session:
            # Fully invalidate session
            self.auth_manager.invalidate_session(session_id)
            logger.info(f"Client disconnected and session invalidated: {session_id} ({reason})")
        else:
            logger.info(f"Client disconnected but session preserved: {session_id} ({reason})")

    @staticmethod
    def _is_closed(websocket) -> bool:
        """Whether a socket is closed, on both websockets APIs.

        The legacy protocol has `.closed`; the asyncio API (websockets >= 13, the
        default since 14) dropped it in favour of `.state`.
        """
        closed = getattr(websocket, "closed", None)
        if closed is not None:
            return closed
        state = getattr(websocket, "state", None)
        return state is not None and state.name in ("CLOSING", "CLOSED")

    async def send_message(self, websocket: WebSocketServerProtocol, message: Message):
        """Send a message to a WebSocket.

        Args:
            websocket: WebSocket to send to
            message: Message to send
        """
        try:
            await websocket.send(message.to_json())
        except websockets.exceptions.ConnectionClosed:
            # Normal race: a broadcast reached a player whose socket just dropped
            logger.info("Not sending to a closed connection")
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def send_message_to_session(self, session_id: str, message: Message):
        """Send a message to a specific session.

        Args:
            session_id: Session ID
            message: Message to send
        """
        websocket = self.connections.get(session_id)
        if websocket:
            await self.send_message(websocket, message)

    async def send_error(self, session_id: str, error_message: str):
        """Send an error message to a session.

        Args:
            session_id: Session ID
            error_message: Error message
        """
        await self.send_message_to_session(
            session_id, Message.error(error_message)
        )

    async def broadcast_to_game(self, game_id: str, message: Message):
        """Broadcast a message to all players in a game.

        Args:
            game_id: Game ID
            message: Message to broadcast
        """
        game = await self.game_manager.get_game(game_id)
        if not game:
            return

        # Send to all players in game
        for player_id in game.players.keys():
            session = self.auth_manager.get_session_by_player(player_id)
            if session:
                await self.send_message_to_session(session.session_id, message)

    async def broadcast_game_state(self, game_id: str, force_full_state: bool = False):
        """Broadcast current game state to all players.

        Args:
            game_id: Game ID
            force_full_state: If True, send full state instead of delta
        """
        game = await self.game_manager.get_game(game_id)
        if not game:
            return

        state_dict = game.get_state_dict(use_delta=not force_full_state)

        # Send appropriate message type based on whether it's a delta or full state
        if state_dict.get("type") == "delta":
            # Send delta message
            await self.broadcast_to_game(game_id, Message.delta(state_dict))
        else:
            # Send full state message
            await self.broadcast_to_game(game_id, Message.state(state_dict))

    CLEANUP_INTERVAL_SECONDS = 10  # Fast enough for reconnection timeouts
    CLEANUP_MAX_BACKOFF_SECONDS = 300

    @classmethod
    def _cleanup_delay(cls, consecutive_failures: int) -> float:
        """Seconds to wait before the next cleanup pass; backs off while it keeps failing."""
        if consecutive_failures <= 0:
            return cls.CLEANUP_INTERVAL_SECONDS
        return min(
            cls.CLEANUP_INTERVAL_SECONDS * 2 ** consecutive_failures,
            cls.CLEANUP_MAX_BACKOFF_SECONDS,
        )

    async def cleanup_task(self):
        """Background task for cleanup operations.

        Always sleeps between passes, even after a failed one, so a persistent
        error can't turn this into a busy loop that floods the log (VB-27).
        """
        consecutive_failures = 0
        while self.is_running:
            try:
                await self._cleanup_once()
                consecutive_failures = 0
            except asyncio.CancelledError:
                raise
            except Exception as e:
                consecutive_failures += 1
                logger.error(
                    f"Error in cleanup task (failure #{consecutive_failures}): {e}",
                    exc_info=True,
                )
            await asyncio.sleep(self._cleanup_delay(consecutive_failures))

    async def _cleanup_once(self):
        """One cleanup pass: expired auth sessions and expired reconnection windows."""
        # Clean up expired sessions
        expired = self.auth_manager.cleanup_expired_sessions(
            config.auth_token_expiry
        )
        if expired > 0:
            logger.info(f"Cleaned up {expired} expired sessions")

        # Clean up players with expired reconnection timeouts
        total_removed = 0
        for game_id, game in list(self.game_manager._games.items()):
            removed_players = await game.cleanup_expired_disconnections()

            if removed_players:
                total_removed += len(removed_players)

                # Notify remaining players and update state
                for player_id in removed_players:
                    # Try to get player info for notification
                    session = self.auth_manager.get_session_by_player(player_id)
                    if session:
                        await self.broadcast_to_game(
                            game_id,
                            Message.system(
                                f"{session.player_name} was removed due to reconnection timeout",
                                "warning"
                            ),
                        )

                # Update game state
                await self.broadcast_game_state(game_id)

        if total_removed > 0:
            logger.info(f"Removed {total_removed} players due to reconnection timeout")


async def main():
    """Main entry point for running the server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    server = VeinbornServer()
    await server.start()

    try:
        # Run forever
        await asyncio.Future()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
