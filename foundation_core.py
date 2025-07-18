"""
Foundation Core - Silent Node Version with Debug Mode
=====================================================

Silent operation for production nodes with debug mode for troubleshooting.
"""
import wifi
import socketpool
import ipaddress
import time
import os
import microcontroller
from adafruit_httpserver import Server, Request, Response
import gc

class Config:
    """Configuration container with node defaults."""
    WIFI_SSID = "wicdhub"
    WIFI_PASSWORD = "pudden789"
    WIFI_MODE = "CLIENT"  # Locked to CLIENT mode
    BLINK_INTERVAL = 0.25
    DEBUG_MODE = False  # Debug mode flag

class PicowicdFoundation:
    """
    Core foundation class for sensor nodes with silent operation.
    
    DEBUG_MODE = False: Complete silence (production)
    DEBUG_MODE = True: Full diagnostic output (troubleshooting)
    """
    
    def __init__(self):
        """Initialize foundation system with node configuration."""
        self.config = Config()
        self.startup_log = []
        self.server = None
        self.modules = {}
        self.config_failed = False
        self.wifi_mode = "CLIENT"  # Always CLIENT mode

    def startup_print(self, message):
        """Print startup message only if debug mode enabled."""
        if self.config.DEBUG_MODE:
            print(f"[STARTUP] {message}")
        self.startup_log.append(message)

    def debug_print(self, message):
        """Print debug message if debug mode enabled."""
        if self.config.DEBUG_MODE:
            print(f"[DEBUG] {message}")

    def decode_html_entities(self, text):
        """Clean web form input of HTML entities."""
        text = text.replace('&quot;', '"')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&#39;', "'")
        return text

    def get_module(self, name):
        """Get registered module by name."""
        return self.modules.get(name)

    def safe_connect_client(self, ssid, password):
        """Connect to existing WiFi network with timeout."""
        try:
            self.startup_print(f"Connecting to WiFi: {ssid}")
            wifi.radio.connect(ssid, password, timeout=30)
            
            if wifi.radio.connected:
                self.startup_print(f"Connected successfully: {wifi.radio.ipv4_address}")
                return True, ssid, password
            else:
                self.startup_print("Connection failed - no connection established")
                return False, ssid, password
                
        except Exception as e:
            self.startup_print(f"Client connection failed: {e}")
            return False, ssid, password

    def load_user_config(self):
        """Load config from settings.toml with debug mode support."""
        try:
            # Must load debug mode first before any startup_print calls
            toml_debug = os.getenv("DEBUG_MODE")
            if toml_debug:
                try:
                    self.config.DEBUG_MODE = str(toml_debug).lower() in ['true', '1', 'yes', 'on']
                except:
                    self.config.DEBUG_MODE = False
            
            self.startup_print("Loading user config...")

            # Try settings.toml first (modern approach)
            toml_ssid = os.getenv("WIFI_SSID")
            toml_password = os.getenv("WIFI_PASSWORD")
            toml_blink = os.getenv("BLINK_INTERVAL")

            # If core WiFi settings found in TOML, use TOML approach
            if toml_ssid and toml_password:
                self.startup_print("Found settings.toml, using TOML configuration")

                try:
                    self.config.WIFI_SSID = self.decode_html_entities(str(toml_ssid))
                except:
                    self.config_failed = True

                try:
                    self.config.WIFI_PASSWORD = self.decode_html_entities(str(toml_password))
                except:
                    self.config_failed = True

                if toml_blink:
                    try:
                        self.config.BLINK_INTERVAL = float(toml_blink)
                    except:
                        self.config_failed = True

                self.startup_print(f"Debug mode: {'ON' if self.config.DEBUG_MODE else 'OFF'}")
                return

            # Fall back to config.py
            self.startup_print("No complete settings.toml found, trying config.py")
            import config as user_config

            try:
                ssid = self.decode_html_entities(str(user_config.WIFI_SSID))
                self.config.WIFI_SSID = ssid
            except:
                self.config_failed = True

            try:
                password = self.decode_html_entities(str(user_config.WIFI_PASSWORD))
                self.config.WIFI_PASSWORD = password
            except:
                self.config_failed = True

            try:
                self.config.BLINK_INTERVAL = float(user_config.BLINK_INTERVAL)
            except:
                self.config_failed = True

            # Try to load debug mode from config.py
            try:
                self.config.DEBUG_MODE = getattr(user_config, 'DEBUG_MODE', False)
            except:
                self.config.DEBUG_MODE = False

        except Exception as e:
            self.startup_print(f"All config loading failed: {e}")
            self.config_failed = True

        # Apply defaults if config failed
        if self.config_failed:
            self.startup_print("Using emergency defaults")
            self.config.WIFI_SSID = "wicdhub"
            self.config.WIFI_PASSWORD = "pudden789"
            self.config.BLINK_INTERVAL = 0.10
            self.config.DEBUG_MODE = False

    def initialize_network(self):
        """Initialize CLIENT mode network connection only."""
        self.load_user_config()
        
        self.startup_print("Node mode: CLIENT only")
        self.debug_print("Network initialization starting...")
        
        # CLIENT mode only - connect to existing network (Pi5 hub)
        client_success, ssid, password = self.safe_connect_client(
            self.config.WIFI_SSID,
            self.config.WIFI_PASSWORD
        )
        self.config.WIFI_SSID = ssid
        self.config.WIFI_PASSWORD = password
        
        if client_success:
            # Create server using client IP
            pool = socketpool.SocketPool(wifi.radio)
            self.server = Server(pool, "/", debug=False)
            server_ip = str(wifi.radio.ipv4_address)
            self.startup_print(f"Node server IP: {server_ip}")
            self.debug_print(f"Server initialized on {server_ip}")
            return True
        else:
            self.startup_print("CLIENT connection failed - node cannot operate")
            self.debug_print("Network initialization failed")
            return False

    def register_module(self, name, module):
        """Register a module with the foundation system."""
        self.modules[name] = module
        module.register_routes(self.server)
        self.debug_print(f"Module registered: {name}")

    def start_server(self):
        """Start minimal web server for node status."""
        # Simple status route only
        @self.server.route("/status", methods=['GET'])
        def node_status(request: Request):
            """Basic node status endpoint."""
            try:
                status = {
                    "node_type": "wicdpico-node",
                    "wifi_mode": "CLIENT",
                    "connected": wifi.radio.connected,
                    "ip": str(wifi.radio.ipv4_address) if wifi.radio.connected else "none",
                    "modules": list(self.modules.keys()),
                    "config_ok": not self.config_failed,
                    "debug_mode": self.config.DEBUG_MODE
                }
                
                status_text = f"Node Status: {status['node_type']}<br>"
                status_text += f"Mode: {status['wifi_mode']}<br>"
                status_text += f"Connected: {status['connected']}<br>"
                status_text += f"IP: {status['ip']}<br>"
                status_text += f"Modules: {len(status['modules'])}<br>"
                status_text += f"Config: {'OK' if status['config_ok'] else 'Failed'}<br>"
                status_text += f"Debug: {'ON' if status['debug_mode'] else 'OFF'}"
                
                return Response(request, status_text, content_type="text/html")
                
            except Exception as e:
                return Response(request, f"Status error: {e}", content_type="text/plain")
        
        server_ip = str(wifi.radio.ipv4_address)
        self.server.start(server_ip, port=80)
        self.startup_print(f"Node status at http://{server_ip}/status")
        self.debug_print("HTTP server started")

    def run_main_loop(self):
        """Main polling loop with module updates."""
        while True:
            self.server.poll()

            # Update all modules
            for module in self.modules.values():
                module.update()

            time.sleep(0.1)
            gc.collect()

    def render_dashboard(self, title="Node Status"):
        """Minimal status page for nodes."""
        system_info = f"""
            <p><strong>Node Type:</strong> wicdpico-node</p>
            <p><strong>WiFi Mode:</strong> {self.wifi_mode}</p>
            <p><strong>WiFi SSID:</strong> {self.config.WIFI_SSID}</p>
            <p><strong>Network:</strong> http://{wifi.radio.ipv4_address}</p>
            <p><strong>Modules loaded:</strong> {len(self.modules)}</p>
            <p><strong>Config status:</strong> {'Failed' if self.config_failed else 'OK'}</p>
            <p><strong>Debug mode:</strong> {'ON' if self.config.DEBUG_MODE else 'OFF'}</p>
        """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .status {{ background: #f0f0f0; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="status">
                {system_info}
            </div>
        </body>
        </html>
        """