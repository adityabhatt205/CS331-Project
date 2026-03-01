"""
Permission definitions and role-based access control for the Factory Floor System.
"""

from enum import Enum
from typing import Set, Dict


class Permission(Enum):
    """Enumeration of all system permissions."""
    
    # User Management
    CREATE_USER = "create_user"
    DELETE_USER = "delete_user" 
    UPDATE_USER = "update_user"
    VIEW_USERS = "view_users"
    
    # Machine Control
    START_MACHINE = "start_machine"
    STOP_MACHINE = "stop_machine"
    CONTROL_CONVEYOR = "control_conveyor"
    ADJUST_SPEED = "adjust_speed"
    EMERGENCY_STOP = "emergency_stop"
    
    # Automation
    CREATE_AUTOMATION_RULE = "create_automation_rule"
    UPDATE_AUTOMATION_RULE = "update_automation_rule"
    DELETE_AUTOMATION_RULE = "delete_automation_rule"
    APPROVE_AUTOMATION = "approve_automation"
    TRIGGER_AUTOMATION = "trigger_automation"
    
    # Monitoring & Visualization
    VIEW_LIVE_STATUS = "view_live_status"
    VIEW_SENSOR_DATA = "view_sensor_data"
    VIEW_MACHINE_STATUS = "view_machine_status"
    MONITOR_OPERATIONS = "monitor_operations"
    
    # Logging & History
    VIEW_LOGS = "view_logs"
    EXPORT_LOGS = "export_logs"
    DELETE_LOGS = "delete_logs"
    
    # Alerts & Notifications
    VIEW_ALERTS = "view_alerts"
    ACKNOWLEDGE_ALERTS = "acknowledge_alerts"
    CONFIGURE_NOTIFICATIONS = "configure_notifications"
    
    # System Configuration
    UPDATE_SYSTEM_CONFIG = "update_system_config"
    VIEW_SYSTEM_CONFIG = "view_system_config"
    ACCESS_SIMULATION_MODE = "access_simulation_mode"


class Role(Enum):
    """User roles in the system."""
    ADMIN = "ADMIN"
    SUPERVISOR = "SUPERVISOR"
    OPERATOR = "OPERATOR"


# Role-Permission mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        # Full access to all permissions
        Permission.CREATE_USER,
        Permission.DELETE_USER,
        Permission.UPDATE_USER,
        Permission.VIEW_USERS,
        Permission.START_MACHINE,
        Permission.STOP_MACHINE,
        Permission.CONTROL_CONVEYOR,
        Permission.ADJUST_SPEED,
        Permission.EMERGENCY_STOP,
        Permission.CREATE_AUTOMATION_RULE,
        Permission.UPDATE_AUTOMATION_RULE,
        Permission.DELETE_AUTOMATION_RULE,
        Permission.APPROVE_AUTOMATION,
        Permission.TRIGGER_AUTOMATION,
        Permission.VIEW_LIVE_STATUS,
        Permission.VIEW_SENSOR_DATA,
        Permission.VIEW_MACHINE_STATUS,
        Permission.MONITOR_OPERATIONS,
        Permission.VIEW_LOGS,
        Permission.EXPORT_LOGS,
        Permission.DELETE_LOGS,
        Permission.VIEW_ALERTS,
        Permission.ACKNOWLEDGE_ALERTS,
        Permission.CONFIGURE_NOTIFICATIONS,
        Permission.UPDATE_SYSTEM_CONFIG,
        Permission.VIEW_SYSTEM_CONFIG,
        Permission.ACCESS_SIMULATION_MODE,
    },
    
    Role.SUPERVISOR: {
        # Elevated permissions - monitoring, approval, and limited configuration
        Permission.VIEW_USERS,
        Permission.START_MACHINE,
        Permission.STOP_MACHINE,
        Permission.CONTROL_CONVEYOR,
        Permission.ADJUST_SPEED,
        Permission.EMERGENCY_STOP,
        Permission.UPDATE_AUTOMATION_RULE,
        Permission.APPROVE_AUTOMATION,
        Permission.TRIGGER_AUTOMATION,
        Permission.VIEW_LIVE_STATUS,
        Permission.VIEW_SENSOR_DATA,
        Permission.VIEW_MACHINE_STATUS,
        Permission.MONITOR_OPERATIONS,
        Permission.VIEW_LOGS,
        Permission.EXPORT_LOGS,
        Permission.VIEW_ALERTS,
        Permission.ACKNOWLEDGE_ALERTS,
        Permission.VIEW_SYSTEM_CONFIG,
        Permission.ACCESS_SIMULATION_MODE,
    },
    
    Role.OPERATOR: {
        # Basic operational permissions
        Permission.START_MACHINE,
        Permission.STOP_MACHINE,
        Permission.CONTROL_CONVEYOR,
        Permission.ADJUST_SPEED,
        Permission.EMERGENCY_STOP,
        Permission.VIEW_LIVE_STATUS,
        Permission.VIEW_SENSOR_DATA,
        Permission.VIEW_MACHINE_STATUS,
        Permission.VIEW_LOGS,
        Permission.VIEW_ALERTS,
        Permission.ACKNOWLEDGE_ALERTS,
    }
}


def get_role_permissions(role: Role) -> Set[Permission]:
    """Get all permissions for a given role."""
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: Role, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())