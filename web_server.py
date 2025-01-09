from microdot import Microdot
import sys
import urequests
from wifi_connector import Wifi_Connector
from relay import Relay
import ssl

_WIFI_CONNECTOR = Wifi_Connector() # current defaults to my wifi and password, can chance ssid and password here by updating initialization
_LED = Relay()
_RELAY_MAP = {
    _LED.pinTag(): _LED  
    }

def web_server():

    global _WIFI_CONNECTOR, _RELAY_MAP, _LED

    if not (_WIFI_CONNECTOR.connect()):
        print(f"wireless connection failed")
        sys.exit()

    app = Microdot()

    @app.route('/activate_pin/<pin_tag>', methods=['GET'])
    def activate_pin(request, pin_tag):

        print(f"Received request to activate pin: {pin_tag}")
        
        led = _RELAY_MAP.get(pin_tag)
        
        if led is not None:
            led.turn_on()
            return f"Successfully activated pin {pin_tag}", 200

        error_message = f"Error: {pin_tag} does not exist"
        print(error_message)
        return error_message, 404

    @app.route('/deactivate_pin/<pin_tag>')
    def deactivate_pin(request, pin_tag):
        print(f"Received request to activate pin: {pin_tag}")
        
        led = _RELAY_MAP.get(pin_tag)
        
        if led is not None:
            led.turn_off()
            return f"Successfully deactivated pin {pin_tag}", 200

        error_message = f"Error: {pin_tag} does not exist"
        print(error_message)
        return error_message, 404

    @app.route('/status/<pin_tag>')
    def get_status(request, pin_tag):
        print(f"Received request to get pin status: {pin_tag}")

        led = _RELAY_MAP.get(pin_tag)

        if led != None:
            return led.status(), 200 # assume all pins have a status
        
        else:
            error_message = f"Error: {pin_tag} does not exist"
            return error_message, 404
    
    # ERROR HANDLERS
    @app.errorhandler(404)
    def not_found(request):
        return {'error': 'resource not found'}, 404




    app.run(port=5000, debug=True)

if __name__ == '__main__':
    web_server()