from typing import List, Dict, Optional
from .user import User
from .permissions import Permission
from .database import db


class Supervisor(User):
    """Supervisor user with elevated monitoring and approval permissions."""
    
    def __init__(self, user_id, username, password=None, password_hash=None, salt=None):
        super().__init__(user_id, username, password, password_hash, salt)
        self._role = "SUPERVISOR"

    def get_role(self) -> str:
        return self._role
    
    def approve_automation_rule(self, rule_id: str, rule_name: str) -> bool:
        """Approve automation rule (Supervisor privilege)."""
        if not self.check_permission(Permission.APPROVE_AUTOMATION):
            self._logger.warning(f"Permission denied: {self.username} cannot approve automation rules")
            return False
        
        try:
            db.log_audit_event(
                user_id=self.user_id,
                username=self.username,
                action="AUTOMATION_RULE_APPROVED",
                resource=f"rule:{rule_id}",
                details=f"Approved automation rule '{rule_name}'",
                success=True
            )
            
            print(f"Automation rule '{rule_name}' approved by Supervisor {self.username}")
            return True
        except Exception as e:
            self._logger.error(f"Error approving automation rule: {e}")
            return False
    
    def reject_automation_rule(self, rule_id: str, rule_name: str, reason: str) -> bool:
        """Reject automation rule with reason."""
        if not self.check_permission(Permission.APPROVE_AUTOMATION):
            print(f"Permission denied: {self.username} cannot reject automation rules")
            return False
        
        print(f"Automation rule '{rule_name}' rejected by Supervisor {self.username}. Reason: {reason}")
        return True
    
    def approveAutomation(self) -> None:
        """Legacy method - display automation approval capabilities."""
        if not self.check_permission(Permission.APPROVE_AUTOMATION):
            print(f"Permission denied: {self.username} cannot approve automation")
            return
        
        print("=== Automation Approval Console ===")
        print(f"Supervisor {self.username} managing automation approvals")
        print(f"Pending approvals: {len(self._pending_approvals)}")
        print("Actions: approve, reject, review pending")
    
    def monitor_factory_operations(self) -> Dict:
        """Monitor overall factory operations."""
        if not self.check_permission(Permission.MONITOR_OPERATIONS):
            print(f"Permission denied: {self.username} cannot monitor operations")
            return {}
        
        operations_data = {
            'total_machines_active': 5,
            'production_rate': '85%',
            'energy_consumption': 'normal',
            'safety_status': 'all clear',
            'alerts_count': 2
        }
        
        self._monitoring_data = operations_data
        print(f"Operations monitoring data updated for {self.username}")
        return operations_data
    
    def monitorOperations(self) -> None:
        """Legacy method - display monitoring capabilities."""
        if not self.check_permission(Permission.MONITOR_OPERATIONS):
            print(f"Permission denied: {self.username} cannot monitor operations")
            return
        
        print("=== Operations Monitoring Dashboard ===")
        print(f"Supervisor {self.username} monitoring factory operations")
        
        if self._monitoring_data:
            for key, value in self._monitoring_data.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
        else:
            print("  No monitoring data available. Run monitor_factory_operations() first.")
    
    def view_production_reports(self) -> bool:
        """View production reports and analytics."""
        if not self.check_permission(Permission.VIEW_LOGS):
            print(f"Permission denied: {self.username} cannot view reports")
            return False
        
        print(f"Production reports accessed by Supervisor {self.username}")
        print("Daily production: 1,250 units")
        print("Quality rate: 98.5%")
        print("Downtime: 2.5 hours")
        return True
    
    def emergency_stop_system(self) -> bool:
        """Initiate emergency stop (Supervisor level authorization)."""
        if not self.check_permission(Permission.EMERGENCY_STOP):
            print(f"Permission denied: {self.username} cannot initiate emergency stop")
            return False
        
        print(f"EMERGENCY STOP initiated by Supervisor {self.username}")
        print("All factory operations halted for safety inspection")
        return True
    
    def export_logs(self, date_range: str) -> bool:
        """Export system logs for analysis."""
        if not self.check_permission(Permission.EXPORT_LOGS):
            print(f"Permission denied: {self.username} cannot export logs")
            return False
        
        print(f"Logs for {date_range} exported by Supervisor {self.username}")
        return True
    
    def access_simulation_mode(self) -> bool:
        """Access simulation mode for testing."""
        if not self.check_permission(Permission.ACCESS_SIMULATION_MODE):
            print(f"Permission denied: {self.username} cannot access simulation mode")
            return False
        
        print(f"Supervisor {self.username} entered simulation mode")
        return True
