# Multiplayer Chat Feature

This document describes the chat functionality for Veinborn multiplayer games.

## Overview

Players in a multiplayer game can now communicate with their party members using an in-game chat system. Chat messages appear in the message log at the bottom of the screen, alongside game events.

## Features

- **Real-time messaging**: Chat messages are instantly broadcast to all players in your game
- **Player identification**: Each message shows the sender's name
- **Message history**: The last 50 chat messages are retained
- **System messages**: Game events (player joined, player left, game started) appear in the message log
- **Easy to use**: Simple keyboard shortcuts to open chat

## How to Use Chat

### Opening the Chat Input

Press one of these keys to open the chat input:
- **'c'** - Chat key
- **Enter** - Alternative chat key

### Sending a Message

1. Press 'c' or Enter to open the chat input
2. Type your message
3. Press Enter to send
4. Your message will be broadcast to all players in your game

### Canceling

- Press **Esc** to cancel and close the chat input without sending

## Starting a Multiplayer Game with Chat

### 1. Start the Server

First, start the multiplayer server (if not already running):

```bash
python -m src.server.websocket_server
```

### 2. Launch Multiplayer Clients

Use the `run_multiplayer.py` script to connect:

#### Create a New Game

```bash
# Player 1 creates a game
python run_multiplayer.py --name Alice --create-game --game-name "Epic Adventure"

# Player 2 joins the game (use the game ID shown when created)
python run_multiplayer.py --name Bob --game-id <game-id>
```

#### Character Classes

You can choose your character class when joining:

```bash
python run_multiplayer.py --name Alice --class warrior --create-game
python run_multiplayer.py --name Bob --class mage --game-id <game-id>
python run_multiplayer.py --name Charlie --class rogue --game-id <game-id>
python run_multiplayer.py --name Dana --class healer --game-id <game-id>
```

Available classes: `warrior`, `mage`, `rogue`, `healer`

### 3. Chat with Your Party

Once in the game:
1. Press **'c'** or **Enter** to open chat
2. Type your message (e.g., "Let's explore the east corridor!")
3. Press **Enter** to send
4. All party members will see your message

## Message Display

Messages appear in the message log at the bottom of the screen:

- **Game messages**: Regular white text (e.g., "You attack the goblin!")
- **Chat messages**: Yellow player name with white text (e.g., `<Alice> Found healing potion!`)
- **System messages**: Cyan italic text in brackets (e.g., `[Bob joined the game]`)

The message log shows the last 4 messages (mixed game/chat/system). Older messages are retained in memory but scroll off the visible area.

## Example Session

```bash
# Terminal 1: Start server
python -m src.server.websocket_server

# Terminal 2: Player 1
python run_multiplayer.py --name Alice --create-game --game-name "Dungeon Dive" --class warrior

# Terminal 3: Player 2
python run_multiplayer.py --name Bob --game-id <game-id> --class mage

# In Alice's game:
# Press 'c'
# Type: "Welcome Bob! Ready to explore?"
# Press Enter

# In Bob's game:
# Press 'c'
# Type: "Ready! Let's go!"
# Press Enter
```

## Technical Details

### Architecture

- **Client**: `src/ui/multiplayer_client.py` - WebSocket client with chat support
- **Server**: `src/server/websocket_server.py` - Handles chat message broadcasting
- **UI Widget**: `src/ui/textual/widgets/chat_input.py` - Modal chat input
- **Message Display**: `src/ui/textual/widgets/message_log.py` - Shows chat and game messages

### Message Flow

1. Player presses 'c' → ChatInput widget appears
2. Player types message and presses Enter
3. Message sent to MultiplayerClient
4. Client sends WebSocket message (type: "chat") to server
5. Server broadcasts message (type: "chat_message") to all players in game
6. Each client receives message and adds to MessageLog
7. MessageLog displays message with player name

### Message Types

#### Client → Server
- `chat`: Send a chat message
  ```json
  {
    "type": "chat",
    "data": {
      "message": "Hello everyone!"
    }
  }
  ```

#### Server → Client
- `chat_message`: Broadcast chat message
  ```json
  {
    "type": "chat_message",
    "data": {
      "player_id": "uuid",
      "player_name": "Alice",
      "message": "Hello everyone!"
    }
  }
  ```

- `system`: System notification
  ```json
  {
    "type": "system",
    "data": {
      "message": "Alice joined the game",
      "level": "info"
    }
  }
  ```

## Single-Player Mode

Chat also works in single-player mode for testing:
- Press 'c' to open chat
- Type a message
- It will appear in your message log (only you will see it)

This is useful for testing the chat UI without connecting to a server.

## Troubleshooting

### Chat not working
- Ensure you're connected to the multiplayer server
- Check that you've joined a game (chat only works within a game)
- Verify the server is running and accessible

### Messages not appearing
- Check the message log at the bottom of the screen
- Messages scroll as new ones arrive (last 4 visible)
- System messages and game messages also use this space

### Cannot open chat input
- Make sure the game window has focus
- Try pressing 'c' or Enter
- Check that another modal isn't already open

## Future Enhancements

Potential improvements for the chat system:
- Private messages (whispers)
- Chat channels (party, global, trade)
- Emotes and quick messages
- Chat commands (/help, /who, etc.)
- Message timestamps
- Chat history scrollback viewer
- Profanity filter
- Ignore/mute players
- Chat macros

## See Also

- [Multiplayer Architecture](architecture/multiplayer.md)
- [WebSocket Protocol](architecture/websocket_protocol.md)
- [UI Widgets](architecture/ui_widgets.md)
