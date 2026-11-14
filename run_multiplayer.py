#!/usr/bin/env python3
"""
Veinborn Multiplayer Client with Chat

Launch a multiplayer Veinborn client that connects to a game server
and supports chat functionality.
"""
import sys
import argparse
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from ui.textual.app import VeinbornApp
from ui.multiplayer_client import MultiplayerClient
from ui import session_store
from ui.textual.game_init import setup_logging


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Veinborn Multiplayer Client with Chat",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_multiplayer.py --name Alice                    # Connect as Alice
  python run_multiplayer.py --name Bob --host 192.168.1.10  # Connect to remote server

Starting a game:
  The creator's status bar shows the game id; others join with --game-id <id>.
  Each player presses 'R' when ready; the game starts when everyone is.
  Each round waits for one action from every living player.

Controls:
  Arrow keys / HJKL / YUBN - Move (bump to attack or mine)
  's' - Survey ore     'e' - Eat/drink     'g' - Pick up     'w' - Equipment
  '>' - Descend stairs '.' - Wait          'i' - Inventory   ':' - Look
  'c' or Enter - Open chat
  'q' - Quit

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

    parser.add_argument(
        '--no-resume',
        action='store_true',
        help="Ignore the saved session: don't resume the last game or auth token"
    )

    return parser.parse_args()


def make_setup(args):
    """Build the coroutine that connects and joins a game.

    It must run inside the Textual app's event loop (VeinbornApp's
    ``multiplayer_setup``): MultiplayerClient._listen is a task of the loop that
    connected, and an earlier ``asyncio.run`` would cancel it when it returned.
    """

    async def setup(client) -> bool:
        # A restarted client resumes its auth session (same identity) and, when no game
        # is named, goes back to its last game: the server seats it again (plan D7)
        saved = {} if args.no_resume else session_store.load(args.host, args.port, args.name)
        success = await client.connect(args.name, auth_token=saved.get("auth_token"))
        if not success:
            return False

        def remember() -> None:
            session_store.save(
                args.host, args.port, args.name, client.state.auth_token, client.state.game_id
            )

        client.on_session = remember
        remember()

        if args.create_game:
            await client.create_game(
                game_name=args.game_name,
                player_class=args.char_class,
                max_players=4
            )
        elif args.game_id or saved.get("game_id"):
            await client.join_game(
                game_id=args.game_id or saved["game_id"],
                player_class=args.char_class
            )
        return True

    return setup


def main():
    """Main entry point for multiplayer Veinborn."""
    args = parse_arguments()

    # Setup logging
    log_dir = Path(__file__).parent / "logs"
    setup_logging(log_dir)

    # Display welcome banner
    print("╔" + "=" * 66 + "╗")
    print("║" + " " * 15 + "VEINBORN MULTIPLAYER (with Chat)" + " " * 20 + "║")
    print("╚" + "=" * 66 + "╝")
    print()

    try:
        print(f"Connecting to server at {args.host}:{args.port} (inside the game window)...")
        print("\nPress 'c' or Enter to chat with your party")
        print("Press 'Q' to quit\n")

        client = MultiplayerClient(host=args.host, port=args.port)

        # The app connects from on_mount, in its own event loop, and disconnects on unmount
        app = VeinbornApp(
            player_name=args.name,
            character_class=None,  # the class is chosen with --class and sent when joining
            multiplayer_client=client,
            multiplayer_setup=make_setup(args),
        )

        app.run(mouse=False)

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
