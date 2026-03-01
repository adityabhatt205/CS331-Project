"""
Authorization decorators for the Factory Floor System.
Provides easy-to-use decorators for protecting methods and operations.
"""

from functools import wraps
from typing import Callable, Union, Any
from .permissions import Permission
from .auth_manager import auth_manager


def require_permission(permission: Union[str, Permission]):
    """
    Decorator to require specific permission for method execution.
    
    Args:
        permission: Required permission (string or Permission enum)
        
    Usage:
        @require_permission(Permission.START_MACHINE)
        def start_machine(session_id, machine_id):
            # Method implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Extract session_id - assume it's the first argument or in kwargs
            session_id = None
            if args and isinstance(args[0], str):
                session_id = args[0]
            elif 'session_id' in kwargs:
                session_id = kwargs['session_id']
            
            if not session_id:
                print(f"Authorization failed: No session_id provided for {func.__name__}")
                return None
            
            # Check permission
            if not auth_manager.check_permission(session_id, permission):
                user = auth_manager.get_user_by_session(session_id)
                username = user.username if user else "Unknown"
                print(f"Authorization failed: User {username} lacks permission {permission} for {func.__name__}")
                return None
            
            # Execute function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(*allowed_roles: str):
    """
    Decorator to require specific roles for method execution.
    
    Args:
        allowed_roles: List of allowed roles
        
    Usage:
        @require_role("ADMIN", "SUPERVISOR")
        def configure_system(session_id, setting):
            # Method implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Extract session_id
            session_id = None
            if args and isinstance(args[0], str):
                session_id = args[0]
            elif 'session_id' in kwargs:
                session_id = kwargs['session_id']
            
            if not session_id:
                print(f"Authorization failed: No session_id provided for {func.__name__}")
                return None
            
            # Check role
            user = auth_manager.get_user_by_session(session_id)
            if not user:
                print(f"Authorization failed: Invalid session for {func.__name__}")
                return None
            
            if user.get_role() not in allowed_roles:
                print(f"Authorization failed: User {user.username} role {user.get_role()} not in {allowed_roles} for {func.__name__}")
                return None
            
            # Execute function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_authentication():
    """
    Decorator to require authentication for method execution.
    
    Usage:
        @require_authentication()
        def view_data(session_id):
            # Method implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Extract session_id
            session_id = None
            if args and isinstance(args[0], str):
                session_id = args[0]
            elif 'session_id' in kwargs:
                session_id = kwargs['session_id']
            
            if not session_id:
                print(f"Authentication failed: No session_id provided for {func.__name__}")
                return None
            
            # Check authentication
            user = auth_manager.get_user_by_session(session_id)
            if not user or not user.is_authenticated:
                print(f"Authentication failed: Invalid or expired session for {func.__name__}")
                return None
            
            # Execute function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def admin_only():
    """
    Decorator to restrict access to admin users only.
    
    Usage:
        @admin_only()
        def delete_all_data(session_id):
            # Method implementation
            pass
    """
    return require_role("ADMIN")


def supervisor_or_admin():
    """
    Decorator to restrict access to supervisor and admin users only.
    
    Usage:
        @supervisor_or_admin()
        def approve_action(session_id, action_id):
            # Method implementation
            pass
    """
    return require_role("ADMIN", "SUPERVISOR")


def authenticated_user():
    """
    Alias for require_authentication decorator.
    """
    return require_authentication()


class PermissionContext:
    """
    Context manager for checking permissions within a block of code.
    
    Usage:
        with PermissionContext(session_id, Permission.START_MACHINE) as authorized:
            if authorized:
                # Perform authorized actions
                pass
    """
    
    def __init__(self, session_id: str, permission: Union[str, Permission]):
        self.session_id = session_id
        self.permission = permission
        self.authorized = False
    
    def __enter__(self):
        self.authorized = auth_manager.check_permission(self.session_id, self.permission)
        return self.authorized
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def check_user_permission(session_id: str, permission: Union[str, Permission]) -> bool:
    """
    Convenience function to check user permission.
    
    Args:
        session_id: User session ID
        permission: Permission to check
        
    Returns:
        True if user has permission, False otherwise
    """
    return auth_manager.check_permission(session_id, permission)


def get_current_user(session_id: str):
    """
    Convenience function to get current user from session.
    
    Args:
        session_id: User session ID
        
    Returns:
        User object if valid session, None otherwise
    """
    return auth_manager.get_user_by_session(session_id)