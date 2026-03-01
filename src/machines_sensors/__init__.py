"""
Machines and Sensors module for the Factory Floor System.
Provides comprehensive machine control, sensor monitoring, PLC communication, and network management.
"""

# Import core classes for easy access
from .machine import (
    Machine,
    MachineStatus,
    MachineType,
    MachineSafetyLevel,
    MachineEvent,
    MachineManager
)

from .sensor import (
    Sensor,
    SensorType,
    SensorStatus,
    AlertLevel,
    SensorReading,
    SensorAlert
)

from .plc_controller import (
    PLCController,
    PLCStatus,
    CommandType,
    PLCProtocol,
    CommandPriority,
    PLCCommand,
    PLCResponse,
    RegisterMap
)

from .sensor_network import (
    SensorNetwork,
    NetworkStatus,
    DataAggregationMethod,
    NetworkAlert,
    NetworkConfiguration,
    SensorGroup,
    NetworkMetrics
)

# Version information
__version__ = "1.0.0"
__author__ = "Factory Floor System Team"

# Module metadata
__all__ = [
    # Machine classes
    "Machine",
    "MachineStatus",
    "MachineType", 
    "MachineSafetyLevel",
    "MachineEvent",
    "MachineManager",
    
    # Sensor classes
    "Sensor",
    "SensorType",
    "SensorStatus",
    "AlertLevel",
    "SensorReading",
    "SensorAlert",
    
    # PLC classes
    "PLCController",
    "PLCStatus",
    "CommandType",
    "PLCProtocol",
    "CommandPriority",
    "PLCCommand",
    "PLCResponse",
    "RegisterMap",
    
    # Network classes
    "SensorNetwork",
    "NetworkStatus",
    "DataAggregationMethod",
    "NetworkAlert",
    "NetworkConfiguration",
    "SensorGroup",
    "NetworkMetrics"
]

def get_module_info():
    """Get module information and available classes."""
    return {
        "version": __version__,
        "author": __author__,
        "description": "Comprehensive factory floor system for machine control and sensor monitoring",
        "components": {
            "machine": "Machine control with status tracking, safety features, and event logging",
            "sensor": "Sensor data collection with calibration, alerts, and monitoring",
            "plc_controller": "PLC communication with command validation and safety controls",
            "sensor_network": "Network-level sensor management with data aggregation"
        },
        "classes": __all__
    }