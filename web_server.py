from microdot import Microdot
import sys
from wifi_connector import Wifi_Connector
from relay import Relay
import ssl

_WIFI_CONNECTOR = Wifi_Connector() # current defaults to my wifi and password, can chance ssid and password here by updating initialization
_LED = Relay()
_RELAY_MAP = {_LED.pinTag(): _LED}

def web_server():

    global _WIFI_CONNECTOR, _RELAY_MAP, _LED

    if not (_WIFI_CONNECTOR.connect()):
        print(f"wireless connection failed")
        sys.exit()

    app = Microdot()

    @app.route('/activate_pin/LED')
    def activate_pin(request):

        led = _RELAY_MAP.get(request)
        
        if led is not None:
            led.turn_on()
            return "Successfully activated pin"
        
        return "Failed to activate pin: pin does not exist"

    @app.route('/deactivate_pin/<str:pin_tag>')
    def deactivate_pin(pin_tag):
        led = _RELAY_MAP.get(pin_tag)
        
        if led != None:
            led.turn_off()
            return "Successfully deactivated pin"
        
        return "Failed to activate pin: pin does not exist"

    @app.route('/status/<pin_tag>')
    def get_status(pin_tag) -> str:

        if _RELAY_MAP.get(pin_tag) != None:
            return _RELAY_MAP.get(pin_tag).status() # assume all pins have a status
        
        else:
            return "No valid pins found"



    app.run(port=5000, debug=True)

if __name__ == '__main__':
    web_server()