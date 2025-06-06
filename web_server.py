import ujson # For saving/loading schedules
import utime # For basic time functions
import ntptime # For synchronizing time with NTP
import uasyncio as asyncio # For concurrent tasks

from microdot import Microdot, Response # Import Microdot and Response
import sys
from wifi_connector import Wifi_Connector
from relay import Relay
import ssl # Note: ssl is not actually used in this server code, can be removed if not used elsewhere

"""
A web server that connects the PicoSprinkler Pico W microcomputer to the
PicoSprinkler app. Allows for pin activation from the app on the pico, as well
as handling errors end to end data transfer.

notes for code cleanup:

why not just normalize the typing of the pin tags being sent in? All strings. 

MAKE AN ON BOOTUP FUNCTION:
Whenever we boot up:
Connect to the internet
Turn off all relays -> Due to the persistent memory of relay states saved on the Pico-Relay-B
Sync Time Properly

author: Dylan O'Connor
"""

# general tasks
_WIFI_CONNECTOR = Wifi_Connector() # current defaults to my wifi and password, can chance ssid and password here by updating initialization
_LED = Relay()
_RELAY1 = Relay(pinTag=21)
_RELAY_MAP = {
    _LED.pinTag(): _LED,
    _RELAY1.pinTag(): _RELAY1
    }

# for scheduling
SCHEDULE_FILE = "schedules.json"
_SCHEDULES = {}

# Make 'app' a global variable so it's accessible everywhere
app = Microdot() # <--- Define app globally here!

def load_schedules():
    global _SCHEDULES
    try:
        with open(SCHEDULE_FILE, 'r') as f:
            _SCHEDULES = ujson.load(f)
        print("Schedules loaded:", _SCHEDULES)
    except (OSError, ValueError): # Handle file not found or invalid JSON
        print("No schedules file found or invalid JSON. Starting fresh.")
        _SCHEDULES = {}

def save_schedules():
    with open(SCHEDULE_FILE, 'w') as f:
        ujson.dump(_SCHEDULES, f)
    print("Schedules saved.")


# No need for a separate web_server() function anymore if you're putting all routes here.
# Just define the routes directly using the global 'app' instance.

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

# SCHEDULING ROUTES

@app.route('/schedule_pin/<pin_tag>', methods=['POST'])
async def schedule_pin(request, pin_tag): # ADDED pin_tag to function arguments
    global _SCHEDULES
    print(f"Incoming POST request to /schedule_pin/{pin_tag}. Headers: {request.headers}")
    print(f"Request Content-Type: {request.headers.get('Content-Type')}")

    try:
        data = request.json

        print(f"Parsed JSON data: {data}")

        # pin_tag is now from the path, not from the JSON body
        action = data.get("action")

        # Basic validation for essential fields
        if action is None: # pin_tag is already guaranteed by the route
            print(f"Missing action in JSON: {data}")
            return Response("Error: 'action' is required in JSON body", status_code=400)

        # Handle string pin_tag for "LED"
        if isinstance(pin_tag, str) and pin_tag.upper() == "LED":
            pin_tag_normalized = "LED"
        else:
            try:
                pin_tag_normalized = int(pin_tag)
            except (ValueError, TypeError):
                print(f"Invalid pin_tag format in path: {pin_tag}")
                return Response("Error: Invalid 'pin_tag' format in URL path. Must be 'LED' or an integer.", status_code=400)


        if pin_tag_normalized not in _RELAY_MAP:
            print(f"Pin tag '{pin_tag_normalized}' does not exist in RELAY_MAP.")
            return Response("Error: Pin does not exist", status_code=404)

        if action == "add_schedule":
            turn_on_time = data.get("turn_on_time")
            turn_off_time = data.get("turn_off_time")
            days = data.get("days")

            if not all([turn_on_time, turn_off_time, days is not None and isinstance(days, list)]):
                print(f"Missing schedule parameters for add_schedule: {data}")
                return Response("Error: Missing 'turn_on_time', 'turn_off_time', or 'days' for add_schedule", status_code=400)

            _SCHEDULES[str(pin_tag_normalized)] = {
                "turn_on_time": turn_on_time,
                "turn_off_time": turn_off_time,
                "days": days,
                "last_triggered_date": ""
            }
            save_schedules()
            print(f"Schedule added/updated for pin {pin_tag_normalized}: {turn_on_time}-{turn_off_time} on {days}")
            return Response(f"Schedule added/updated for pin {pin_tag_normalized}", status_code=200)

        elif action == "delete_schedule":
            if str(pin_tag_normalized) in _SCHEDULES:
                del _SCHEDULES[str(pin_tag_normalized)]
                save_schedules()
                print(f"Schedule deleted for pin {pin_tag_normalized}.")
                return Response(f"Schedule deleted for pin {pin_tag_normalized}", status_code=200)
            else:
                print(f"Schedule not found for pin {pin_tag_normalized}.")
                return Response("Error: Schedule not found for pin", status_code=404)
        else:
            print(f"Invalid schedule action received: {action}")
            return Response("Error: Invalid schedule action. Must be 'add_schedule' or 'delete_schedule'", status_code=400)

    except ValueError as e:
        sys.print_exception(e)
        print(f"JSON Parsing Error: {e}")
        return Response(f"Error parsing JSON: {e}", status_code=400)
    except Exception as e:
        sys.print_exception(e)
        print(f"Unexpected error processing schedule request: {e}")
        return Response(f"Internal Server Error: {e}", status_code=500)

@app.route('/get_schedules', methods=['GET'])
async def get_schedules(request):
    # Returns all currently stored schedules
    return Response(ujson.dumps(_SCHEDULES), status_code=200, headers={'Content-Type': 'application/json'})

# ERROR HANDLERS
@app.errorhandler(404)
async def not_found(request):
    return {'error': 'resource not found'}, 404


# asynchronous tasks
async def sync_time():
    print("Synchronizing time with NTP...")
    try:
        ntptime.settime()
        print("Time synchronized.")

    except Exception as e:
        print(f"Failed to sync time: {e}")
    await asyncio.sleep(3600) # Sync every hour (3600 seconds)

async def schedule_checker():
    global _RELAY_MAP, _SCHEDULES
    print("Starting schedule checker...")

    # --- MANUAL TIME ZONE OFFSET (THIS IS WHERE IT GOES!) ---
    # For San Francisco (PDT) which is UTC-7
    # -7 hours converted to seconds: -7 * 3600 = -25200 seconds
    # Adjust this value if your timezone changes (e.g., for PST in winter)
    TIMEZONE_OFFSET_SECONDS = -7 * 3600 # -25200 for PDT
    while True:
        # Get current UTC epoch seconds
        current_utc_epoch_seconds = utime.time()
        
        # Add the timezone offset to get local epoch seconds
        local_epoch_seconds = current_utc_epoch_seconds + TIMEZONE_OFFSET_SECONDS
        
        # Convert this local epoch time back to a time tuple
        current_time_local_tuple = utime.localtime(local_epoch_seconds)

        # Extract local time components
        current_year = current_time_local_tuple[0]
        current_month = current_time_local_tuple[1]
        current_day_of_month = current_time_local_tuple[2]
        current_hour = current_time_local_tuple[3]
        current_minute = current_time_local_tuple[4] 
        current_weekday = current_time_local_tuple[6] 
        
        # Format local date string
        current_date_str = f"{current_year}-{current_month:02d}-{current_day_of_month:02d}"

        days_of_week_map = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        current_day_name = days_of_week_map[current_weekday]

        print(f"Current Local Time: {current_date_str} {current_hour:02d}:{current_minute:02d} ({current_day_name})")

        for pin_tag, schedule_data in _SCHEDULES.items():
            if pin_tag != "LED":
                pin_tag = int(pin_tag)

            if pin_tag not in _RELAY_MAP:
                continue 
            
            relay = _RELAY_MAP[pin_tag]

            scheduled_days = schedule_data.get("days", [])
            turn_on_str = schedule_data.get("turn_on_time")
            turn_off_str = schedule_data.get("turn_off_time")
            last_triggered_date = schedule_data.get("last_triggered_date", "")

            if current_day_name in scheduled_days:
                try:
                    on_hour, on_minute = map(int, turn_on_str.split(':'))
                    off_hour, off_minute = map(int, turn_off_str.split(':'))
                except ValueError:
                    print(f"Invalid time format for schedule on {pin_tag}. Skipping.")
                    continue

                # Check for turn ON event
                if current_hour == on_hour and current_minute == on_minute:
                    ("turning on")
                    if last_triggered_date != current_date_str: 
                        if relay.status() == "Off":
                            relay.turn_on()
                            _SCHEDULES[str(pin_tag)]["last_triggered_date"] = current_date_str
                            save_schedules()
                            print(f"Scheduled ON for {pin_tag} at {current_date_str} {turn_on_str}")
                # Check for turn OFF event
                elif current_hour == off_hour and current_minute == off_minute:
                    if relay.status() == "On":
                        relay.turn_off()
                        _SCHEDULES[str(pin_tag)]["last_triggered_date"] = current_date_str
                        save_schedules()
                        print(f"Scheduled OFF for {pin_tag} at {current_date_str} {turn_off_str}")

            # Reset last_triggered_date for the next day after both events could have passed
            # This ensures the schedule is re-evaluated daily
            if last_triggered_date == current_date_str:
                # Check if current time has passed both scheduled on and off times
                current_minutes_since_midnight = current_hour * 60 + current_minute
                on_minutes_since_midnight = on_hour * 60 + on_minute
                off_minutes_since_midnight = off_hour * 60 + off_minute

                # Handle case where off_time is on the next day (e.g., on 23:00, off 01:00)
                # For simplicity here, assuming on_time <= off_time on the same day for a single event.
                # If spanning midnight, logic would need to be more complex.
                if current_minutes_since_midnight > max(on_minutes_since_midnight, off_minutes_since_midnight):
                    _SCHEDULES[str(pin_tag)]["last_triggered_date"] = "" # Reset
                    save_schedules()
                    print(f"Resetting schedule for {pin_tag} for next day.")


        await asyncio.sleep(60) # Check every 60 seconds (adjust as needed)

async def main_loop():
    # Load schedules from file when the Pico W boots
    load_schedules()

    asyncio.create_task(sync_time())
    asyncio.create_task(schedule_checker())

    # Run the Microdot web server (this will run concurrently)
    app.run(port=5000, debug=True) # Now 'app' is globally defined

if __name__ == '__main__':
    if not (_WIFI_CONNECTOR.connect()):
        print("Wireless connection failed, exiting.")
        sys.exit()

    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("Server stopped by user.")
    finally:
        pass