import network
import time

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

    def connect(self):
        SSID = self.ssid
        PASSWORD = self.password

        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(SSID, PASSWORD)

        print("Connecting to WiFi...")
        while not wlan.isconnected() and wlan.status() >= 0:
            print(".", end="")
            time.sleep(1)

        if wlan.isconnected():
            print("\nConnected to WiFi!")
            print("IP Address:", wlan.ifconfig()[0])
            return True
        else:
            print("Failed to connect.")
            return False
