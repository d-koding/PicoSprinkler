from microdot import Microdot
import sys
import urequests
from wifi_connector import Wifi_Connector
from relay import Relay
import ssl
from forecastAnalyzer import ForecastAnalyzer

_WIFI_CONNECTOR = Wifi_Connector() # current defaults to my wifi and password, can chance ssid and password here by updating initialization
_LED = Relay()
_RELAY1 = Relay(pinTag=21)
_RELAY_MAP = {
    _LED.pinTag(): _LED, 
    _RELAY1.pinTag(): _RELAY1
    }

def RunInBackground():
    global _WIFI_CONNECTOR, _RELAY_MAP

    if not (_WIFI_CONNECTOR.connect()):
        print(f"wireless connection failed")
        sys.exit()

    forecast_analyzer = ForecastAnalyzer("config.json")
    
    if not forecast_analyzer._zipcode:
        forecast_analyzer.set_zipcode("94127")
    
    print("setting latitude and longitude...")
    if not forecast_analyzer._latitude or not forecast_analyzer._longitude:
        forecast_analyzer.set_lat_lon()
    
    print("saving config")
    forecast_analyzer.save_config()

    print("Fetching weather for tomorrow:")
    forecast_analyzer.fetch_weather_tomorrow()

    print("\nFetching weather for the next week:")
    forecast_analyzer.fetch_weather_next_week()

if __name__ == '__main__':
    RunInBackground()