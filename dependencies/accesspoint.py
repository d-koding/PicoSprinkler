# ap_mode_manager.py
import network
import time

class APModeManager:
    """
    Manages the Access Point (AP) mode functionality for the Pico W.

    Author: Dylan O'Connor
    """
    def __init__(self, ssid="PicoRelayAP", password="ILOVEPICO",
                 ip_address="192.168.4.1", subnet_mask="255.255.255.0",
                 gateway="192.168.4.1", dns="8.8.8.8"):
        
        self.ssid = ssid
        self.password = password
        self.ip_address = ip_address
        self.subnet_mask = subnet_mask
        self.gateway = gateway
        self.dns = dns
        self.ap = network.WLAN(network.AP_IF)

    def setup_ap_mode(self) -> bool:
        """
        Activates and configures the Pico W in Access Point mode.
        Returns True if successful, False otherwise.
        """
        print("Attempting to set up Access Point mode...")
        try:
            self.ap.active(True)
            
            # modes: 0=Open, 1=WEP, 2=WPA-PSK, 3=WPA2-PSK, 4=WPA/WPA2-PSK
            self.ap.config(essid=self.ssid, password=self.password, security=4)
            
            # Set a static IP for the AP
            self.ap.ifconfig((self.ip_address, self.subnet_mask, self.gateway, self.dns))

            timeout = 10
            start_time = time.time()
            while not self.ap.active() and (time.time() - start_time) < timeout:
                time.sleep(0.5)
                print("Waiting for AP to activate...")

            if self.ap.active():
                current_ip = self.ap.ifconfig()[0]
                print(f"Access Point Mode Activated!")
                print(f"SSID: {self.ssid}")
                print(f"AP IP Address: {current_ip}")
                return True
            else:
                print("Failed to activate AP mode within timeout.")
                return False
        except Exception as e:
            print(f"Error setting up AP mode: {e}")
            self.ap.active(False) 
            return False

    def disconnect(self):
        """
        Deactivates the Access Point.
        """
        if self.ap.active():
            self.ap.active(False)
            print("Access Point Deactivated.")

    def get_ip_address(self) -> str:
        """
        Returns the IP address of the Access Point if active, otherwise returns an empty string.
        """
        if self.ap.active():
            return self.ap.ifconfig()[0]
        return ""
    
    