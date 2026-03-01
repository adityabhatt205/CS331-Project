"""
Production-ready Authentication Manager for the Factory Floor System.
Provides centralized user authentication, authorization, and user management with database persistence.
"""

import logging
from typing import Dict, List, Optional, Union, Set
from .user import User
from .user_admin import Admin
from .user_supervisor import Supervisor
from .user_operator import Operator
from .permissions import Permission, Role
from .session_manager import session_manager
from .database import db
from .security import password_security, rate_limiter


class AuthenticationManager:
    """Production-ready authentication and authorization manager with database persistence."""
    
    def __init__(self):
        """Initialize authentication manager."""
        self._logger = logging.getLogger(__name__)
        self._init_default_users()
    
    def _init_default_users(self):
        """Initialize system with default users if they don't exist."""
        try:
            # Check if admin user exists
            if not db.get_user_by_username("admin"):
                admin_user = Admin(user_id=1, username="admin", password="admin123")
                if admin_user.save_to_database():
                    self._logger.info("Created default admin user")
            
            # Check if supervisor user exists
            if not db.get_user_by_username("supervisor"):
                supervisor_user = Supervisor(user_id=2, username="supervisor", password="super123")
                if supervisor_user.save_to_database():
                    self._logger.info("Created default supervisor user")
            
            # Check if operator user exists
            if not db.get_user_by_username("operator"):
                operator_user = Operator(user_id=3, username="operator", password="op123")
                if operator_user.save_to_database():
                    self._logger.info("Created default operator user")
                    
        except Exception as e:
            self._logger.error(f"Failed to initialize default users: {e}")
    
    def authenticate_user(self, username: str, password: str, 
                         ip_address: str = None) -> Optional[str]:
        """
        Authenticate a user and create session with security features.
        
        Args:
            username: Username
            password: Password
            ip_address: Client IP address
            
        Returns:
            Session ID if authentication successful, None otherwise
        """
        try:
            # Rate limiting check
            identifier = ip_address or username
            if rate_limiter.is_rate_limited(identifier):
                self._logger.warning(f"Rate limit exceeded for {identifier}")
                return None
            
            # Get user from database
            user_data = db.get_user_by_username(username)
            if not user_data:
                self._logger.warning(f"User {username} not found")
                rate_limiter.record_attempt(identifier, False)
                return None
            
            # Check if user account is locked
            if user_data.get('locked_until'):
                from datetime import datetime
                locked_until = datetime.fromisoformat(user_data['locked_until'])
                if datetime.now() < locked_until:
                    self._logger.warning(f"User account {username} is locked until {locked_until}")
                    return None
            
            # Create user instance from database data
            user = User.from_database(user_data)
            
            # Attempt authentication
            if user.authenticate(password, ip_address):
                rate_limiter.record_attempt(identifier, True)
                self._logger.info(f"User {username} authenticated successfully from {ip_address}")
                return user.current_session_id
            else:
                rate_limiter.record_attempt(identifier, False)
                self._logger.warning(f"Authentication failed for {username} from {ip_address}")
                return None
                
        except Exception as e:
            self._logger.error(f"Authentication error for {username}: {e}")
            return None
    
    def logout_user(self, username: str) -> bool:
        """
        Logout a user.
        
        Args:
            username: Username to logout
            
        Returns:
            True if logout successful, False otherwise
        """
        try:
            user_data = db.get_user_by_username(username)
            if not user_data:
                return False
            
            # Invalidate all sessions for the user
            db.invalidate_user_sessions(user_data['user_id'])
            
            # Also invalidate from session manager cache
            session_manager.remove_user_session(user_data['user_id'])
            
            self._logger.info(f"User {username} logged out")
            return True
            
        except Exception as e:
            self._logger.error(f"Logout error for {username}: {e}")
            return False
    
    def get_user_by_session(self, session_id: str) -> Optional[User]:
        """
        Get user by session ID with database lookup.
        
        Args:
            session_id: Session ID
            
        Returns:
            User object if session valid, None otherwise
        """
        try:
            session = session_manager.get_session(session_id)
            if not session:
                return None
            
            # Get fresh user data from database
            user_data = db.get_user_by_id(session.user_id)
            if not user_data:
                # User was deleted, invalidate session
                session_manager.invalidate_session(session_id)
                return None
            
            # Create user instance
            user = User.from_database(user_data)
            
            # Restore authentication state
            user._is_authenticated = True
            user._current_session = session_id
            
            return user
            
        except Exception as e:
            self._logger.error(f"Error getting user by session {session_id}: {e}")
            return None
    
    def check_permission(self, session_id: str, permission: Union[str, Permission]) -> bool:
        """
        Check if user has permission for an action.
        
        Args:
            session_id: User session ID
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        try:
            user = self.get_user_by_session(session_id)
            if user and user.is_authenticated:
                return user.hasPermission(permission)
            return False
        except Exception as e:
            self._logger.error(f"Permission check error for session {session_id}: {e}")
            return False
    
    def get_system_stats(self) -> Dict:
        """
        Get comprehensive system statistics.
        
        Returns:
            Dictionary with system statistics
        """
        try:
            # Get database stats
            db_stats = db.get_database_stats()
            
            # Get session stats
            session_stats = session_manager.get_session_stats()
            
            # Get role distribution
            users = db.list_users()
            role_counts = {}
            for user in users:
                role = user['role']
                role_counts[role] = role_counts.get(role, 0) + 1
            
            return {
                'total_users': db_stats.get('total_users', 0),
                'active_sessions': db_stats.get('active_sessions', 0),
                'role_distribution': role_counts,
                'logged_in_users': len(session_manager.get_logged_in_users()),
                'database_size_mb': db_stats.get('database_size_mb', 0),
                'total_audit_logs': db_stats.get('total_audit_logs', 0),
                'session_stats': session_stats
            }
            
        except Exception as e:
            self._logger.error(f"Error getting system stats: {e}")
            return {}


# Global authentication manager instance
auth_manager = AuthenticationManager()