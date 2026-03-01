from typing import List, Dict, Optional
from .user import User
from .permissions import Permission
from .database import db


class Operator(User):
    """Operator user with machine control and monitoring permissions."""
    
    def __init__(self, user_id, username, password=None, password_hash=None, salt=None):
        super().__init__(user_id, username, password, password_hash, salt)
        self._role = "OPERATOR"

    def get_role(self) -> str:
        return self._role
    
    def start_machine(self, machine_id: str) -> bool:
        """Start a specific machine."""
        if not self.check_permission(Permission.START_MACHINE):
            self._logger.warning(f"Permission denied: {self.username} cannot start machines")
            return False
        
        try:
            db.log_audit_event(
                user_id=self.user_id,
                username=self.username,
                action="MACHINE_START",
                resource=f"machine:{machine_id}",
                details=f"Started machine {machine_id}",
                success=True
            )
            
            print(f"Machine {machine_id} started by Operator {self.username}")
            return True
        except Exception as e:
            self._logger.error(f"Error starting machine {machine_id}: {e}")
            return False
    
    def stop_machine(self, machine_id: str) -> bool:
        """Stop a specific machine."""
        if not self.check_permission(Permission.STOP_MACHINE):
            print(f"Permission denied: {self.username} cannot stop machines")
            return False
        
        print(f"Machine {machine_id} stopped by Operator {self.username}")
        return True
    
    def control_conveyor_belt(self, conveyor_id: str, action: str, speed: Optional[int] = None) -> bool:
        """Control conveyor belt operations."""
        if not self.check_permission(Permission.CONTROL_CONVEYOR):
            print(f"Permission denied: {self.username} cannot control conveyor belts")
            return False
        
        if action == "start":
            print(f"Conveyor {conveyor_id} started by Operator {self.username}")
        elif action == "stop":
            print(f"Conveyor {conveyor_id} stopped by Operator {self.username}")
        elif action == "adjust_speed" and speed is not None:
            if self.check_permission(Permission.ADJUST_SPEED):
                print(f"Conveyor {conveyor_id} speed adjusted to {speed} RPM by Operator {self.username}")
            else:
                print(f"Permission denied: {self.username} cannot adjust speeds")
                return False
        else:
            print(f"Invalid conveyor action: {action}")
            return False
        
        return True
    
    def controlMachines(self) -> None:
        """Legacy method - display machine control capabilities."""
        if not self.check_permission(Permission.START_MACHINE):
            print(f"Permission denied: {self.username} cannot control machines")
            return
        
        print("=== Machine Control Console ===")
        print(f"Operator {self.username} controlling factory machines")
        print(f"Currently controlling machines: {self._controlled_machines}")
        print("Available actions: start, stop, adjust speed")
    
    def view_machine_status(self, machine_id: Optional[str] = None) -> Dict:
        """View status of machines."""
        if not self.check_permission(Permission.VIEW_MACHINE_STATUS):
            print(f"Permission denied: {self.username} cannot view machine status")
            return {}
        
        if machine_id:
            status = {
                'machine_id': machine_id,
                'status': 'running',
                'temperature': '75°C',
                'speed': '1200 RPM',
                'last_maintenance': '2024-02-15'
            }
            print(f"Status for machine {machine_id} retrieved by {self.username}")
        else:
            status = {
                'total_machines': 8,
                'active': 6,
                'maintenance': 1,
                'offline': 1
            }
            print(f"Overall machine status retrieved by {self.username}")
        
        return status
    
    def view_sensor_data(self, sensor_type: Optional[str] = None) -> Dict:
        """View real-time sensor data."""
        if not self.check_permission(Permission.VIEW_SENSOR_DATA):
            print(f"Permission denied: {self.username} cannot view sensor data")
            return {}
        
        sensor_data = {
            'temperature_sensors': {'avg': 72, 'max': 85, 'alerts': 0},
            'pressure_sensors': {'avg': 2.1, 'max': 3.0, 'alerts': 1},
            'vibration_sensors': {'status': 'normal', 'alerts': 0}
        }
        
        print(f"Sensor data accessed by Operator {self.username}")
        return sensor_data.get(sensor_type, sensor_data) if sensor_type else sensor_data
    
    def viewLiveStatus(self) -> None:
        """Legacy method - display live status monitoring."""
        if not self.check_permission(Permission.VIEW_LIVE_STATUS):
            print(f"Permission denied: {self.username} cannot view live status")
            return
        
        print("=== Live Status Dashboard ===")
        print(f"Operator {self.username} monitoring live factory status")
        print("Production line: Active")
        print("Current output: 125 units/hour")
        print("System alerts: 1 warning")
        print("Next maintenance: Machine-3 in 48 hours")
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge system alerts."""
        if not self.check_permission(Permission.ACKNOWLEDGE_ALERTS):
            print(f"Permission denied: {self.username} cannot acknowledge alerts")
            return False
        
        print(f"Alert {alert_id} acknowledged by Operator {self.username}")
        return True
    
    def emergency_stop(self) -> bool:
        """Trigger emergency stop of all operations."""
        if not self.check_permission(Permission.EMERGENCY_STOP):
            print(f"Permission denied: {self.username} cannot trigger emergency stop")
            return False
        
        print(f"EMERGENCY STOP activated by Operator {self.username}")
        print("All machines and conveyor belts stopped immediately")
        return True
