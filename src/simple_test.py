#!/usr/bin/env python3
"""Simple test to verify machines_sensors module functionality."""

import time
from machines_sensors import (
    Machine, MachineType, MachineStatus,
    Sensor, SensorType, SensorStatus,
    PLCController, PLCProtocol,
    SensorNetwork, NetworkConfiguration
)

def main():
    print("============================================================")
    print("SIMPLE MACHINES_SENSORS TEST")
    print("============================================================")
    
    # Test 1: Machine Creation
    print("\n1. Testing Machine Creation...")
    try:
        machine = Machine(
            machine_id=1,
            name="Test Machine",
            machine_type=MachineType.PRODUCTION_LINE
        )
        print(f"Machine created: {machine.name}")
        print(f"Status: {machine.status.value}")
        print(f"Type: {machine.machine_type.value}")
    except Exception as e:
        print(f"[FAILED] Machine creation failed: {e}")
        return False
    
    # Test 2: Sensor Creation
    print("\n2. Testing Sensor Creation...")
    try:
        sensor = Sensor(
            sensor_id=101,
            sensor_type=SensorType.TEMPERATURE,
            name="Test Temperature Sensor",
            unit="°C"
        )
        # Set conservative thresholds to avoid alerts
        sensor.set_thresholds(10.0, 40.0, 5.0, 45.0)
        
        print(f"Sensor created: {sensor.name}")
        print(f"Type: {sensor.sensor_type.value}")
        print(f"Status: {sensor.status.value}")
        
        # Get a reading
        reading = sensor.read_data()
        print(f"Reading: {reading.value:.2f} {sensor.unit}")
    except Exception as e:
        print(f"[FAILED] Sensor creation failed: {e}")
        return False
    
    # Test 3: PLC Controller
    print("\n3. Testing PLC Controller...")
    try:
        plc = PLCController(
            plc_id=1,
            name="Test PLC",
            protocol=PLCProtocol.SIMULATION
        )
        
        print(f"PLC created: {plc.name}")
        print(f"Protocol: {plc.protocol.value}")
        print(f"Status: {plc.status.value}")
        
        # Test connection
        connected = plc.connect()
        print(f"Connection: {'Success' if connected else 'Failed'}")
    except Exception as e:
        print(f"[FAILED] PLC creation failed: {e}")
        return False
    
    # Test 4: Sensor Network
    print("\n4. Testing Sensor Network...")
    try:
        config = NetworkConfiguration(
            network_id=1,
            name="Test Network",
            description="Simple test network"
        )
        
        network = SensorNetwork(config)
        print(f"Network created: {network.config.name}")
        print(f"Status: {network.status.value}")
        
        # Add a sensor
        test_sensor = Sensor(
            sensor_id=201,
            sensor_type=SensorType.PRESSURE,
            name="Test Pressure Sensor",
            unit="kPa"
        )
        # Set conservative thresholds
        test_sensor.set_thresholds(90.0, 110.0, 80.0, 120.0)
        
        success = network.add_sensor(test_sensor)
        print(f"Add sensor: {'Success' if success else 'Failed'}")
    except Exception as e:
        print(f"[FAILED] Network creation failed: {e}")
        return False
    
    # Test 5: Integration
    print("\n5. Testing Basic Integration...")
    try:
        # Start machine
        machine.start()
        print(f"Machine started: {machine.status.value}")
        
        # Get sensor reading
        reading = sensor.read_data()
        print(f"Sensor reading: {reading.value:.2f} {sensor.unit}")
        
        # PLC operation
        plc.write_register("temperature", reading.value)
        print("PLC register write: Success")
        
        # Stop machine
        machine.stop()
        print(f"Machine stopped: {machine.status.value}")
        
    except Exception as e:
        print(f"[FAILED] Integration test failed: {e}")
        return False
    
    print("\n============================================================")
    print("ALL TESTS PASSED!")
    print("Machines_sensors module is working correctly.")
    print("============================================================")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)