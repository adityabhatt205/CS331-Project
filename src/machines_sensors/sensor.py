"""
Sensor module for the Factory Floor System.
Provides comprehensive sensor management with different sensor types, calibration, and monitoring.
"""

from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import time
import threading
import logging
import random
import math
from datetime import datetime, timedelta


class SensorType(Enum):
    """Sensor type enumeration."""
    TEMPERATURE = "TEMPERATURE"
    PRESSURE = "PRESSURE"
    VIBRATION = "VIBRATION"
    HUMIDITY = "HUMIDITY"
    FLOW_RATE = "FLOW_RATE"
    LEVEL = "LEVEL"
    PROXIMITY = "PROXIMITY"
    MOTION = "MOTION"
    LIGHT = "LIGHT"
    SOUND = "SOUND"
    PH = "PH"
    CONDUCTIVITY = "CONDUCTIVITY"


class SensorStatus(Enum):
    """Sensor status enumeration."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"
    CALIBRATING = "CALIBRATING"
    MAINTENANCE = "MAINTENANCE"


class AlertLevel(Enum):
    """Alert level enumeration."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class SensorReading:
    """Sensor reading data structure."""
    
    def __init__(self, sensor_id: int, value: float, unit: str, quality: float = 1.0,
                 timestamp: Optional[datetime] = None):
        """
        Initialize sensor reading.
        
        Args:
            sensor_id: Sensor identifier
            value: Measured value
            unit: Unit of measurement
            quality: Reading quality (0.0-1.0, where 1.0 is perfect)
            timestamp: Reading timestamp
        """
        self.sensor_id = sensor_id
        self.value = value
        self.unit = unit
        self.quality = quality
        self.timestamp = timestamp or datetime.now()


class SensorAlert:
    """Sensor alert data structure."""
    
    def __init__(self, sensor_id: int, alert_type: str, level: AlertLevel, 
                 message: str, value: float, threshold: float):
        """
        Initialize sensor alert.
        
        Args:
            sensor_id: Sensor identifier
            alert_type: Type of alert
            level: Alert severity level
            message: Alert message
            value: Current sensor value
            threshold: Threshold that was exceeded
        """
        self.sensor_id = sensor_id
        self.alert_type = alert_type
        self.level = level
        self.message = message
        self.value = value
        self.threshold = threshold
        self.timestamp = datetime.now()


class Sensor:
    """
    Comprehensive Sensor class for factory floor monitoring.
    Provides sensor reading, calibration, alerts, and data logging.
    """
    
    def __init__(self, sensor_id: int, sensor_type: SensorType, name: str,
                 unit: str, location: str = "", machine_id: Optional[int] = None):
        """
        Initialize sensor.
        
        Args:
            sensor_id: Unique sensor identifier
            sensor_type: Type of sensor
            name: Sensor name
            unit: Unit of measurement
            location: Physical location
            machine_id: Associated machine ID
        """
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.name = name
        self.unit = unit
        self.location = location
        self.machine_id = machine_id
        
        # Status and control
        self._status = SensorStatus.ACTIVE
        self._is_calibrated = True
        self._last_calibration = datetime.now() - timedelta(hours=1)  # Recent calibration
        self._calibration_due = False
        
        # Current reading
        self._current_value = 0.0
        self._last_reading_time = datetime.now()
        self._reading_quality = 1.0
        
        # Operational ranges and thresholds
        self._min_value = self._get_default_range()[0]
        self._max_value = self._get_default_range()[1]
        self._warning_low = self._min_value + (self._max_value - self._min_value) * 0.1
        self._warning_high = self._max_value - (self._max_value - self._min_value) * 0.1
        self._critical_low = self._min_value
        self._critical_high = self._max_value
        
        # Calibration parameters
        self._calibration_offset = 0.0
        self._calibration_scale = 1.0
        self._drift_factor = 0.000001  # Much smaller sensor drift over time
        
        # Data collection
        self._reading_history = []
        self._max_history_size = 10000
        self._sampling_rate = 1.0  # seconds between readings
        
        # Alerts and monitoring
        self._active_alerts = []
        self._alert_callbacks = []
        self._reading_callbacks = []
        
        # Threading for continuous monitoring
        self._monitor_thread = None
        self._monitoring_active = False
        self._reading_lock = threading.Lock()
        
        # Logger
        self._logger = logging.getLogger(f"Sensor_{sensor_id}")
        
        # Initialize sensor
        self._logger.info(f"Sensor {name} ({sensor_type.value}) initialized")
    
    @property
    def status(self) -> SensorStatus:
        """Get current sensor status."""
        return self._status
    
    @property
    def current_value(self) -> float:
        """Get current sensor value."""
        with self._reading_lock:
            return self._current_value
    
    @property
    def is_active(self) -> bool:
        """Check if sensor is active."""
        return self._status == SensorStatus.ACTIVE
    
    @property
    def calibration_due(self) -> bool:
        """Check if calibration is due."""
        return self._calibration_due
    
    @property
    def active_alerts(self) -> List[SensorAlert]:
        """Get active alerts."""
        return self._active_alerts.copy()
    
    def read_data(self) -> SensorReading:
        """
        Read current sensor data.
        
        Returns:
            SensorReading object with current value and metadata
        """
        if self._status != SensorStatus.ACTIVE:
            raise RuntimeError(f"Cannot read from sensor in {self._status.value} status")
        
        with self._reading_lock:
            # Simulate sensor reading with some realistic behavior
            raw_value = self._simulate_sensor_reading()
            
            # Apply calibration
            calibrated_value = self._apply_calibration(raw_value)
            
            # Update current value
            self._current_value = calibrated_value
            self._last_reading_time = datetime.now()
            
            # Determine reading quality
            self._reading_quality = self._calculate_reading_quality()
            
            # Create reading object
            reading = SensorReading(
                sensor_id=self.sensor_id,
                value=calibrated_value,
                unit=self.unit,
                quality=self._reading_quality,
                timestamp=self._last_reading_time
            )
            
            # Store in history
            self._reading_history.append(reading)
            if len(self._reading_history) > self._max_history_size:
                self._reading_history.pop(0)
            
            # Check for alerts
            self._check_alerts(reading)
            
            # Notify callbacks
            for callback in self._reading_callbacks:
                try:
                    callback(reading)
                except Exception as e:
                    self._logger.error(f"Reading callback error: {e}")
            
            return reading
    
    def calibrate(self, reference_value: float, user_id: Optional[int] = None) -> bool:
        """
        Calibrate the sensor against a reference value.
        
        Args:
            reference_value: Known reference value
            user_id: ID of user performing calibration
            
        Returns:
            True if calibration successful, False otherwise
        """
        old_status = self._status
        self._status = SensorStatus.CALIBRATING
        
        try:
            # Take multiple readings for calibration
            raw_readings = []
            for _ in range(10):
                raw_value = self._simulate_sensor_reading(calibration_mode=True)
                raw_readings.append(raw_value)
                time.sleep(0.1)
            
            # Calculate average raw reading
            avg_raw = sum(raw_readings) / len(raw_readings)
            
            # Calculate new calibration parameters
            if avg_raw != 0:
                self._calibration_scale = reference_value / avg_raw
                self._calibration_offset = 0.0
            else:
                self._calibration_offset = reference_value
                self._calibration_scale = 1.0
            
            # Update calibration status
            self._last_calibration = datetime.now()
            self._is_calibrated = True
            self._calibration_due = False
            
            self._logger.info(f"Sensor calibrated: scale={self._calibration_scale:.4f}, offset={self._calibration_offset:.4f}")
            
            return True
            
        except Exception as e:
            self._logger.error(f"Calibration failed: {e}")
            return False
            
        finally:
            self._status = old_status
    
    def set_thresholds(self, warning_low: float, warning_high: float,
                      critical_low: float, critical_high: float) -> None:
        """
        Set alert thresholds.
        
        Args:
            warning_low: Low warning threshold
            warning_high: High warning threshold
            critical_low: Low critical threshold
            critical_high: High critical threshold
        """
        self._warning_low = warning_low
        self._warning_high = warning_high
        self._critical_low = critical_low
        self._critical_high = critical_high
        
        self._logger.info(f"Thresholds updated: warn({warning_low}-{warning_high}), critical({critical_low}-{critical_high})")
    
    def set_sampling_rate(self, rate: float) -> None:
        """
        Set sensor sampling rate.
        
        Args:
            rate: Sampling rate in seconds
        """
        self._sampling_rate = max(0.1, rate)  # Minimum 0.1 second
        self._logger.info(f"Sampling rate set to {self._sampling_rate} seconds")
    
    def start_monitoring(self) -> None:
        """Start continuous sensor monitoring."""
        if not self._monitoring_active:
            self._monitoring_active = True
            self._monitor_thread = threading.Thread(target=self._monitor_sensor, daemon=True)
            self._monitor_thread.start()
            self._logger.info("Sensor monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop continuous sensor monitoring."""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)
        self._logger.info("Sensor monitoring stopped")
    
    def get_statistics(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """
        Get sensor statistics for specified duration.
        
        Args:
            duration_minutes: Duration in minutes to analyze
            
        Returns:
            Dictionary containing sensor statistics
        """
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_readings = [r for r in self._reading_history if r.timestamp >= cutoff_time]
        
        if not recent_readings:
            return {"error": "No readings in specified duration"}
        
        values = [r.value for r in recent_readings]
        qualities = [r.quality for r in recent_readings]
        
        return {
            "sensor_id": self.sensor_id,
            "duration_minutes": duration_minutes,
            "reading_count": len(recent_readings),
            "min_value": min(values),
            "max_value": max(values),
            "avg_value": sum(values) / len(values),
            "avg_quality": sum(qualities) / len(qualities),
            "current_value": self._current_value,
            "status": self._status.value,
            "active_alerts": len(self._active_alerts),
            "last_calibration": self._last_calibration.isoformat()
        }
    
    def get_trend_analysis(self, duration_minutes: int = 30) -> Dict[str, Any]:
        """
        Analyze sensor value trends.
        
        Args:
            duration_minutes: Duration in minutes to analyze
            
        Returns:
            Dictionary containing trend analysis
        """
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_readings = [r for r in self._reading_history if r.timestamp >= cutoff_time]
        
        if len(recent_readings) < 2:
            return {"error": "Insufficient data for trend analysis"}
        
        # Simple linear trend calculation
        values = [r.value for r in recent_readings]
        time_points = [(r.timestamp - recent_readings[0].timestamp).total_seconds() for r in recent_readings]
        
        # Calculate slope (trend)
        n = len(values)
        sum_x = sum(time_points)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(time_points, values))
        sum_x2 = sum(x * x for x in time_points)
        
        if n * sum_x2 - sum_x * sum_x != 0:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            trend_direction = "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable"
        else:
            slope = 0.0
            trend_direction = "stable"
        
        return {
            "sensor_id": self.sensor_id,
            "trend_direction": trend_direction,
            "slope": slope,
            "confidence": min(1.0, len(recent_readings) / 100),  # More readings = higher confidence
            "stability": self._calculate_stability(values)
        }
    
    def add_alert_callback(self, callback: Callable[[SensorAlert], None]) -> None:
        """Add callback for sensor alerts."""
        self._alert_callbacks.append(callback)
    
    def add_reading_callback(self, callback: Callable[[SensorReading], None]) -> None:
        """Add callback for sensor readings."""
        self._reading_callbacks.append(callback)
    
    def set_maintenance_mode(self, enabled: bool, user_id: Optional[int] = None) -> None:
        """Set sensor maintenance mode."""
        if enabled:
            self._status = SensorStatus.MAINTENANCE
            self.stop_monitoring()
            self._logger.info("Sensor entered maintenance mode")
        else:
            self._status = SensorStatus.ACTIVE
            self.start_monitoring()
            self._logger.info("Sensor exited maintenance mode")
    
    def reset_alerts(self) -> None:
        """Reset all active alerts."""
        alert_count = len(self._active_alerts)
        self._active_alerts.clear()
        self._logger.info(f"Reset {alert_count} active alerts")
    
    def _simulate_sensor_reading(self, calibration_mode: bool = False) -> float:
        """
        Simulate sensor reading with realistic behavior.
        
        Args:
            calibration_mode: If True, provide more stable reading for calibration
            
        Returns:
            Simulated raw sensor value
        """
        # Base value depends on sensor type
        base_value = self._get_base_value()
        
        if calibration_mode:
            # More stable reading for calibration
            noise = random.uniform(-0.01, 0.01)
        else:
            # Normal reading with noise and drift
            noise = random.uniform(-0.1, 0.1)
            drift = self._drift_factor * (datetime.now() - self._last_calibration).total_seconds()
            base_value += drift
        
        # Add time-based variation for some sensor types
        if self.sensor_type in [SensorType.TEMPERATURE, SensorType.PRESSURE]:
            time_factor = math.sin(time.time() * 0.1) * 0.05  # Slow oscillation
            base_value += time_factor * (self._max_value - self._min_value)
        
        return base_value + noise * (self._max_value - self._min_value)
    
    def _get_base_value(self) -> float:
        """Get base value for sensor type."""
        # Return typical operational value for each sensor type
        ranges = {
            SensorType.TEMPERATURE: 25.0,  # 25°C
            SensorType.PRESSURE: 101.3,    # 101.3 kPa
            SensorType.HUMIDITY: 50.0,     # 50%
            SensorType.VIBRATION: 2.0,     # 2 mm/s
            SensorType.FLOW_RATE: 100.0,   # 100 L/min
            SensorType.LEVEL: 50.0,        # 50%
            SensorType.PROXIMITY: 0.0,     # 0 (not detected)
            SensorType.MOTION: 0.0,        # 0 (no motion)
            SensorType.LIGHT: 500.0,       # 500 lux
            SensorType.SOUND: 40.0,        # 40 dB
            SensorType.PH: 7.0,            # pH 7.0
            SensorType.CONDUCTIVITY: 100.0  # 100 µS/cm
        }
        return ranges.get(self.sensor_type, 50.0)
    
    def _get_default_range(self) -> Tuple[float, float]:
        """Get default value range for sensor type."""
        ranges = {
            SensorType.TEMPERATURE: (-10.0, 100.0),     # °C
            SensorType.PRESSURE: (80.0, 120.0),         # kPa
            SensorType.HUMIDITY: (0.0, 100.0),          # %
            SensorType.VIBRATION: (0.0, 10.0),          # mm/s
            SensorType.FLOW_RATE: (0.0, 1000.0),        # L/min
            SensorType.LEVEL: (0.0, 100.0),             # %
            SensorType.PROXIMITY: (0.0, 1.0),           # boolean
            SensorType.MOTION: (0.0, 1.0),              # boolean
            SensorType.LIGHT: (0.0, 10000.0),           # lux
            SensorType.SOUND: (20.0, 120.0),            # dB
            SensorType.PH: (0.0, 14.0),                 # pH
            SensorType.CONDUCTIVITY: (0.0, 2000.0)      # µS/cm
        }
        return ranges.get(self.sensor_type, (0.0, 100.0))
    
    def _apply_calibration(self, raw_value: float) -> float:
        """Apply calibration parameters to raw value."""
        return (raw_value * self._calibration_scale) + self._calibration_offset
    
    def _calculate_reading_quality(self) -> float:
        """Calculate reading quality based on various factors."""
        quality = 1.0
        
        # Reduce quality if calibration is overdue
        days_since_calibration = (datetime.now() - self._last_calibration).days
        if days_since_calibration > 90:
            quality *= 0.8
        elif days_since_calibration > 180:
            quality *= 0.6
        
        # Reduce quality based on signal stability
        if len(self._reading_history) >= 10:
            recent_values = [r.value for r in self._reading_history[-10:]]
            stability = self._calculate_stability(recent_values)
            quality *= stability
        
        return max(0.0, min(1.0, quality))
    
    def _calculate_stability(self, values: List[float]) -> float:
        """Calculate stability metric for values."""
        if len(values) < 2:
            return 1.0
        
        mean_val = sum(values) / len(values)
        if mean_val == 0:
            return 1.0
        
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        coefficient_of_variation = math.sqrt(variance) / abs(mean_val)
        
        # Convert to stability score (lower variability = higher stability)
        return max(0.0, 1.0 - coefficient_of_variation)
    
    def _check_alerts(self, reading: SensorReading) -> None:
        """Check for alert conditions."""
        value = reading.value
        
        # Clear existing alerts for same conditions
        self._active_alerts = [alert for alert in self._active_alerts 
                              if not alert.alert_type.startswith(f"{self.sensor_id}_")]
        
        # Check critical thresholds
        if value <= self._critical_low:
            alert = SensorAlert(
                self.sensor_id, "CRITICAL_LOW", AlertLevel.CRITICAL,
                f"Sensor value {value:.2f} below critical threshold {self._critical_low:.2f}",
                value, self._critical_low
            )
            self._active_alerts.append(alert)
            self._trigger_alert(alert)
        
        elif value >= self._critical_high:
            alert = SensorAlert(
                self.sensor_id, "CRITICAL_HIGH", AlertLevel.CRITICAL,
                f"Sensor value {value:.2f} above critical threshold {self._critical_high:.2f}",
                value, self._critical_high
            )
            self._active_alerts.append(alert)
            self._trigger_alert(alert)
        
        # Check warning thresholds
        elif value <= self._warning_low:
            alert = SensorAlert(
                self.sensor_id, "WARNING_LOW", AlertLevel.WARNING,
                f"Sensor value {value:.2f} below warning threshold {self._warning_low:.2f}",
                value, self._warning_low
            )
            self._active_alerts.append(alert)
            self._trigger_alert(alert)
        
        elif value >= self._warning_high:
            alert = SensorAlert(
                self.sensor_id, "WARNING_HIGH", AlertLevel.WARNING,
                f"Sensor value {value:.2f} above warning threshold {self._warning_high:.2f}",
                value, self._warning_high
            )
            self._active_alerts.append(alert)
            self._trigger_alert(alert)
        
        # Check reading quality
        if reading.quality < 0.8:
            alert = SensorAlert(
                self.sensor_id, "QUALITY_LOW", AlertLevel.WARNING,
                f"Sensor reading quality low: {reading.quality:.2f}",
                reading.quality, 0.8
            )
            self._active_alerts.append(alert)
            self._trigger_alert(alert)
        
        # Check calibration due
        if self._calibration_due:
            alert = SensorAlert(
                self.sensor_id, "CALIBRATION_DUE", AlertLevel.INFO,
                "Sensor calibration is due",
                0, 0
            )
            self._active_alerts.append(alert)
            self._trigger_alert(alert)
    
    def _trigger_alert(self, alert: SensorAlert) -> None:
        """Trigger sensor alert."""
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self._logger.error(f"Alert callback error: {e}")
        
        # Log alert
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.CRITICAL: logging.ERROR,
            AlertLevel.EMERGENCY: logging.CRITICAL
        }.get(alert.level, logging.INFO)
        
        self._logger.log(log_level, f"[{alert.alert_type}] {alert.message}")
    
    def _monitor_sensor(self) -> None:
        """Background thread for sensor monitoring."""
        while self._monitoring_active:
            try:
                if self._status == SensorStatus.ACTIVE:
                    self.read_data()
                
                # Check if calibration is due
                days_since_calibration = (datetime.now() - self._last_calibration).days
                if days_since_calibration > 90 and not self._calibration_due:
                    self._calibration_due = True
                    self._logger.warning("Sensor calibration is due")
                
                time.sleep(self._sampling_rate)
                
            except Exception as e:
                self._logger.error(f"Monitoring error: {e}")
                time.sleep(1)
