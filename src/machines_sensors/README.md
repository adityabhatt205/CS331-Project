# Machines & Sensors Module

A comprehensive factory floor system module providing enterprise-grade machine control, sensor monitoring, PLC communication, and network management capabilities.

## Features

### 🏭 Machine Management (`machine.py`)
- **Comprehensive Machine Control**: Production lines, assembly robots, conveyors, and more
- **Status Tracking**: Real-time machine status monitoring with detailed state management
- **Safety Systems**: Multi-level safety controls with emergency stop capabilities
- **Event Logging**: Complete audit trail of machine operations and state changes
- **Performance Monitoring**: Real-time metrics including uptime, efficiency, and cycle counts
- **Threading Support**: Background monitoring and data collection
- **PLC Integration**: Direct integration with PLC controllers for seamless control

**Machine Types Supported:**
- Production Lines
- Assembly Robots
- Conveyors
- Quality Control Stations
- Packaging Systems
- Testing Equipment

**Safety Levels:**
- LOW: Basic safety features
- MEDIUM: Enhanced safety with interlocks
- HIGH: Full safety systems with redundancy
- CRITICAL: Maximum safety for hazardous operations

### 🔧 PLC Controller (`plc_controller.py`)
- **Multi-Protocol Support**: MODBUS TCP, Ethernet/IP, PROFINET, and simulation mode
- **Command Validation**: Comprehensive command validation and safety checks
- **Register Management**: Complete register mapping and access control
- **Priority Queuing**: Command prioritization with emergency handling
- **Background Processing**: Asynchronous command execution and monitoring
- **Safety Features**: Write protection, emergency stop handling, and interlocks
- **Performance Monitoring**: Communication statistics and response time tracking

**Supported Operations:**
- Read/Write Registers
- Read/Write Coils
- Emergency Stop Commands
- System Reset
- Heartbeat Monitoring

### 📊 Sensor System (`sensor.py`)
- **Multi-Type Sensors**: Temperature, pressure, vibration, humidity, and 12+ sensor types
- **Real-Time Monitoring**: Continuous data collection with configurable sampling rates
- **Alert System**: Configurable thresholds with multi-level alerting
- **Data Quality**: Quality metrics and reliability scoring
- **Calibration**: Automatic and manual calibration with drift compensation
- **Trend Analysis**: Statistical analysis and trend detection
- **History Management**: Configurable data retention and storage

**Sensor Types:**
- Temperature
- Pressure
- Vibration
- Humidity
- Flow Rate
- Level
- Proximity
- Motion
- Light
- Sound
- pH
- Conductivity

### 🌐 Sensor Network (`sensor_network.py`)
- **Network Management**: Centralized control of multiple sensors
- **Data Aggregation**: Multiple aggregation methods (average, min, max, median, etc.)
- **Group Management**: Logical sensor grouping with custom aggregation
- **Health Monitoring**: Automatic sensor health checks and failure detection
- **Alert Correlation**: Network-level alert processing and correlation
- **Data Export**: JSON and CSV data export capabilities
- **Performance Metrics**: Network-wide performance monitoring

**Aggregation Methods:**
- Average
- Minimum
- Maximum
- Sum
- Median
- Most Recent

## Installation & Setup

### Prerequisites
- Python 3.8+
- Required packages: `typing`, `enum`, `threading`, `logging`, `datetime`, `dataclasses`
- Optional: `statistics` (for advanced analytics)

### Module Structure
```
machines_sensors/
├── __init__.py          # Module exports and metadata
├── machine.py           # Machine management system
├── sensor.py           # Sensor monitoring system
├── plc_controller.py   # PLC communication system
└── sensor_network.py   # Network management system
```

### Basic Usage

```python
from machines_sensors import (
    Machine, MachineType, MachineStatus,
    Sensor, SensorType,
    PLCController, PLCProtocol,
    SensorNetwork, NetworkConfiguration
)

# Create PLC controller
plc = PLCController(
    plc_id=1,
    name="Main PLC",
    protocol=PLCProtocol.SIMULATION
)

# Create machine
machine = Machine(
    machine_id=1,
    name="Production Line A",
    machine_type=MachineType.PRODUCTION_LINE,
    location="Factory Floor",
    plc_controller=plc
)

# Create sensor
sensor = Sensor(
    sensor_id=101,
    sensor_type=SensorType.TEMPERATURE,
    name="Area Temperature",
    unit="°C",
    location="Production Area"
)

# Start operations
machine.start()
sensor.start_monitoring()

# Read data
reading = sensor.read_data()
print(f"Temperature: {reading.value}°C")

# Get machine status
stats = machine.get_performance_stats()
print(f"Uptime: {stats['uptime_hours']} hours")
```

## Advanced Features

### Machine Management
```python
# Create machine manager for fleet control
from machines_sensors import MachineManager

manager = MachineManager()
manager.add_machine(machine)

# Batch operations
manager.start_all_machines()
manager.emergency_stop_all()
fleet_stats = manager.get_fleet_statistics()
```

### Sensor Network
```python
# Create sensor network
from machines_sensors import NetworkConfiguration, SensorGroup

config = NetworkConfiguration(
    network_id=1,
    name="Factory Network",
    data_retention_hours=24,
    quality_threshold=0.85
)

network = SensorNetwork(config)
network.add_sensor(sensor)

# Create sensor groups
temp_group = SensorGroup(
    group_id="temperature_zone",
    name="Temperature Monitoring",
    sensor_ids={101, 102, 103},
    aggregation_method=DataAggregationMethod.AVERAGE
)

network.create_sensor_group(temp_group)
network.start_network()

# Get aggregated data
group_data = network.get_group_data("temperature_zone")
print(f"Average temperature: {group_data['aggregated_value']}°C")
```

### PLC Communication
```python
# Advanced PLC operations
from machines_sensors import PLCCommand, CommandType, CommandPriority

# Create prioritized command
command = PLCCommand(
    command_id="emergency_001",
    command_type=CommandType.EMERGENCY_STOP,
    address="EMERGENCY_STOP",
    priority=CommandPriority.EMERGENCY
)

# Execute command
response = plc.execute_command(command)
print(f"Command executed: {response.success}")

# Queue commands for batch processing
plc.queue_command(command)
```

## Testing

Run the test suite to verify functionality:

```bash
# Basic functionality test
python test_machines_sensors.py

# Comprehensive demo
python machines_sensors_demo.py
```

## Logging

The module provides comprehensive logging for debugging and monitoring:

```python
import logging

# Configure logging level
logging.basicConfig(level=logging.INFO)

# Module-specific loggers
machine_logger = logging.getLogger("Machine_1")
sensor_logger = logging.getLogger("Sensor_101")
plc_logger = logging.getLogger("PLC_1")
network_logger = logging.getLogger("SensorNetwork_1")
```

## Performance Considerations

- **Threading**: All monitoring operations run in background threads
- **Memory Management**: Configurable data retention and circular buffers
- **Scalability**: Designed to handle hundreds of sensors and machines
- **Error Handling**: Comprehensive exception handling and recovery
- **Resource Cleanup**: Proper resource management and cleanup procedures

## Security Features

- **User Authentication**: Integration with user security system
- **Command Authorization**: Role-based access control for operations
- **Audit Logging**: Complete audit trail of all operations
- **Safety Interlocks**: Multi-level safety systems with emergency controls
- **Data Validation**: Input validation and sanitization

## Integration Examples

### With User Security System
```python
from user_security.user_supervisor import UserSupervisor

supervisor = UserSupervisor()
supervisor.login("supervisor1", "password")

if supervisor.hasPermission("MANAGE_MACHINES"):
    machine.start(user_id=supervisor.getCurrentUser())
```

### With Visualization System
```python
# Export data for visualization
export_data = network.export_sensor_data(
    duration_hours=24,
    format_type="json"
)

# Real-time data streaming
def data_callback(reading):
    # Send to visualization system
    viz_system.update_sensor_data(reading)

sensor.add_reading_callback(data_callback)
```

## API Reference

### Machine Class
- `start(user_id=None)` - Start machine operations
- `stop(user_id=None)` - Stop machine operations
- `emergency_stop(user_id=None)` - Emergency stop
- `get_performance_stats()` - Get performance metrics
- `set_speed(speed, user_id=None)` - Set operating speed
- `add_event_callback(callback)` - Add event listener

### Sensor Class
- `read_data()` - Read current sensor value
- `calibrate(reference_value, user_id=None)` - Calibrate sensor
- `set_thresholds(warn_low, warn_high, crit_low, crit_high)` - Set alert thresholds
- `start_monitoring()` - Start continuous monitoring
- `get_statistics(duration_minutes=60)` - Get sensor statistics
- `add_alert_callback(callback)` - Add alert listener

### PLCController Class
- `connect()` - Connect to PLC
- `execute_command(command)` - Execute PLC command
- `read_register(address, user_id=None)` - Read PLC register
- `write_register(address, value, user_id=None)` - Write PLC register
- `emergency_stop(user_id=None)` - Trigger emergency stop
- `get_register_map()` - Get available registers

### SensorNetwork Class
- `add_sensor(sensor)` - Add sensor to network
- `create_sensor_group(group)` - Create sensor group
- `start_network()` - Start network monitoring
- `get_network_summary()` - Get network status
- `export_sensor_data(duration_hours, format_type)` - Export data
- `calibrate_sensor_group(group_id, reference_values)` - Calibrate group

## Version History

### v1.0.0 (Current)
- Initial comprehensive implementation
- Complete machine management system
- Full sensor monitoring capabilities
- PLC communication system
- Sensor network management
- Integration with user security system
- Comprehensive testing and documentation

## Contributing

This module is part of the Factory Floor System project. Contributions should follow the established patterns and maintain compatibility with the existing user security system.

## License

Part of the Factory Floor System - CS331 Project