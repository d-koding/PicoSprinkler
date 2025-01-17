import urequests

ZIP_CODE = "94127"

ZIP_API_URL = f"http://api.zippopotam.us/us/{ZIP_CODE}"

class ForecastAnalyzer:
    def __init__(self, zipcode):
        self._zipcode = zipcode
        self._latitude, self._longitude = None, None
        self.set_lat_lon()
        self._zipapi = ZIP_API_URL
    
    def get_lat(self):
        return self._latitude

    def get_long(self):
        return self._longitude
    
    def set_zipcode(self, zipcode):
        self._zipcode = zipcode
        return
        
    def set_lat_lon(self):
        print(f"Resolving ZIP code: {self._zipcode}")
        response = urequests.get(ZIP_API_URL)
        if response.status_code == 200:
            data = response.json()
            latitude = data['places'][0]['latitude']
            longitude = data['places'][0]['longitude']
            print(f"Latitude: {latitude}, Longitude: {longitude}")
            self._latitude = latitude
            self._longitude = longitude
            return None
        else:
            print("Failed to resolve ZIP code. Check the ZIP code or try again later.")
            response.close()
            return None

    def fetch_weather(self, latitude, longitude):
        weather_url = f"https://api.weather.gov/points/{latitude},{longitude}"
        print("Fetching weather data from NWS...")
        response = urequests.get(weather_url)
        if response.status_code == 200:
            data = response.json()
            forecast_url = data['properties']['forecast']
            print(f"Fetching detailed forecast from: {forecast_url}")
            
            forecast_response = urequests.get(forecast_url)
            if forecast_response.status_code == 200:
                forecast_data = forecast_response.json()
                periods = forecast_data['properties']['periods']
                for period in periods[:5]:  # Display the next 5 forecast periods
                    print(f"{period['name']}: {period['detailedForecast']}")
                forecast_response.close()
            else:
                print("Failed to fetch forecast details.")
                forecast_response.close()
        else:
            print("Failed to fetch data from NWS API.")
        response.close()

