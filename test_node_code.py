# test_node_code.py - Test stripped foundation core
"""
Test Node Foundation - Verify CLIENT-only mode works
"""
import gc
import time
import wifi

def main():
    try:
        print("=== WICDPICO-NODE TEST - FOUNDATION CORE ===")
        
        # Replace your foundation_core.py with the new version first
        from foundation_core import PicowicdFoundation
        foundation = PicowicdFoundation()
        
        print(f"WiFi mode locked to: {foundation.wifi_mode}")
        
        if foundation.initialize_network():
            server_ip = str(wifi.radio.ipv4_address)
            
            # Test basic module loading
            from sht45_module import SHT45Module
            sht45 = SHT45Module(foundation)
            foundation.register_module("sht45", sht45)
            
            from mqtt_module import MQTTModule  
            mqtt = MQTTModule(foundation)
            foundation.register_module("mqtt", mqtt)
            
            foundation.start_server()
            
            print(f"✓ Node ready at: http://{server_ip}/status")
            print("✓ CLIENT mode only - no AP fallback")
            print("✓ Basic status server running")
            print("✓ Modules loaded successfully")
            
            # Test status endpoint
            print(f"✓ Visit http://{server_ip}/status to verify")
            
            # Brief test loop
            for i in range(10):
                foundation.server.poll()
                for module in foundation.modules.values():
                    module.update()
                time.sleep(1)
                print(f"Test cycle {i+1}/10 complete")
                gc.collect()
            
            print("✓ Foundation core test PASSED")
            print("Ready for Step 5")
                
        else:
            print("✗ Network failed - check WiFi settings")
            
    except KeyboardInterrupt:
        print("Test stopped")
    except Exception as e:
        print(f"✗ Error: {e}")
        import sys
        sys.print_exception(e)

if __name__ == "__main__":
    main()
else:
    main()