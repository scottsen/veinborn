#!/usr/bin/env python3
"""Simple test client for the Brogue multiplayer server.

This is a basic command-line client to test server connectivity and functionality.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import websockets
except ImportError:
    print("Error: websockets library not installed")
    print("Install with: pip install websockets")
    sys.exit(1)

from server.messages import Message


class TestClient:
    """Simple test client for multiplayer server."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.ws = None
        self.session_id = None
        self.player_id = None
        self.player_name = None
        self.player_entity_id = None  # Entity ID for sending actions

    async def connect(self, player_name: str):
        """Connect to the server and authenticate.

        Args:
            player_name: Name to use for this player
        """
        uri = f"ws://{self.host}:{self.port}"
        print(f"Connecting to {uri}...")

        try:
            self.ws = await websockets.connect(uri)
            print("Connected!")

            # Send auth message
            self.player_name = player_name
            auth_msg = Message.auth(player_name)
            await self.ws.send(auth_msg.to_json())
            print(f"Sent authentication as '{player_name}'")

            # Wait for auth response
            response_str = await self.ws.recv()
            response = Message.from_json(response_str)

            if response.type == "auth_success":
                self.session_id = response.data["session_id"]
                self.player_id = response.data["player_id"]
                print(f"✓ Authenticated successfully!")
                print(f"  Session ID: {self.session_id}")
                print(f"  Player ID: {self.player_id}")
                return True
            else:
                print(f"✗ Authentication failed: {response.data}")
                return False

        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False

    async def create_game(self, game_name: str = "Test Game", player_class: str = "warrior"):
        """Create a new game.

        Args:
            game_name: Name for the game
            player_class: Character class (warrior, mage, rogue, healer)
        """
        if not self.ws:
            print("✗ Not connected")
            return

        msg = Message.create_game(game_name, max_players=4, player_class=player_class)
        await self.ws.send(msg.to_json())
        print(f"Sent create game request: '{game_name}' as {player_class}")

    async def join_game(self, game_id: str, player_class: str = "warrior"):
        """Join an existing game.

        Args:
            game_id: Game ID to join
            player_class: Character class (warrior, mage, rogue, healer)
        """
        if not self.ws:
            print("✗ Not connected")
            return

        msg = Message.join_game(game_id, player_class=player_class)
        await self.ws.send(msg.to_json())
        print(f"Sent join game request: {game_id} as {player_class}")

    async def send_ready(self):
        """Send ready status."""
        if not self.ws:
            print("✗ Not connected")
            return

        msg = Message(type="ready", data={"ready": True})
        await self.ws.send(msg.to_json())
        print("Sent ready status")

    async def send_chat(self, message: str):
        """Send a chat message.

        Args:
            message: Chat message text
        """
        if not self.ws:
            print("✗ Not connected")
            return

        msg = Message(type="chat", data={"message": message})
        await self.ws.send(msg.to_json())
        print(f"Sent chat: {message}")

    async def send_move(self, dx: int, dy: int):
        """Send a movement action.

        Args:
            dx: X offset (-1, 0, 1)
            dy: Y offset (-1, 0, 1)
        """
        if not self.ws:
            print("✗ Not connected")
            return

        if not self.player_entity_id:
            print("✗ Game not started or entity ID unknown")
            return

        # Create MoveAction serialized format
        action_data = {
            "action_type": "MoveAction",
            "actor_id": self.player_entity_id,
            "dx": dx,
            "dy": dy,
        }

        msg = Message(type="action", data={"action_data": action_data})
        await self.ws.send(msg.to_json())
        print(f"Sent move: dx={dx}, dy={dy}")

    async def listen(self):
        """Listen for messages from the server."""
        if not self.ws:
            print("✗ Not connected")
            return

        try:
            async for message_str in self.ws:
                message = Message.from_json(message_str)
                await self.handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            print("\n✗ Connection closed by server")
        except Exception as e:
            print(f"\n✗ Error: {e}")

    async def handle_message(self, message: Message):
        """Handle a message from the server.

        Args:
            message: Received message
        """
        msg_type = message.type

        if msg_type == "system":
            level = message.data.get("level", "info")
            text = message.data.get("message", "")
            symbol = "✓" if level == "success" else "ℹ"
            print(f"\n{symbol} System: {text}")

        elif msg_type == "error":
            print(f"\n✗ Error: {message.data.get('message')}")

        elif msg_type == "chat_message":
            player_name = message.data.get("player_name", "Unknown")
            text = message.data.get("message", "")
            print(f"\n💬 {player_name}: {text}")

        elif msg_type == "state":
            state = message.data.get("state", {})
            print(f"\n📊 Game State Update:")
            print(f"   Game: {state.get('game_name', 'Unknown')}")
            print(f"   Players: {state.get('player_count', 0)}/{state.get('max_players', 0)}")
            if state.get("is_started"):
                print(f"   Turn: {state.get('turn_count', 0)}")
                print(f"   Round: {state.get('round_number', 0)}")
                print(f"   Actions: {state.get('actions_this_round', 0)}/{state.get('actions_per_round', 4)}")

                # Extract player entity ID for movement
                players = state.get("players", [])
                for player in players:
                    if player.get("player_id") == self.player_id:
                        old_entity_id = self.player_entity_id
                        self.player_entity_id = player.get("entity_id")
                        if not old_entity_id and self.player_entity_id:
                            print(f"   Your entity: {self.player_entity_id}")
                            print(f"   Use /move <dir> to move (n,s,e,w,ne,nw,se,sw)")

                        # Show position
                        pos = player.get("position", {})
                        print(f"   Your position: ({pos.get('x', 0)}, {pos.get('y', 0)})")

        elif msg_type == "player_joined":
            name = message.data.get("player_name", "Unknown")
            player_class = message.data.get("player_class", "warrior")
            print(f"\n👤 {name} joined the game as {player_class}")

        elif msg_type == "player_left":
            name = message.data.get("player_name", "Unknown")
            print(f"\n👤 {name} left the game")

        elif msg_type == "game_start":
            players = message.data.get("players", [])
            print(f"\n🎮 Game started with {len(players)} players!")

        else:
            print(f"\n📨 Received: {msg_type}")
            print(f"   Data: {message.data}")

    async def interactive_mode(self):
        """Run in interactive mode."""
        print("\n" + "=" * 60)
        print("Interactive Mode")
        print("=" * 60)
        print("Commands:")
        print("  /create <name> [class]  - Create a new game (warrior, mage, rogue, healer)")
        print("  /join <id> [class]      - Join a game by ID")
        print("  /ready                  - Mark yourself as ready")
        print("  /move <dir>             - Move (n, s, e, w, ne, nw, se, sw)")
        print("  /quit                   - Disconnect")
        print("  <message>               - Send chat message")
        print("=" * 60 + "\n")

        # Start listening task
        listen_task = asyncio.create_task(self.listen())

        try:
            while True:
                # Get user input
                try:
                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None, input, f"{self.player_name}> "
                    )
                except EOFError:
                    break

                if not user_input.strip():
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    parts = user_input.split(maxsplit=1)
                    cmd = parts[0].lower()

                    if cmd == "/quit":
                        print("Disconnecting...")
                        break
                    elif cmd == "/create":
                        # Parse: /create <name> [class]
                        args = parts[1].split() if len(parts) > 1 else []
                        game_name = args[0] if len(args) > 0 else "Test Game"
                        player_class = args[1] if len(args) > 1 else "warrior"
                        await self.create_game(game_name, player_class)
                    elif cmd == "/join":
                        # Parse: /join <id> [class]
                        if len(parts) < 2:
                            print("Usage: /join <game_id> [class]")
                        else:
                            args = parts[1].split()
                            game_id = args[0]
                            player_class = args[1] if len(args) > 1 else "warrior"
                            await self.join_game(game_id, player_class)
                    elif cmd == "/ready":
                        await self.send_ready()
                    elif cmd == "/move":
                        if len(parts) < 2:
                            print("Usage: /move <direction>")
                            print("Directions: n, s, e, w, ne, nw, se, sw")
                        else:
                            direction = parts[1].lower()
                            # Map direction to dx, dy
                            dir_map = {
                                "n": (0, -1),
                                "s": (0, 1),
                                "e": (1, 0),
                                "w": (-1, 0),
                                "ne": (1, -1),
                                "nw": (-1, -1),
                                "se": (1, 1),
                                "sw": (-1, 1),
                            }
                            if direction in dir_map:
                                dx, dy = dir_map[direction]
                                await self.send_move(dx, dy)
                            else:
                                print(f"Unknown direction: {direction}")
                    else:
                        print(f"Unknown command: {cmd}")
                else:
                    # Send as chat
                    await self.send_chat(user_input)

        except KeyboardInterrupt:
            print("\nInterrupted")
        finally:
            listen_task.cancel()
            if self.ws:
                await self.ws.close()

    async def close(self):
        """Close the connection."""
        if self.ws:
            await self.ws.close()
            print("Disconnected")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Brogue multiplayer test client")
    parser.add_argument(
        "--host", default="localhost", help="Server host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=8765, help="Server port (default: 8765)"
    )
    parser.add_argument(
        "--name", default="TestPlayer", help="Player name (default: TestPlayer)"
    )

    args = parser.parse_args()

    client = TestClient(args.host, args.port)

    try:
        # Connect and authenticate
        success = await client.connect(args.name)
        if not success:
            return 1

        # Run interactive mode
        await client.interactive_mode()

    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        await client.close()

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(0)
