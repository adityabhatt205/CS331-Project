#!/usr/bin/env python3
"""
Main entry point for the Factory Floor System.
Demonstrates enhanced user security with RBAC.
"""

from user_security import auth_manager, Permission, initialize_security_system, demo_authentication_flow


def main():
    """Main application entry point."""
    print("Factory Floor Visualization and Control System")
    print("=" * 50)
    
    # Initialize security system
    initialize_security_system()
    
    # Demo authentication flow
    demo_authentication_flow()
    
    # Interactive login demo
    print("\n=== Interactive Login Demo ===")
    
    while True:
        print("\nAvailable users:")
        print("1. admin (password: admin123) - Full access")
        print("2. supervisor (password: super123) - Monitoring & approval")
        print("3. operator (password: op123) - Machine control")
        print("4. Exit")
        
        choice = input("\nSelect user to login as (1-4): ").strip()
        
        if choice == "4":
            break
        
        credentials = {
            "1": ("admin", "admin123"),
            "2": ("supervisor", "super123"),
            "3": ("operator", "op123")
        }
        
        if choice in credentials:
            username, password = credentials[choice]
            
            # Authenticate user
            session_id = auth_manager.authenticate_user(username, password)
            
            if session_id:
                user = auth_manager.get_user_by_session(session_id)
                print(f"\n✓ Successfully logged in as {user.username} ({user.get_role()})")
                
                # Show available actions based on role
                show_user_capabilities(user, session_id)
                
                # Logout
                auth_manager.logout_user(username)
                print(f"✓ {username} logged out")
            else:
                print("✗ Authentication failed")
        else:
            print("Invalid choice")
    
    print("\nThank you for using Factory Floor System!")


def show_user_capabilities(user, session_id):
    """Show what the current user can do based on their role."""
    print(f"\n--- {user.get_role()} Capabilities ---")
    
    # Common capabilities
    if user.check_permission(Permission.VIEW_LIVE_STATUS):
        print("✓ View live factory status")
    
    if user.check_permission(Permission.VIEW_MACHINE_STATUS):
        print("✓ View machine status")
    
    if user.check_permission(Permission.VIEW_ALERTS):
        print("✓ View system alerts")
    
    # Machine control
    if user.check_permission(Permission.START_MACHINE):
        print("✓ Start/stop machines")
    
    if user.check_permission(Permission.CONTROL_CONVEYOR):
        print("✓ Control conveyor belts")
    
    if user.check_permission(Permission.EMERGENCY_STOP):
        print("✓ Emergency stop")
    
    # Automation
    if user.check_permission(Permission.APPROVE_AUTOMATION):
        print("✓ Approve automation rules")
    
    if user.check_permission(Permission.CREATE_AUTOMATION_RULE):
        print("✓ Create automation rules")
    
    # Administration
    if user.check_permission(Permission.CREATE_USER):
        print("✓ User management (create/delete users)")
    
    if user.check_permission(Permission.UPDATE_SYSTEM_CONFIG):
        print("✓ System configuration")
    
    # Demonstrate specific role functionality
    print(f"\n--- {user.get_role()} Specific Actions ---")
    
    if user.get_role() == "ADMIN":
        user.manageUsers()
        user.configureAutomationRules()
        
    elif user.get_role() == "SUPERVISOR":
        user.approveAutomation()
        user.monitorOperations()
        
    elif user.get_role() == "OPERATOR":
        user.controlMachines()
        user.viewLiveStatus()


if __name__ == "__main__":
    main()
