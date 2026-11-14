"""Message protocol for client-server communication."""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, Optional
import json

from . import PROTOCOL_VERSION


class MessageType(Enum):
    """Message types for client-server protocol."""

    # Client -> Server
    AUTH = "auth"
    RECONNECT = "reconnect"
    INTENT = "intent"
    CHAT = "chat"
    QUICK_COMMAND = "quick_command"
    JOIN_GAME = "join_game"
    CREATE_GAME = "create_game"
    LEAVE_GAME = "leave_game"
    READY = "ready"
    GET_SNAPSHOT = "get_snapshot"
    PAUSE = "pause"

    # Server -> Client
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    SNAPSHOT = "snapshot"
    LOBBY = "lobby"
    CHAT_MESSAGE = "chat_message"
    SYSTEM = "system"
    ERROR = "error"
    INTENT_RESULT = "intent_result"
    GAME_START = "game_start"
    GAME_END = "game_end"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    PLAYER_DISCONNECTED = "player_disconnected"
    PLAYER_RECONNECTED = "player_reconnected"


@dataclass
class Message:
    """Base message class for all protocol messages."""

    type: str
    data: Dict[str, Any]
    timestamp: Optional[float] = None
    v: int = PROTOCOL_VERSION          # protocol version of the sender
    seq: Optional[int] = None          # per-game sequence number on state messages

    def to_json(self) -> str:
        """Serialize message to JSON."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """Deserialize message from JSON."""
        data = json.loads(json_str)
        # A sender that predates versioning is, by definition, not this version
        data.setdefault("v", 0)
        return cls(**data)

    @classmethod
    def auth(cls, player_name: str, auth_token: Optional[str] = None) -> "Message":
        """Create authentication request.

        auth_token, if provided, resumes a previously issued session
        instead of minting a new one (used when reconnecting).
        """
        data = {"player_name": player_name}
        if auth_token:
            data["auth_token"] = auth_token
        return cls(
            type=MessageType.AUTH.value,
            data=data,
        )

    @classmethod
    def auth_success(cls, session_id: str, player_id: str, auth_token: Optional[str] = None) -> "Message":
        """Create authentication success response."""
        data = {
            "session_id": session_id,
            "player_id": player_id,
        }
        if auth_token:
            data["auth_token"] = auth_token
        return cls(
            type=MessageType.AUTH_SUCCESS.value,
            data=data,
        )

    @classmethod
    def auth_failure(cls, reason: str) -> "Message":
        """Create authentication failure response."""
        return cls(
            type=MessageType.AUTH_FAILURE.value,
            data={"reason": reason},
        )

    @classmethod
    def intent(cls, intent: str, rid: Optional[int] = None, **args: Any) -> "Message":
        """Create intent message: what the player wants, never who acts.

        The server takes the actor from the session's seat, so the payload
        carries no actor id (nothing to spoof). `rid` (optional) is echoed in
        the `intent_result` reply so the sender can match it.
        """
        data: Dict[str, Any] = {"intent": intent, "args": args}
        if rid is not None:
            data["rid"] = rid
        return cls(type=MessageType.INTENT.value, data=data)

    @classmethod
    def intent_result(cls, rid: Optional[int], ok: bool, messages: Optional[list] = None) -> "Message":
        """The server's answer to one intent, to its sender only: accepted, or refused and why.

        Sent after the state broadcast an accepted intent causes, so the sender's
        snapshot is already current when the result arrives.
        """
        return cls(
            type=MessageType.INTENT_RESULT.value,
            data={"rid": rid, "ok": ok, "messages": list(messages or [])},
        )

    @classmethod
    def snapshot(cls, seq: int, game: Dict[str, Any], snapshot: Dict[str, Any]) -> "Message":
        """One viewer's whole view of a running game (`core.snapshot.Snapshot.to_dict()`).

        `seq` grows with every state message of a game; a client keeps the highest
        one it has seen and ignores anything older.
        """
        return cls(
            type=MessageType.SNAPSHOT.value,
            data={"game": game, "snapshot": snapshot},
            seq=seq,
        )

    @classmethod
    def lobby(cls, lobby: Dict[str, Any]) -> "Message":
        """The game before it starts: who is seated and who is ready."""
        return cls(type=MessageType.LOBBY.value, data=lobby)

    @classmethod
    def get_snapshot(cls) -> "Message":
        """Ask for the current state (join late, or resync)."""
        return cls(type=MessageType.GET_SNAPSHOT.value, data={})

    @classmethod
    def chat_message(
        cls, player_id: str, player_name: str, message: str
    ) -> "Message":
        """Create chat message."""
        return cls(
            type=MessageType.CHAT_MESSAGE.value,
            data={
                "player_id": player_id,
                "player_name": player_name,
                "message": message,
            },
        )

    @classmethod
    def system(cls, message: str, level: str = "info") -> "Message":
        """Create system message."""
        return cls(
            type=MessageType.SYSTEM.value,
            data={
                "message": message,
                "level": level,
            },
        )

    @classmethod
    def error(cls, error_message: str, code: Optional[str] = None) -> "Message":
        """Create error message."""
        return cls(
            type=MessageType.ERROR.value,
            data={
                "message": error_message,
                "code": code,
            },
        )

    @classmethod
    def create_game(cls, game_name: str, max_players: int = 4, player_class: str = "warrior",
                    reveal_map: bool = False) -> "Message":
        """Create game creation request."""
        return cls(
            type=MessageType.CREATE_GAME.value,
            data={
                "game_name": game_name,
                "max_players": max_players,
                "player_class": player_class,
                "reveal_map": reveal_map,
            },
        )

    @classmethod
    def join_game(cls, game_id: str, player_class: str = "warrior") -> "Message":
        """Create join game request."""
        return cls(
            type=MessageType.JOIN_GAME.value,
            data={
                "game_id": game_id,
                "player_class": player_class,
            },
        )

    @classmethod
    def player_joined(cls, player_id: str, player_name: str, player_class: str = "warrior") -> "Message":
        """Create player joined notification."""
        return cls(
            type=MessageType.PLAYER_JOINED.value,
            data={
                "player_id": player_id,
                "player_name": player_name,
                "player_class": player_class,
            },
        )

    @classmethod
    def player_left(cls, player_id: str, player_name: str) -> "Message":
        """Create player left notification."""
        return cls(
            type=MessageType.PLAYER_LEFT.value,
            data={
                "player_id": player_id,
                "player_name": player_name,
            },
        )

    @classmethod
    def game_start(cls, game_id: str, players: list[Dict[str, str]]) -> "Message":
        """Create game start notification."""
        return cls(
            type=MessageType.GAME_START.value,
            data={
                "game_id": game_id,
                "players": players,
            },
        )

    @classmethod
    def player_disconnected(cls, player_id: str, player_name: str) -> "Message":
        """Create player disconnected notification."""
        return cls(
            type=MessageType.PLAYER_DISCONNECTED.value,
            data={
                "player_id": player_id,
                "player_name": player_name,
            },
        )

    @classmethod
    def player_reconnected(cls, player_id: str, player_name: str) -> "Message":
        """Create player reconnected notification."""
        return cls(
            type=MessageType.PLAYER_RECONNECTED.value,
            data={
                "player_id": player_id,
                "player_name": player_name,
            },
        )

    @classmethod
    def reconnect(cls, session_id: str) -> "Message":
        """Create reconnection request."""
        return cls(
            type=MessageType.RECONNECT.value,
            data={"session_id": session_id},
        )
