

from microdot import Microdot
import sys
import urequests
from wifi_connector import Wifi_Connector
from relay import Relay
import ssl

"""
A web server that connects the PicoSprinkler Pico W microcomputer to the
PicoSprinkler app. Allows for pin activation from the app on the pico, as well
as handling errors end to end data transfer.

author: Dylan O'Connor
"""

_WIFI_CONNECTOR = Wifi_Connector() # current defaults to my wifi and password, can chance ssid and password here by updating initialization
_LED = Relay()
_RELAY1 = Relay(pinTag=21)
_RELAY_MAP = {
    _LED.pinTag(): _LED, 
    _RELAY1.pinTag(): _RELAY1
    }

def web_server():

    global _WIFI_CONNECTOR, _RELAY_MAP

    if not (_WIFI_CONNECTOR.connect()):
        print(f"wireless connection failed")
        sys.exit()

    app = Microdot()

    @app.route('/activate_pin/<pin_tag>', methods=['GET'])
    async def activate_pin(request, pin_tag):

        print(f"Received request to activate pin: {pin_tag}")

        if pin_tag != "LED":
            pin_tag = int(pin_tag)
        
        pin = _RELAY_MAP.get(pin_tag)
        
        if pin is not None:
            pin.turn_on()
            return f"Successfully activated pin {pin_tag}", 200

        error_message = f"Error: {pin_tag} does not exist"
        print(error_message)
        return error_message, 404

    @app.route('/deactivate_pin/<pin_tag>', methods=['GET'])
    async def deactivate_pin(request, pin_tag):
        print(f"Received request to activate pin: {pin_tag}")

        if pin_tag != "LED":
            pin_tag = int(pin_tag)
        
        pin = _RELAY_MAP.get(pin_tag)
        
        if pin is not None:
            pin.turn_off()
            return f"Successfully deactivated pin {pin_tag}", 200

        error_message = f"Error: {pin_tag} does not exist"
        print(error_message)
        return error_message, 404

    @app.route('/status/<pin_tag>')
    async def get_status(request, pin_tag):
        print(f"Received request to get pin status: {pin_tag}")

        if pin_tag != "LED":
            pin_tag = int(pin_tag)

        pin = _RELAY_MAP.get(pin_tag)

        if pin != None:
            return pin.status(), 200 # assume all pins have a status
        
        else:
            error_message = f"Error: {pin_tag} does not exist"
            return error_message, 404
    
    # ERROR HANDLERS
    @app.errorhandler(404)
    async def not_found(request):
        return {'error': 'resource not found'}, 404




    app.run(port=5000, debug=True)

if __name__ == '__main__':
    web_server()