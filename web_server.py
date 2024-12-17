from dependencies.microdot import Microdot
import sys
from dependencies.wifi_connector import Wifi_Connector

_WIFI_CONNECTOR = Wifi_Connector()

def web_server():

    global _WIFI_CONNECTOR
    if not (_WIFI_CONNECTOR.connect()):
        print(f"wireless connection failed")
        sys.exit()

    app = Microdot()

    @app.route('/')
    def index(request):
        return 'Hello, World!'

    app.run(port=5000, debug=True)

if __name__ == '__main__':
    web_server()