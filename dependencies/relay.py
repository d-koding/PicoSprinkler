from microdot import Microdot
import machine

class Relay:
    def __init__(self, pinTag="LED", status="Off"):
        self._pinTag = pinTag # refers to the name fo the pin on the pico
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

        

        
