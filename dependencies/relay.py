from microdot import Microdot
import machine

"""
Relay class controls pins on Pico W, turning them off and on as well as
saving the status of those pins 

author: Dylan O'Connor
"""

class Relay:
    def __init__(self, pinTag="LED", status="Off"):
        self._pinTag = pinTag # refers to the name of the pin on the pico
        self._status = status
    
    def turn_on(self):
        led = machine.Pin(self._pinTag, machine.Pin.OUT)
        self._status = "On"
        led.on()
    
    def turn_off(self):
        led = machine.Pin(self._pinTag, machine.Pin.OUT)
        self._status = "Off"
        led.off()
    
    def status(self):
        return self._status

    def pinTag(self):
        return self._pinTag

        

        
