import network
import time
import sys

"""
Connects your micropico to wifi based based off of entered password and ssid.
Set password = your internet password
Set ssid = your internet ssid (internet name)

and you will be able to connect to the internet

author: Dylan O'Connor
"""

class Wifi_Connector:
    def __init__(self, password='F@RG0000', ssid='DALEWOOD_5G') -> None:
        self.ssid = ssid
        self.password = password
        self.wlan = network.WLAN(network.STA_IF) # Initialize WLAN object here

    def connect(self, timeout_seconds=30): # Added a timeout parameter
        SSID = self.ssid
        PASSWORD = self.password

        # Deactivate first to ensure a clean start, especially after a previous failed connection
        if self.wlan.active():
            self.wlan.active(False)
            time.sleep(0.5) # Give it a moment to de-activate

        self.wlan.active(True)

        print(f"Connecting to WiFi '{SSID}'...")
        self.wlan.connect(SSID, PASSWORD)

        start_time = time.time()
        while True:
            current_status = self.wlan.status()
            elapsed_time = time.time() - start_time

            if self.wlan.isconnected():
                print("\nConnected to WiFi!")
                print("IP Address:", self.wlan.ifconfig()[0])
                return True
            
            if elapsed_time > timeout_seconds:
                print(f"\nConnection timed out after {timeout_seconds} seconds.")
                # print final status for debugging
                print(f"Final WLAN Status: {current_status}")
                return False

            # More informative status messages
            if current_status == network.STAT_CONNECTING:
                print(".", end="")
            elif current_status == network.STAT_WRONG_PASSWORD:
                print("\nError: Wrong password!")
                return False
            elif current_status == network.STAT_NO_AP_FOUND:
                print("\nError: No access point found (SSID may be incorrect or out of range).")
                return False
            elif current_status == network.STAT_CONNECT_FAIL:
                print("\nError: Connection failed for an unknown reason.")
                return False
            elif current_status == network.STAT_IDLE:
                # This could happen if it tried to connect and failed, but didn't give a specific error code yet
                print(".", end="") # Keep waiting
            else:
                print(f"\nUnexpected WLAN Status: {current_status}") # For any other status codes
            
            time.sleep(1)

        # Fallback return (should be caught by the loop)
        print("Failed to connect.")
        return False
    
    def get_ip_address(self) -> str | None:
        """
        Returns the IP address if connected, otherwise None.
        """
        if self.wlan.isconnected():
            return self.wlan.ifconfig()[0]
        return None

    def get_network_info(self) -> tuple | None:
        """
        Returns the full network configuration tuple (IP, Subnet, Gateway, DNS)
        if connected, otherwise None.
        """
        if self.wlan.isconnected():
            return self.wlan.ifconfig()
        return None

    def is_connected(self) -> bool:
        """
        Checks if the WiFi connection is currently active.
        """
        return self.wlan.isconnected()

# Example usage in main.py:
# if __name__ == '__main__':
#     wifi = Wifi_Connector(ssid='YOUR_SSID', password='YOUR_PASSWORD') # Use your actual SSID and password
#     if not wifi.connect():
#         print("Exiting due to WiFi connection failure.")
#         sys.exit() # Exit the script if connection fails
#     # Rest of your application logic starts here