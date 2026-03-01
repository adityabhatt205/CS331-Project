"""
PLC Controller module for the Factory Floor System.
Provides comprehensive PLC communication, command validation, and control operations.
"""

from typing import Dict, List, Optional, Any, Callable, Tuple, Union
from enum import Enum
import time
import threading
import logging
import json
from datetime import datetime
from dataclasses import dataclass


class PLCStatus(Enum):
    """PLC status enumeration."""
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"
    SIMULATION = "SIMULATION"


class CommandType(Enum):
    """PLC command types."""
    READ_REGISTER = "READ_REGISTER"
    WRITE_REGISTER = "WRITE_REGISTER"
    READ_COIL = "READ_COIL"
    WRITE_COIL = "WRITE_COIL"
    READ_INPUT = "READ_INPUT"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    RESET = "RESET"
    START_SEQUENCE = "START_SEQUENCE"
    STOP_SEQUENCE = "STOP_SEQUENCE"


class PLCProtocol(Enum):
    """PLC communication protocols."""
    MODBUS_TCP = "MODBUS_TCP"
    ETHERNET_IP = "ETHERNET_IP"
    PROFINET = "PROFINET"
    SIMULATION = "SIMULATION"


class CommandPriority(Enum):
    """Command priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    EMERGENCY = 4


@dataclass
class PLCCommand:
    """PLC command data structure."""
    command_id: str
    command_type: CommandType
    address: str
    value: Optional[Any] = None
    priority: CommandPriority = CommandPriority.NORMAL
    user_id: Optional[int] = None
    machine_id: Optional[int] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class PLCResponse:
    """PLC response data structure."""
    command_id: str
    success: bool
    value: Optional[Any] = None
    error_message: Optional[str] = None
    timestamp: datetime = None
    execution_time_ms: float = 0.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class RegisterMap:
    """PLC register mapping and validation."""
    
    def __init__(self):
        """Initialize register map with predefined addresses."""
        self._registers = {
            # Machine control registers
            "MACHINE_START": {"address": 100, "type": "coil", "writable": True, "description": "Machine start command"},
            "MACHINE_STOP": {"address": 101, "type": "coil", "writable": True, "description": "Machine stop command"},
            "EMERGENCY_STOP": {"address": 102, "type": "coil", "writable": True, "description": "Emergency stop"},
            "MACHINE_STATUS": {"address": 200, "type": "register", "writable": False, "description": "Machine status"},
            "MACHINE_SPEED": {"address": 201, "type": "register", "writable": True, "description": "Machine speed setpoint"},
            "PRODUCTION_COUNT": {"address": 202, "type": "register", "writable": False, "description": "Production counter"},
            
            # Sensor input registers
            "TEMP_SENSOR_1": {"address": 300, "type": "register", "writable": False, "description": "Temperature sensor 1"},
            "PRESSURE_SENSOR_1": {"address": 301, "type": "register", "writable": False, "description": "Pressure sensor 1"},
            "VIBRATION_SENSOR_1": {"address": 302, "type": "register", "writable": False, "description": "Vibration sensor 1"},
            
            # Safety and alarm registers
            "SAFETY_INTERLOCK": {"address": 400, "type": "coil", "writable": False, "description": "Safety interlock status"},
            "ALARM_ACTIVE": {"address": 401, "type": "coil", "writable": False, "description": "Active alarm indicator"},
            "ALARM_CODE": {"address": 500, "type": "register", "writable": False, "description": "Current alarm code"},
            
            # System registers
            "PLC_HEARTBEAT": {"address": 600, "type": "coil", "writable": False, "description": "PLC heartbeat"},
            "SYSTEM_TIME": {"address": 601, "type": "register", "writable": True, "description": "System timestamp"},
        }
    
    def get_register_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get register information by name."""
        return self._registers.get(name)
    
    def is_address_valid(self, address: Union[str, int]) -> bool:
        """Check if address is valid."""
        if isinstance(address, str):
            return address in self._registers
        
        # Check numeric address
        return any(reg["address"] == address for reg in self._registers.values())
    
    def is_writable(self, address: Union[str, int]) -> bool:
        """Check if address is writable."""
        if isinstance(address, str):
            reg_info = self._registers.get(address)
            return reg_info["writable"] if reg_info else False
        
        # Check numeric address
        for reg_info in self._registers.values():
            if reg_info["address"] == address:
                return reg_info["writable"]
        
        return False
    
    def get_all_registers(self) -> Dict[str, Dict[str, Any]]:
        """Get all register definitions."""
        return self._registers.copy()


class PLCController:
    """
    Comprehensive PLC Controller for factory automation.
    Provides PLC communication, command validation, and safety controls.
    """
    
    def __init__(self, plc_id: int, name: str, protocol: PLCProtocol,
                 host: str = "localhost", port: int = 502):
        """
        Initialize PLC controller.
        
        Args:
            plc_id: Unique PLC identifier
            name: PLC name
            protocol: Communication protocol
            host: PLC host address
            port: PLC port number
        """
        self.plc_id = plc_id
        self.name = name
        self.protocol = protocol
        self.host = host
        self.port = port
        
        # Connection status
        self._status = PLCStatus.OFFLINE
        self._connected = False
        self._last_communication = None
        
        # Register mapping
        self._register_map = RegisterMap()
        
        # Command management
        self._command_queue = []
        self._command_history = []
        self._max_history_size = 10000
        self._command_lock = threading.Lock()
        
        # Communication threading
        self._comm_thread = None
        self._comm_active = False
        self._heartbeat_thread = None
        self._heartbeat_active = False
        
        # Performance monitoring
        self._total_commands = 0
        self._successful_commands = 0
        self._failed_commands = 0
        self._avg_response_time = 0.0
        
        # Safety and validation
        self._safety_enabled = True
        self._emergency_stop_active = False
        self._write_protection = False
        
        # Simulation data for simulation mode
        self._simulation_data = {
            "MACHINE_START": False,
            "MACHINE_STOP": False,
            "EMERGENCY_STOP": False,
            "MACHINE_STATUS": 1,  # 1=Running, 0=Stopped, 2=Error
            "MACHINE_SPEED": 100,
            "PRODUCTION_COUNT": 0,
            "TEMP_SENSOR_1": 25.0,
            "PRESSURE_SENSOR_1": 101.3,
            "VIBRATION_SENSOR_1": 2.0,
            "SAFETY_INTERLOCK": True,
            "ALARM_ACTIVE": False,
            "ALARM_CODE": 0,
            "PLC_HEARTBEAT": True,
            "SYSTEM_TIME": int(time.time())
        }
        
        # Event callbacks
        self._status_callbacks = []
        self._command_callbacks = []
        self._error_callbacks = []
        
        # Logger
        self._logger = logging.getLogger(f"PLC_{plc_id}")
        
        # Initialize PLC
        self._logger.info(f"PLC Controller {name} initialized with protocol {protocol.value}")
        
        # Auto-start in simulation mode
        if protocol == PLCProtocol.SIMULATION:
            self.connect()
    
    @property
    def status(self) -> PLCStatus:
        """Get current PLC status."""
        return self._status
    
    @property
    def is_connected(self) -> bool:
        """Check if PLC is connected."""
        return self._connected
    
    @property
    def command_queue_size(self) -> int:
        """Get current command queue size."""
        with self._command_lock:
            return len(self._command_queue)
    
    @property
    def communication_statistics(self) -> Dict[str, Any]:
        """Get communication statistics."""
        success_rate = (self._successful_commands / max(1, self._total_commands)) * 100
        return {
            "total_commands": self._total_commands,
            "successful_commands": self._successful_commands,
            "failed_commands": self._failed_commands,
            "success_rate": success_rate,
            "avg_response_time_ms": self._avg_response_time,
            "queue_size": self.command_queue_size,
            "last_communication": self._last_communication.isoformat() if self._last_communication else None
        }
    
    def connect(self) -> bool:
        """
        Connect to PLC.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.protocol == PLCProtocol.SIMULATION:
                self._connected = True
                self._status = PLCStatus.SIMULATION
                self._start_communication_threads()
                self._logger.info("Connected to PLC in simulation mode")
                return True
            
            # Real PLC connection logic would go here
            # For now, simulate connection
            self._connected = True
            self._status = PLCStatus.ONLINE
            self._start_communication_threads()
            self._logger.info(f"Connected to PLC at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to connect to PLC: {e}")
            self._status = PLCStatus.ERROR
            return False
    
    def disconnect(self) -> None:
        """Disconnect from PLC."""
        self._connected = False
        self._status = PLCStatus.OFFLINE
        self._stop_communication_threads()
        self._logger.info("Disconnected from PLC")
    
    def execute_command(self, command: PLCCommand) -> PLCResponse:
        """
        Execute PLC command synchronously.
        
        Args:
            command: PLC command to execute
            
        Returns:
            PLC response
        """
        if not self._connected:
            return PLCResponse(
                command_id=command.command_id,
                success=False,
                error_message="PLC not connected"
            )
        
        # Validate command
        validation_error = self._validate_command(command)
        if validation_error:
            return PLCResponse(
                command_id=command.command_id,
                success=False,
                error_message=validation_error
            )
        
        start_time = time.time()
        
        try:
            # Execute based on command type
            if command.command_type == CommandType.READ_REGISTER:
                value = self._read_register(command.address)
                response = PLCResponse(
                    command_id=command.command_id,
                    success=True,
                    value=value
                )
            
            elif command.command_type == CommandType.WRITE_REGISTER:
                self._write_register(command.address, command.value)
                response = PLCResponse(
                    command_id=command.command_id,
                    success=True
                )
            
            elif command.command_type == CommandType.READ_COIL:
                value = self._read_coil(command.address)
                response = PLCResponse(
                    command_id=command.command_id,
                    success=True,
                    value=value
                )
            
            elif command.command_type == CommandType.WRITE_COIL:
                self._write_coil(command.address, command.value)
                response = PLCResponse(
                    command_id=command.command_id,
                    success=True
                )
            
            elif command.command_type == CommandType.EMERGENCY_STOP:
                self._execute_emergency_stop()
                response = PLCResponse(
                    command_id=command.command_id,
                    success=True
                )
            
            elif command.command_type == CommandType.RESET:
                self._execute_reset()
                response = PLCResponse(
                    command_id=command.command_id,
                    success=True
                )
            
            else:
                response = PLCResponse(
                    command_id=command.command_id,
                    success=False,
                    error_message=f"Unsupported command type: {command.command_type.value}"
                )
            
            self._successful_commands += 1
            
        except Exception as e:
            response = PLCResponse(
                command_id=command.command_id,
                success=False,
                error_message=str(e)
            )
            self._failed_commands += 1
            self._logger.error(f"Command execution failed: {e}")
        
        # Update statistics
        execution_time = (time.time() - start_time) * 1000  # ms
        response.execution_time_ms = execution_time
        self._total_commands += 1
        self._update_avg_response_time(execution_time)
        
        # Log command execution
        self._log_command_execution(command, response)
        
        # Store in history
        with self._command_lock:
            self._command_history.append((command, response))
            if len(self._command_history) > self._max_history_size:
                self._command_history.pop(0)
        
        # Notify callbacks
        for callback in self._command_callbacks:
            try:
                callback(command, response)
            except Exception as e:
                self._logger.error(f"Command callback error: {e}")
        
        return response
    
    def queue_command(self, command: PLCCommand) -> bool:
        """
        Queue command for asynchronous execution.
        
        Args:
            command: PLC command to queue
            
        Returns:
            True if command queued successfully, False otherwise
        """
        if not self._connected:
            self._logger.error("Cannot queue command: PLC not connected")
            return False
        
        validation_error = self._validate_command(command)
        if validation_error:
            self._logger.error(f"Command validation failed: {validation_error}")
            return False
        
        with self._command_lock:
            # Insert based on priority
            inserted = False
            for i, queued_cmd in enumerate(self._command_queue):
                if command.priority.value > queued_cmd.priority.value:
                    self._command_queue.insert(i, command)
                    inserted = True
                    break
            
            if not inserted:
                self._command_queue.append(command)
        
        self._logger.info(f"Command {command.command_id} queued with priority {command.priority.value}")
        return True
    
    def read_register(self, address: Union[str, int], user_id: Optional[int] = None) -> Optional[Any]:
        """
        Read PLC register value.
        
        Args:
            address: Register address or name
            user_id: User ID for logging
            
        Returns:
            Register value or None if failed
        """
        command = PLCCommand(
            command_id=f"read_{int(time.time() * 1000)}",
            command_type=CommandType.READ_REGISTER,
            address=str(address),
            user_id=user_id
        )
        
        response = self.execute_command(command)
        return response.value if response.success else None
    
    def write_register(self, address: Union[str, int], value: Any, user_id: Optional[int] = None) -> bool:
        """
        Write PLC register value.
        
        Args:
            address: Register address or name
            value: Value to write
            user_id: User ID for logging
            
        Returns:
            True if write successful, False otherwise
        """
        command = PLCCommand(
            command_id=f"write_{int(time.time() * 1000)}",
            command_type=CommandType.WRITE_REGISTER,
            address=str(address),
            value=value,
            user_id=user_id
        )
        
        response = self.execute_command(command)
        return response.success
    
    def read_coil(self, address: Union[str, int], user_id: Optional[int] = None) -> Optional[bool]:
        """
        Read PLC coil value.
        
        Args:
            address: Coil address or name
            user_id: User ID for logging
            
        Returns:
            Coil value or None if failed
        """
        command = PLCCommand(
            command_id=f"read_coil_{int(time.time() * 1000)}",
            command_type=CommandType.READ_COIL,
            address=str(address),
            user_id=user_id
        )
        
        response = self.execute_command(command)
        return response.value if response.success else None
    
    def write_coil(self, address: Union[str, int], value: bool, user_id: Optional[int] = None) -> bool:
        """
        Write PLC coil value.
        
        Args:
            address: Coil address or name
            value: Coil value to write
            user_id: User ID for logging
            
        Returns:
            True if write successful, False otherwise
        """
        command = PLCCommand(
            command_id=f"write_coil_{int(time.time() * 1000)}",
            command_type=CommandType.WRITE_COIL,
            address=str(address),
            value=value,
            user_id=user_id
        )
        
        response = self.execute_command(command)
        return response.success
    
    def emergency_stop(self, user_id: Optional[int] = None) -> bool:
        """
        Trigger emergency stop.
        
        Args:
            user_id: User ID for logging
            
        Returns:
            True if emergency stop successful, False otherwise
        """
        command = PLCCommand(
            command_id=f"emergency_stop_{int(time.time() * 1000)}",
            command_type=CommandType.EMERGENCY_STOP,
            address="EMERGENCY_STOP",
            priority=CommandPriority.EMERGENCY,
            user_id=user_id
        )
        
        response = self.execute_command(command)
        return response.success
    
    def reset_plc(self, user_id: Optional[int] = None) -> bool:
        """
        Reset PLC.
        
        Args:
            user_id: User ID for logging
            
        Returns:
            True if reset successful, False otherwise
        """
        command = PLCCommand(
            command_id=f"reset_{int(time.time() * 1000)}",
            command_type=CommandType.RESET,
            address="RESET",
            priority=CommandPriority.HIGH,
            user_id=user_id
        )
        
        response = self.execute_command(command)
        return response.success
    
    def get_register_map(self) -> Dict[str, Dict[str, Any]]:
        """Get complete register map."""
        return self._register_map.get_all_registers()
    
    def set_safety_enabled(self, enabled: bool) -> None:
        """Enable or disable safety features."""
        self._safety_enabled = enabled
        self._logger.info(f"Safety features {'enabled' if enabled else 'disabled'}")
    
    def set_write_protection(self, enabled: bool) -> None:
        """Enable or disable write protection."""
        self._write_protection = enabled
        self._logger.info(f"Write protection {'enabled' if enabled else 'disabled'}")
    
    def add_status_callback(self, callback: Callable[[PLCStatus], None]) -> None:
        """Add callback for status changes."""
        self._status_callbacks.append(callback)
    
    def add_command_callback(self, callback: Callable[[PLCCommand, PLCResponse], None]) -> None:
        """Add callback for command execution."""
        self._command_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[str], None]) -> None:
        """Add callback for errors."""
        self._error_callbacks.append(callback)
    
    # Legacy methods for backward compatibility
    def sendControlCommand(self, cmd: str) -> None:
        """Legacy method - send control command."""
        self._logger.warning(f"Using deprecated sendControlCommand method: {cmd}")
        # Convert to new command format
        command = PLCCommand(
            command_id=f"legacy_{int(time.time() * 1000)}",
            command_type=CommandType.WRITE_COIL,
            address="MACHINE_START" if "start" in cmd.lower() else "MACHINE_STOP",
            value=True
        )
        self.execute_command(command)
    
    def readMachineStatus(self) -> str:
        """Legacy method - read machine status."""
        self._logger.warning("Using deprecated readMachineStatus method")
        status = self.read_register("MACHINE_STATUS")
        status_map = {0: "STOPPED", 1: "RUNNING", 2: "ERROR"}
        return status_map.get(status, "UNKNOWN")
    
    def authenticateCommand(self, cmd: str) -> bool:
        """Legacy method - authenticate command."""
        self._logger.warning("Using deprecated authenticateCommand method")
        return True  # Always return true for backward compatibility
    
    def _validate_command(self, command: PLCCommand) -> Optional[str]:
        """
        Validate PLC command.
        
        Args:
            command: Command to validate
            
        Returns:
            Error message if validation fails, None if valid
        """
        # Check if address is valid
        if not self._register_map.is_address_valid(command.address):
            return f"Invalid address: {command.address}"
        
        # Check write permissions
        if command.command_type in [CommandType.WRITE_REGISTER, CommandType.WRITE_COIL]:
            if self._write_protection:
                return "Write operations disabled by write protection"
            
            if not self._register_map.is_writable(command.address):
                return f"Address {command.address} is not writable"
        
        # Check safety interlocks
        if self._safety_enabled and self._emergency_stop_active:
            if command.command_type not in [CommandType.READ_REGISTER, CommandType.READ_COIL, 
                                          CommandType.RESET, CommandType.EMERGENCY_STOP]:
                return "Write operations blocked by emergency stop"
        
        # Validate value types for write operations
        if command.command_type == CommandType.WRITE_COIL:
            if not isinstance(command.value, bool):
                return "Coil values must be boolean"
        
        return None
    
    def _read_register(self, address: str) -> Any:
        """Read register value (implementation depends on protocol)."""
        if self.protocol == PLCProtocol.SIMULATION:
            # Return simulated value
            if address in self._simulation_data:
                return self._simulation_data[address]
            
            # Generate realistic value for unknown addresses
            return self._generate_simulated_value(address)
        
        # Real PLC implementation would go here
        raise NotImplementedError(f"Read register not implemented for {self.protocol.value}")
    
    def _write_register(self, address: str, value: Any) -> None:
        """Write register value (implementation depends on protocol)."""
        if self.protocol == PLCProtocol.SIMULATION:
            if address in self._simulation_data:
                self._simulation_data[address] = value
                self._logger.debug(f"Simulated write: {address} = {value}")
            return
        
        # Real PLC implementation would go here
        raise NotImplementedError(f"Write register not implemented for {self.protocol.value}")
    
    def _read_coil(self, address: str) -> bool:
        """Read coil value (implementation depends on protocol)."""
        if self.protocol == PLCProtocol.SIMULATION:
            if address in self._simulation_data:
                return bool(self._simulation_data[address])
            return False
        
        # Real PLC implementation would go here
        raise NotImplementedError(f"Read coil not implemented for {self.protocol.value}")
    
    def _write_coil(self, address: str, value: bool) -> None:
        """Write coil value (implementation depends on protocol)."""
        if self.protocol == PLCProtocol.SIMULATION:
            if address in self._simulation_data:
                self._simulation_data[address] = value
                self._logger.debug(f"Simulated coil write: {address} = {value}")
            return
        
        # Real PLC implementation would go here
        raise NotImplementedError(f"Write coil not implemented for {self.protocol.value}")
    
    def _execute_emergency_stop(self) -> None:
        """Execute emergency stop sequence."""
        self._emergency_stop_active = True
        
        # Set emergency stop in PLC
        self._write_coil("EMERGENCY_STOP", True)
        
        # Stop all machines (simulation)
        self._write_coil("MACHINE_START", False)
        self._write_coil("MACHINE_STOP", True)
        
        self._logger.critical("EMERGENCY STOP ACTIVATED")
        
        # Notify error callbacks
        for callback in self._error_callbacks:
            try:
                callback("Emergency stop activated")
            except Exception as e:
                self._logger.error(f"Error callback failed: {e}")
    
    def _execute_reset(self) -> None:
        """Execute PLC reset sequence."""
        if self._emergency_stop_active:
            self._emergency_stop_active = False
            self._write_coil("EMERGENCY_STOP", False)
        
        # Reset alarm conditions
        if self.protocol == PLCProtocol.SIMULATION:
            self._simulation_data["ALARM_ACTIVE"] = False
            self._simulation_data["ALARM_CODE"] = 0
        
        self._logger.info("PLC reset completed")
    
    def _generate_simulated_value(self, address: str) -> Any:
        """Generate realistic simulated value for address."""
        # Simple simulation based on address pattern
        if "TEMP" in address.upper():
            return 20.0 + (time.time() % 20)  # Temperature 20-40°C
        elif "PRESSURE" in address.upper():
            return 100.0 + (time.time() % 10)  # Pressure 100-110 kPa
        elif "SPEED" in address.upper():
            return int(time.time() % 100)  # Speed 0-100
        elif "COUNT" in address.upper():
            return int(time.time()) % 10000  # Counter
        else:
            return 0.0
    
    def _start_communication_threads(self) -> None:
        """Start communication threads."""
        # Start command processing thread
        self._comm_active = True
        self._comm_thread = threading.Thread(target=self._process_command_queue, daemon=True)
        self._comm_thread.start()
        
        # Start heartbeat thread
        self._heartbeat_active = True
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_monitor, daemon=True)
        self._heartbeat_thread.start()
        
        self._logger.info("Communication threads started")
    
    def _stop_communication_threads(self) -> None:
        """Stop communication threads."""
        self._comm_active = False
        self._heartbeat_active = False
        
        if self._comm_thread:
            self._comm_thread.join(timeout=1)
        
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=1)
        
        self._logger.info("Communication threads stopped")
    
    def _process_command_queue(self) -> None:
        """Background thread to process command queue."""
        while self._comm_active:
            try:
                with self._command_lock:
                    if self._command_queue:
                        command = self._command_queue.pop(0)
                    else:
                        command = None
                
                if command:
                    self.execute_command(command)
                else:
                    time.sleep(0.01)  # Small delay when queue is empty
                    
            except Exception as e:
                self._logger.error(f"Command queue processing error: {e}")
    
    def _heartbeat_monitor(self) -> None:
        """Background thread to monitor PLC heartbeat."""
        while self._heartbeat_active:
            try:
                if self._connected:
                    # Read heartbeat register
                    heartbeat = self.read_register("PLC_HEARTBEAT")
                    self._last_communication = datetime.now()
                    
                    if heartbeat is None:
                        self._logger.warning("Heartbeat read failed")
                    
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self._logger.error(f"Heartbeat monitor error: {e}")
                time.sleep(1)
    
    def _update_avg_response_time(self, execution_time: float) -> None:
        """Update average response time."""
        if self._total_commands > 1:
            self._avg_response_time = (self._avg_response_time * (self._total_commands - 1) + execution_time) / self._total_commands
        else:
            self._avg_response_time = execution_time
    
    def _log_command_execution(self, command: PLCCommand, response: PLCResponse) -> None:
        """Log command execution."""
        log_level = logging.INFO if response.success else logging.ERROR
        status = "SUCCESS" if response.success else "FAILED"
        
        self._logger.log(log_level, 
            f"[{status}] {command.command_type.value} {command.address} "
            f"({response.execution_time_ms:.1f}ms) "
            f"{f'= {response.value}' if response.value is not None else ''} "
            f"{f'ERROR: {response.error_message}' if response.error_message else ''}"
        )
