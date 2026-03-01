#!/usr/bin/env python3
"""
Demo script for the Factory Floor System.
Demonstrates enhanced user security, RBAC, and integration with machine control.
"""

from user_security import auth_manager, Permission
from user_security.decorators import require_permission, require_role, PermissionContext


# Mock machine management to demonstrate integration
class MachineController:
    """Mock machine controller to demonstrate security integration."""
    
    def __init__(self):
        self.machines = {
            'M001': {'status': 'stopped', 'temperature': 25, 'speed': 0},
            'M002': {'status': 'running', 'temperature': 78, 'speed': 1200},
            'M003': {'status': 'maintenance', 'temperature': 0, 'speed': 0}
        }
    
    @require_permission(Permission.START_MACHINE)
    def start_machine(self, session_id: str, machine_id: str) -> bool:
        """Start a machine (requires permission)."""
        if machine_id in self.machines:
            self.machines[machine_id]['status'] = 'running'
            self.machines[machine_id]['speed'] = 1200
            print(f"Machine {machine_id} started")
            return True
        
        print(f"[FAILED] Machine {machine_id} not found")
        return False
    
    @require_permission(Permission.STOP_MACHINE)
    def stop_machine(self, session_id: str, machine_id: str) -> bool:
        """Stop a machine (requires permission)."""
        if machine_id in self.machines:
            self.machines[machine_id]['status'] = 'stopped'
            self.machines[machine_id]['speed'] = 0
            print(f"Machine {machine_id} stopped")
            return True
        
        print(f"[FAILED] Machine {machine_id} not found")
        return False
    
    @require_permission(Permission.VIEW_MACHINE_STATUS)
    def get_machine_status(self, session_id: str, machine_id: str = None) -> dict:
        """Get machine status (requires permission)."""
        if machine_id:
            return self.machines.get(machine_id, {})
        return self.machines
    
    @require_role("ADMIN", "SUPERVISOR")
    def set_maintenance_mode(self, session_id: str, machine_id: str) -> bool:
        """Set machine to maintenance mode (Admin/Supervisor only)."""
        if machine_id in self.machines:
            self.machines[machine_id]['status'] = 'maintenance'
            self.machines[machine_id]['speed'] = 0
            print(f"Machine {machine_id} set to maintenance mode")
            return True
        
        print(f"[FAILED] Machine {machine_id} not found")
        return False


def demo_role_based_access():
    """Demonstrate role-based access control."""
    print("\n=== Role-Based Access Control Demo ===")
    
    # Create machine controller
    controller = MachineController()
    
    # Test different user roles
    test_users = [
        ("admin", "admin123"),
        ("supervisor", "super123"),
        ("operator", "op123")
    ]
    
    for username, password in test_users:
        print(f"\n--- Testing {username.upper()} capabilities ---")
        
        # Authenticate user
        session_id = auth_manager.authenticate_user(username, password)
        
        if not session_id:
            print(f"[FAILED] Authentication failed for {username}")
            continue
        
        user = auth_manager.get_user_by_session(session_id)
        print(f"{username} authenticated as {user.get_role()}")
        
        # Test machine operations
        print(f"\n{username} trying to:")
        
        # View machine status (all roles should have this)
        status = controller.get_machine_status(session_id, 'M001')
        if status:
            print(f"  View machine status: {status}")
        
        # Start machine (Operator+ should have this)
        result = controller.start_machine(session_id, 'M001')
        if not result:
            print(f"  [FAILED] Start machine: Permission denied")
        
        # Set maintenance mode (Admin/Supervisor only)
        result = controller.set_maintenance_mode(session_id, 'M002')
        if not result:
            print(f"  [FAILED] Set maintenance mode: Permission denied")
        
        # Test user management (Admin only)
        if user.get_role() == "ADMIN":
            new_user = auth_manager.create_user(session_id, f"test_{username}", "test123", "OPERATOR")
            if new_user:
                print(f"  Created test user: {new_user.username}")
        else:
            # Try to create user (should fail for non-admin)
            new_user = auth_manager.create_user(session_id, f"test_{username}", "test123", "OPERATOR")
            if not new_user:
                print(f"  [FAILED] Create user: Permission denied")
        
        # Logout
        auth_manager.logout_user(username)
        print(f"{username} logged out")


def demo_permission_context():
    """Demonstrate permission context manager."""
    print("\n=== Permission Context Demo ===")
    
    # Authenticate admin
    admin_session = auth_manager.authenticate_user("admin", "admin123")
    
    print("Using PermissionContext for safe operations:")
    
    # Safe operation with context manager
    with PermissionContext(admin_session, Permission.CREATE_USER) as authorized:
        if authorized:
            print("  Admin is authorized to create users")
            # Would perform user creation here
        else:
            print("  [FAILED] Not authorized to create users")
    
    # Cleanup
    auth_manager.logout_user("admin")


def demo_session_management():
    """Demonstrate session management features."""
    print("\n=== Session Management Demo ===")
    
    # Show initial state
    stats = auth_manager.get_system_stats()
    print(f"Initial state - Active sessions: {stats['active_sessions']}")
    
    # Login multiple users
    sessions = []
    for username, password in [("admin", "admin123"), ("supervisor", "super123"), ("operator", "op123")]:
        session_id = auth_manager.authenticate_user(username, password)
        if session_id:
            sessions.append((username, session_id))
            print(f"{username} logged in")
    
    # Show active sessions
    active = auth_manager.get_active_sessions()
    print(f"\nActive sessions: {len(active)}")
    for session_info in active:
        print(f"  - {session_info['username']} ({session_info['role']}) - Duration: {session_info['duration']:.1f}s")
    
    # Logout all users
    for username, session_id in sessions:
        auth_manager.logout_user(username)
        print(f"{username} logged out")
    
    # Final state
    stats = auth_manager.get_system_stats()
    print(f"Final state - Active sessions: {stats['active_sessions']}")


def demo_permission_checking():
    """Demonstrate various permission checking methods."""
    print("\n=== Permission Checking Demo ===")
    
    # Login operator
    op_session = auth_manager.authenticate_user("operator", "op123")
    operator = auth_manager.get_user_by_session(op_session)
    
    print(f"Operator permissions:")
    
    # Check specific permissions
    permissions_to_check = [
        Permission.START_MACHINE,
        Permission.CREATE_USER,
        Permission.VIEW_LIVE_STATUS,
        Permission.UPDATE_SYSTEM_CONFIG
    ]
    
    for perm in permissions_to_check:
        has_perm = operator.check_permission(perm)
        status = "[OK]" if has_perm else "[NO]"
        print(f"  {status} {perm.value}")
    
    # Show all operator permissions
    all_perms = operator.get_permissions()
    print(f"\nAll operator permissions ({len(all_perms)}):")
    for perm in sorted(all_perms, key=lambda x: x.value):
        print(f"  • {perm.value}")
    
    # Cleanup
    auth_manager.logout_user("operator")


def interactive_demo():
    """Interactive demo for user testing."""
    print("\n=== Interactive Demo ===")
    print("This demo lets you login and test different operations")
    
    controller = MachineController()
    current_session = None
    current_user = None
    
    while True:
        if not current_session:
            # Login phase
            print("\nLogin options:")
            print("1. admin / admin123")
            print("2. supervisor / super123") 
            print("3. operator / op123")
            print("4. Exit")
            
            choice = input("Choose login (1-4): ").strip()
            
            if choice == "4":
                break
                
            credentials = {
                "1": ("admin", "admin123"),
                "2": ("supervisor", "super123"),
                "3": ("operator", "op123")
            }
            
            if choice in credentials:
                username, password = credentials[choice]
                current_session = auth_manager.authenticate_user(username, password)
                
                if current_session:
                    current_user = auth_manager.get_user_by_session(current_session)
                    print(f"\nLogged in as {current_user.username} ({current_user.get_role()})")
                else:
                    print("[FAILED] Login failed")
            else:
                print("Invalid choice")
                
        else:
            # Action phase
            print(f"\nLogged in as: {current_user.username} ({current_user.get_role()})")
            print("\nActions:")
            print("1. View machine status")
            print("2. Start machine M001")
            print("3. Stop machine M001")
            print("4. Set machine M002 to maintenance (Admin/Supervisor only)")
            print("5. Create user (Admin only)")
            print("6. View my permissions")
            print("7. Logout")
            
            action = input("Choose action (1-7): ").strip()
            
            if action == "1":
                status = controller.get_machine_status(current_session)
                if status:
                    print("\nMachine Status:")
                    for machine_id, info in status.items():
                        print(f"  {machine_id}: {info}")
                        
            elif action == "2":
                controller.start_machine(current_session, "M001")
                
            elif action == "3":
                controller.stop_machine(current_session, "M001")
                
            elif action == "4":
                controller.set_maintenance_mode(current_session, "M002")
                
            elif action == "5":
                username = input("New username: ")
                password = input("New password: ")
                role = input("Role (ADMIN/SUPERVISOR/OPERATOR): ").upper()
                
                auth_manager.create_user(current_session, username, password, role)
                
            elif action == "6":
                perms = current_user.get_permissions()
                print(f"\nYour permissions ({len(perms)}):")
                for perm in sorted(perms, key=lambda x: x.value):
                    print(f"  • {perm.value}")
                    
            elif action == "7":
                auth_manager.logout_user(current_user.username)
                print(f"{current_user.username} logged out")
                current_session = None
                current_user = None
                
            else:
                print("Invalid action")


def main():
    """Main demo function."""
    print("Factory Floor System - Enhanced User Security Demo")
    print("=" * 60)
    
    # Initialize system
    from user_security import initialize_security_system
    initialize_security_system()
    
    print("\nRunning comprehensive security demos...")
    
    # Run all demos
    demo_role_based_access()
    demo_permission_context()
    demo_session_management()
    demo_permission_checking()
    
    # Interactive portion
    print("\n" + "=" * 60)
    interactive_demo()
    
    print("\nDemo completed!")


if __name__ == "__main__":
    main()
