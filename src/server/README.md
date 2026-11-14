# Veinborn Multiplayer Server

WebSocket-based multiplayer server for Veinborn, enabling real-time cooperative gameplay.

## Quick Start

### Starting the Server

```bash
# From the project root
python src/server/run_server.py

# Or with custom host/port
VEINBORN_HOST=0.0.0.0 VEINBORN_PORT=8765 python src/server/run_server.py
```

The server will start and listen for WebSocket connections.

### Testing with the Test Client

```bash
# Start a test client
python src/server/test_client.py --name Player1

# In another terminal, start a second client
python src/server/test_client.py --name Player2 --port 8765
```

### Test Client Commands

Once connected, use these commands:
- `/create <name>` - Create a new game
- `/join <id>` - Join an existing game by ID
- `/ready` - Mark yourself as ready to start
- `/quit` - Disconnect
- `<message>` - Send a chat message to other players

## Architecture

### Components

1. **WebSocket Server** (`websocket_server.py`)
   - Handles client connections
   - Routes messages between clients
   - Manages game sessions

2. **Authentication** (`auth.py`)
   - Session management
   - Token-based authentication
   - Activity tracking

3. **Game Sessions** (`game_session.py`)
   - Manages individual game instances
   - Handles player joins/leaves
   - Processes game actions

4. **Multiplayer Game State** (`multiplayer_game_state.py`)
   - Wraps single-player GameState
   - Manages multiple player entities
   - Tracks rounds and actions

5. **Message Protocol** (`src/protocol/messages.py`)
   - Defines client-server message format
   - Type-safe message construction

### Message Flow

```
Client → WebSocket → Server → GameSession → GameState
                               ↓
                          Broadcast
                               ↓
                        All clients in game
```

## Configuration

Configure via environment variables:

```bash
VEINBORN_HOST=0.0.0.0          # Server bind address
VEINBORN_PORT=8765             # Server port
VEINBORN_MAX_CONNECTIONS=100   # Max concurrent connections
VEINBORN_LOG_LEVEL=INFO        # Logging level
```

Or edit `src/server/config.py` for defaults.

## Protocol

### Client → Server Messages

#### Authentication
```json
{
  "type": "auth",
  "data": {
    "player_name": "PlayerName"
  }
}
```

#### Create Game
```json
{
  "type": "create_game",
  "data": {
    "game_name": "My Game",
    "max_players": 4
  }
}
```

#### Join Game
```json
{
  "type": "join_game",
  "data": {
    "game_id": "uuid-here"
  }
}
```

#### Ready
```json
{
  "type": "ready",
  "data": {
    "ready": true
  }
}
```

#### Chat
```json
{
  "type": "chat",
  "data": {
    "message": "Hello world!"
  }
}
```

#### Intent
What the player wants to do. The server takes the actor from the session's seat
(never from the payload) and builds the action with the same `ActionFactory`
single-player uses. `rid` is optional and echoed in the `intent_result`.
```json
{
  "type": "intent",
  "data": {"intent": "move", "args": {"dx": 1, "dy": 0}, "rid": 7}
}
```
Intents: `move` (dx, dy; bumping attacks or mines), `survey`, `descend`, `pickup`,
`use` / `drop` (item_id, or none to pick the best healing / least useful item),
`equip` (item_id), `unequip` (slot), `ability`, `wait`. One turn-consuming intent
per living player per round.

#### Get Snapshot
`{"type": "get_snapshot", "data": {}}`: resend this player's current snapshot (resync).

### Server → Client Messages

#### Auth Success
```json
{
  "type": "auth_success",
  "data": {
    "session_id": "uuid",
    "player_id": "uuid"
  }
}
```

#### System Message
```json
{
  "type": "system",
  "data": {
    "message": "Game created",
    "level": "success"
  }
}
```

#### Lobby (before the game starts)
```json
{
  "type": "lobby",
  "data": {"game_id": "uuid", "game_name": "My Game", "is_started": false, "max_players": 4,
           "players": [{"player_id": "...", "player_name": "Alice", "player_class": "warrior", "is_ready": true}]}
}
```

#### Snapshot (once it runs)
Each player gets their own view (`core.snapshot.Snapshot.to_dict()`: player, entities,
map, messages, message_count, party, round), one `seq` per broadcast; a client keeps the
newest `seq` and drops older ones.
```json
{"type": "snapshot", "seq": 12, "data": {"game": {"game_id": "uuid", "is_started": true}, "snapshot": {...}}}
```

#### Intent Result
The answer to one intent, to its sender only: refused with the reason, or accepted
(sent after the snapshot the intent caused).
```json
{"type": "intent_result", "data": {"rid": 7, "ok": false, "messages": ["Waiting for the party: Bob"]}}
```

#### Chat Message
```json
{
  "type": "chat_message",
  "data": {
    "player_id": "uuid",
    "player_name": "Alice",
    "message": "Hello!"
  }
}
```

#### Player Joined/Left
```json
{
  "type": "player_joined",
  "data": {
    "player_id": "uuid",
    "player_name": "Bob"
  }
}
```

## Current Status

Every message carries the protocol version (`v`, `protocol.PROTOCOL_VERSION`); a peer on
another version is refused at auth. The architecture, the decisions behind it (one engine,
intents, per-viewer snapshots, round scheduling, seats) and what is left are in
`docs/architecture/MULTIPLAYER_ARCHITECTURE_PLAN.md`; the human client is the TUI on a
`RemoteDriver` (`run_multiplayer.py`), and `test_client.py` is a dev client.

## Testing

### Automated (real websockets)

`tests/integration/test_multiplayer_real_sockets.py` starts a `VeinbornServer` on an OS-assigned port and drives it with two real websocket clients (join, play, drop, reconnect). The other multiplayer tests use mock websockets and cannot catch protocol-level bugs (a handshake that failed on every real connection went unnoticed until this test existed).

### Manual Testing

1. Start the server:
   ```bash
   python src/server/run_server.py
   ```

2. Connect two test clients in separate terminals:
   ```bash
   python src/server/test_client.py --name Alice
   python src/server/test_client.py --name Bob
   ```

3. Create a game with Alice:
   ```
   Alice> /create Test Game
   ```

4. Join with Bob (use game ID from output):
   ```
   Bob> /join <game-id>
   ```

5. Both players mark ready:
   ```
   Alice> /ready
   Bob> /ready
   ```

6. Game should start automatically!

### Expected Behavior

- ✓ Both clients should authenticate successfully
- ✓ Game creation should return a game ID
- ✓ Second player should be able to join
- ✓ Both players should see join/leave notifications
- ✓ Chat messages should broadcast to all players
- ✓ Game should start when all players ready
- ✓ State updates should broadcast to all players

## Development

### Adding New Message Types

1. Add enum to `MessageType` in `src/protocol/messages.py`
2. Add constructor method to `Message` class
3. Add handler method to `VeinbornServer` class
4. Update `handle_message()` routing

### Adding New Game Features

1. Extend `MultiplayerGameState` if needed
2. Update `GameSession.process_action()` for new mechanics
3. Show it to players by extending the snapshot (`core/snapshot.py`) and `GameSession.snapshot_for()`
4. Update broadcast logic in `websocket_server.py`

## Performance Notes

- Current design supports ~100 concurrent connections
- Each game runs in its own async task
- State broadcasting is O(n) per game (n = player count)
- No delta compression: every state message is the receiving player's whole view (`snapshot`, ~8 KB for 4 players, `seq` per game; `lobby` before the game starts), built per recipient in `GameSession.state_messages()`. Add deltas only if a measurement shows a need.

## Security Notes

- All game logic runs server-side (client can't cheat)
- Sessions expire after 24 hours
- Connection timeout after 30 seconds
- Idle timeout after 5 minutes
- Max message size: 1MB

## Troubleshooting

### "Connection refused"
- Ensure server is running
- Check host/port are correct
- Verify firewall settings

### "Authentication failed"
- Check player name is valid (non-empty string)
- Verify WebSocket connection succeeded

### "Failed to join game"
- Game may be full (max 4 players)
- Game may already be started
- Check game ID is correct

### "Action execution failed"
- Action system not fully implemented yet
- Check logs for detailed error

## Next Steps

1. **Complete Action Routing** - Wire up movement and combat actions
2. **State Synchronization** - Ensure all clients see consistent state
3. **Test 2-Player Movement** - Verify basic multiplayer gameplay
4. **Add Monster Turn Processing** - Integrate existing AI system
5. **Implement Dungeon Generation** - Shared dungeon for all players

See `docs/design/MULTIPLAYER_DESIGN_2025.md` for full roadmap.
