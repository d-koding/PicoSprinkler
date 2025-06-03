import urequests
import ujson as json

"""
A forecast analyzer that saves latitude and longitude data to your personal PicoW and
uses that data to query the NWS weather api for forecasts tomorrow and the next week.

Configs are in ujson because it is more lightweight than yml for the pico W. Make sure to update
latitude and longitude when moving, by running set zipcode and set lat and long. Maybe in the future
I will add a parameter to the initialization of the forecast analyzer to account for moving. 

author: Dylan O'Connor
"""

class ForecastAnalyzer:
    def __init__(self, config_file):
        self.config_file = config_file
        self._zipcode = None
        self._latitude = None
        self._longitude = None
        self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r') as file:
                config = json.load(file)
                self._zipcode = config.get('zipcode')
                self._latitude = config.get('latitude')
                self._longitude = config.get('longitude')
                print(f"Config loaded: ZIP Code: {self._zipcode}, Latitude: {self._latitude}, Longitude: {self._longitude}")
        except Exception as e:
            print(f"Error loading config: {e}")

    def save_config(self):
        try:
            config = {
                'zipcode': self._zipcode,
                'latitude': self._latitude,
                'longitude': self._longitude
            }
            with open(self.config_file, 'w') as file:
                json.dump(config, file)
            print(f"Config saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving config: {e}")


    def get_lat_lon(self):
        return self._latitude, self._longitude

    def set_zipcode(self, zipcode):
        self._zipcode = zipcode
        self.set_lat_lon()
        self.save_config()

    def set_lat_lon(self):
        if not self._zipcode:
            print("ZIP code is not set. Unable to resolve latitude and longitude.")
            return
        self._zipapi = f"http://api.zippopotam.us/us/{self._zipcode}"
        try:
            print(f"Resolving ZIP code: {self._zipcode}")
            response = urequests.get(self._zipapi)
            if response.status_code == 200:
                data = response.json()
                self._latitude = float(data['places'][0]['latitude'])
                self._longitude = float(data['places'][0]['longitude'])
                print(f"Latitude: {self._latitude}, Longitude: {self._longitude}")
                self.save_config()
            else:
                print(f"Failed to resolve ZIP code. Status Code: {response.status_code}")
        except Exception as e:
            print(f"Error resolving ZIP code: {e}")

    def fetch_weather_tomorrow(self):
        if not self._latitude or not self._longitude:
            print("Latitude and longitude are not set. Please resolve them first.")
            return
        
        weather_url = f"https://api.weather.gov/points/{self._latitude},{self._longitude}"
        headers = {
            "User-Agent": "MyWeatherApp/1.0 (https://myweatherapp.com; contact@myweatherapp.com)"
        }
        
        try:
            print("Fetching weather data from NWS...")
            response = urequests.get(weather_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                forecast_url = data['properties']['forecast']
                forecast_response = urequests.get(forecast_url, headers=headers)
                if forecast_response.status_code == 200:
                    forecast_data = forecast_response.json()
                    tomorrow_forecast = forecast_data['properties']['periods'][1]  # Tomorrow's forecast
                    print(f"Tomorrow's Forecast: {tomorrow_forecast['name']}: {tomorrow_forecast['detailedForecast']}")
                else:
                    print(f"Failed to fetch forecast details. Status Code: {forecast_response.status_code}")
            else:
                print(f"Failed to fetch weather data. Status Code: {response.status_code}")
        except Exception as e:
            print(f"Error fetching weather data: {e}")

    # FIX WITH USER AGENT HEADER
    def fetch_weather_next_week(self):
        if not self._latitude or not self._longitude:
            print("Latitude and longitude are not set. Please resolve them first.")
            return
        weather_url = f"https://api.weather.gov/points/{self._latitude},{self._longitude}"
        try:
            print("Fetching weather data from NWS...")
            response = urequests.get(weather_url)
            if response.status_code == 200:
                data = response.json()
                forecast_url = data['properties']['forecast']
                forecast_response = urequests.get(forecast_url)
                if forecast_response.status_code == 200:
                    forecast_data = forecast_response.json()
                    print("Next Week's Forecast:")
                    for period in forecast_data['properties']['periods']:
                        print(f"{period['name']}: {period['detailedForecast']}")
                else:
                    print(f"Failed to fetch forecast details. Status Code: {forecast_response.status_code}")
            else:
                print(f"Failed to fetch weather data. Status Code: {response.status_code}")
        except Exception as e:
            print(f"Error fetching weather data: {e}")
