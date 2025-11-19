#!/usr/bin/env python3
"""Script to run the Brogue multiplayer server."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.websocket_server import BrogueServer
from server.config import config


def setup_logging():
    """Configure logging for the server."""
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("brogue_server.log"),
        ],
    )


async def async_main():
    """Async main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Brogue Multiplayer Server")
    logger.info("=" * 60)
    logger.info(f"Host: {config.host}")
    logger.info(f"Port: {config.port}")
    logger.info(f"Max connections: {config.max_connections}")
    logger.info(f"Actions per round: {config.actions_per_round}")
    logger.info("=" * 60)

    server = BrogueServer(config.host, config.port)

    try:
        await server.start()
        logger.info("Server is running. Press Ctrl+C to stop.")
        # Run forever
        await asyncio.Future()
    except KeyboardInterrupt:
        logger.info("\nReceived interrupt signal. Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
    finally:
        await server.stop()
        logger.info("Server shutdown complete")

    return 0


def main():
    """Entry point for pip-installed brogue-server command."""
    try:
        exit_code = asyncio.run(async_main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
