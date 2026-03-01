from typing import List, Dict, Optional
from .user import User
from .permissions import Permission
from .database import db


class Admin(User):
    """Administrator user with full system access and database persistence."""
    
    def __init__(self, user_id, username, password=None, password_hash=None, salt=None):
        super().__init__(user_id, username, password, password_hash, salt)
        self._role = "ADMIN"

    def get_role(self) -> str:
        return self._role
    
    def create_user(self, username: str, password: str, role: str) -> bool:
        """Create a new user (Admin only)."""
        if not self.check_permission(Permission.CREATE_USER):
            self._logger.warning(f"Permission denied: {self.username} cannot create users")
            return False
        
        try:
            # Check if username already exists
            if db.get_user_by_username(username):
                self._logger.warning(f"Username {username} already exists")
                return False
            
            # Generate new user ID
            user_id = self._generate_user_id()
            
            # Create user based on role
            if role.upper() == "ADMIN":
                new_user = Admin(user_id, username, password)
            elif role.upper() == "SUPERVISOR":
                from .user_supervisor import Supervisor
                new_user = Supervisor(user_id, username, password)
            elif role.upper() == "OPERATOR":
                from .user_operator import Operator
                new_user = Operator(user_id, username, password)
            else:
                self._logger.error(f"Invalid role: {role}")
                return False
            
            # Save to database
            if new_user.save_to_database():
                db.log_audit_event(
                    user_id=self.user_id,
                    username=self.username,
                    action="USER_CREATED",
                    resource=f"user:{username}",
                    details=f"Created user {username} with role {role}",
                    success=True
                )
                
                self._logger.info(f"User {username} created successfully with role {role}")
                return True
            else:
                self._logger.error(f"Failed to save user {username} to database")
                return False
                
        except Exception as e:
            self._logger.error(f"Error creating user {username}: {e}")
            return False
    
    def _generate_user_id(self) -> int:
        """Generate a new user ID."""
        # Get highest user ID from database and increment
        users = db.list_users()
        if users:
            max_id = max(user['user_id'] for user in users)
            return max_id + 1
        return 1
    
    def delete_user(self, username: str) -> bool:
        """Delete a user (Admin only)."""
        if not self.check_permission(Permission.DELETE_USER):
            self._logger.warning(f"Permission denied: {self.username} cannot delete users")
            return False
        
        try:
            user_data = db.get_user_by_username(username)
            if not user_data:
                self._logger.warning(f"User {username} not found")
                return False
            
            user_id = user_data['user_id']
            
            # Don't allow deletion of the last admin
            if user_data['role'] == "ADMIN":
                admin_count = len([u for u in db.list_users() if u['role'] == "ADMIN"])
                if admin_count <= 1:
                    self._logger.warning("Cannot delete the last admin user")
                    return False
            
            # Invalidate user sessions
            db.invalidate_user_sessions(user_id)
            
            # Soft delete user
            if db.delete_user(user_id):
                db.log_audit_event(
                    user_id=self.user_id,
                    username=self.username,
                    action="USER_DELETED",
                    resource=f"user:{username}",
                    details=f"Deleted user {username}",
                    success=True
                )
                
                self._logger.info(f"User {username} deleted successfully")
                return True
            else:
                self._logger.error(f"Failed to delete user {username}")
                return False
                
        except Exception as e:
            self._logger.error(f"Error deleting user {username}: {e}")
            return False
    
    def list_users(self) -> List[Dict]:
        """List all users (Admin only)."""
        if not self.check_permission(Permission.VIEW_USERS):
            self._logger.warning(f"Permission denied: {self.username} cannot view users")
            return []
        
        try:
            return db.list_users()
        except Exception as e:
            self._logger.error(f"Error listing users: {e}")
            return []
    
    def manageUsers(self) -> None:
        """Legacy method - display user management capabilities."""
        if not self.check_permission(Permission.VIEW_USERS):
            print(f"Permission denied: {self.username} cannot manage users")
            return
        
        try:
            users = self.list_users()
            print("=== User Management Console ===")
            print(f"Current users: {len(users)}")
            for user_data in users:
                print(f"  - {user_data['username']} (ID: {user_data['user_id']}, Role: {user_data['role']})")
            print("Available operations: create, delete, update role")
        except Exception as e:
            print(f"Error in user management: {e}")
    
    def create_automation_rule(self, rule_name: str, condition: str, action: str) -> bool:
        """Create automation rule (Admin only)."""
        if not self.check_permission(Permission.CREATE_AUTOMATION_RULE):
            print(f"Permission denied: {self.username} cannot create automation rules")
            return False
        
        print(f"Automation rule '{rule_name}' created: IF {condition} THEN {action}")
        return True
    
    def delete_automation_rule(self, rule_name: str) -> bool:
        """Delete automation rule (Admin only)."""
        if not self.check_permission(Permission.DELETE_AUTOMATION_RULE):
            print(f"Permission denied: {self.username} cannot delete automation rules")
            return False
        
        print(f"Automation rule '{rule_name}' deleted")
        return True
    
    def configureAutomationRules(self) -> None:
        """Legacy method - display automation rule configuration."""
        if not self.check_permission(Permission.CREATE_AUTOMATION_RULE):
            print(f"Permission denied: {self.username} cannot configure automation rules")
            return
        
        print("=== Automation Rule Configuration ===")
        print("Admin can create, update, and delete automation rules")
        print("Available rule types: fault detection, performance optimization, safety protocols")
    
    def update_system_config(self, setting: str, value: str) -> bool:
        """Update system configuration (Admin only)."""
        if not self.check_permission(Permission.UPDATE_SYSTEM_CONFIG):
            print(f"Permission denied: {self.username} cannot update system configuration")
            return False
        
        print(f"System configuration updated: {setting} = {value}")
        return True
    
    def access_simulation_mode(self) -> bool:
        """Access simulation mode (Admin has full access)."""
        if not self.check_permission(Permission.ACCESS_SIMULATION_MODE):
            print(f"Permission denied: {self.username} cannot access simulation mode")
            return False
        
        print(f"Admin {self.username} entered simulation mode with full privileges")
        return True
