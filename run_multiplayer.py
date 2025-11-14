#!/usr/bin/env python3
"""
Brogue Multiplayer Client with Chat

Launch a multiplayer Brogue client that connects to a game server
and supports chat functionality.
"""
import sys
import asyncio
import argparse
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ui.textual.app import BrogueApp
from ui.multiplayer_client import MultiplayerClient
from ui.textual.game_init import setup_logging


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Brogue Multiplayer Client with Chat",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_multiplayer.py --name Alice                    # Connect as Alice
  python run_multiplayer.py --name Bob --host 192.168.1.10  # Connect to remote server

Controls:
  Arrow keys / HJKL - Move
  'c' or Enter - Open chat
  's' - Survey ore
  'm' - Mine
  '>' - Descend stairs
  'Q' - Quit

Chat:
  Press 'c' or Enter to open chat
  Type your message and press Enter to send
  Press Esc to cancel
        """
    )

    parser.add_argument(
        '--name',
        type=str,
        required=True,
        help='Player name (required for multiplayer)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='WebSocket server host (default: localhost)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8765,
        help='WebSocket server port (default: 8765)'
    )
    parser.add_argument(
        '--game-id',
        type=str,
        help='Game ID to join (if not creating a new game)'
    )
    parser.add_argument(
        '--create-game',
        action='store_true',
        help='Create a new game instead of joining'
    )
    parser.add_argument(
        '--game-name',
        type=str,
        default='My Game',
        help='Name for the game (when creating)'
    )
    parser.add_argument(
        '--class',
        dest='char_class',
        type=str,
        choices=['warrior', 'rogue', 'mage', 'healer'],
        default='warrior',
        help='Character class (default: warrior)'
    )

    return parser.parse_args()


async def connect_to_server(args):
    """Connect to the multiplayer server.

    Args:
        args: Command-line arguments

    Returns:
        MultiplayerClient instance if successful, None otherwise
    """
    print(f"Connecting to server at {args.host}:{args.port}...")

    client = MultiplayerClient(host=args.host, port=args.port)

    success = await client.connect(args.name)

    if not success:
        print("Failed to connect to server")
        return None

    print(f"✓ Connected as '{args.name}'")

    # Create or join game
    if args.create_game:
        print(f"Creating game '{args.game_name}'...")
        await client.create_game(
            game_name=args.game_name,
            player_class=args.char_class,
            max_players=4
        )
        # Wait a moment for the game to be created
        await asyncio.sleep(0.5)
    elif args.game_id:
        print(f"Joining game '{args.game_id}'...")
        await client.join_game(
            game_id=args.game_id,
            player_class=args.char_class
        )
        # Wait a moment for join confirmation
        await asyncio.sleep(0.5)
    else:
        print("\nWaiting for game assignment...")
        print("(You can create a game with --create-game or join with --game-id)")

    return client


def main():
    """Main entry point for multiplayer Brogue."""
    args = parse_arguments()

    # Setup logging
    log_dir = Path(__file__).parent / "logs"
    setup_logging(log_dir)

    # Display welcome banner
    print("╔" + "=" * 66 + "╗")
    print("║" + " " * 15 + "BROGUE MULTIPLAYER (with Chat)" + " " * 20 + "║")
    print("╚" + "=" * 66 + "╝")
    print()

    # Connect to server (synchronously start the async connection)
    try:
        client = asyncio.run(connect_to_server(args))

        if not client:
            sys.exit(1)

        print("\n✓ Ready to play!")
        print("\nPress 'c' or Enter to chat with your party")
        print("Press 'Q' to quit\n")

        # Create and run the app with multiplayer client
        app = BrogueApp(
            player_name=args.name,
            character_class=None,  # Will be set by server
            multiplayer_client=client
        )

        # Run the app
        app.run(mouse=False)

        # Cleanup on exit
        asyncio.run(client.disconnect())

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
