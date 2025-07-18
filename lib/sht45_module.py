# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT

"""
`sht45_module`
====================================================

SHT45 Temperature and Humidity Sensor Module for PicoWicd system.

Provides comprehensive I2C access to all Adafruit SHT45 sensor parameters
including temperature, humidity, precision modes, heater control, and
advanced sensor features through web interface.

* Author(s): PicoWicd Development Team

Implementation Notes
--------------------

**Hardware:**

* Designed for use with Adafruit SHT45 Temperature & Humidity Sensor
* Uses I2C communication (GP4=SDA, GP5=SCL)
* Requires adafruit_sht4x library

**Software and Dependencies:**

* Adafruit CircuitPython firmware for Raspberry Pi Pico 2 W
* adafruit_sht4x library
* adafruit_httpserver
* PicoWicd foundation system

**Notes:**

* Supports all SHT45 measurement modes and heater settings
* Web interface provides real-time sensor monitoring and configuration
* Automatic error handling for missing or failed hardware

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
from adafruit_httpserver import Request, Response

import adafruit_sht4x

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/picowicd/picowicd.git"


class SHT45Module(PicowicdModule):
    """
    SHT45 Temperature and Humidity Sensor Module for PicoWicd system.
    
    Provides comprehensive web interface and management for SHT45 sensor hardware.
    Supports all measurement modes, heater settings, and advanced sensor features
    available through the Adafruit SHT4x library.
    
    :param foundation: PicoWicd foundation instance for system integration
    :type foundation: PicowicdFoundation
    
    **Quickstart: Importing and using the module**
    
    Here is an example of using the SHT45Module:
    
    .. code-block:: python
    
        from foundation_core import PicowicdFoundation
        from sht45_module import SHT45Module
        
        # Initialize foundation system
        foundation = PicowicdFoundation()
        foundation.initialize_network()
        
        # Create SHT45 module
        sht45_module = SHT45Module(foundation)
        
        # Register with foundation
        foundation.register_module("sht45", sht45_module)
        
        # Start system
        foundation.start_server()
        foundation.run_main_loop()
    
    **Available Features:**
    
    * Temperature and humidity readings
    * Multiple precision modes (HIGH, MEDIUM, LOW)
    * Heater control for condensation removal
    * Serial number identification
    * Soft reset functionality
    * Real-time web dashboard
    * Configurable measurement intervals
    """
    
    def __init__(self, foundation):
        """
        Initialize SHT45 Module.
        
        Sets up module identification and configuration. Hardware initialization
        will be added in Step 2.
        
        :param foundation: PicoWicd foundation instance
        :type foundation: PicowicdFoundation
        """
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
        """
        Initialize I2C bus and SHT45 sensor hardware.
        
        Sets up I2C communication on GP4(SDA)/GP5(SCL) and attempts to
        connect to SHT45 sensor. Handles initialization errors gracefully.
        """
        try:
            # Set up I2C bus (GP4=SDA, GP5=SCL to match other modules)
            self.i2c = busio.I2C(board.GP5, board.GP4)
            self.foundation.startup_print("I2C bus initialized (GP5=SCL, GP4=SDA)")
            
            # Initialize SHT45 sensor
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

    def register_routes(self, server):
        """
        Register HTTP routes for SHT45 web interface.
        
        Provides REST endpoints for sensor readings and control.
        Routes will be implemented in subsequent steps.
        
        :param server: HTTP server instance to register routes with
        :type server: adafruit_httpserver.Server
        
        **Planned Routes:**
        
        * ``POST /sht45-reading`` - Get current sensor readings
        * ``POST /sht45-mode`` - Set measurement mode
        * ``POST /sht45-heater`` - Control heater settings
        * ``POST /sht45-reset`` - Perform sensor reset
        """
        # Routes will be implemented in subsequent steps
        self.foundation.startup_print("SHT45 routes registered (placeholder)")

    def get_dashboard_html(self):
        """
        Generate HTML dashboard widget for SHT45 control.
        
        Creates interactive web interface with sensor readings display
        and control buttons. Full implementation will be added in later steps.
        
        :return: HTML string containing dashboard widget
        :rtype: str
        """
        # Basic placeholder dashboard - will be enhanced in later steps
        sensor_status = "✓ Connected" if self.sensor_available else "✗ Not found"
        sensor_info = f"Serial: 0x{self.sensor_serial:08X}" if self.sensor_serial else "No serial"
        error_display = f"<br><strong>Error:</strong> {self.last_error}" if self.last_error else ""
        
        return '''
        <div class="module">
            <h3>SHT45 Temperature & Humidity Sensor</h3>
            <div class="status">
                <strong>Status:</strong> {}<br>
                <strong>Sensor:</strong> {}<br>
                <strong>Mode:</strong> {}<br>
                <strong>Heater:</strong> {}{}
            </div>
            <div class="control-group">
                <button onclick="alert('Reading functionality coming in Step 3!')">Get Reading</button>
            </div>
            <p id="sht45-status">SHT45 Module - Step 2 hardware initialization complete!</p>
        </div>
        '''.format(self.status_message, sensor_info, self.current_mode, self.current_heater, error_display)

    def update(self):
        """
        Periodic update method called by foundation system.
        
        Will handle automatic sensor readings and status updates.
        Implementation will be added in subsequent steps.
        
        .. note::
           This method is called periodically by the PicoWicd foundation.
           Override this method to add custom periodic tasks.
        """
        # Automatic sensor reading logic will be implemented in later steps
        pass

    def cleanup(self):
        """
        Cleanup method called during system shutdown.
        
        Performs any necessary cleanup operations before module shutdown.
        Currently no cleanup is required but method is provided for completeness.
        """
        if self.sensor_available:
            self.foundation.startup_print("SHT45 cleanup: Sensor shutdown")
        pass

    @property
    def sensor_info(self):
        """
        Get sensor information and status.
        
        :return: Dictionary containing sensor status information
        :rtype: dict
        
        .. code-block:: python
        
            # Get sensor info
            info = sht45_module.sensor_info
            print(f"Available: {info['available']}")
            print(f"Last reading: {info['last_reading_time']}")
        """
        return {
            "available": self.sensor_available,
            "last_reading_time": self.last_reading_time,
            "current_mode": self.current_mode,
            "current_heater": self.current_heater,
            "status_message": self.status_message,
            "last_error": self.last_error
        }