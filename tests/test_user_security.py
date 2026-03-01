#!/usr/bin/env python3
"""
Test suite for the User Security module.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from user_security import auth_manager, Permission, Role


def test_authentication():
    """Test user authentication functionality."""
    print("Testing authentication...")
    
    # Test valid login
    session_id = auth_manager.authenticate_user("admin", "admin123")
    assert session_id is not None, "Admin authentication should succeed"
    
    # Test invalid login
    invalid_session = auth_manager.authenticate_user("admin", "wrong_password")
    assert invalid_session is None, "Invalid password should fail"
    
    # Test nonexistent user
    nonexistent_session = auth_manager.authenticate_user("nonexistent", "password")
    assert nonexistent_session is None, "Nonexistent user should fail"
    
    print("Authentication tests passed")


def test_permissions():
    """Test permission system."""
    print("Testing permissions...")
    
    # Login different user types
    admin_session = auth_manager.authenticate_user("admin", "admin123")
    supervisor_session = auth_manager.authenticate_user("supervisor", "super123")
    operator_session = auth_manager.authenticate_user("operator", "op123")
    
    # Test admin permissions
    assert auth_manager.check_permission(admin_session, Permission.CREATE_USER), "Admin should be able to create users"
    assert auth_manager.check_permission(admin_session, Permission.START_MACHINE), "Admin should be able to start machines"
    
    # Test supervisor permissions
    assert auth_manager.check_permission(supervisor_session, Permission.APPROVE_AUTOMATION), "Supervisor should approve automation"
    assert not auth_manager.check_permission(supervisor_session, Permission.CREATE_USER), "Supervisor should not create users"
    
    # Test operator permissions
    assert auth_manager.check_permission(operator_session, Permission.START_MACHINE), "Operator should start machines"
    assert not auth_manager.check_permission(operator_session, Permission.CREATE_USER), "Operator should not create users"
    assert not auth_manager.check_permission(operator_session, Permission.APPROVE_AUTOMATION), "Operator should not approve automation"
    
    print("Permission tests passed")


def test_user_management():
    """Test user management functionality."""
    print("Testing user management...")
    
    # Login as admin
    admin_session = auth_manager.authenticate_user("admin", "admin123")
    
    # Create new user
    new_user = auth_manager.create_user(admin_session, "testuser", "test123", "OPERATOR")
    assert new_user is not None, "User creation should succeed"
    
    # Try to create duplicate user
    duplicate_user = auth_manager.create_user(admin_session, "testuser", "test123", "OPERATOR")
    assert duplicate_user is None, "Duplicate user creation should fail"
    
    # List users
    users = auth_manager.list_users(admin_session)
    assert len(users) >= 4, "Should have at least 4 users (3 default + 1 created)"
    
    # Delete user
    deleted = auth_manager.delete_user(admin_session, "testuser")
    assert deleted, "User deletion should succeed"
    
    # Try to delete nonexistent user
    not_deleted = auth_manager.delete_user(admin_session, "nonexistent")
    assert not not_deleted, "Deleting nonexistent user should fail"
    
    print("User management tests passed")


def test_session_management():
    """Test session management."""
    print("Testing session management...")
    
    # Login user
    session_id = auth_manager.authenticate_user("operator", "op123")
    assert session_id is not None, "Login should succeed"
    
    # Check session exists
    user = auth_manager.get_user_by_session(session_id)
    assert user is not None, "Session should be valid"
    assert user.username == "operator", "Session should belong to correct user"
    
    # Logout user
    logged_out = auth_manager.logout_user("operator")
    assert logged_out, "Logout should succeed"
    
    # Check session is invalid
    user_after_logout = auth_manager.get_user_by_session(session_id)
    assert user_after_logout is None or not user_after_logout.is_authenticated, "Session should be invalid after logout"
    
    print("Session management tests passed")


def test_role_hierarchy():
    """Test that role hierarchy works correctly."""
    print("Testing role hierarchy...")
    
    # Admin should have all permissions
    admin_session = auth_manager.authenticate_user("admin", "admin123")
    admin_user = auth_manager.get_user_by_session(admin_session)
    admin_perms = admin_user.get_permissions()
    
    # Supervisor should have fewer permissions than admin
    supervisor_session = auth_manager.authenticate_user("supervisor", "super123")
    supervisor_user = auth_manager.get_user_by_session(supervisor_session)
    supervisor_perms = supervisor_user.get_permissions()
    
    # Operator should have fewer permissions than supervisor
    operator_session = auth_manager.authenticate_user("operator", "op123")
    operator_user = auth_manager.get_user_by_session(operator_session)
    operator_perms = operator_user.get_permissions()
    
    assert len(admin_perms) > len(supervisor_perms), "Admin should have more permissions than supervisor"
    assert len(supervisor_perms) > len(operator_perms), "Supervisor should have more permissions than operator"
    
    # Operator permissions should be subset of supervisor permissions
    assert operator_perms.issubset(supervisor_perms), "Operator permissions should be subset of supervisor"
    
    print("Role hierarchy tests passed")


def run_all_tests():
    """Run all tests."""
    print("Running User Security Module Tests")
    print("=" * 40)
    
    try:
        test_authentication()
        test_permissions()
        test_user_management()
        test_session_management()
        test_role_hierarchy()
        
        print("\n" + "=" * 40)
        print("[SUCCESS] All tests passed!")
        return True
        
    except AssertionError as e:
        print(f"\n[FAILED] Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n[FAILED] Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)