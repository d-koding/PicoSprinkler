import network
import time

# WiFi credentials
SSID = 'DALEWOOD_5G'
PASSWORD = 'F@RG0000'

# Connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

# Wait for connection
print("Connecting to WiFi...")
while not wlan.isconnected() and wlan.status() >= 0:
    print(".", end="")
    time.sleep(1)

# Print connection status
if wlan.isconnected():
    print("\nConnected to WiFi!")
    print("IP Address:", wlan.ifconfig()[0])
else:
    print("Failed to connect.")
