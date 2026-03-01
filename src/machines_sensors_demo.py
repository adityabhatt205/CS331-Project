#!/usr/bin/env python3
"""
Demo script for the Factory Floor System - Machines and Sensors Module.
Demonstrates the comprehensive machines_sensors module functionality.
"""

import logging
import time
from datetime import datetime, timedelta

# Import machine and sensor modules
from machines_sensors import (
    Machine, MachineType, MachineStatus, MachineSafetyLevel,
    Sensor, SensorType, SensorStatus,
    PLCController, PLCProtocol,
    SensorNetwork, NetworkConfiguration, SensorGroup, DataAggregationMethod
)

# Import user security modules
from user_security import auth_manager, Permission

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('factory_demo.log')
        ]
    )

def demo_user_security():
    """Demonstrate user security system."""
    print("\n" + "="*60)
    print("FACTORY FLOOR SYSTEM - USER SECURITY DEMO")
    print("="*60)
    
    # Test authentication with default users
    print("\n1. Testing Authentication...")
    
    # Admin login
    admin_session = auth_manager.authenticate_user("admin", "admin123", "127.0.0.1")
    if admin_session:
        print("✓ Admin authentication successful")
        print(f"  Session ID: {admin_session}")
    else:
        print("✗ Admin authentication failed")
    
    # Supervisor login
    supervisor_session = auth_manager.authenticate_user("supervisor", "super123", "127.0.0.1")
    if supervisor_session:
        print("✓ Supervisor authentication successful") 
        print(f"  Session ID: {supervisor_session}")
    else:
        print("✗ Supervisor authentication failed")
    
    # Operator login
    operator_session = auth_manager.authenticate_user("operator", "op123", "127.0.0.1")
    if operator_session:
        print("✓ Operator authentication successful")
        print(f"  Session ID: {operator_session}")
    else:
        print("✗ Operator authentication failed")
    
    # Test permissions
    print("\n2. Testing Permissions...")
    
    # Admin permissions
    if auth_manager.check_permission(admin_session, Permission.CREATE_USER):
        print("✓ Admin can create users")
    
    if auth_manager.check_permission(admin_session, Permission.START_MACHINE):
        print("✓ Admin can start machines")
    
    # Supervisor permissions
    if auth_manager.check_permission(supervisor_session, Permission.START_MACHINE):
        print("✓ Supervisor can start machines")
    
    if not auth_manager.check_permission(supervisor_session, Permission.CREATE_USER):
        print("✓ Supervisor cannot create users (correct restriction)")
    
    # Operator permissions
    if not auth_manager.check_permission(operator_session, Permission.START_MACHINE):
        print("✓ Operator cannot start machines (correct restriction)")
    
    if auth_manager.check_permission(operator_session, Permission.VIEW_SENSOR_DATA):
        print("✓ Operator can view sensor data")
    
    # Display system stats
    print("\n3. System Statistics...")
    stats = auth_manager.get_system_stats()
    print(f"Total users: {stats['total_users']}")
    print(f"Active sessions: {stats['active_sessions']}")
    print(f"Logged in users: {stats['logged_in_users']}")
    print(f"Total audit logs: {stats['total_audit_logs']}")
    
    return admin_session, supervisor_session, operator_session

def demo_machine_management(admin_session, supervisor_session):
    """Demonstrate machine management system."""
    print("\n" + "="*60)
    print("MACHINE MANAGEMENT DEMO")
    print("="*60)
    
    # Create PLC controller
    print("\n1. Initializing PLC Controller...")
    plc = PLCController(
        plc_id=1,
        name="Main Factory PLC",
        protocol=PLCProtocol.SIMULATION,
        host="192.168.1.100"
    )
    
    print(f"PLC Status: {plc.status.value}")
    print(f"PLC Connected: {plc.is_connected}")
    
    # Create machines
    print("\n2. Creating Factory Machines...")
    
    # Production machine
    production_machine = Machine(
        machine_id=1,
        machine_type=MachineType.PRODUCTION_LINE,
        name="Production Line A",
        location="Factory Floor Zone A"
    )
    
    # Assembly machine
    assembly_machine = Machine(
        machine_id=2,
        machine_type=MachineType.ASSEMBLY_ROBOT,
        name="Assembly Robot 1",
        location="Factory Floor Zone B",
        safety_level=MachineSafetyLevel.HIGH
    )
    
    # Conveyor system
    conveyor_machine = Machine(
        machine_id=3,
        machine_type=MachineType.CONVEYOR,
        name="Main Conveyor",
        location="Factory Floor Main Line",
        safety_level=MachineSafetyLevel.MEDIUM
    )
    
    machines = [production_machine, assembly_machine, conveyor_machine]
    
    for machine in machines:
        print(f"Created machine: {machine.name} ({machine.machine_type.value})")
        print(f"  Status: {machine.status.value}")
        print(f"  Safety Level: {machine.safety_level.value}")
    
    # Start machines
    print("\n3. Starting Machines...")
    for machine in machines:
        if auth_manager.check_permission(supervisor_session, Permission.START_MACHINE):
            success = machine.start()  # Remove user_id parameter
            print(f"Started {machine.name}: {'✓' if success else '✗'}")
            time.sleep(1)
    
    # Monitor machine operations
    print("\n4. Machine Operations...")
    time.sleep(2)
    
    for machine in machines:
        stats = machine.get_status_info()
        print(f"\n{machine.name} Status:")
        print(f"  Status: {stats['status']}")
        print(f"  Operating Hours: {stats['operating_hours']:.2f} hours")
        print(f"  Current Speed: {stats['speed']:.1f}%")
        print(f"  Safety Level: {stats['safety_level']}")
        print(f"  Cycle Count: {stats['cycle_count']}")
    
    # Test emergency stop
    print("\n5. Testing Emergency Stop...")
    if auth_manager.check_permission(supervisor_session, Permission.EMERGENCY_STOP):
        success = assembly_machine.emergency_stop()  # Remove user_id parameter
        print(f"Emergency stop executed: {'✓' if success else '✗'}")
        print(f"Assembly machine status: {assembly_machine.status.value}")
    
    return machines, plc

def demo_sensor_system():
    """Demonstrate sensor monitoring system."""
    print("\n" + "="*60)
    print("SENSOR MONITORING DEMO")
    print("="*60)
    
    # Create sensors
    print("\n1. Creating Factory Sensors...")
    
    # Temperature sensors
    temp_sensor_1 = Sensor(
        sensor_id=101,
        sensor_type=SensorType.TEMPERATURE,
        name="Production Area Temp 1",
        unit="°C",
        location="Zone A",
        machine_id=1
    )
    
    temp_sensor_2 = Sensor(
        sensor_id=102,
        sensor_type=SensorType.TEMPERATURE,
        name="Production Area Temp 2", 
        unit="°C",
        location="Zone B",
        machine_id=2
    )
    
    # Pressure sensor
    pressure_sensor = Sensor(
        sensor_id=201,
        sensor_type=SensorType.PRESSURE,
        name="Hydraulic Pressure",
        unit="kPa",
        location="Hydraulic System",
        machine_id=2
    )
    
    # Vibration sensor
    vibration_sensor = Sensor(
        sensor_id=301,
        sensor_type=SensorType.VIBRATION,
        name="Motor Vibration",
        unit="mm/s",
        location="Main Motor",
        machine_id=1
    )
    
    sensors = [temp_sensor_1, temp_sensor_2, pressure_sensor, vibration_sensor]
    
    for sensor in sensors:
        print(f"Created sensor: {sensor.name} ({sensor.sensor_type.value})")
        print(f"  Location: {sensor.location}")
        print(f"  Status: {sensor.status.value}")
    
    # Set sensor thresholds
    print("\n2. Configuring Sensor Thresholds...")
    temp_sensor_1.set_thresholds(15.0, 35.0, 10.0, 40.0)  # °C
    temp_sensor_2.set_thresholds(15.0, 35.0, 10.0, 40.0)  # °C
    pressure_sensor.set_thresholds(90.0, 110.0, 80.0, 120.0)  # kPa
    vibration_sensor.set_thresholds(1.0, 5.0, 0.5, 8.0)  # mm/s
    
    # Start sensor monitoring
    print("\n3. Starting Sensor Monitoring...")
    for sensor in sensors:
        sensor.start_monitoring()
        print(f"Started monitoring: {sensor.name}")
    
    # Collect some readings
    print("\n4. Collecting Sensor Data...")
    time.sleep(3)
    
    for sensor in sensors:
        reading = sensor.read_data()
        print(f"\n{sensor.name}:")
        print(f"  Value: {reading.value:.2f} {reading.unit}")
        print(f"  Quality: {reading.quality:.2f}")
        print(f"  Timestamp: {reading.timestamp}")
        
        # Check alerts
        alerts = sensor.active_alerts
        if alerts:
            print(f"  Active Alerts: {len(alerts)}")
            for alert in alerts:
                print(f"    - {alert.level.value}: {alert.message}")
    
    return sensors

def demo_sensor_network(sensors):
    """Demonstrate sensor network management."""
    print("\n" + "="*60)
    print("SENSOR NETWORK DEMO")
    print("="*60)
    
    # Create network configuration
    print("\n1. Creating Sensor Network...")
    network_config = NetworkConfiguration(
        network_id=1,
        name="Factory Floor Sensor Network",
        description="Main production area sensor monitoring",
        data_retention_hours=24,
        health_check_interval=30,
        quality_threshold=0.8
    )
    
    # Create sensor network
    sensor_network = SensorNetwork(network_config)
    
    # Add sensors to network
    print("\n2. Adding Sensors to Network...")
    for sensor in sensors:
        success = sensor_network.add_sensor(sensor)
        print(f"Added sensor {sensor.name}: {'✓' if success else '✗'}")
    
    # Create sensor groups
    print("\n3. Creating Sensor Groups...")
    
    # Temperature group
    temp_group = SensorGroup(
        group_id="temperature_zone",
        name="Temperature Monitoring",
        description="All temperature sensors",
        sensor_ids={101, 102},
        aggregation_method=DataAggregationMethod.AVERAGE
    )
    
    # Machine monitoring group
    machine_group = SensorGroup(
        group_id="machine_monitoring", 
        name="Machine Health",
        description="Critical machine sensors",
        sensor_ids={201, 301},
        aggregation_method=DataAggregationMethod.MAXIMUM
    )
    
    network_groups = [temp_group, machine_group]
    for group in network_groups:
        success = sensor_network.create_sensor_group(group)
        print(f"Created group '{group.name}': {'✓' if success else '✗'}")
    
    # Start network monitoring
    print("\n4. Starting Network Monitoring...")
    success = sensor_network.start_network()
    print(f"Network started: {'✓' if success else '✗'}")
    print(f"Network status: {sensor_network.status.value}")
    
    # Let the network collect some data
    time.sleep(5)
    
    # Get network summary
    print("\n5. Network Summary...")
    summary = sensor_network.get_network_summary()
    print(f"Total sensors: {summary['metrics']['total_sensors']}")
    print(f"Active sensors: {summary['metrics']['active_sensors']}")
    print(f"Average data quality: {summary['metrics']['avg_data_quality']:.2f}")
    print(f"Total readings collected: {summary['total_readings_collected']}")
    
    # Get group data
    print("\n6. Sensor Group Data...")
    for group_id in ["temperature_zone", "machine_monitoring"]:
        group_data = sensor_network.get_group_data(group_id, duration_minutes=10)
        if group_data and "error" not in group_data:
            print(f"\n{group_data['group_name']}:")
            print(f"  Aggregated Value: {group_data['aggregated_value']:.2f}")
            print(f"  Reading Count: {group_data['reading_count']}")
            print(f"  Average Quality: {group_data['avg_quality']:.2f}")
            print(f"  Aggregation Method: {group_data['aggregation_method']}")
    
    # Analyze sensor trends
    print("\n7. Sensor Trend Analysis...")
    for sensor in sensors[:2]:  # Analyze first two sensors
        trends = sensor_network.get_sensor_data_trends(sensor.sensor_id, duration_minutes=10)
        if trends and "error" not in trends:
            print(f"\n{trends['sensor_name']} Trends:")
            print(f"  Trend Direction: {trends['trend_direction']}")
            print(f"  Average Value: {trends['avg_value']:.2f}")
            print(f"  Min/Max: {trends['min_value']:.2f} / {trends['max_value']:.2f}")
            print(f"  Standard Deviation: {trends['std_deviation']:.2f}")
    
    return sensor_network

def demo_integrated_operations(machines, sensors, sensor_network, admin_session, supervisor_session):
    """Demonstrate integrated factory operations."""
    print("\n" + "="*60)
    print("INTEGRATED FACTORY OPERATIONS DEMO")
    print("="*60)
    
    # Simulate production scenario
    print("\n1. Simulating Production Scenario...")
    
    # Check machine states
    print("\nMachine Status Check:")
    for machine in machines:
        print(f"  {machine.name}: {machine.status.value}")
        if machine.status == MachineStatus.STOPPED:
            # Restart stopped machines
            if auth_manager.check_permission(admin_session, Permission.START_MACHINE):
                machine.start()  # Remove user_id parameter
                print(f"    Restarted by admin")
    
    # Monitor for alerts
    print("\n2. Alert Monitoring...")
    time.sleep(3)
    
    # Check for sensor alerts
    total_alerts = 0
    for sensor in sensors:
        alerts = sensor.active_alerts
        if alerts:
            total_alerts += len(alerts)
            print(f"\n{sensor.name} Alerts:")
            for alert in alerts:
                print(f"  {alert.level.value}: {alert.message}")
    
    # Check network alerts
    network_summary = sensor_network.get_network_summary()
    network_alerts = network_summary.get('recent_alerts', [])
    if network_alerts:
        print(f"\nNetwork Alerts ({len(network_alerts)}):")
        for alert in network_alerts[-5:]:  # Show last 5
            print(f"  {alert.get('level', 'INFO')}: {alert.get('message', 'No message')}")
    
    print(f"\nTotal active alerts: {total_alerts + len(network_alerts)}")
    
    # Performance summary
    print("\n3. Performance Summary...")
    
    # Machine performance
    total_uptime = 0
    total_efficiency = 0
    machine_count = 0
    
    for machine in machines:
        if machine.status in [MachineStatus.RUNNING, MachineStatus.STOPPED]:
            stats = machine.get_status_info()
            total_uptime += stats['operating_hours']
            total_efficiency += 90  # Default efficiency value
            machine_count += 1
    
    avg_uptime = total_uptime / machine_count if machine_count > 0 else 0
    avg_efficiency = total_efficiency / machine_count if machine_count > 0 else 0
    
    print(f"Average Machine Uptime: {avg_uptime:.2f} hours")
    print(f"Average Machine Efficiency: {avg_efficiency:.1f}%")
    
    # Network performance
    network_metrics = sensor_network.network_metrics
    print(f"Network Uptime: {network_metrics.network_uptime:.1f}%")
    print(f"Average Data Quality: {network_metrics.avg_data_quality:.2f}")
    print(f"Active Sensors: {network_metrics.active_sensors}/{network_metrics.total_sensors}")
    
    # Export data
    print("\n4. Exporting Data...")
    export_data = sensor_network.export_sensor_data(duration_hours=1, format_type="json")
    if export_data:
        print(f"Exported sensor data: {len(export_data)} characters")
        # In a real system, this would be saved to a file
    
    return {
        "total_alerts": total_alerts + len(network_alerts),
        "avg_machine_uptime": avg_uptime,
        "avg_efficiency": avg_efficiency,
        "network_uptime": network_metrics.network_uptime,
        "data_quality": network_metrics.avg_data_quality
    }

def cleanup_demo(machines, sensors, sensor_network):
    """Clean up demo resources."""
    print("\n" + "="*60)
    print("DEMO CLEANUP")
    print("="*60)
    
    # Stop sensor monitoring
    print("\nStopping sensors...")
    for sensor in sensors:
        sensor.stop_monitoring()
        print(f"Stopped: {sensor.name}")
    
    # Stop network monitoring
    print("\nStopping sensor network...")
    sensor_network.stop_network()
    print(f"Network status: {sensor_network.status.value}")
    
    # Stop machines
    print("\nStopping machines...")
    for machine in machines:
        machine.stop()
        print(f"Stopped: {machine.name} - Status: {machine.status.value}")
    
    print("\nDemo cleanup completed!")

def main():
    """Main demo function."""
    setup_logging()
    
    print("FACTORY FLOOR SYSTEM - COMPREHENSIVE DEMO")
    print("Starting demonstration of all system components...")
    
    try:
        # Demo user security
        admin_session, supervisor_session, operator_session = demo_user_security()
        
        # Demo machine management
        machines, plc = demo_machine_management(admin_session, supervisor_session)
        
        # Demo sensor system
        sensors = demo_sensor_system()
        
        # Demo sensor network
        sensor_network = demo_sensor_network(sensors)
        
        # Demo integrated operations
        results = demo_integrated_operations(machines, sensors, sensor_network, admin_session, supervisor_session)
        
        # Final results
        print("\n" + "="*60)
        print("DEMO RESULTS SUMMARY")
        print("="*60)
        print(f"Total Alerts Generated: {results['total_alerts']}")
        print(f"Average Machine Uptime: {results['avg_machine_uptime']:.2f} hours")
        print(f"Average Machine Efficiency: {results['avg_efficiency']:.1f}%")
        print(f"Network Uptime: {results['network_uptime']:.1f}%")
        print(f"Data Quality: {results['data_quality']:.2f}")
        
        # Keep demo running for observation
        print(f"\nDemo running... Press Ctrl+C to stop")
        time.sleep(10)
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        if 'machines' in locals() and 'sensors' in locals() and 'sensor_network' in locals():
            cleanup_demo(machines, sensors, sensor_network)
        
        print("\nThank you for trying the Factory Floor System Demo!")

if __name__ == "__main__":
    main()