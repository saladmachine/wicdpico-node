# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
SHT45 Module - Silent Node Version
==================================

SHT45 sensor module with silent operation for production nodes.
Only outputs to serial when DEBUG_MODE = true.
"""

# === CONFIGURATION PARAMETERS ===
SENSOR_READ_INTERVAL = 2.0      # seconds between automatic readings
TEMPERATURE_UNITS = "C"         # "C" for Celsius, "F" for Fahrenheit  
DEFAULT_PRECISION_MODE = "HIGH" # "HIGH", "MED", "LOW"
DEFAULT_HEATER_MODE = "NONE"    # "NONE", "LOW_100MS", "LOW_1S", "MED_100MS", "MED_1S", "HIGH_100MS", "HIGH_1S"
ENABLE_AUTO_UPDATES = True      # Enable automatic sensor readings in update loop
LOG_SENSOR_READINGS = False     # Log each sensor reading to foundation
# === END CONFIGURATION ===

import time
import board
import busio
from module_base import PicowicdModule

# Try to import SHT4x library, create mock if not available
try:
    import adafruit_sht4x
    SHT4X_AVAILABLE = True
except ImportError:
    # Create mock classes for testing without hardware
    class MockMode:
        NOHEAT_HIGHPRECISION = 0
        NOHEAT_MEDPRECISION = 1  
        NOHEAT_LOWPRECISION = 2
        LOWHEAT_100MS = 3
        LOWHEAT_1S = 4
        MEDHEAT_100MS = 5
        MEDHEAT_1S = 6
        HIGHHEAT_100MS = 7
        HIGHHEAT_1S = 8
        
    class MockSHT4x:
        def __init__(self, i2c):
            self.mode = 0
            self.serial_number = 0x12345678
            
        @property
        def measurements(self):
            import random
            return (22.5 + random.random() * 5, 65.0 + random.random() * 10)
    
    # Create mock module
    class adafruit_sht4x:
        Mode = MockMode
        SHT4x = MockSHT4x
    
    SHT4X_AVAILABLE = False

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/picowicd/picowicd.git"


class SHT45Module(PicowicdModule):
    """
    SHT45 Sensor Module - Silent Node Version.
    
    Operates silently in production, full diagnostics in debug mode.
    """
    
    def __init__(self, foundation):
        """Initialize SHT45 Module for silent node operation."""
        super().__init__(foundation)
        self.name = "SHT45 Sensor"
        
        # Configuration from module parameters
        self.read_interval = SENSOR_READ_INTERVAL
        self.temperature_units = TEMPERATURE_UNITS
        self.auto_updates_enabled = ENABLE_AUTO_UPDATES
        self.log_readings = LOG_SENSOR_READINGS
        
        # Sensor state tracking
        self.sensor_available = False
        self.last_reading_time = 0
        self.last_temperature = None
        self.last_humidity = None
        self.current_mode = DEFAULT_PRECISION_MODE
        self.current_heater = DEFAULT_HEATER_MODE
        
        # Status and error tracking
        self.status_message = "SHT45 module initialized"
        self.last_error = None
        
        # Initialize I2C and sensor hardware
        self._initialize_sensor()
        
        self.foundation.startup_print("SHT45 module created")
        self.foundation.startup_print(f"Read interval: {self.read_interval}s")
        self.foundation.startup_print(f"Temperature units: {self.temperature_units}")

    def _initialize_sensor(self):
        """Initialize I2C bus and SHT45 sensor hardware."""
        try:
            # Set up I2C bus (GP4=SDA, GP5=SCL to match other modules)
            self.i2c = busio.I2C(board.GP5, board.GP4)
            self.foundation.startup_print("I2C bus initialized (GP5=SCL, GP4=SDA)")
            
            if not SHT4X_AVAILABLE:
                self.foundation.startup_print("Using mock SHT4x for testing (library not installed)")
            
            # Initialize SHT45 sensor (real or mock)
            self.sht45 = adafruit_sht4x.SHT4x(self.i2c)
            self.sensor_available = True
            
            # Get sensor serial number for identification
            try:
                self.sensor_serial = self.sht45.serial_number
                self.foundation.startup_print(f"SHT45 found! Serial: 0x{self.sensor_serial:08X}")
            except Exception as e:
                self.sensor_serial = None
                self.foundation.startup_print(f"SHT45 serial read failed: {e}")
            
            # Set default mode
            try:
                if DEFAULT_PRECISION_MODE == "HIGH":
                    self.sht45.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
                elif DEFAULT_PRECISION_MODE == "MED":
                    self.sht45.mode = adafruit_sht4x.Mode.NOHEAT_MEDPRECISION  
                else:  # LOW
                    self.sht45.mode = adafruit_sht4x.Mode.NOHEAT_LOWPRECISION
                
                self.foundation.startup_print(f"SHT45 mode set to: {DEFAULT_PRECISION_MODE} precision")
                self.status_message = f"SHT45 ready (Serial: 0x{self.sensor_serial:08X})" if self.sensor_serial else "SHT45 ready"
                
            except Exception as e:
                self.foundation.startup_print(f"SHT45 mode setting failed: {e}")
                self.status_message = "SHT45 connected but mode setting failed"
                
        except Exception as e:
            self.sensor_available = False
            self.sht45 = None
            self.i2c = None
            self.last_error = f"SHT45 initialization failed: {e}"
            self.status_message = self.last_error
            self.foundation.startup_print(self.last_error)

    def get_sensor_reading(self):
        """Get current temperature and humidity readings from SHT45 sensor."""
        if not self.sensor_available or not self.sht45:
            return {
                "success": False,
                "error": "Sensor not available",
                "temperature": None,
                "humidity": None,
                "temperature_units": self.temperature_units,
                "timestamp": time.monotonic()
            }
        
        try:
            # Get measurements from sensor
            temperature_c, humidity = self.sht45.measurements
            
            # Convert temperature if needed
            if self.temperature_units == "F":
                temperature = (temperature_c * 9/5) + 32
            else:
                temperature = temperature_c
            
            # Update module state
            self.last_temperature = temperature
            self.last_humidity = humidity
            self.last_reading_time = time.monotonic()
            
            # Log reading if enabled and in debug mode
            if self.log_readings and self.foundation.config.DEBUG_MODE:
                self.foundation.startup_print(f"SHT45: {temperature:.1f}°{self.temperature_units}, {humidity:.1f}%RH")
            
            return {
                "success": True,
                "error": None,
                "temperature": round(temperature, 1),
                "humidity": round(humidity, 1),
                "temperature_units": self.temperature_units,
                "timestamp": self.last_reading_time
            }
            
        except Exception as e:
            error_msg = f"Reading failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"SHT45 error: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "temperature": None,
                "humidity": None,
                "temperature_units": self.temperature_units,
                "timestamp": time.monotonic()
            }

    def set_measurement_mode(self, mode):
        """Set SHT45 measurement precision mode."""
        if not self.sensor_available or not self.sht45:
            return False, "Sensor not available"
        
        try:
            # Map mode strings to adafruit_sht4x constants
            mode_map = {
                "HIGH": adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION,
                "MED": adafruit_sht4x.Mode.NOHEAT_MEDPRECISION,
                "LOW": adafruit_sht4x.Mode.NOHEAT_LOWPRECISION
            }
            
            if mode not in mode_map:
                return False, f"Invalid mode: {mode}. Use HIGH, MED, or LOW"
            
            # Set the new mode
            self.sht45.mode = mode_map[mode]
            self.current_mode = mode
            
            self.foundation.startup_print(f"SHT45 mode changed to: {mode}")
            self.status_message = f"Mode: {mode} precision"
            
            return True, f"Mode set to {mode} precision"
            
        except Exception as e:
            error_msg = f"Mode change failed: {e}"
            self.last_error = error_msg
            self.foundation.startup_print(f"SHT45 mode error: {error_msg}")
            return False, error_msg

    def get_sensor_info(self):
        """Get comprehensive sensor information and status."""
        return {
            "available": self.sensor_available,
            "serial_number": self.sensor_serial,
            "serial_hex": f"0x{self.sensor_serial:08X}" if self.sensor_serial else "N/A",
            "current_mode": self.current_mode,
            "current_heater": self.current_heater,
            "last_reading_time": self.last_reading_time,
            "last_temperature": self.last_temperature,
            "last_humidity": self.last_humidity,
            "temperature_units": self.temperature_units,
            "status_message": self.status_message,
            "last_error": self.last_error,
            "library_available": SHT4X_AVAILABLE
        }

    def register_routes(self, server):
        """Register minimal HTTP routes for node operation."""
        # Only basic status route for debugging
        pass

    def get_dashboard_html(self):
        """No dashboard for node version."""
        return ""

    def update(self):
        """Periodic update method called by foundation system."""
        if not self.auto_updates_enabled:
            return
            
        current_time = time.monotonic()
        
        # Auto-read sensor at configured interval
        if current_time - self.last_reading_time >= self.read_interval:
            if self.sensor_available:
                reading = self.get_sensor_reading()
                if reading['success'] and self.log_readings and self.foundation.config.DEBUG_MODE:
                    self.foundation.debug_print(f"Auto-read: {reading['temperature']}°{reading['temperature_units']}, {reading['humidity']}%RH")

    def cleanup(self):
        """Cleanup method called during system shutdown."""
        if self.sensor_available and self.foundation.config.DEBUG_MODE:
            self.foundation.startup_print("SHT45 cleanup: Sensor shutdown")
        pass