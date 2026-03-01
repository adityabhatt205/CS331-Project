"""
Machine module for the Factory Floor System.
Provides machine management with status tracking, safety features, and event logging.
"""

from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import time
import threading
import logging
from datetime import datetime, timedelta


class MachineStatus(Enum):
    """Machine status enumeration."""
    IDLE = "IDLE"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"


class MachineType(Enum):
    """Machine type enumeration."""
    CONVEYOR = "CONVEYOR"
    ASSEMBLY = "ASSEMBLY"
    ASSEMBLY_ROBOT = "ASSEMBLY_ROBOT"
    WELDING = "WELDING"
    PACKAGING = "PACKAGING"
    QUALITY_CHECK = "QUALITY_CHECK"
    ROBOTIC_ARM = "ROBOTIC_ARM"
    PRODUCTION_LINE = "PRODUCTION_LINE"
    TESTING_EQUIPMENT = "TESTING_EQUIPMENT"
    MATERIAL_HANDLING = "MATERIAL_HANDLING"


class MachineSafetyLevel(Enum):
    """Machine safety level enumeration."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class MachineEvent:
    """Machine event data structure."""
    
    def __init__(self, event_type: str, message: str, severity: str = "INFO", 
                 user_id: Optional[int] = None, details: Optional[Dict] = None):
        self.timestamp = datetime.now()
        self.event_type = event_type
        self.message = message
        self.severity = severity
        self.user_id = user_id
        self.details = details or {}


class Machine:
    """
    Comprehensive Machine class for factory floor operations.
    Provides machine control, monitoring, and safety features.
    """
    
    def __init__(self, machine_id: int, machine_type: MachineType, name: str,
                 location: str = "", safety_level: MachineSafetyLevel = MachineSafetyLevel.MEDIUM):
        """
        Initialize machine.
        
        Args:
            machine_id: Unique machine identifier
            machine_type: Type of machine
            name: Machine name
            location: Physical location
            safety_level: Safety classification level
        """
        self.machine_id = machine_id
        self.machine_type = machine_type
        self.name = name
        self.location = location
        self.safety_level = safety_level
        
        # Status and control
        self._status = MachineStatus.IDLE
        self._speed = 0  # 0-100 percentage
        self._target_speed = 0
        self._is_locked = False
        self._emergency_stop_active = False
        
        # Operational parameters
        self._operating_hours = 0.0
        self._cycle_count = 0
        self._last_maintenance = datetime.now()
        self._maintenance_due = False
        
        # Safety and monitoring
        self._max_speed = 100
        self._min_speed = 0
        self._safety_interlocks = []
        self._alarm_conditions = []
        
        # Event tracking
        self._event_history = []
        self._max_event_history = 1000
        
        # Threading for status monitoring
        self._monitor_thread = None
        self._monitoring_active = False
        self._status_lock = threading.Lock()
        
        # Callbacks
        self._status_change_callbacks = []
        self._alarm_callbacks = []
        
        # Logger
        self._logger = logging.getLogger(f"Machine_{machine_id}")
        
        # Initialize machine
        self._log_event("MACHINE_CREATED", f"Machine {name} initialized", "INFO")
    
    @property
    def status(self) -> MachineStatus:
        """Get current machine status."""
        with self._status_lock:
            return self._status
    
    @property
    def speed(self) -> int:
        """Get current machine speed."""
        return self._speed
    
    @property
    def is_running(self) -> bool:
        """Check if machine is running."""
        return self._status == MachineStatus.RUNNING
    
    @property
    def is_emergency_stopped(self) -> bool:
        """Check if machine is in emergency stop state."""
        return self._emergency_stop_active
    
    @property
    def operating_hours(self) -> float:
        """Get total operating hours."""
        return self._operating_hours
    
    @property
    def cycle_count(self) -> int:
        """Get total cycle count."""
        return self._cycle_count
    
    def start(self, user_id: Optional[int] = None, target_speed: int = 50) -> bool:
        """
        Start the machine.
        
        Args:
            user_id: ID of user starting the machine
            target_speed: Target operating speed (0-100)
            
        Returns:
            True if started successfully, False otherwise
        """
        with self._status_lock:
            if self._status not in [MachineStatus.IDLE, MachineStatus.STOPPED]:
                self._log_event("START_FAILED", 
                               f"Cannot start machine from status {self._status.value}", 
                               "WARNING", user_id)
                return False
            
            if self._is_locked:
                self._log_event("START_FAILED", "Machine is locked", "WARNING", user_id)
                return False
            
            if self._emergency_stop_active:
                self._log_event("START_FAILED", "Emergency stop is active", "WARNING", user_id)
                return False
            
            if not self._check_safety_interlocks():
                self._log_event("START_FAILED", "Safety interlock violation", "ERROR", user_id)
                return False
            
            # Validate target speed
            target_speed = max(self._min_speed, min(target_speed, self._max_speed))
            self._target_speed = target_speed
            
            # Start sequence
            self._status = MachineStatus.STARTING
            self._log_event("MACHINE_STARTING", f"Starting machine to {target_speed}% speed", "INFO", user_id)
            
            # Simulate startup time
            threading.Thread(target=self._startup_sequence, daemon=True).start()
            
            return True
    
    def stop(self, user_id: Optional[int] = None, immediate: bool = False) -> bool:
        """
        Stop the machine.
        
        Args:
            user_id: ID of user stopping the machine
            immediate: If True, stop immediately without ramp-down
            
        Returns:
            True if stopped successfully, False otherwise
        """
        with self._status_lock:
            if self._status in [MachineStatus.STOPPED, MachineStatus.IDLE]:
                return True
            
            if self._status == MachineStatus.EMERGENCY_STOP:
                self._log_event("STOP_INFO", "Machine already in emergency stop", "INFO", user_id)
                return True
            
            stop_type = "immediate" if immediate else "controlled"
            self._log_event("MACHINE_STOPPING", f"Stopping machine ({stop_type})", "INFO", user_id)
            
            if immediate:
                self._status = MachineStatus.STOPPED
                self._speed = 0
                self._target_speed = 0
            else:
                self._status = MachineStatus.STOPPING
                threading.Thread(target=self._shutdown_sequence, daemon=True).start()
            
            return True
    
    def emergency_stop(self, user_id: Optional[int] = None, reason: str = "Emergency stop activated") -> None:
        """
        Immediately stop machine for emergency.
        
        Args:
            user_id: ID of user activating emergency stop
            reason: Reason for emergency stop
        """
        with self._status_lock:
            self._emergency_stop_active = True
            self._status = MachineStatus.EMERGENCY_STOP
            self._speed = 0
            self._target_speed = 0
            
            self._log_event("EMERGENCY_STOP", reason, "CRITICAL", user_id)
            self._trigger_alarms("EMERGENCY_STOP", reason)
    
    def reset_emergency_stop(self, user_id: Optional[int] = None) -> bool:
        """
        Reset emergency stop condition.
        
        Args:
            user_id: ID of user resetting emergency stop
            
        Returns:
            True if reset successful, False otherwise
        """
        with self._status_lock:
            if not self._emergency_stop_active:
                return True
            
            # Check if it's safe to reset
            if not self._check_safety_interlocks():
                self._log_event("EMERGENCY_RESET_FAILED", "Safety conditions not met", "ERROR", user_id)
                return False
            
            self._emergency_stop_active = False
            self._status = MachineStatus.IDLE
            self._log_event("EMERGENCY_RESET", "Emergency stop reset", "INFO", user_id)
            
            return True
    
    def adjust_speed(self, new_speed: int, user_id: Optional[int] = None) -> bool:
        """
        Adjust machine operating speed.
        
        Args:
            new_speed: New target speed (0-100)
            user_id: ID of user adjusting speed
            
        Returns:
            True if adjustment successful, False otherwise
        """
        if not self.is_running:
            self._log_event("SPEED_ADJUST_FAILED", "Cannot adjust speed - machine not running", "WARNING", user_id)
            return False
        
        # Validate speed range
        new_speed = max(self._min_speed, min(new_speed, self._max_speed))
        
        if new_speed == self._target_speed:
            return True
        
        old_speed = self._target_speed
        self._target_speed = new_speed
        
        self._log_event("SPEED_ADJUSTED", 
                       f"Speed adjusted from {old_speed}% to {new_speed}%", 
                       "INFO", user_id)
        
        # Gradual speed change in background thread
        threading.Thread(target=self._adjust_speed_gradually, args=(new_speed,), daemon=True).start()
        
        return True
    
    def set_maintenance_mode(self, enabled: bool, user_id: Optional[int] = None) -> bool:
        """
        Enable/disable maintenance mode.
        
        Args:
            enabled: True to enable maintenance mode
            user_id: ID of user setting maintenance mode
            
        Returns:
            True if successful, False otherwise
        """
        with self._status_lock:
            if enabled:
                if self._status not in [MachineStatus.IDLE, MachineStatus.STOPPED]:
                    self._log_event("MAINTENANCE_FAILED", "Machine must be stopped for maintenance", "WARNING", user_id)
                    return False
                
                self._status = MachineStatus.MAINTENANCE
                self._log_event("MAINTENANCE_STARTED", "Machine entered maintenance mode", "INFO", user_id)
            else:
                if self._status == MachineStatus.MAINTENANCE:
                    self._status = MachineStatus.IDLE
                    self._last_maintenance = datetime.now()
                    self._maintenance_due = False
                    self._log_event("MAINTENANCE_COMPLETED", "Machine exited maintenance mode", "INFO", user_id)
            
            return True
    
    def lock_machine(self, user_id: Optional[int] = None, reason: str = "Machine locked") -> None:
        """
        Lock machine to prevent operations.
        
        Args:
            user_id: ID of user locking machine
            reason: Reason for locking
        """
        self._is_locked = True
        self._log_event("MACHINE_LOCKED", reason, "INFO", user_id)
    
    def unlock_machine(self, user_id: Optional[int] = None) -> None:
        """
        Unlock machine to allow operations.
        
        Args:
            user_id: ID of user unlocking machine
        """
        self._is_locked = False
        self._log_event("MACHINE_UNLOCKED", "Machine unlocked", "INFO", user_id)
    
    def get_status_info(self) -> Dict[str, Any]:
        """
        Get comprehensive machine status information.
        
        Returns:
            Dictionary containing machine status information
        """
        return {
            "machine_id": self.machine_id,
            "name": self.name,
            "type": self.machine_type.value,
            "location": self.location,
            "status": self._status.value,
            "speed": self._speed,
            "target_speed": self._target_speed,
            "is_locked": self._is_locked,
            "emergency_stop_active": self._emergency_stop_active,
            "operating_hours": self._operating_hours,
            "cycle_count": self._cycle_count,
            "maintenance_due": self._maintenance_due,
            "last_maintenance": self._last_maintenance.isoformat(),
            "safety_level": self.safety_level.value,
            "active_alarms": len(self._alarm_conditions),
            "uptime_percentage": self._calculate_uptime_percentage()
        }
    
    def get_event_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent machine event history.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        return [
            {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "message": event.message,
                "severity": event.severity,
                "user_id": event.user_id,
                "details": event.details
            }
            for event in self._event_history[-limit:]
        ]
    
    def add_status_change_callback(self, callback: Callable[[MachineStatus, MachineStatus], None]) -> None:
        """Add callback for status changes."""
        self._status_change_callbacks.append(callback)
    
    def add_alarm_callback(self, callback: Callable[[str, str], None]) -> None:
        """Add callback for alarms."""
        self._alarm_callbacks.append(callback)
    
    def validate_command(self, command: str, user_id: Optional[int] = None) -> bool:
        """
        Validate if a command can be executed.
        
        Args:
            command: Command to validate
            user_id: ID of user executing command
            
        Returns:
            True if command is valid, False otherwise
        """
        if self._is_locked and command not in ["unlock", "get_status"]:
            return False
        
        if self._emergency_stop_active and command not in ["reset_emergency_stop", "get_status"]:
            return False
        
        # Command-specific validation
        if command == "start":
            return self._status in [MachineStatus.IDLE, MachineStatus.STOPPED]
        elif command == "stop":
            return self._status in [MachineStatus.RUNNING, MachineStatus.STARTING]
        elif command == "adjust_speed":
            return self._status == MachineStatus.RUNNING
        elif command == "maintenance":
            return self._status in [MachineStatus.IDLE, MachineStatus.STOPPED, MachineStatus.MAINTENANCE]
        
        return True
    
    def start_monitoring(self) -> None:
        """Start machine status monitoring."""
        if not self._monitoring_active:
            self._monitoring_active = True
            self._monitor_thread = threading.Thread(target=self._monitor_machine, daemon=True)
            self._monitor_thread.start()
            self._log_event("MONITORING_STARTED", "Machine monitoring started", "INFO")
    
    def stop_monitoring(self) -> None:
        """Stop machine status monitoring."""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)
        self._log_event("MONITORING_STOPPED", "Machine monitoring stopped", "INFO")
    
    def _startup_sequence(self) -> None:
        """Execute machine startup sequence."""
        # Simulate startup time
        time.sleep(2)
        
        with self._status_lock:
            if self._status == MachineStatus.STARTING:
                self._status = MachineStatus.RUNNING
                self._speed = self._target_speed
                self._log_event("MACHINE_STARTED", f"Machine started at {self._speed}% speed", "INFO")
                
                # Notify callbacks
                for callback in self._status_change_callbacks:
                    try:
                        callback(MachineStatus.STARTING, MachineStatus.RUNNING)
                    except Exception as e:
                        self._logger.error(f"Status change callback error: {e}")
    
    def _shutdown_sequence(self) -> None:
        """Execute machine shutdown sequence."""
        # Gradual speed reduction
        while self._speed > 0:
            self._speed = max(0, self._speed - 10)
            time.sleep(0.5)
        
        with self._status_lock:
            self._status = MachineStatus.STOPPED
            self._target_speed = 0
            self._log_event("MACHINE_STOPPED", "Machine stopped", "INFO")
    
    def _adjust_speed_gradually(self, target_speed: int) -> None:
        """Gradually adjust speed to target."""
        while self._speed != target_speed and self.is_running:
            if self._speed < target_speed:
                self._speed = min(target_speed, self._speed + 5)
            else:
                self._speed = max(target_speed, self._speed - 5)
            time.sleep(0.1)
    
    def _check_safety_interlocks(self) -> bool:
        """Check all safety interlocks."""
        for interlock in self._safety_interlocks:
            if not interlock():
                return False
        return True
    
    def _monitor_machine(self) -> None:
        """Background thread for machine monitoring."""
        while self._monitoring_active:
            try:
                # Update operating hours
                if self.is_running:
                    self._operating_hours += 0.1 / 3600  # 0.1 second in hours
                    
                    # Increment cycle count periodically
                    if int(self._operating_hours * 10) % 100 == 0:
                        self._cycle_count += 1
                
                # Check maintenance schedule
                if datetime.now() - self._last_maintenance > timedelta(days=30):
                    if not self._maintenance_due:
                        self._maintenance_due = True
                        self._log_event("MAINTENANCE_DUE", "Scheduled maintenance is due", "WARNING")
                
                time.sleep(0.1)
                
            except Exception as e:
                self._logger.error(f"Monitoring error: {e}")
                time.sleep(1)
    
    def _log_event(self, event_type: str, message: str, severity: str, user_id: Optional[int] = None) -> None:
        """Log machine event."""
        event = MachineEvent(event_type, message, severity, user_id)
        
        self._event_history.append(event)
        
        # Limit event history size
        if len(self._event_history) > self._max_event_history:
            self._event_history.pop(0)
        
        # Log to standard logger
        log_level = getattr(logging, severity, logging.INFO)
        self._logger.log(log_level, f"[{event_type}] {message}")
    
    def _trigger_alarms(self, alarm_type: str, message: str) -> None:
        """Trigger machine alarms."""
        self._alarm_conditions.append(f"{alarm_type}: {message}")
        
        for callback in self._alarm_callbacks:
            try:
                callback(alarm_type, message)
            except Exception as e:
                self._logger.error(f"Alarm callback error: {e}")
    
    def _calculate_uptime_percentage(self) -> float:
        """Calculate machine uptime percentage."""
        # Simple calculation based on running time vs total time
        if self._operating_hours == 0:
            return 0.0
        
        total_time = (datetime.now() - (datetime.now() - timedelta(hours=self._operating_hours))).total_seconds() / 3600
        return min(100.0, (self._operating_hours / total_time) * 100) if total_time > 0 else 0.0


class MachineManager:
    """Manager class for multiple machines."""
    
    def __init__(self):
        """Initialize machine manager."""
        self._machines: Dict[int, Machine] = {}
        self._logger = logging.getLogger(__name__)
    
    def add_machine(self, machine: Machine) -> None:
        """Add machine to manager."""
        self._machines[machine.machine_id] = machine
        machine.start_monitoring()
        self._logger.info(f"Added machine {machine.machine_id}: {machine.name}")
    
    def remove_machine(self, machine_id: int) -> bool:
        """Remove machine from manager."""
        if machine_id in self._machines:
            machine = self._machines[machine_id]
            machine.stop_monitoring()
            del self._machines[machine_id]
            self._logger.info(f"Removed machine {machine_id}")
            return True
        return False
    
    def get_machine(self, machine_id: int) -> Optional[Machine]:
        """Get machine by ID."""
        return self._machines.get(machine_id)
    
    def get_all_machines(self) -> List[Machine]:
        """Get all machines."""
        return list(self._machines.values())
    
    def get_machines_by_type(self, machine_type: MachineType) -> List[Machine]:
        """Get machines by type."""
        return [machine for machine in self._machines.values() 
                if machine.machine_type == machine_type]
    
    def get_machines_by_status(self, status: MachineStatus) -> List[Machine]:
        """Get machines by status."""
        return [machine for machine in self._machines.values() 
                if machine.status == status]
    
    def emergency_stop_all(self, user_id: Optional[int] = None, reason: str = "System emergency stop") -> None:
        """Emergency stop all machines."""
        for machine in self._machines.values():
            machine.emergency_stop(user_id, reason)
        self._logger.critical(f"Emergency stop activated for all machines: {reason}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        running_count = len(self.get_machines_by_status(MachineStatus.RUNNING))
        idle_count = len(self.get_machines_by_status(MachineStatus.IDLE))
        error_count = len(self.get_machines_by_status(MachineStatus.ERROR))
        maintenance_count = len(self.get_machines_by_status(MachineStatus.MAINTENANCE))
        
        return {
            "total_machines": len(self._machines),
            "running_machines": running_count,
            "idle_machines": idle_count,
            "error_machines": error_count,
            "maintenance_machines": maintenance_count,
            "system_efficiency": (running_count / len(self._machines)) * 100 if self._machines else 0
        }
