from abc import ABC, abstractmethod
from typing import Optional, Set
import logging

from .permissions import Permission, Role, get_role_permissions, has_permission
from .session_manager import session_manager
from .database import db
from .security import password_security


class User(ABC):
    """Abstract base class for all users in the system with database persistence."""
    
    def __init__(self, user_id: int, username: str, password: str = None, 
                 password_hash: str = None, salt: str = None):
        """
        Initialize user. Can be created with either plain password or existing hash/salt.
        
        Args:
            user_id: Unique user ID
            username: Username
            password: Plain text password (for new users)
            password_hash: Existing password hash (for loading from database)
            salt: Existing salt (for loading from database)
        """
        self._user_id = user_id
        self._username = username
        self._role = None
        self._is_authenticated = False
        self._current_session = None
        self._logger = logging.getLogger(f"{__name__}.{username}")
        
        # Handle password/hash initialization
        if password and not password_hash:
            # New user with plain password
            self._password_hash, self._salt = password_security.hash_password(password)
        elif password_hash and salt:
            # Existing user loaded from database
            self._password_hash = password_hash
            self._salt = salt
        else:
            raise ValueError("Must provide either password or both password_hash and salt")

    @property
    def user_id(self) -> int:
        """Get user ID."""
        return self._user_id
    
    @property
    def username(self) -> str:
        """Get username."""
        return self._username
    
    @property 
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return self._is_authenticated and self._current_session is not None
    
    @property
    def current_session_id(self) -> Optional[str]:
        """Get current session ID if authenticated."""
        return self._current_session

    def authenticate(self, password: str, ip_address: str = None) -> bool:
        """
        Authenticate user with password.
        
        Args:
            password: Plain text password
            ip_address: Client IP address for auditing
            
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Verify password
            if password_security.verify_password(password, self._password_hash, self._salt):
                # Create session
                self._current_session = session_manager.create_session(
                    user_id=self._user_id,
                    username=self._username,
                    role=self.get_role(),
                    ip_address=ip_address
                )
                self._is_authenticated = True
                
                # Update database login info
                db.update_user_login(self._user_id, success=True)
                
                # Log successful authentication
                db.log_audit_event(
                    user_id=self._user_id,
                    username=self._username,
                    action="LOGIN",
                    details="User authenticated successfully",
                    ip_address=ip_address,
                    success=True
                )
                
                self._logger.info(f"User {self._username} authenticated successfully")
                return True
            else:
                # Update failed login attempts
                db.update_user_login(self._user_id, success=False)
                
                # Log failed authentication
                db.log_audit_event(
                    user_id=self._user_id,
                    username=self._username,
                    action="LOGIN_FAILED",
                    details="Invalid password",
                    ip_address=ip_address,
                    success=False
                )
                
                self._logger.warning(f"Authentication failed for {self._username}")
                return False
                
        except Exception as e:
            self._logger.error(f"Authentication error for {self._username}: {e}")
            return False

    def login(self, username: str, password: str) -> bool:
        """
        Legacy login method for backward compatibility.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            True if login successful, False otherwise
        """
        if self._username == username:
            return self.authenticate(password)
        return False

    def logout(self) -> None:
        """Logout user and invalidate session."""
        try:
            if self._current_session:
                session_manager.invalidate_session(self._current_session)
                
                # Log logout
                db.log_audit_event(
                    user_id=self._user_id,
                    username=self._username,
                    action="LOGOUT",
                    details="User logged out",
                    success=True
                )
                
                self._current_session = None
            
            self._is_authenticated = False
            self._logger.info(f"User {self._username} logged out")
            
        except Exception as e:
            self._logger.error(f"Logout error for {self._username}: {e}")

    def change_password(self, old_password: str, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            old_password: Current password
            new_password: New password
            
        Returns:
            True if password changed successfully
        """
        try:
            # Verify old password
            if not password_security.verify_password(old_password, self._password_hash, self._salt):
                self._logger.warning(f"Password change failed for {self._username} - incorrect old password")
                return False
            
            # Check new password strength
            is_strong, issues = password_security.is_password_strong(new_password)
            if not is_strong:
                self._logger.warning(f"Password change failed for {self._username} - weak password: {issues}")
                return False
            
            # Hash new password
            new_hash, new_salt = password_security.hash_password(new_password)
            
            # Update in database
            if db.update_user_password(self._user_id, new_hash, new_salt):
                self._password_hash = new_hash
                self._salt = new_salt
                
                # Log password change
                db.log_audit_event(
                    user_id=self._user_id,
                    username=self._username,
                    action="PASSWORD_CHANGE",
                    details="Password changed successfully",
                    success=True
                )
                
                self._logger.info(f"Password changed successfully for {self._username}")
                return True
            else:
                self._logger.error(f"Failed to update password in database for {self._username}")
                return False
                
        except Exception as e:
            self._logger.error(f"Password change error for {self._username}: {e}")
            return False

    def hasPermission(self, action: str) -> bool:
        """
        Check if user has permission for an action.
        
        Args:
            action: Action name (string) or Permission enum
            
        Returns:
            True if user has permission, False otherwise
        """
        if not self.is_authenticated:
            return False
        
        # Update session activity
        if self._current_session:
            session = session_manager.get_session(self._current_session)
            if not session:
                # Session expired or invalid
                self._is_authenticated = False
                self._current_session = None
                return False
        
        try:
            # Convert string to Permission enum if necessary
            if isinstance(action, str):
                permission = Permission(action)
            else:
                permission = action
                
            role = Role(self.get_role())
            return has_permission(role, permission)
            
        except ValueError:
            # Invalid permission name
            self._logger.warning(f"Invalid permission: {action}")
            return False
    
    def get_permissions(self) -> Set[Permission]:
        """Get all permissions for this user's role."""
        if not self.is_authenticated:
            return set()
        
        try:
            role = Role(self.get_role())
            return get_role_permissions(role)
        except ValueError:
            return set()
    
    def check_permission(self, permission: Permission) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        return self.hasPermission(permission)

    def to_dict(self) -> dict:
        """Convert user to dictionary representation."""
        return {
            'user_id': self._user_id,
            'username': self._username,
            'role': self.get_role(),
            'is_authenticated': self._is_authenticated,
            'current_session': self._current_session
        }
    
    @classmethod
    def from_database(cls, user_data: dict):
        """
        Create user instance from database data.
        
        Args:
            user_data: Dictionary containing user data from database
            
        Returns:
            User instance of appropriate type
        """
        from .user_admin import Admin
        from .user_supervisor import Supervisor
        from .user_operator import Operator
        
        role = user_data['role']
        
        if role == "ADMIN":
            user_class = Admin
        elif role == "SUPERVISOR":
            user_class = Supervisor
        elif role == "OPERATOR":
            user_class = Operator
        else:
            raise ValueError(f"Unknown role: {role}")
        
        return user_class(
            user_id=user_data['user_id'],
            username=user_data['username'],
            password_hash=user_data['password_hash'],
            salt=user_data['salt']
        )

    def save_to_database(self) -> bool:
        """
        Save user to database.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            user_data = {
                'user_id': self._user_id,
                'username': self._username,
                'password_hash': self._password_hash,
                'salt': self._salt,
                'role': self.get_role()
            }
            
            return db.create_user(user_data)
            
        except Exception as e:
            self._logger.error(f"Failed to save user {self._username} to database: {e}")
            return False

    @abstractmethod
    def get_role(self) -> str:
        """Get user role. Must be implemented by subclasses."""
        pass
