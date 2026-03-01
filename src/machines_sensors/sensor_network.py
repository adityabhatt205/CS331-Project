"""
Sensor Network module for the Factory Floor System.
Provides comprehensive sensor network management, data aggregation, and monitoring.
"""

from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from enum import Enum
import time
import threading
import logging
import json
import statistics
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass, field

from .sensor import Sensor, SensorType, SensorStatus, SensorReading, SensorAlert, AlertLevel


class NetworkStatus(Enum):
    """Sensor network status enumeration."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"


class DataAggregationMethod(Enum):
    """Data aggregation methods."""
    AVERAGE = "AVERAGE"
    MINIMUM = "MINIMUM"
    MAXIMUM = "MAXIMUM"
    SUM = "SUM"
    MEDIAN = "MEDIAN"
    MOST_RECENT = "MOST_RECENT"


class NetworkAlert(Enum):
    """Network-level alert types."""
    SENSOR_OFFLINE = "SENSOR_OFFLINE"
    SENSOR_ERROR = "SENSOR_ERROR"
    DATA_QUALITY_LOW = "DATA_QUALITY_LOW"
    COMMUNICATION_FAILURE = "COMMUNICATION_FAILURE"
    THRESHOLD_VIOLATED = "THRESHOLD_VIOLATED"
    CALIBRATION_DUE = "CALIBRATION_DUE"


@dataclass
class NetworkConfiguration:
    """Network configuration settings."""
    network_id: int
    name: str
    description: str = ""
    auto_discovery: bool = True
    data_retention_hours: int = 24
    alert_threshold_count: int = 3
    health_check_interval: int = 30  # seconds
    auto_calibration_enabled: bool = False
    redundancy_enabled: bool = True
    quality_threshold: float = 0.8


@dataclass
class SensorGroup:
    """Logical grouping of sensors."""
    group_id: str
    name: str
    description: str
    sensor_ids: Set[int] = field(default_factory=set)
    aggregation_method: DataAggregationMethod = DataAggregationMethod.AVERAGE
    alert_enabled: bool = True
    group_thresholds: Dict[str, float] = field(default_factory=dict)


@dataclass
class NetworkMetrics:
    """Network performance metrics."""
    total_sensors: int = 0
    active_sensors: int = 0
    error_sensors: int = 0
    offline_sensors: int = 0
    avg_data_quality: float = 0.0
    total_readings: int = 0
    avg_response_time: float = 0.0
    network_uptime: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class SensorNetwork:
    """
    Comprehensive Sensor Network management system.
    Manages multiple sensors, data aggregation, and network-level monitoring.
    """
    
    def __init__(self, config: NetworkConfiguration):
        """
        Initialize sensor network.
        
        Args:
            config: Network configuration
        """
        self.config = config
        
        # Sensor management
        self._sensors: Dict[int, Sensor] = {}
        self._sensor_groups: Dict[str, SensorGroup] = {}
        self._network_status = NetworkStatus.INACTIVE
        
        # Data collection and storage
        self._sensor_data: Dict[int, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._aggregated_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._network_alerts: List[Dict[str, Any]] = []
        self._max_alerts = 1000
        
        # Network monitoring
        self._network_metrics = NetworkMetrics()
        self._health_check_thread = None
        self._data_collection_thread = None
        self._alert_processing_thread = None
        
        # Threading control
        self._monitoring_active = False
        self._data_lock = threading.RLock()
        self._sensor_lock = threading.RLock()
        
        # Performance tracking
        self._start_time = datetime.now()
        self._total_readings_collected = 0
        self._total_alerts_generated = 0
        
        # Event callbacks
        self._sensor_callbacks: Dict[str, List[Callable]] = {
            "sensor_added": [],
            "sensor_removed": [],
            "sensor_status_changed": [],
            "data_received": [],
            "alert_generated": [],
            "network_status_changed": []
        }
        
        # Data validation and filtering
        self._quality_filters = []
        self._value_filters = []
        
        # Auto-discovery settings
        self._discovery_enabled = config.auto_discovery
        self._discovered_sensors = set()
        
        # Logger
        self._logger = logging.getLogger(f"SensorNetwork_{config.network_id}")
        
        # Initialize network
        self._logger.info(f"Sensor Network '{config.name}' initialized")
    
    @property
    def status(self) -> NetworkStatus:
        """Get current network status."""
        return self._network_status
    
    @property
    def sensor_count(self) -> int:
        """Get total number of sensors."""
        with self._sensor_lock:
            return len(self._sensors)
    
    @property
    def active_sensor_count(self) -> int:
        """Get number of active sensors."""
        with self._sensor_lock:
            return sum(1 for sensor in self._sensors.values() 
                      if sensor.status == SensorStatus.ACTIVE)
    
    @property
    def network_metrics(self) -> NetworkMetrics:
        """Get current network metrics."""
        return self._update_network_metrics()
    
    def add_sensor(self, sensor: Sensor) -> bool:
        """
        Add sensor to network.
        
        Args:
            sensor: Sensor instance to add
            
        Returns:
            True if sensor added successfully, False otherwise
        """
        with self._sensor_lock:
            if sensor.sensor_id in self._sensors:
                self._logger.warning(f"Sensor {sensor.sensor_id} already exists in network")
                return False
            
            # Add sensor
            self._sensors[sensor.sensor_id] = sensor
            
            # Initialize data storage
            sensor_data = deque(maxlen=10000)
            self._sensor_data[sensor.sensor_id] = sensor_data
            
            # Setup sensor callbacks
            sensor.add_reading_callback(self._on_sensor_reading)
            sensor.add_alert_callback(self._on_sensor_alert)
            
            # Start sensor monitoring if network is active
            if self._monitoring_active and sensor.status == SensorStatus.ACTIVE:
                sensor.start_monitoring()
            
            self._logger.info(f"Added sensor {sensor.sensor_id} ({sensor.name}) to network")
            
            # Notify callbacks
            self._notify_callbacks("sensor_added", sensor)
            
            # Update network status
            self._update_network_status()
            
            return True
    
    def remove_sensor(self, sensor_id: int) -> bool:
        """
        Remove sensor from network.
        
        Args:
            sensor_id: ID of sensor to remove
            
        Returns:
            True if sensor removed successfully, False otherwise
        """
        with self._sensor_lock:
            if sensor_id not in self._sensors:
                self._logger.warning(f"Sensor {sensor_id} not found in network")
                return False
            
            sensor = self._sensors[sensor_id]
            
            # Stop sensor monitoring
            sensor.stop_monitoring()
            
            # Remove from groups
            for group in self._sensor_groups.values():
                group.sensor_ids.discard(sensor_id)
            
            # Remove sensor data
            if sensor_id in self._sensor_data:
                del self._sensor_data[sensor_id]
            
            # Remove sensor
            del self._sensors[sensor_id]
            
            self._logger.info(f"Removed sensor {sensor_id} from network")
            
            # Notify callbacks
            self._notify_callbacks("sensor_removed", {"sensor_id": sensor_id, "sensor": sensor})
            
            # Update network status
            self._update_network_status()
            
            return True
    
    def get_sensor(self, sensor_id: int) -> Optional[Sensor]:
        """
        Get sensor by ID.
        
        Args:
            sensor_id: Sensor ID
            
        Returns:
            Sensor instance or None if not found
        """
        with self._sensor_lock:
            return self._sensors.get(sensor_id)
    
    def get_sensors_by_type(self, sensor_type: SensorType) -> List[Sensor]:
        """
        Get all sensors of specified type.
        
        Args:
            sensor_type: Sensor type to filter by
            
        Returns:
            List of sensors of specified type
        """
        with self._sensor_lock:
            return [sensor for sensor in self._sensors.values() 
                   if sensor.sensor_type == sensor_type]
    
    def create_sensor_group(self, group: SensorGroup) -> bool:
        """
        Create sensor group for data aggregation.
        
        Args:
            group: Sensor group configuration
            
        Returns:
            True if group created successfully, False otherwise
        """
        if group.group_id in self._sensor_groups:
            self._logger.warning(f"Sensor group {group.group_id} already exists")
            return False
        
        # Validate sensor IDs exist
        with self._sensor_lock:
            invalid_sensors = group.sensor_ids - set(self._sensors.keys())
            if invalid_sensors:
                self._logger.error(f"Invalid sensor IDs in group: {invalid_sensors}")
                return False
        
        self._sensor_groups[group.group_id] = group
        self._logger.info(f"Created sensor group '{group.name}' with {len(group.sensor_ids)} sensors")
        return True
    
    def get_group_data(self, group_id: str, duration_minutes: int = 60) -> Optional[Dict[str, Any]]:
        """
        Get aggregated data for sensor group.
        
        Args:
            group_id: Group ID
            duration_minutes: Duration to analyze in minutes
            
        Returns:
            Aggregated group data or None if group not found
        """
        if group_id not in self._sensor_groups:
            return None
        
        group = self._sensor_groups[group_id]
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        # Collect recent readings from group sensors
        group_readings = []
        with self._data_lock:
            for sensor_id in group.sensor_ids:
                if sensor_id in self._sensor_data:
                    sensor_readings = [
                        reading for reading in self._sensor_data[sensor_id]
                        if reading.timestamp >= cutoff_time
                    ]
                    group_readings.extend(sensor_readings)
        
        if not group_readings:
            return {"group_id": group_id, "error": "No data available"}
        
        # Apply aggregation method
        values = [reading.value for reading in group_readings]
        qualities = [reading.quality for reading in group_readings]
        
        aggregated_value = self._apply_aggregation(values, group.aggregation_method)
        avg_quality = sum(qualities) / len(qualities) if qualities else 0.0
        
        return {
            "group_id": group_id,
            "group_name": group.name,
            "aggregated_value": aggregated_value,
            "reading_count": len(group_readings),
            "sensor_count": len(group.sensor_ids),
            "avg_quality": avg_quality,
            "aggregation_method": group.aggregation_method.value,
            "timestamp": datetime.now().isoformat()
        }
    
    def start_network(self) -> bool:
        """
        Start network monitoring and data collection.
        
        Returns:
            True if network started successfully, False otherwise
        """
        try:
            # Start monitoring threads
            self._monitoring_active = True
            
            self._health_check_thread = threading.Thread(
                target=self._health_check_monitor, daemon=True)
            self._health_check_thread.start()
            
            self._data_collection_thread = threading.Thread(
                target=self._data_collection_monitor, daemon=True)
            self._data_collection_thread.start()
            
            self._alert_processing_thread = threading.Thread(
                target=self._alert_processing_monitor, daemon=True)
            self._alert_processing_thread.start()
            
            # Start all active sensors
            with self._sensor_lock:
                for sensor in self._sensors.values():
                    if sensor.status == SensorStatus.ACTIVE:
                        sensor.start_monitoring()
            
            self._network_status = NetworkStatus.ACTIVE
            self._logger.info("Sensor network started")
            
            # Notify callbacks
            self._notify_callbacks("network_status_changed", self._network_status)
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to start sensor network: {e}")
            return False
    
    def stop_network(self) -> None:
        """Stop network monitoring and data collection."""
        self._monitoring_active = False
        self._network_status = NetworkStatus.INACTIVE
        
        # Stop all sensors
        with self._sensor_lock:
            for sensor in self._sensors.values():
                sensor.stop_monitoring()
        
        # Wait for threads to complete
        threads = [self._health_check_thread, self._data_collection_thread, self._alert_processing_thread]
        for thread in threads:
            if thread:
                thread.join(timeout=1)
        
        self._logger.info("Sensor network stopped")
        
        # Notify callbacks
        self._notify_callbacks("network_status_changed", self._network_status)
    
    def get_network_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive network summary.
        
        Returns:
            Network summary data
        """
        metrics = self._update_network_metrics()
        
        # Sensor status breakdown
        sensor_status_counts = defaultdict(int)
        with self._sensor_lock:
            for sensor in self._sensors.values():
                sensor_status_counts[sensor.status.value] += 1
        
        # Recent alerts summary
        recent_alerts = [
            alert for alert in self._network_alerts[-10:]
        ]
        
        # Group summary
        group_summary = {}
        for group_id, group in self._sensor_groups.items():
            group_data = self.get_group_data(group_id, 15)  # Last 15 minutes
            group_summary[group_id] = {
                "name": group.name,
                "sensor_count": len(group.sensor_ids),
                "aggregation_method": group.aggregation_method.value,
                "recent_value": group_data.get("aggregated_value") if group_data else None
            }
        
        return {
            "network_id": self.config.network_id,
            "network_name": self.config.name,
            "status": self._network_status.value,
            "metrics": {
                "total_sensors": metrics.total_sensors,
                "active_sensors": metrics.active_sensors,
                "error_sensors": metrics.error_sensors,
                "offline_sensors": metrics.offline_sensors,
                "avg_data_quality": metrics.avg_data_quality,
                "network_uptime": metrics.network_uptime,
                "total_readings": metrics.total_readings
            },
            "sensor_status_counts": dict(sensor_status_counts),
            "groups": group_summary,
            "recent_alerts": recent_alerts,
            "uptime_hours": (datetime.now() - self._start_time).total_seconds() / 3600,
            "total_readings_collected": self._total_readings_collected,
            "total_alerts_generated": self._total_alerts_generated
        }
        
    # Legacy methods for backward compatibility
    def collectSensorData(self) -> None:
        """Legacy method - collect sensor data."""
        self._logger.warning("Using deprecated collectSensorData method")
        with self._sensor_lock:
            for sensor in self._sensors.values():
                try:
                    if sensor.status == SensorStatus.ACTIVE:
                        sensor.read_data()
                except Exception as e:
                    self._logger.error(f"Error collecting data from sensor {sensor.sensor_id}: {e}")
    
    def get_sensor_data_trends(self, sensor_id: int, duration_minutes: int = 60) -> Optional[Dict[str, Any]]:
        """
        Get sensor data trends and analysis.
        
        Args:
            sensor_id: Sensor ID to analyze
            duration_minutes: Duration to analyze in minutes
            
        Returns:
            Trend analysis data or None if sensor not found
        """
        if sensor_id not in self._sensors:
            return None
        
        sensor = self._sensors[sensor_id]
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        with self._data_lock:
            recent_readings = [
                reading for reading in self._sensor_data[sensor_id]
                if reading.timestamp >= cutoff_time
            ]
        
        if len(recent_readings) < 2:
            return {"error": "Insufficient data for trend analysis"}
        
        values = [r.value for r in recent_readings]
        times = [(r.timestamp - recent_readings[0].timestamp).total_seconds() for r in recent_readings]
        qualities = [r.quality for r in recent_readings]
        
        # Calculate basic statistics
        try:
            trend_slope = self._calculate_trend_slope(times, values)
            trend_direction = "increasing" if trend_slope > 0.01 else "decreasing" if trend_slope < -0.01 else "stable"
            
            return {
                "sensor_id": sensor_id,
                "sensor_name": sensor.name,
                "duration_minutes": duration_minutes,
                "reading_count": len(recent_readings),
                "min_value": min(values),
                "max_value": max(values),
                "avg_value": statistics.mean(values),
                "median_value": statistics.median(values),
                "std_deviation": statistics.stdev(values) if len(values) > 1 else 0.0,
                "trend_direction": trend_direction,
                "trend_slope": trend_slope,
                "avg_quality": statistics.mean(qualities),
                "first_reading": recent_readings[0].timestamp.isoformat(),
                "last_reading": recent_readings[-1].timestamp.isoformat()
            }
            
        except Exception as e:
            self._logger.error(f"Trend analysis failed for sensor {sensor_id}: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    def calibrate_sensor_group(self, group_id: str, reference_values: Dict[int, float], 
                              user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Calibrate all sensors in a group.
        
        Args:
            group_id: Group ID
            reference_values: Mapping of sensor_id to reference value
            user_id: User performing calibration
            
        Returns:
            Calibration results
        """
        if group_id not in self._sensor_groups:
            return {"error": "Group not found"}
        
        group = self._sensor_groups[group_id]
        results = {}
        
        with self._sensor_lock:
            for sensor_id in group.sensor_ids:
                if sensor_id in self._sensors and sensor_id in reference_values:
                    sensor = self._sensors[sensor_id]
                    reference_value = reference_values[sensor_id]
                    
                    success = sensor.calibrate(reference_value, user_id)
                    results[sensor_id] = {
                        "success": success,
                        "reference_value": reference_value,
                        "sensor_name": sensor.name
                    }
        
        self._logger.info(f"Group calibration completed for {group_id}: {len(results)} sensors")
        return {"group_id": group_id, "calibration_results": results}
    
    def add_callback(self, event_type: str, callback: Callable) -> bool:
        """
        Add event callback.
        
        Args:
            event_type: Event type (sensor_added, data_received, etc.)
            callback: Callback function
            
        Returns:
            True if callback added successfully, False otherwise
        """
        if event_type in self._sensor_callbacks:
            self._sensor_callbacks[event_type].append(callback)
            return True
        return False
    
    def set_quality_filter(self, min_quality: float) -> None:
        """Set minimum quality threshold for data acceptance."""
        def quality_filter(reading: SensorReading) -> bool:
            return reading.quality >= min_quality
        
        self._quality_filters = [quality_filter]
        self._logger.info(f"Quality filter set: minimum quality {min_quality}")
    
    def export_sensor_data(self, duration_hours: int = 1, format_type: str = "json") -> str:
        """
        Export sensor data for analysis.
        
        Args:
            duration_hours: Hours of data to export
            format_type: Export format ('json' or 'csv')
            
        Returns:
            Exported data as string
        """
        cutoff_time = datetime.now() - timedelta(hours=duration_hours)
        export_data = {}
        
        with self._data_lock:
            for sensor_id, readings in self._sensor_data.items():
                sensor = self._sensors.get(sensor_id)
                if sensor:
                    recent_readings = [
                        {
                            "timestamp": r.timestamp.isoformat(),
                            "value": r.value,
                            "unit": r.unit,
                            "quality": r.quality
                        }
                        for r in readings if r.timestamp >= cutoff_time
                    ]
                    
                    export_data[sensor_id] = {
                        "sensor_name": sensor.name,
                        "sensor_type": sensor.sensor_type.value,
                        "location": sensor.location,
                        "readings": recent_readings
                    }
        
        if format_type == "json":
            return json.dumps(export_data, indent=2)
        elif format_type == "csv":
            # Simple CSV export (would need more sophisticated implementation for production)
            csv_data = "sensor_id,sensor_name,timestamp,value,unit,quality\n"
            for sensor_id, data in export_data.items():
                for reading in data["readings"]:
                    csv_data += f"{sensor_id},{data['sensor_name']},{reading['timestamp']},{reading['value']},{reading['unit']},{reading['quality']}\n"
            return csv_data
        
        return ""
    
    def _on_sensor_reading(self, reading: SensorReading) -> None:
        """Handle sensor reading callback."""
        # Apply quality filters
        if self._quality_filters:
            if not all(filter_func(reading) for filter_func in self._quality_filters):
                return
        
        # Store reading
        with self._data_lock:
            if reading.sensor_id in self._sensor_data:
                self._sensor_data[reading.sensor_id].append(reading)
                self._total_readings_collected += 1
        
        # Notify callbacks
        self._notify_callbacks("data_received", reading)
    
    def _on_sensor_alert(self, alert: SensorAlert) -> None:
        """Handle sensor alert callback."""
        # Convert to network alert format
        network_alert = {
            "sensor_id": alert.sensor_id,
            "alert_type": alert.alert_type,
            "level": alert.level.value,
            "message": alert.message,
            "value": alert.value,
            "threshold": alert.threshold,
            "timestamp": alert.timestamp.isoformat()
        }
        
        # Store alert
        self._network_alerts.append(network_alert)
        if len(self._network_alerts) > self._max_alerts:
            self._network_alerts.pop(0)
        
        self._total_alerts_generated += 1
        
        # Notify callbacks
        self._notify_callbacks("alert_generated", network_alert)
        
        self._logger.warning(f"Network alert: {alert.message}")
    
    def _apply_aggregation(self, values: List[float], method: DataAggregationMethod) -> float:
        """Apply aggregation method to values."""
        if not values:
            return 0.0
        
        if method == DataAggregationMethod.AVERAGE:
            return sum(values) / len(values)
        elif method == DataAggregationMethod.MINIMUM:
            return min(values)
        elif method == DataAggregationMethod.MAXIMUM:
            return max(values)
        elif method == DataAggregationMethod.SUM:
            return sum(values)
        elif method == DataAggregationMethod.MEDIAN:
            return statistics.median(values)
        elif method == DataAggregationMethod.MOST_RECENT:
            return values[-1]
        else:
            return sum(values) / len(values)  # Default to average
    
    def _calculate_trend_slope(self, x_values: List[float], y_values: List[float]) -> float:
        """Calculate linear regression slope."""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0
        
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if abs(denominator) < 1e-10:  # Avoid division by zero
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope
    
    def _update_network_status(self) -> None:
        """Update overall network status."""
        with self._sensor_lock:
            if not self._sensors:
                self._network_status = NetworkStatus.INACTIVE
                return
            
            active_count = sum(1 for sensor in self._sensors.values() 
                             if sensor.status == SensorStatus.ACTIVE)
            error_count = sum(1 for sensor in self._sensors.values() 
                            if sensor.status == SensorStatus.ERROR)
            total_count = len(self._sensors)
            
            if active_count == total_count:
                self._network_status = NetworkStatus.ACTIVE
            elif active_count > 0:
                self._network_status = NetworkStatus.PARTIAL
            elif error_count > 0:
                self._network_status = NetworkStatus.ERROR
            else:
                self._network_status = NetworkStatus.INACTIVE
    
    def _update_network_metrics(self) -> NetworkMetrics:
        """Update network performance metrics."""
        with self._sensor_lock:
            total_sensors = len(self._sensors)
            active_sensors = sum(1 for sensor in self._sensors.values() 
                               if sensor.status == SensorStatus.ACTIVE)
            error_sensors = sum(1 for sensor in self._sensors.values() 
                              if sensor.status == SensorStatus.ERROR)
            offline_sensors = total_sensors - active_sensors - error_sensors
        
        # Calculate average data quality
        total_quality = 0.0
        quality_count = 0
        
        with self._data_lock:
            for readings in self._sensor_data.values():
                if readings:
                    recent_readings = list(readings)[-10:]  # Last 10 readings
                    for reading in recent_readings:
                        total_quality += reading.quality
                        quality_count += 1
        
        avg_quality = total_quality / quality_count if quality_count > 0 else 0.0
        
        # Calculate uptime
        uptime_seconds = (datetime.now() - self._start_time).total_seconds()
        uptime_percentage = 100.0 if self._monitoring_active else 90.0  # Simplified
        
        self._network_metrics = NetworkMetrics(
            total_sensors=total_sensors,
            active_sensors=active_sensors,
            error_sensors=error_sensors,
            offline_sensors=offline_sensors,
            avg_data_quality=avg_quality,
            total_readings=self._total_readings_collected,
            avg_response_time=0.0,  # Would need timing data for real implementation
            network_uptime=uptime_percentage,
            timestamp=datetime.now()
        )
        
        return self._network_metrics
    
    def _notify_callbacks(self, event_type: str, data: Any) -> None:
        """Notify event callbacks."""
        if event_type in self._sensor_callbacks:
            for callback in self._sensor_callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    self._logger.error(f"Callback error for {event_type}: {e}")
    
    def _health_check_monitor(self) -> None:
        """Background thread for sensor health monitoring."""
        while self._monitoring_active:
            try:
                with self._sensor_lock:
                    for sensor in self._sensors.values():
                        # Check sensor responsiveness
                        if sensor.status == SensorStatus.ACTIVE:
                            # Check if sensor has produced recent data
                            cutoff_time = datetime.now() - timedelta(
                                seconds=self.config.health_check_interval * 2)
                            
                            with self._data_lock:
                                recent_readings = [
                                    reading for reading in self._sensor_data[sensor.sensor_id]
                                    if reading.timestamp >= cutoff_time
                                ]
                            
                            if not recent_readings:
                                self._generate_network_alert(
                                    NetworkAlert.SENSOR_OFFLINE,
                                    f"Sensor {sensor.sensor_id} not responding",
                                    sensor.sensor_id
                                )
                
                time.sleep(self.config.health_check_interval)
                
            except Exception as e:
                self._logger.error(f"Health check error: {e}")
                time.sleep(5)
    
    def _data_collection_monitor(self) -> None:
        """Background thread for data collection monitoring."""
        while self._monitoring_active:
            try:
                # Update network metrics
                self._update_network_metrics()
                
                # Check data quality trends
                self._check_data_quality_trends()
                
                # Clean old data if needed
                self._cleanup_old_data()
                
                time.sleep(60)  # Run every minute
                
            except Exception as e:
                self._logger.error(f"Data collection monitor error: {e}")
                time.sleep(5)
    
    def _alert_processing_monitor(self) -> None:
        """Background thread for alert processing."""
        while self._monitoring_active:
            try:
                # Process and correlate alerts
                self._process_correlated_alerts()
                
                time.sleep(10)  # Run every 10 seconds
                
            except Exception as e:
                self._logger.error(f"Alert processing error: {e}")
                time.sleep(5)
    
    def _generate_network_alert(self, alert_type: NetworkAlert, message: str, 
                               sensor_id: Optional[int] = None) -> None:
        """Generate network-level alert."""
        alert = {
            "alert_type": alert_type.value,
            "message": message,
            "sensor_id": sensor_id,
            "level": "WARNING",
            "timestamp": datetime.now().isoformat()
        }
        
        self._network_alerts.append(alert)
        if len(self._network_alerts) > self._max_alerts:
            self._network_alerts.pop(0)
        
        self._notify_callbacks("alert_generated", alert)
        self._logger.warning(f"Network alert: {message}")
    
    def _check_data_quality_trends(self) -> None:
        """Check for data quality issues across the network."""
        low_quality_sensors = []
        
        with self._sensor_lock:
            for sensor_id, sensor in self._sensors.items():
                if sensor.status == SensorStatus.ACTIVE:
                    with self._data_lock:
                        recent_readings = list(self._sensor_data[sensor_id])[-10:]
                        if recent_readings:
                            avg_quality = sum(r.quality for r in recent_readings) / len(recent_readings)
                            if avg_quality < self.config.quality_threshold:
                                low_quality_sensors.append((sensor_id, avg_quality))
        
        if low_quality_sensors:
            message = f"Low data quality detected: {len(low_quality_sensors)} sensors"
            self._generate_network_alert(NetworkAlert.DATA_QUALITY_LOW, message)
    
    def _process_correlated_alerts(self) -> None:
        """Process and correlate related alerts."""
        # Simple correlation - count recent alerts by type
        recent_time = datetime.now() - timedelta(minutes=5)
        
        alert_counts = defaultdict(int)
        for alert in self._network_alerts:
            alert_time = datetime.fromisoformat(alert["timestamp"])
            if alert_time >= recent_time:
                alert_counts[alert["alert_type"]] += 1
        
        # Generate correlated alerts if threshold exceeded
        for alert_type, count in alert_counts.items():
            if count >= self.config.alert_threshold_count:
                message = f"Multiple {alert_type} alerts detected ({count} in last 5 minutes)"
                self._generate_network_alert(NetworkAlert.COMMUNICATION_FAILURE, message)
    
    def _cleanup_old_data(self) -> None:
        """Clean up old data beyond retention period."""
        cutoff_time = datetime.now() - timedelta(hours=self.config.data_retention_hours)
        
        with self._data_lock:
            for readings in self._sensor_data.values():
                # Remove old readings
                while readings and readings[0].timestamp < cutoff_time:
                    readings.popleft()
        
        # Clean old alerts
        self._network_alerts = [
            alert for alert in self._network_alerts
            if datetime.fromisoformat(alert["timestamp"]) >= cutoff_time
        ]
