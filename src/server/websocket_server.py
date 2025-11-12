"""WebSocket server for Brogue multiplayer."""

import asyncio
import json
import logging
from typing import Dict, Set
from uuid import uuid4

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


logger = logging.getLogger(__name__)


class BrogueServer:
    """Main WebSocket server for Brogue multiplayer."""

    def __init__(self, host: str = None, port: int = None):
        self.host = host or config.host
        self.port = port or config.port

        # Managers
        self.auth_manager = AuthManager()
        self.game_manager = GameSessionManager()

        # Connection tracking
        self.connections: Dict[str, WebSocketServerProtocol] = {}  # session_id -> websocket
        self.session_to_player: Dict[str, str] = {}  # session_id -> player_id

        # Server state
        self.is_running = False
        self.server = None

    async def start(self):
        """Start the WebSocket server."""
        if websockets is None:
            raise RuntimeError(
                "websockets library not installed. "
                "Install with: pip install websockets"
            )

        logger.info(f"Starting Brogue multiplayer server on {self.host}:{self.port}")

        self.is_running = True
        self.server = await websockets.serve(
            self.handle_connection,
            self.host,
            self.port,
            max_size=config.max_message_size,
        )

        logger.info("Server started successfully")

        # Start background tasks
        asyncio.create_task(self.cleanup_task())

    async def stop(self):
        """Stop the WebSocket server."""
        logger.info("Stopping server...")
        self.is_running = False

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

    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            path: Connection path
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
            # Cleanup
            if session_id:
                await self.disconnect_client(session_id, "Connection closed")

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

            # Create session
            auth_token, session = self.auth_manager.create_session(player_name)

            # Send success response
            await self.send_message(
                websocket,
                Message.auth_success(session.session_id, session.player_id),
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
        elif msg_type == MessageType.READY.value:
            await self.handle_ready(session_id, session, message)
        elif msg_type == MessageType.ACTION.value:
            await self.handle_action(session_id, session, message)
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

        game = await self.game_manager.create_game(
            game_name=game_name,
            max_players=max_players,
            actions_per_round=config.actions_per_round,
        )

        # Auto-join creator
        success, error = await self.game_manager.join_game(
            game.game_id, session.player_id, session.player_name
        )

        if success:
            session.game_id = game.game_id
            await self.send_message_to_session(
                session_id,
                Message.system(
                    f"Created game '{game_name}' (ID: {game.game_id})", "success"
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

        success, error = await self.game_manager.join_game(
            game_id, session.player_id, session.player_name
        )

        if success:
            session.game_id = game_id
            await self.send_message_to_session(
                session_id,
                Message.system(f"Joined game {game_id}", "success"),
            )
            # Notify all players in game
            await self.broadcast_to_game(
                game_id,
                Message.player_joined(session.player_id, session.player_name),
            )
            await self.broadcast_game_state(game_id)
        else:
            await self.send_error(session_id, error or "Failed to join game")

    async def handle_leave_game(
        self, session_id: str, session: Session, message: Message
    ):
        """Handle leave game request."""
        if not session.game_id:
            await self.send_error(session_id, "Not in a game")
            return

        game_id = session.game_id
        success, error = await self.game_manager.leave_game(session.player_id)

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

    async def handle_action(self, session_id: str, session: Session, message: Message):
        """Handle player action."""
        if not session.game_id:
            await self.send_error(session_id, "Not in a game")
            return

        game = await self.game_manager.get_game(session.game_id)
        if not game or not game.is_started:
            await self.send_error(session_id, "Game not active")
            return

        # TODO: Deserialize and execute action
        # For now, just acknowledge
        await self.send_message_to_session(
            session_id,
            Message.system("Action received (not yet implemented)", "info"),
        )

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

    async def disconnect_client(self, session_id: str, reason: str = "Disconnected"):
        """Disconnect a client and clean up.

        Args:
            session_id: Session to disconnect
            reason: Disconnect reason
        """
        # Remove from game if in one
        session = self.auth_manager.get_session(session_id)
        if session and session.game_id:
            await self.game_manager.leave_game(session.player_id)

        # Close WebSocket
        websocket = self.connections.pop(session_id, None)
        if websocket and not websocket.closed:
            try:
                await websocket.close(1000, reason)
            except Exception:
                pass

        # Clean up session
        self.session_to_player.pop(session_id, None)
        self.auth_manager.invalidate_session(session_id)

        logger.info(f"Client disconnected: {session_id} ({reason})")

    async def send_message(self, websocket: WebSocketServerProtocol, message: Message):
        """Send a message to a WebSocket.

        Args:
            websocket: WebSocket to send to
            message: Message to send
        """
        try:
            await websocket.send(message.to_json())
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

    async def broadcast_game_state(self, game_id: str):
        """Broadcast current game state to all players.

        Args:
            game_id: Game ID
        """
        game = await self.game_manager.get_game(game_id)
        if not game:
            return

        state_dict = game.get_state_dict()
        await self.broadcast_to_game(game_id, Message.state(state_dict))

    async def cleanup_task(self):
        """Background task for cleanup operations."""
        while self.is_running:
            try:
                # Clean up expired sessions
                expired = self.auth_manager.cleanup_expired_sessions(
                    config.auth_token_expiry
                )
                if expired > 0:
                    logger.info(f"Cleaned up {expired} expired sessions")

                # TODO: Clean up abandoned games

                await asyncio.sleep(60)  # Run every minute

            except Exception as e:
                logger.error(f"Error in cleanup task: {e}", exc_info=True)


async def main():
    """Main entry point for running the server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    server = BrogueServer()
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
