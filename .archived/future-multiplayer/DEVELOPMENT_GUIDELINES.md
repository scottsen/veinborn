# Brogue Development Guidelines

**Document Type:** Development Standards
**Audience:** All Developers
**Status:** Active
**Last Updated:** 2025-10-23

---

## Overview

This document defines development standards, recommended libraries, testing approaches, and coding patterns for Brogue development.

---

## Technology Stack

### Core Dependencies

```txt
# requirements.txt

# ===== Core Infrastructure =====
python>=3.10

# Messaging & Networking
nats-py>=2.6.0              # NATS messaging
websockets>=12.0            # WebSocket server/client
aiohttp>=3.9.0             # Async HTTP (REST API)

# Database
asyncpg>=0.29.0            # PostgreSQL async driver (fastest!)
alembic>=1.13.0            # Database migrations

# ===== Data & Validation =====
pydantic>=2.0              # Type-safe models, validation
pydantic-settings>=2.0     # Environment variable config

# ===== UI =====
textual>=0.45.0            # Terminal UI framework
rich>=13.7.0               # Rich terminal output

# ===== Logging & Observability =====
structlog>=23.2.0          # Structured logging (JSON)
prometheus-client>=0.19.0  # Metrics for Grafana

# ===== Utilities =====
tenacity>=8.2.0            # Retry logic with backoff
python-dateutil>=2.8.0     # Date/time handling

# ===== Development =====
pytest>=7.4.0
pytest-asyncio>=0.23.0
pytest-mock>=3.12.0
pytest-cov>=4.1.0
pytest-timeout>=2.2.0
hypothesis>=6.92.0         # Property-based testing
faker>=20.0.0              # Test data generation
freezegun>=1.4.0           # Mock time for testing

# ===== Optional (add if needed) =====
# lupa>=2.0                # Lua scripting engine
# watchdog>=3.0            # File system monitoring (hot-reload)
```

---

## Project Structure

```
brogue/
├── src/
│   └── brogue/
│       ├── __init__.py
│       ├── config.py                # Pydantic settings
│       │
│       ├── messages/                # Message models
│       │   ├── __init__.py
│       │   ├── base.py              # BrogueMessage base class
│       │   ├── actions.py           # Player actions
│       │   ├── events.py            # State updates
│       │   └── critical.py          # Critical events
│       │
│       ├── messaging/               # Messaging infrastructure
│       │   ├── __init__.py
│       │   ├── subjects.py          # NATS subject definitions
│       │   ├── registry.py          # MessageRegistry
│       │   └── bus.py               # MessageBus abstraction
│       │
│       ├── services/                # Game services
│       │   ├── __init__.py
│       │   ├── game_instance.py     # Game logic service
│       │   ├── connection.py        # WebSocket gateway
│       │   └── persistence.py       # Database service
│       │
│       ├── systems/                 # Pluggable game systems
│       │   ├── __init__.py
│       │   ├── base.py              # GameSystem base class
│       │   ├── combat.py            # Combat system
│       │   ├── mining.py            # Mining system
│       │   └── crafting.py          # Crafting system
│       │
│       ├── events/                  # Event bus (game logic)
│       │   ├── __init__.py
│       │   └── event_bus.py         # GameEventBus
│       │
│       ├── content/                 # Content loading
│       │   ├── __init__.py
│       │   └── loader.py            # YAML content loader
│       │
│       ├── logging/                 # Logging setup
│       │   ├── __init__.py
│       │   ├── setup.py             # Structlog configuration
│       │   └── logger.py            # Context-aware logger
│       │
│       └── models/                  # Domain models
│           ├── __init__.py
│           ├── player.py
│           ├── monster.py
│           └── dungeon.py
│
├── data/                            # Game content (YAML)
│   ├── monsters/
│   ├── abilities/
│   ├── recipes/
│   └── status_effects/
│
├── tests/                           # Test suite
│   ├── conftest.py                  # Pytest fixtures
│   ├── test_messaging.py
│   ├── test_game_logic.py
│   └── integration/
│
├── docs/                            # Documentation
│   └── architecture/
│
├── requirements.txt
├── pyproject.toml
├── docker-compose.yml               # Dev environment
└── README.md
```

---

## Configuration Management

### Pydantic Settings (12-Factor App)

```python
# brogue/config.py
from pydantic_settings import BaseSettings
from typing import List

class ServerConfig(BaseSettings):
    """
    All configuration from environment variables.

    Override via .env file or ENV vars.
    """

    # ===== Service =====
    environment: str = "development"  # development, staging, production
    service_name: str = "brogue-game-instance"

    # ===== NATS =====
    nats_urls: List[str] = ["nats://localhost:4222"]
    nats_user: str | None = None
    nats_password: str | None = None

    # ===== Database =====
    db_url: str = "postgresql://brogue:brogue@localhost/brogue"
    db_pool_min: int = 2
    db_pool_max: int = 10

    # ===== Game Settings =====
    max_players_per_party: int = 4
    tick_rate_ms: int = 100  # 10 Hz

    # ===== Logging =====
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    log_format: str = "json"  # json or console

    # ===== Observability =====
    metrics_enabled: bool = True
    metrics_port: int = 9090

    class Config:
        env_file = ".env"
        env_prefix = "BROGUE_"  # All env vars: BROGUE_NATS_URLS, etc.

# Singleton instance
config = ServerConfig()
```

### Environment Variables

```bash
# .env (development)
BROGUE_ENVIRONMENT=development
BROGUE_NATS_URLS=["nats://localhost:4222"]
BROGUE_DB_URL=postgresql://brogue:brogue@localhost/brogue
BROGUE_LOG_LEVEL=DEBUG
BROGUE_LOG_FORMAT=console

# .env.production
BROGUE_ENVIRONMENT=production
BROGUE_NATS_URLS=["nats://nats-01:4222","nats://nats-02:4222","nats://nats-03:4222"]
BROGUE_DB_URL=postgresql://brogue:***@db.internal/brogue
BROGUE_LOG_LEVEL=INFO
BROGUE_LOG_FORMAT=json
```

---

## Dependency Injection

### Simple Factory Pattern (Recommended)

```python
# brogue/container.py
from brogue.config import config
from brogue.messaging.bus import MessageBus
from brogue.services.game_instance import GameInstanceService
from nats.aio.client import Client as NATS
import asyncpg

class ServiceContainer:
    """Simple DI container - manages service lifecycle"""

    def __init__(self, config: ServerConfig):
        self.config = config
        self._nats = None
        self._db_pool = None
        self._message_bus = None

    async def nats(self) -> NATS:
        """Get or create NATS connection"""
        if not self._nats:
            self._nats = await NATS().connect(
                servers=self.config.nats_urls,
                user=self.config.nats_user,
                password=self.config.nats_password
            )
        return self._nats

    async def db_pool(self) -> asyncpg.Pool:
        """Get or create database pool"""
        if not self._db_pool:
            self._db_pool = await asyncpg.create_pool(
                self.config.db_url,
                min_size=self.config.db_pool_min,
                max_size=self.config.db_pool_max
            )
        return self._db_pool

    async def message_bus(self) -> MessageBus:
        """Get or create MessageBus"""
        if not self._message_bus:
            nats = await self.nats()
            self._message_bus = MessageBus(nats)
        return self._message_bus

    async def game_instance(self, instance_id: str) -> GameInstanceService:
        """Create GameInstance (factory)"""
        bus = await self.message_bus()
        db = await self.db_pool()
        return GameInstanceService(bus, db, instance_id)

    async def cleanup(self):
        """Cleanup resources on shutdown"""
        if self._nats:
            await self._nats.drain()
        if self._db_pool:
            await self._db_pool.close()

# Usage:
container = ServiceContainer(config)
game = await container.game_instance("instance_42")
```

---

## Testing Strategy

### Test Structure

```python
# tests/conftest.py
import pytest
import asyncio
from brogue.config import ServerConfig
from brogue.container import ServiceContainer

@pytest.fixture
def test_config():
    """Test configuration"""
    return ServerConfig(
        environment="test",
        nats_urls=["nats://localhost:4222"],
        db_url="postgresql://brogue:brogue@localhost/brogue_test",
        log_level="DEBUG"
    )

@pytest.fixture
async def container(test_config):
    """Service container for tests"""
    c = ServiceContainer(test_config)
    yield c
    await c.cleanup()

@pytest.fixture
async def message_bus(container):
    """MessageBus fixture"""
    return await container.message_bus()

@pytest.fixture
def sample_player():
    """Sample player for testing"""
    from brogue.models.player import Player
    return Player(
        id="test_player",
        class_name="warrior",
        hp=20,
        max_hp=20,
        pos=(5, 5)
    )
```

### Unit Tests

```python
# tests/test_messages.py
import pytest
from brogue.messages.actions import MoveAction, Direction
from brogue.messaging.registry import MessageRegistry

def test_message_serialization():
    """Test Pydantic serialization"""
    action = MoveAction(
        player_id="alice",
        direction=Direction.NORTH
    )

    # Serialize to bytes
    data = action.to_nats()
    assert isinstance(data, bytes)

    # Deserialize back
    parsed = MoveAction.from_nats(data)
    assert parsed.player_id == "alice"
    assert parsed.direction == Direction.NORTH
    assert parsed.message_id  # Auto-generated

def test_message_registry():
    """Test auto-parsing"""
    MessageRegistry.register(MoveAction)

    data = b'{"type": "move", "player_id": "alice", "direction": "north"}'
    message = MessageRegistry.parse(data)

    assert isinstance(message, MoveAction)
    assert message.player_id == "alice"
    assert message.direction == Direction.NORTH
```

### Async Tests

```python
# tests/test_game_logic.py
import pytest
from brogue.services.game_instance import GameInstanceService
from brogue.messages.actions import MoveAction, Direction

@pytest.mark.asyncio
async def test_player_movement(message_bus, sample_player):
    """Test player can move"""
    game = GameInstanceService(message_bus, instance_id="test")
    game.add_player(sample_player)

    # Create move action
    action = MoveAction(
        player_id="test_player",
        direction=Direction.NORTH
    )

    # Process action
    result = await game.process_action(action)

    # Assert
    assert result.success
    player = game.get_player("test_player")
    assert player.pos == (5, 4)  # Moved north (y-1)

@pytest.mark.asyncio
async def test_cant_move_through_walls(message_bus):
    """Server validates movement"""
    game = GameInstanceService(message_bus, instance_id="test")

    # Place wall north of player
    game.map.set_tile(5, 4, TileType.WALL)

    # Try to move into wall
    action = MoveAction(player_id="test_player", direction=Direction.NORTH)
    result = await game.process_action(action)

    # Assert
    assert not result.success
    assert "not walkable" in result.error
```

### Property-Based Tests (Hypothesis)

```python
from hypothesis import given, strategies as st

@given(
    x=st.integers(0, 79),
    y=st.integers(0, 23)
)
def test_all_coordinates_valid(x, y):
    """Any coordinate in range should be valid"""
    from brogue.models.dungeon import Dungeon

    dungeon = Dungeon(width=80, height=24)
    tile = dungeon.get_tile(x, y)

    assert tile is not None  # Never crashes!
    assert 0 <= tile.x <= 79
    assert 0 <= tile.y <= 23

@given(damage=st.integers(1, 1000))
def test_damage_never_negative_hp(damage):
    """Player HP can't go negative"""
    from brogue.models.player import Player

    player = Player(hp=10, max_hp=10)
    player.take_damage(damage)

    assert player.hp >= 0  # Always >= 0
    assert player.hp <= player.max_hp
```

### Integration Tests

```python
# tests/integration/test_message_flow.py
import pytest
import asyncio

@pytest.mark.asyncio
async def test_client_server_message_flow(nats_server):
    """Test full message flow: Client → Server → Client"""
    from brogue.services.connection import ConnectionService
    from brogue.services.game_instance import GameInstanceService
    from brogue.client.game_client import GameClient

    # Start services
    connection_svc = ConnectionService(nats_url=nats_server.url)
    game_svc = GameInstanceService(instance_id="test")

    await connection_svc.start()
    await game_svc.start()

    # Connect client
    client = GameClient(server_url="ws://localhost:8765")
    await client.connect()

    # Send action
    await client.send_move(Direction.NORTH)

    # Wait for state update
    await asyncio.sleep(0.2)

    # Assert state updated
    assert client.state is not None
    assert client.state.players[0].pos.y == 4  # Moved north
```

### Load Tests

```python
# tests/load/test_concurrent_players.py
import pytest
import asyncio

@pytest.mark.asyncio
@pytest.mark.slow
async def test_100_concurrent_players():
    """Can handle 100 concurrent players"""
    from brogue.client.game_client import GameClient

    # Create 100 clients
    clients = [GameClient(f"player_{i}") for i in range(100)]

    # Connect all
    await asyncio.gather(*[c.connect() for c in clients])

    # All move simultaneously
    start = time.time()
    await asyncio.gather(*[c.send_move(Direction.NORTH) for c in clients])
    duration = time.time() - start

    # Should handle in <1 second
    assert duration < 1.0
```

---

## Code Style & Linting

### Type Hints (Required)

```python
# ✅ Good - typed
async def process_action(
    self,
    action: MoveAction,
    player_id: str
) -> ActionResult:
    """Process player action"""
    # Type hints enable IDE autocomplete, catch bugs
    ...

# ❌ Bad - untyped
async def process_action(self, action, player_id):
    ...
```

### Ruff Configuration

```toml
# pyproject.toml
[tool.ruff]
line-length = 120

[tool.ruff.lint]
select = [
    "F",    # Pyflakes (undefined names, etc.)
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "I",    # isort (import sorting)
    "N",    # pep8-naming
    "UP",   # pyupgrade (modern Python syntax)
    "B",    # flake8-bugbear (likely bugs)
    "C4",   # flake8-comprehensions
    "SIM",  # flake8-simplify
]

ignore = [
    "E501",  # Line too long (formatter handles this)
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

---

## Logging Standards

### Structured Logging (Required)

```python
from brogue.logging.logger import get_logger

logger = get_logger(__name__)

# ✅ Good - structured, searchable
logger.info(
    "player_moved",
    player_id="alice",
    from_pos=(5, 5),
    to_pos=(5, 4),
    tick=1234
)

# ❌ Bad - unstructured string
logger.info(f"Player alice moved from (5,5) to (5,4) at tick 1234")
```

### Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| **DEBUG** | Development details | Player state dump, message contents |
| **INFO** | Normal operations | Player joined, action processed |
| **WARNING** | Unusual but not error | High latency, retrying connection |
| **ERROR** | Operation failed | Database error, invalid message |
| **CRITICAL** | Service failure | Can't connect to NATS, out of memory |

### Context Propagation

```python
from brogue.logging.logger import LogContext

async def handle_action(action: MoveAction):
    # Set context for this scope
    with LogContext(
        player_id=action.player_id,
        party_id="dragon_slayers"
    ):
        logger.info("processing_action")  # Auto includes context
        # ... process ...
        logger.info("action_complete")    # Also includes context
```

---

## Error Handling

### Async Exception Handling

```python
# ✅ Good - don't let exceptions crash the service
async def handle_message(msg):
    try:
        action = MessageRegistry.parse(msg.data)
        await process(action)
    except ValidationError as e:
        logger.error("Invalid message", error=str(e))
        # Continue processing other messages
    except Exception as e:
        logger.error("Unexpected error", error=str(e), exc_info=True)
        # Log but don't crash
```

### Retries with Backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def save_to_database(data):
    """Retry with exponential backoff"""
    await db.execute("INSERT INTO ...", data)
    # Retries: 0s, 2s, 4s, then gives up
```

---

## Performance Guidelines

### Async Best Practices

```python
# ✅ Good - run in parallel
results = await asyncio.gather(
    fetch_player_data(player_id),
    fetch_inventory(player_id),
    fetch_stats(player_id)
)

# ❌ Bad - sequential (slow!)
player = await fetch_player_data(player_id)
inventory = await fetch_inventory(player_id)
stats = await fetch_stats(player_id)
```

### Database Queries

```python
# ✅ Good - use connection pool
async with db_pool.acquire() as conn:
    result = await conn.fetchrow("SELECT * FROM players WHERE id = $1", player_id)

# ✅ Good - batch queries
player_ids = ["alice", "bob", "carol"]
results = await conn.fetch(
    "SELECT * FROM players WHERE id = ANY($1)",
    player_ids
)

# ❌ Bad - N+1 query problem
for player_id in player_ids:
    await conn.fetchrow("SELECT * FROM players WHERE id = $1", player_id)
```

---

## Git Workflow

### Branch Naming

```
feature/add-mining-system
bugfix/fix-combat-crash
refactor/extract-event-bus
docs/update-architecture
```

### Commit Messages

```
feat: Add mining system with turn-based mechanics

- Implement MiningSystem as pluggable game system
- Add YAML content for ore deposits
- Subscribe to mining events via event bus

Refs: #123
```

---

## References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)
- [structlog Documentation](https://www.structlog.org/)
- [NATS Python Client](https://github.com/nats-io/nats.py)

---

**Next Steps:**
1. Set up development environment (Docker Compose)
2. Install dependencies (`pip install -r requirements.txt`)
3. Run tests (`pytest`)
4. Review coding examples in `src/brogue/`
