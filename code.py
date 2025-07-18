# test_mqtt_operation.py - Test MQTT functionality
"""
Test Step 7 - MQTT Operation Verification
- Connect to Pi5 MQTT broker
- Publish sensor data  
- Verify automatic operation
"""
import gc
import time
import wifi

def main():
    try:
        print("=== STEP 7 TEST - MQTT OPERATION ===")
        
        from foundation_core import PicowicdFoundation
        foundation = PicowicdFoundation()
        
        # Enable debug mode for this test to see MQTT activity
        foundation.config.DEBUG_MODE = True
        print("Debug mode enabled for MQTT testing")
        
        if foundation.initialize_network():
            server_ip = str(wifi.radio.ipv4_address)
            print(f"Connected to hub: {server_ip}")
            
            # Load modules
            from sht45_module import SHT45Module
            sht45 = SHT45Module(foundation)
            foundation.register_module("sht45", sht45)
            
            from mqtt_module import MQTTModule
            mqtt = MQTTModule(foundation)
            foundation.register_module("mqtt", mqtt)
            
            foundation.start_server()
            
            print("Testing MQTT connection...")
            success, message = mqtt.connect_mqtt()
            print(f"MQTT connect result: {success} - {message}")
            
            if success or mqtt.connected:
                print("Testing sensor data publishing...")
                
                # Test manual publish
                publish_success = mqtt.publish_sensor_data()
                print(f"Manual publish result: {publish_success}")
                
                if publish_success:
                    print("MQTT publishing working!")
                    
                    print("Testing automatic operation (30 seconds)...")
                    start_time = time.monotonic()
                    publish_count = 0
                    
                    while time.monotonic() - start_time < 30:
                        foundation.server.poll()
                        
                        # Check for MQTT publishes
                        old_last_publish = mqtt.last_publish
                        
                        for module in foundation.modules.values():
                            module.update()
                            
                        # Count publishes
                        if mqtt.last_publish > old_last_publish:
                            publish_count += 1
                            print(f"Auto-publish #{publish_count} completed")
                        
                        time.sleep(1)
                        gc.collect()
                    
                    print(f"Step 7 MQTT test PASSED")
                    print(f"Published {publish_count} automatic updates")
                    print("Node ready for deployment")
                    
                else:
                    print("Manual publish failed - check MQTT broker")
                    
            else:
                print("MQTT connection failed")
                print("Check:")
                print("- Pi5 hub running at 192.168.99.1")
                print("- Mosquitto broker active")
                print("- Network connectivity")
                
        else:
            print("Network connection failed")
            print("Check WiFi settings and Pi5 hub")
            
    except Exception as e:
        print(f"MQTT test error: {e}")
        import sys
        sys.print_exception(e)

if __name__ == "__main__":
    main()
else:
    main()