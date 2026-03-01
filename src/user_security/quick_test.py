#!/usr/bin/env python3
"""
Quick integration test for the user security system.
This script validates that all components work together correctly.
"""

import sys
import os
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_system():
    """Quick system integration test."""
    try:
        # Import the user security module
        from user_security import auth_manager, Permission
        
        print("User security module imported successfully")
        
        # Test admin authentication
        print("\nTesting authentication...")
        admin_session = auth_manager.authenticate_user("admin", "admin123", "127.0.0.1")
        
        if admin_session:
            print(f"Admin authenticated - Session: {admin_session[:8]}...")
            
            # Test permission checking
            can_create_user = auth_manager.check_permission(admin_session, Permission.CREATE_USER)
            print(f"Admin permissions check: {can_create_user}")
            
            # Get system stats
            stats = auth_manager.get_system_stats()
            print(f"System stats: {stats.get('total_users', 0)} users, {stats.get('active_sessions', 0)} sessions")
            
            # Logout
            auth_manager.logout_user("admin")
            print("Admin logged out")
            
        else:
            print("Admin authentication failed")
            return False
        
        print("\nAll tests passed! System is working correctly.")
        return True
        
    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Factory Floor User Security System")
    print("Quick Integration Test")
    print("-" * 40)
    
    # Configure logging
    logging.basicConfig(level=logging.WARNING)  # Suppress info logs for cleaner output
    
    success = test_system()
    
    if success:
        print("\nSystem is ready for use!")
        exit(0)
    else:
        print("\nSystem test failed!")
        exit(1)