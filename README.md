# PicoSprinkler
Sprinkler automation through micro python controller

microdot webserver functionality achieved

Dependencies -> currently not working and so files need to be uploaded individually:
Microdot - web server framework

wifi_connector - connects micropico to wifi

relay - a class that maps commands to different pins on the pico, activating, deactivating, and saving status of pins for reference

schedule - **WIP** schedules specific functions to run at different time

forecastAnalyzer - **untested** checks for a */ config.json /* and uses saved latitude and longitude data (found through ziparchive API) to query NWS API for weather forecast tomorrow and in the coming weeks.





