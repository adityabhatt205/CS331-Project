"""
User Security Module for Factory Floor System.

This module provides comprehensive Role-Based Access Control (RBAC) functionality
including user authentication, authorization, session management, and security decorators.

Main Components:
- User classes: Admin, Supervisor, Operator
- Permission system: Comprehensive permission definitions
- Authentication Manager: Centralized user and session management  
- Session Manager: Session tracking and timeout handling
- Security Decorators: Easy authorization enforcement

Usage:
    from user_security import auth_manager, Permission
    from user_security.decorators import require_permission
    
    # Authenticate user
    session_id = auth_manager.authenticate_user("username", "password")
    
    # Check permissions
    if auth_manager.check_permission(session_id, Permission.START_MACHINE):
        # Perform authorized action
        pass
"""

from .user import User
from .user_admin import Admin
from .user_supervisor import Supervisor
from .user_operator import Operator
from .permissions import Permission, Role, get_role_permissions, has_permission
from .session_manager import SessionManager, session_manager
from .auth_manager import AuthenticationManager, auth_manager
from .database import db
from .security import password_security, rate_limiter
from .decorators import (
    require_permission,
    require_role,
    require_authentication,
    admin_only,
    supervisor_or_admin,
    authenticated_user,
    PermissionContext,
    check_user_permission,
    get_current_user
)

__all__ = [
    # User classes
    'User',
    'Admin', 
    'Supervisor',
    'Operator',
    
    # Permission system
    'Permission',
    'Role',
    'get_role_permissions',
    'has_permission',
    
    # Session management
    'SessionManager',
    'session_manager',
    
    # Database layer
    'db',
    
    # Security utilities
    'password_security',
    'rate_limiter',
    
    # Authentication management
    'AuthenticationManager',
    'auth_manager',
    
    # Decorators
    'require_permission',
    'require_role', 
    'require_authentication',
    'admin_only',
    'supervisor_or_admin',
    'authenticated_user',
    'PermissionContext',
    'check_user_permission',
    'get_current_user'
]


def get_version():
    """Get module version."""
    return "1.0.0"


def initialize_security_system():
    """
    Initialize the security system with default configuration.
    This function can be called at application startup.
    """
    print("Factory Floor Security System initialized")
    print(f"Version: {get_version()}")
    
    # Display system stats
    stats = auth_manager.get_system_stats()
    print(f"Total users: {stats['total_users']}")
    print(f"Active sessions: {stats['active_sessions']}")
    print(f"Role distribution: {stats['role_distribution']}")
    
    return True


def demo_authentication_flow():
    """
    Demonstrate basic authentication flow.
    This can be used for testing or demonstration purposes.
    """
    print("\n=== User Security Demo ===")
    
    # Authenticate admin
    admin_session = auth_manager.authenticate_user("admin", "admin123")
    if admin_session:
        print("Admin authenticated successfully")
        
        # Check admin permissions
        if auth_manager.check_permission(admin_session, Permission.CREATE_USER):
            print("Admin has user creation permissions")
            
        # Create a new operator
        new_user = auth_manager.create_user(
            admin_session, "testop", "test123", "OPERATOR"
        )
        if new_user:
            print("New operator created successfully")
        
        # List all users
        users = auth_manager.list_users(admin_session)
        print(f"Total users in system: {len(users)}")
        
        # Logout admin
        auth_manager.logout_user("admin")
        print("Admin logged out")
    
    # Test operator authentication
    op_session = auth_manager.authenticate_user("testop", "test123")
    if op_session:
        print("Operator authenticated successfully")
        
        # Test operator permissions
        can_start_machine = auth_manager.check_permission(op_session, Permission.START_MACHINE)
        can_create_user = auth_manager.check_permission(op_session, Permission.CREATE_USER)
        
        print(f"Operator can start machines: {can_start_machine}")
        print(f"Operator can create users: {can_create_user}")
        
        # Logout operator
        auth_manager.logout_user("testop")
        print("Operator logged out")
    
    print("=== Demo completed ===\n")