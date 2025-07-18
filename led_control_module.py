"""
LED Control Module - Node Version (No Web Interface)
====================================================

LED control for wicdpico-node with no web interface.
Core LED functionality for status indication only.
"""
import digitalio
import board
import time
from module_base import PicowicdModule

class LEDControlModule(PicowicdModule):
    """
    LED Control Module - Node Version.
    
    Provides basic LED control for status indication:
    - Manual LED on/off
    - Automatic blinking
    - No web interface or HTTP routes
    """
    
    def __init__(self, foundation):
        """Initialize LED control hardware."""
        super().__init__(foundation)

        # Initialize LED hardware
        self.led = digitalio.DigitalInOut(board.LED)
        self.led.direction = digitalio.Direction.OUTPUT

        # LED state management
        self.last_blink = time.monotonic()
        self.led_state = False
        self.blinky_enabled = False
        self.manual_mode = False

        # Get blink interval from config
        self.blink_interval = foundation.config.BLINK_INTERVAL
        
        self.foundation.startup_print("LED control initialized for node")

    def set_led(self, state):
        """Set LED to specific state."""
        self.led_state = state
        self.led.value = state
        
    def enable_blinky(self, enabled):
        """Enable or disable automatic blinky mode."""
        self.blinky_enabled = enabled
        if enabled:
            self.manual_mode = False
        else:
            self.set_led(False)

    def register_routes(self, server):
        """No web routes for node version."""
        pass

    def get_dashboard_html(self):
        """No dashboard for node version."""
        return ""

    def update(self):
        """Handle blinky timing - called from main loop."""
        if not self.blinky_enabled or self.manual_mode:
            return

        current_time = time.monotonic()

        if current_time - self.last_blink >= self.blink_interval:
            self.led_state = not self.led_state
            self.led.value = self.led_state
            self.last_blink = current_time