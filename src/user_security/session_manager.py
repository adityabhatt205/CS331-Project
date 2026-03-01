"""
Session management for the Factory Floor System.
Handles user sessions with database persistence, tracking, and timeout.
"""

import time
import logging
from typing import Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta

from .database import db


@dataclass
class Session:
    """Represents a user session with database persistence."""
    session_id: str
    user_id: int
    username: str
    role: str
    login_time: float
    last_activity: float
    expires_at: float
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True
    
    @property
    def duration(self) -> float:
        """Get session duration in seconds."""
        return time.time() - self.login_time
    
    @property
    def idle_time(self) -> float:
        """Get idle time since last activity in seconds."""
        return time.time() - self.last_activity
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return time.time() > self.expires_at
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        current_time = time.time()
        self.last_activity = current_time
        
        # Update in database
        try:
            db.update_session_activity(self.session_id)
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to update session activity: {e}")


class SessionManager:
    """Manages user sessions with database persistence and production features."""
    
    def __init__(self, max_idle_time: int = 3600, max_session_time: int = 28800,
                 persist_sessions: bool = True):
        """
        Initialize session manager.
        
        Args:
            max_idle_time: Maximum idle time in seconds (default: 1 hour)
            max_session_time: Maximum session time in seconds (default: 8 hours)
            persist_sessions: Whether to persist sessions in database
        """
        self._sessions: Dict[str, Session] = {}  # In-memory cache
        self._user_sessions: Dict[int, str] = {}  # user_id -> session_id
        self._max_idle_time = max_idle_time
        self._max_session_time = max_session_time
        self._persist_sessions = persist_sessions
        self._session_counter = 0
        self._logger = logging.getLogger(__name__)
        
        # Load active sessions from database on startup
        if self._persist_sessions:
            self._load_active_sessions()
    
    def _load_active_sessions(self) -> None:
        """Load active sessions from database on startup."""
        try:
            active_sessions = db.get_active_sessions()
            
            for session_data in active_sessions:
                session = Session(
                    session_id=session_data['session_id'],
                    user_id=session_data['user_id'],
                    username=session_data['username'],
                    role=session_data['role'],
                    login_time=time.mktime(datetime.fromisoformat(
                        session_data['login_time'].replace('Z', '+00:00')
                    ).timetuple()),
                    last_activity=time.mktime(datetime.fromisoformat(
                        session_data['last_activity'].replace('Z', '+00:00')
                    ).timetuple()),
                    expires_at=time.mktime(datetime.fromisoformat(
                        session_data['expires_at'].replace('Z', '+00:00')
                    ).timetuple()),
                    is_active=True
                )
                
                # Only load non-expired sessions
                if not session.is_expired():
                    self._sessions[session.session_id] = session
                    self._user_sessions[session.user_id] = session.session_id
                else:
                    # Mark expired session as inactive in database
                    db.invalidate_session(session.session_id)
            
            self._logger.info(f"Loaded {len(self._sessions)} active sessions from database")
            
        except Exception as e:
            self._logger.error(f"Failed to load sessions from database: {e}")
    
    def create_session(self, user_id: int, username: str, role: str,
                      ip_address: str = None, user_agent: str = None) -> str:
        """
        Create a new session for a user.
        
        Args:
            user_id: User ID
            username: Username
            role: User role
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Session ID
        """
        try:
            # Remove existing session for the user
            self.remove_user_session(user_id)
            
            # Generate session ID
            import secrets
            self._session_counter += 1
            session_id = f"session_{user_id}_{self._session_counter}_{secrets.token_hex(16)}"
            
            # Calculate session times
            current_time = time.time()
            expires_at = current_time + self._max_session_time
            
            # Create session
            session = Session(
                session_id=session_id,
                user_id=user_id,
                username=username,
                role=role,
                login_time=current_time,
                last_activity=current_time,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Store in memory cache
            self._sessions[session_id] = session
            self._user_sessions[user_id] = session_id
            
            # Persist to database if enabled
            if self._persist_sessions:
                session_data = {
                    'session_id': session_id,
                    'user_id': user_id,
                    'username': username,
                    'role': role,
                    'login_time': datetime.fromtimestamp(current_time).isoformat(),
                    'last_activity': datetime.fromtimestamp(current_time).isoformat(),
                    'expires_at': datetime.fromtimestamp(expires_at).isoformat(),
                    'ip_address': ip_address,
                    'user_agent': user_agent
                }
                
                if not db.create_session(session_data):
                    self._logger.warning(f"Failed to persist session {session_id} to database")
            
            self._logger.info(f"Created session {session_id} for user {username}")
            return session_id
            
        except Exception as e:
            self._logger.error(f"Failed to create session for user {username}: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by session ID with activity update."""
        try:
            session = self._sessions.get(session_id)
            
            if not session:
                # Try to load from database
                if self._persist_sessions:
                    session_data = db.get_session(session_id)
                    if session_data:
                        session = Session(
                            session_id=session_data['session_id'],
                            user_id=session_data['user_id'],
                            username=session_data['username'],
                            role=session_data['role'],
                            login_time=time.mktime(datetime.fromisoformat(
                                session_data['login_time'].replace('Z', '+00:00')
                            ).timetuple()),
                            last_activity=time.mktime(datetime.fromisoformat(
                                session_data['last_activity'].replace('Z', '+00:00')
                            ).timetuple()),
                            expires_at=time.mktime(datetime.fromisoformat(
                                session_data['expires_at'].replace('Z', '+00:00')
                            ).timetuple()),
                            is_active=bool(session_data['is_active'])
                        )
                        self._sessions[session_id] = session
            
            if session and session.is_active:
                # Check if session has expired
                if self._is_session_expired(session):
                    self.invalidate_session(session_id)
                    return None
                
                # Update activity
                session.update_activity()
                return session
            
            return None
            
        except Exception as e:
            self._logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    def get_user_session(self, user_id: int) -> Optional[Session]:
        """Get active session for a user."""
        session_id = self._user_sessions.get(user_id)
        if session_id:
            return self.get_session(session_id)
        return None
    
    def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate a session.
        
        Returns:
            True if session was found and invalidated, False otherwise
        """
        try:
            session = self._sessions.get(session_id)
            if session:
                session.is_active = False
                
                # Remove from user sessions mapping
                if session.user_id in self._user_sessions:
                    del self._user_sessions[session.user_id]
                
                # Update database if persistence is enabled
                if self._persist_sessions:
                    db.invalidate_session(session_id)
                
                # Remove from memory cache
                if session_id in self._sessions:
                    del self._sessions[session_id]
                
                self._logger.info(f"Invalidated session {session_id}")
                return True
            
            return False
            
        except Exception as e:
            self._logger.error(f"Error invalidating session {session_id}: {e}")
            return False
    
    def remove_user_session(self, user_id: int) -> bool:
        """Remove any existing session for a user."""
        session_id = self._user_sessions.get(user_id)
        if session_id:
            return self.invalidate_session(session_id)
        return False
    
    def is_user_logged_in(self, user_id: int) -> bool:
        """Check if a user has an active session."""
        return self.get_user_session(user_id) is not None
    
    def get_active_sessions(self) -> Dict[str, Session]:
        """Get all active sessions."""
        # Clean up expired sessions first
        self.cleanup_expired_sessions()
        return {sid: session for sid, session in self._sessions.items() 
                if session.is_active and not session.is_expired()}
    
    def get_logged_in_users(self) -> Set[int]:
        """Get set of currently logged in user IDs."""
        active_sessions = self.get_active_sessions()
        return {session.user_id for session in active_sessions.values()}
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            expired_count = 0
            expired_sessions = []
            
            # Find expired sessions
            for session_id, session in self._sessions.items():
                if self._is_session_expired(session):
                    expired_sessions.append(session_id)
            
            # Invalidate expired sessions
            for session_id in expired_sessions:
                if self.invalidate_session(session_id):
                    expired_count += 1
            
            # Also cleanup in database
            if self._persist_sessions:
                db_cleanup_count = db.cleanup_expired_sessions()
                self._logger.info(f"Cleaned up {db_cleanup_count} expired sessions from database")
            
            if expired_count > 0:
                self._logger.info(f"Cleaned up {expired_count} expired sessions")
            
            return expired_count
            
        except Exception as e:
            self._logger.error(f"Error during session cleanup: {e}")
            return 0
    
    def _is_session_expired(self, session: Session) -> bool:
        """Check if a session has expired."""
        current_time = time.time()
        
        # Check idle timeout
        if (current_time - session.last_activity) > self._max_idle_time:
            return True
        
        # Check absolute expiration
        if current_time > session.expires_at:
            return True
        
        return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session information for debugging/monitoring."""
        session = self._sessions.get(session_id)
        if session:
            return {
                'session_id': session.session_id,
                'user_id': session.user_id,
                'username': session.username,
                'role': session.role,
                'login_time': datetime.fromtimestamp(session.login_time),
                'last_activity': datetime.fromtimestamp(session.last_activity),
                'expires_at': datetime.fromtimestamp(session.expires_at),
                'duration': session.duration,
                'idle_time': session.idle_time,
                'is_active': session.is_active,
                'is_expired': self._is_session_expired(session),
                'ip_address': session.ip_address,
                'user_agent': session.user_agent
            }
        return None
    
    def extend_session(self, session_id: str, extend_by: int = 3600) -> bool:
        """
        Extend session expiration time.
        
        Args:
            session_id: Session to extend
            extend_by: Seconds to extend by (default: 1 hour)
            
        Returns:
            True if session was extended, False otherwise
        """
        try:
            session = self._sessions.get(session_id)
            if session and session.is_active:
                session.expires_at += extend_by
                self._logger.info(f"Extended session {session_id} by {extend_by} seconds")
                return True
            return False
        except Exception as e:
            self._logger.error(f"Error extending session {session_id}: {e}")
            return False
    
    def get_session_stats(self) -> Dict:
        """Get session statistics."""
        try:
            active_sessions = self.get_active_sessions()
            
            stats = {
                'total_active_sessions': len(active_sessions),
                'sessions_by_role': {},
                'average_session_duration': 0,
                'logged_in_users': len(self.get_logged_in_users())
            }
            
            if active_sessions:
                # Group by role
                for session in active_sessions.values():
                    role = session.role
                    stats['sessions_by_role'][role] = stats['sessions_by_role'].get(role, 0) + 1
                
                # Calculate average duration
                total_duration = sum(session.duration for session in active_sessions.values())
                stats['average_session_duration'] = total_duration / len(active_sessions)
            
            return stats
            
        except Exception as e:
            self._logger.error(f"Error getting session stats: {e}")
            return {}


# Global session manager instance
session_manager = SessionManager()