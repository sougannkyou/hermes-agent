"""
Session Manager for AGP

Manages chat sessions and conversation history.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from threading import Lock


@dataclass
class Session:
    """Represents a chat session."""
    id: str
    created_at: float
    updated_at: float
    messages: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    current_agent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionManager:
    """Manages chat sessions with in-memory storage."""
    
    def __init__(self, max_sessions: int = 1000, session_ttl: int = 3600):
        """
        Initialize the session manager.
        
        Args:
            max_sessions: Maximum number of sessions to keep in memory
            session_ttl: Session time-to-live in seconds (default 1 hour)
        """
        self._sessions: Dict[str, Session] = {}
        self._lock = Lock()
        self._max_sessions = max_sessions
        self._session_ttl = session_ttl
    
    def create_session(
        self,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """Create a new session."""
        with self._lock:
            # Clean up old sessions if needed
            self._cleanup_old_sessions()
            
            sid = session_id or str(uuid.uuid4())
            now = time.time()
            
            session = Session(
                id=sid,
                created_at=now,
                updated_at=now,
                context=context or {},
            )
            
            self._sessions[sid] = session
            return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                # Check if session has expired
                if time.time() - session.updated_at > self._session_ttl:
                    del self._sessions[session_id]
                    return None
                return session
            return None
    
    def get_or_create_session(
        self,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """Get an existing session or create a new one."""
        if session_id:
            session = self.get_session(session_id)
            if session:
                # Update context if provided
                if context:
                    session.context.update(context)
                session.updated_at = time.time()
                return session
        
        return self.create_session(session_id, context)
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        **kwargs
    ) -> None:
        """Add a message to a session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                message = {"role": role, "content": content, **kwargs}
                session.messages.append(message)
                session.updated_at = time.time()
    
    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a session."""
        session = self.get_session(session_id)
        if session:
            return session.messages.copy()
        return []
    
    def update_context(
        self,
        session_id: str,
        context: Dict[str, Any],
    ) -> None:
        """Update session context."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.context.update(context)
                session.updated_at = time.time()
    
    def set_current_agent(
        self,
        session_id: str,
        agent_id: str,
    ) -> None:
        """Set the current agent for a session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.current_agent_id = agent_id
                session.updated_at = time.time()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    def _cleanup_old_sessions(self) -> None:
        """Remove expired sessions and enforce max limit."""
        now = time.time()
        
        # Remove expired sessions
        expired = [
            sid for sid, session in self._sessions.items()
            if now - session.updated_at > self._session_ttl
        ]
        for sid in expired:
            del self._sessions[sid]
        
        # If still over limit, remove oldest sessions
        if len(self._sessions) >= self._max_sessions:
            sorted_sessions = sorted(
                self._sessions.items(),
                key=lambda x: x[1].updated_at
            )
            # Remove oldest 10%
            to_remove = len(self._sessions) - int(self._max_sessions * 0.9)
            for sid, _ in sorted_sessions[:to_remove]:
                del self._sessions[sid]


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
