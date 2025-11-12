"""Authentication and session management for multiplayer server."""

import secrets
import time
from dataclasses import dataclass, field
from typing import Dict, Optional
from uuid import uuid4


@dataclass
class Session:
    """Represents an authenticated player session."""

    session_id: str
    player_id: str
    player_name: str
    created_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    game_id: Optional[str] = None

    def is_expired(self, expiry_seconds: int) -> bool:
        """Check if session has expired."""
        return (time.time() - self.created_at) > expiry_seconds

    def update_activity(self) -> None:
        """Update last seen timestamp."""
        self.last_seen = time.time()

    def is_idle(self, idle_seconds: int) -> bool:
        """Check if session is idle."""
        return (time.time() - self.last_seen) > idle_seconds


class AuthManager:
    """Manages player authentication and sessions."""

    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._player_to_session: Dict[str, str] = {}
        self._tokens: Dict[str, str] = {}  # token -> session_id

    def create_session(self, player_name: str) -> tuple[str, Session]:
        """Create a new authenticated session.

        Args:
            player_name: Name of the player

        Returns:
            Tuple of (auth_token, session)
        """
        # Generate unique IDs
        player_id = str(uuid4())
        session_id = str(uuid4())
        auth_token = secrets.token_urlsafe(32)

        # Create session
        session = Session(
            session_id=session_id,
            player_id=player_id,
            player_name=player_name,
        )

        # Store session
        self._sessions[session_id] = session
        self._player_to_session[player_id] = session_id
        self._tokens[auth_token] = session_id

        return auth_token, session

    def verify_token(self, auth_token: str) -> Optional[Session]:
        """Verify an authentication token.

        Args:
            auth_token: Token to verify

        Returns:
            Session if valid, None otherwise
        """
        session_id = self._tokens.get(auth_token)
        if not session_id:
            return None

        session = self._sessions.get(session_id)
        if session:
            session.update_activity()

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def get_session_by_player(self, player_id: str) -> Optional[Session]:
        """Get a session by player ID."""
        session_id = self._player_to_session.get(player_id)
        if session_id:
            return self._sessions.get(session_id)
        return None

    def invalidate_session(self, session_id: str) -> None:
        """Invalidate a session."""
        session = self._sessions.pop(session_id, None)
        if session:
            self._player_to_session.pop(session.player_id, None)
            # Remove token
            self._tokens = {
                token: sid
                for token, sid in self._tokens.items()
                if sid != session_id
            }

    def cleanup_expired_sessions(self, expiry_seconds: int) -> int:
        """Remove expired sessions.

        Args:
            expiry_seconds: Session expiry time in seconds

        Returns:
            Number of sessions cleaned up
        """
        expired = [
            sid
            for sid, session in self._sessions.items()
            if session.is_expired(expiry_seconds)
        ]

        for sid in expired:
            self.invalidate_session(sid)

        return len(expired)

    def get_active_sessions(self) -> list[Session]:
        """Get all active sessions."""
        return list(self._sessions.values())

    def session_count(self) -> int:
        """Get count of active sessions."""
        return len(self._sessions)
