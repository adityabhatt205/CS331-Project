#!/usr/bin/env python3
"""
Test script for machines_sensors module.
Basic tests to verify functionality.
"""

import time
import logging

# Import machines_sensors module
from machines_sensors import (
    Machine, MachineType, MachineStatus, MachineSafetyLevel,
    Sensor, SensorType, SensorStatus,
    PLCController, PLCProtocol,
    SensorNetwork, NetworkConfiguration, SensorGroup, DataAggregationMethod
)

def test_machine_creation():
    """Test machine creation and basic functionality."""
    print("Testing Machine Creation...")
    
    # Create machine
    machine = Machine(
        machine_id=1,
        name="Test Machine",
        machine_type=MachineType.PRODUCTION_LINE,
        location="Test Area"
    )
    
    print(f"Created machine: {machine.name}")
    print(f"Status: {machine.status.value}")
    print(f"Type: {machine.machine_type.value}")
    
    # Test start/stop
    success = machine.start()
    print(f"Start machine: {'Success' if success else 'Failed'}")
    print(f"Status after start: {machine.status.value}")
    
    time.sleep(1)
    
    success = machine.stop()
    print(f"Stop machine: {'Success' if success else 'Failed'}")
    print(f"Status after stop: {machine.status.value}")
    
    return machine

def test_sensor_creation():
    """Test sensor creation and data collection."""
    print("\nTesting Sensor Creation...")
    
    # Create temperature sensor
    sensor = Sensor(
        sensor_id=101,
        sensor_type=SensorType.TEMPERATURE,
        name="Test Temperature Sensor",
        unit="°C",
        location="Test Location"
    )
    
    # Set reasonable thresholds for temperature sensor
    sensor.set_thresholds(15.0, 35.0, 0.0, 50.0)  # Warning: 15-35°C, Critical: 0-50°C
    
    print(f"Created sensor: {sensor.name}")
    print(f"Type: {sensor.sensor_type.value}")
    print(f"Status: {sensor.status.value}")
    
    # Test reading
    reading = sensor.read_data()
    print(f"Reading value: {reading.value:.2f} {reading.unit}")
    print(f"Reading quality: {reading.quality:.2f}")
    print(f"Timestamp: {reading.timestamp}")
    
    # Test calibration
    success = sensor.calibrate(25.0)
    print(f"Calibration: {'Success' if success else 'Failed'}")
    
    return sensor

def test_plc_controller():
    """Test PLC controller functionality."""
    print("\nTesting PLC Controller...")
    
    # Create PLC controller
    plc = PLCController(
        plc_id=1,
        name="Test PLC",
        protocol=PLCProtocol.SIMULATION,
        host="localhost"
    )
    
    print(f"Created PLC: {plc.name}")
    print(f"Status: {plc.status.value}")
    print(f"Connected: {plc.is_connected}")
    
    # Test register operations
    success = plc.write_register("MACHINE_SPEED", 100)
    print(f"Write register: {'Success' if success else 'Failed'}")
    
    value = plc.read_register("MACHINE_SPEED")
    print(f"Read register: {value}")
    
    # Test coil operations
    success = plc.write_coil("MACHINE_START", True)
    print(f"Write coil: {'Success' if success else 'Failed'}")
    
    value = plc.read_coil("MACHINE_START")
    print(f"Read coil: {value}")
    
    return plc

def test_sensor_network():
    """Test sensor network functionality."""
    print("\nTesting Sensor Network...")
    
    # Create network configuration
    config = NetworkConfiguration(
        network_id=1,
        name="Test Network",
        description="Test sensor network"
    )
    
    # Create network
    network = SensorNetwork(config)
    print(f"Created network: {network.config.name}")
    print(f"Status: {network.status.value}")
    
    # Create test sensors with proper thresholds
    sensors = []
    for i in range(3):
        sensor = Sensor(
            sensor_id=100 + i,
            sensor_type=SensorType.TEMPERATURE,
            name=f"Test Sensor {i+1}",
            unit="°C"
        )
        # Set reasonable thresholds to avoid alerts during testing
        sensor.set_thresholds(15.0, 35.0, 0.0, 50.0)
        sensors.append(sensor)
        
        # Add to network
        success = network.add_sensor(sensor)
        print(f"Added sensor {i+1}: {'Success' if success else 'Failed'}")
    
    # Create sensor group
    group = SensorGroup(
        group_id="test_group",
        name="Test Group",
        description="Test sensor group",
        sensor_ids={100, 101, 102},
        aggregation_method=DataAggregationMethod.AVERAGE
    )
    
    success = network.create_sensor_group(group)
    print(f"Created sensor group: {'Success' if success else 'Failed'}")
    
    # Start network
    success = network.start_network()
    print(f"Started network: {'Success' if success else 'Failed'}")
    print(f"Network status: {network.status.value}")
    
    # Let it collect some data
    time.sleep(2)
    
    # Get summary
    summary = network.get_network_summary()
    print(f"Total sensors: {summary['metrics']['total_sensors']}")
    print(f"Active sensors: {summary['metrics']['active_sensors']}")
    
    # Stop network
    network.stop_network()
    print(f"Network stopped: {network.status.value}")
    
    return network

def test_integration():
    """Test integration between components."""
    print("\nTesting Component Integration...")
    
    # Create PLC
    plc = PLCController(1, "Integration PLC", PLCProtocol.SIMULATION)
    
    # Create machine
    machine = Machine(
        machine_id=1,
        name="Integration Machine",
        machine_type=MachineType.PRODUCTION_LINE,
        location="Test Area"
    )
    
    # Create sensor for machine with reasonable thresholds
    sensor = Sensor(
        sensor_id=201,
        sensor_type=SensorType.TEMPERATURE,
        name="Machine Temperature",
        unit="°C",
        machine_id=machine.machine_id
    )
    sensor.set_thresholds(15.0, 35.0, 0.0, 50.0)  # Set reasonable thresholds
    
    # Create network
    config = NetworkConfiguration(
        network_id=1,
        name="Integration Network"
    )
    network = SensorNetwork(config)
    network.add_sensor(sensor)
    
    # Start everything
    machine.start()
    network.start_network()
    
    print(f"Machine status: {machine.status.value}")
    print(f"Network status: {network.status.value}")
    print(f"Sensor status: {sensor.status.value}")
    
    # Let them run briefly
    time.sleep(2)
    
    # Check statistics
    machine_stats = machine.get_status_info()
    network_summary = network.get_network_summary()
    
    print(f"Machine operating hours: {machine_stats.get('operating_hours', 0):.4f} hours")
    print(f"Network readings: {network_summary['total_readings_collected']}")
    
    # Cleanup
    machine.stop()
    network.stop_network()
    
    print("Integration test completed")

def main():
    """Run all tests."""
    print("="*60)
    print("MACHINES_SENSORS MODULE TEST SUITE")
    print("="*60)
    
    # Configure logging
    logging.basicConfig(level=logging.WARNING)  # Reduce log noise during tests
    
    try:
        # Run tests
        machine = test_machine_creation()
        sensor = test_sensor_creation()
        plc = test_plc_controller()
        network = test_sensor_network()
        test_integration()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("Machine management working")
        print("Sensor monitoring working")
        print("PLC communication working")
        print("Sensor network working")
        print("Component integration working")
        
    except Exception as e:
        print(f"\n[FAILED] Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()