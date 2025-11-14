"""Message protocol for client-server communication."""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, Optional
import json


class MessageType(Enum):
    """Message types for client-server protocol."""

    # Client -> Server
    AUTH = "auth"
    ACTION = "action"
    CHAT = "chat"
    QUICK_COMMAND = "quick_command"
    JOIN_GAME = "join_game"
    CREATE_GAME = "create_game"
    LEAVE_GAME = "leave_game"
    READY = "ready"
    PAUSE = "pause"

    # Server -> Client
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    STATE = "state"
    DELTA = "delta"
    CHAT_MESSAGE = "chat_message"
    SYSTEM = "system"
    ERROR = "error"
    GAME_START = "game_start"
    GAME_END = "game_end"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"


@dataclass
class Message:
    """Base message class for all protocol messages."""

    type: str
    data: Dict[str, Any]
    timestamp: Optional[float] = None

    def to_json(self) -> str:
        """Serialize message to JSON."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """Deserialize message from JSON."""
        data = json.loads(json_str)
        return cls(**data)

    @classmethod
    def auth(cls, player_name: str) -> "Message":
        """Create authentication request."""
        return cls(
            type=MessageType.AUTH.value,
            data={"player_name": player_name},
        )

    @classmethod
    def auth_success(cls, session_id: str, player_id: str) -> "Message":
        """Create authentication success response."""
        return cls(
            type=MessageType.AUTH_SUCCESS.value,
            data={
                "session_id": session_id,
                "player_id": player_id,
            },
        )

    @classmethod
    def auth_failure(cls, reason: str) -> "Message":
        """Create authentication failure response."""
        return cls(
            type=MessageType.AUTH_FAILURE.value,
            data={"reason": reason},
        )

    @classmethod
    def action(cls, action_type: str, action_data: Dict[str, Any]) -> "Message":
        """Create action message."""
        return cls(
            type=MessageType.ACTION.value,
            data={
                "action_type": action_type,
                "action_data": action_data,
            },
        )

    @classmethod
    def state(cls, game_state: Dict[str, Any]) -> "Message":
        """Create full state update message."""
        return cls(
            type=MessageType.STATE.value,
            data={"state": game_state},
        )

    @classmethod
    def delta(cls, changes: Dict[str, Any]) -> "Message":
        """Create delta (partial) state update message."""
        return cls(
            type=MessageType.DELTA.value,
            data={"changes": changes},
        )

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
    def create_game(cls, game_name: str, max_players: int = 4, player_class: str = "warrior") -> "Message":
        """Create game creation request."""
        return cls(
            type=MessageType.CREATE_GAME.value,
            data={
                "game_name": game_name,
                "max_players": max_players,
                "player_class": player_class,
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
