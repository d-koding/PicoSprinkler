import ujson # For saving/loading schedules and Wi-Fi config
import utime # For basic time functions
import ntptime # For synchronizing time with NTP
import uasyncio as asyncio # For concurrent tasks

from microdot import Microdot, Response # Import Microdot and Response
import sys
from wifi_connector import Wifi_Connector
from accesspoint import APModeManager
from relay import Relay
# Removed unused 'ssl' import

"""
A web server that connects the PicoSprinkler Pico W microcomputer to the
PicoSprinkler app. Allows for pin activation from the app on the pico, as well
as handling errors end to end data transfer.

author: Dylan O'Connor
"""

# --- Configuration ---
# AP Mode Configuration
AP_SSID = "PicoSprinklerAP"
AP_PASSWORD = "ILOVEPICO!"
AP_IP_ADDRESS = "192.168.4.1"

# File for persisting Wi-Fi credentials
WIFI_CONFIG_FILE = "wifi_config.json"

# --- General Setup ---
_AP_MANAGER = APModeManager(ssid=AP_SSID, password=AP_PASSWORD, ip_address=AP_IP_ADDRESS)

# general tasks
_WIFI_CONNECTOR = Wifi_Connector() # current defaults to my wifi and password, can change ssid and password here by updating initialization
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

# --- Wi-Fi Configuration Persistence Helper Functions ---
def save_wifi_credentials(ssid, password):
    """Saves the given Wi-Fi SSID and password to a file for persistence."""
    try:
        with open(WIFI_CONFIG_FILE, 'w') as f:
            ujson.dump({"ssid": ssid, "password": password}, f)
        print("Wi-Fi credentials saved successfully.")
    except Exception as e:
        print(f"Error saving Wi-Fi credentials: {e}")

def load_wifi_credentials():
    """Loads Wi-Fi SSID and password from the configuration file."""
    try:
        with open(WIFI_CONFIG_FILE, 'r') as f:
            config = ujson.load(f)
            return config.get("ssid"), config.get("password")
    except (OSError, ValueError):
        # OSError: File not found (e.g., first boot)
        # ValueError: Invalid JSON in file
        print("No Wi-Fi config file found or invalid JSON. Starting fresh.")
        return None, None
    except Exception as e:
        print(f"Unexpected error loading Wi-Fi credentials: {e}")
        return None, None

# --- Schedule Management Functions ---
def load_schedules():
    """Loads schedules from the schedules.json file."""
    global _SCHEDULES
    try:
        with open(SCHEDULE_FILE, 'r') as f:
            _SCHEDULES = ujson.load(f)
        print("Schedules loaded:", _SCHEDULES)
    except (OSError, ValueError): # Handle file not found or invalid JSON
        print("No schedules file found or invalid JSON. Starting fresh.")
        _SCHEDULES = {}

def save_schedules():
    """Saves current schedules to the schedules.json file."""
    with open(SCHEDULE_FILE, 'w') as f:
        ujson.dump(_SCHEDULES, f)
    print("Schedules saved.")

def turn_off_all_relays():
    """Ensures all connected relays are turned off."""
    print("Turning off all relays...")
    for pin in _RELAY_MAP.values():
        pin.turn_off()
    print("All relays off.")

# --- Microdot Web Server Routes ---

@app.route('/configure_wifi', methods=['POST'])
async def configure_wifi(request):
    """
    Handles POST requests to configure the PicoSprinkler's connection to a home Wi-Fi network.
    Expected JSON body: {"ssid": "YourWifiName", "password": "YourWifiPassword"}
    """
    global _AP_MANAGER, _WIFI_CONNECTOR # Declare globals to modify them

    print(f"Received Wi-Fi configuration request.")
    try:
        data = request.json
        ssid = data.get("ssid")
        password = data.get("password")

        if not ssid:
            print("Error: SSID is required in Wi-Fi configuration request.")
            return Response("Error: 'ssid' is required.", status_code=400)

        print(f"Attempting to connect to home Wi-Fi: {ssid}")

        # If currently in AP mode, disconnect from it before trying client mode
        if _AP_MANAGER.is_ap_active: # Assuming APModeManager has a way to check if AP is active
            _AP_MANAGER.disconnect()
            print("Disconnected from AP mode.")
            await asyncio.sleep(0.5) # Give a moment for network interface to settle

        # Update the Wifi_Connector instance with the new credentials
        _WIFI_CONNECTOR.ssid = ssid
        _WIFI_CONNECTOR.password = password

        # Attempt to connect to the new home Wi-Fi
        if _WIFI_CONNECTOR.connect():
            save_wifi_credentials(ssid, password) # Save for persistence on successful connection
            ip_address = _WIFI_CONNECTOR.get_ip_address()
            print(f"Successfully connected to home Wi-Fi: {ssid}. IP: {ip_address}")
            # If successful, the PicoSprinkler should now be on the home network.
            return Response(f"Successfully connected to Wi-Fi: {ssid}. Device IP: {ip_address}", status_code=200)
        else:
            print(f"Failed to connect to home Wi-Fi: {ssid}. Re-enabling AP mode.")
            # If connection fails, re-enable AP mode so the user can try again
            await asyncio.sleep(1) # Give a moment before re-starting AP
            _AP_MANAGER.setup_ap_mode() # Re-activate AP for retry
            return Response(f"Failed to connect to Wi-Fi: {ssid}. Please re-connect to PicoSprinkler AP and try again.", status_code=500)

    except ValueError as e:
        sys.print_exception(e)
        print(f"JSON Parsing Error in /configure_wifi: {e}")
        return Response(f"Error parsing JSON: {e}", status_code=400)
    except Exception as e:
        sys.print_exception(e)
        print(f"Unexpected error in /configure_wifi: {e}")
        return Response(f"Internal Server Error: {e}", status_code=500)


@app.route('/activate_pin/<pin_tag>', methods=['GET'])
async def activate_pin(request, pin_tag):
    """Activates a specified relay pin."""
    print(f"Received request to activate pin: {pin_tag}")

    # Normalize pin_tag: "LED" remains string, others converted to int
    if pin_tag != "LED":
        try:
            pin_tag = int(pin_tag)
        except ValueError:
            error_message = f"Error: Invalid pin_tag format '{pin_tag}'. Must be 'LED' or an integer."
            print(error_message)
            return error_message, 400

    pin = _RELAY_MAP.get(pin_tag)

    if pin is not None:
        pin.turn_on()
        return f"Successfully activated pin {pin_tag}", 200

    error_message = f"Error: Pin '{pin_tag}' does not exist"
    print(error_message)
    return error_message, 404

@app.route('/deactivate_pin/<pin_tag>', methods=['GET'])
async def deactivate_pin(request, pin_tag):
    """Deactivates a specified relay pin."""
    print(f"Received request to deactivate pin: {pin_tag}")

    # Normalize pin_tag
    if pin_tag != "LED":
        try:
            pin_tag = int(pin_tag)
        except ValueError:
            error_message = f"Error: Invalid pin_tag format '{pin_tag}'. Must be 'LED' or an integer."
            print(error_message)
            return error_message, 400

    pin = _RELAY_MAP.get(pin_tag)

    if pin is not None:
        pin.turn_off()
        return f"Successfully deactivated pin {pin_tag}", 200

    error_message = f"Error: Pin '{pin_tag}' does not exist"
    print(error_message)
    return error_message, 404

@app.route('/status/<pin_tag>')
async def get_status(request, pin_tag):
    """Gets the current status of a specified relay pin."""
    print(f"Received request to get pin status: {pin_tag}")

    # Normalize pin_tag
    if pin_tag != "LED":
        try:
            pin_tag = int(pin_tag)
        except ValueError:
            error_message = f"Error: Invalid pin_tag format '{pin_tag}'. Must be 'LED' or an integer."
            print(error_message)
            return error_message, 400

    pin = _RELAY_MAP.get(pin_tag)

    if pin is not None:
        return pin.status(), 200 # assume all pins have a status
    else:
        error_message = f"Error: Pin '{pin_tag}' does not exist"
        return error_message, 404

# --- SCHEDULING ROUTES ---

@app.route('/schedule_pin/<pin_tag>', methods=['POST'])
async def schedule_pin(request, pin_tag):
    """
    Handles scheduling operations (add/delete) for a specific pin.
    Expects JSON body with 'action' and schedule details.
    """
    global _SCHEDULES
    print(f"Incoming POST request to /schedule_pin/{pin_tag}. Headers: {request.headers}")
    print(f"Request Content-Type: {request.headers.get('Content-Type')}")

    try:
        data = request.json
        print(f"Parsed JSON data: {data}")

        action = data.get("action")

        if action is None:
            print(f"Missing 'action' in JSON: {data}")
            return Response("Error: 'action' is required in JSON body", status_code=400)

        # Normalize pin_tag from URL path
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
                "last_triggered_date": "" # Reset for new schedule
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
    """Returns all currently stored schedules as a JSON response."""
    return Response(ujson.dumps(_SCHEDULES), status_code=200, headers={'Content-Type': 'application/json'})

# --- ERROR HANDLERS ---
@app.errorhandler(404)
async def not_found(request):
    """Handles 404 Not Found errors."""
    return {'error': 'resource not found'}, 404

# --- Asynchronous Background Tasks ---
async def sync_time():
    """Synchronizes the PicoSprinkler's time with an NTP server."""
    print("Synchronizing time with NTP...")
    try:
        ntptime.settime()
        print("Time synchronized.")
    except Exception as e:
        print(f"Failed to sync time: {e}")
    await asyncio.sleep(3600) # Sync every hour (3600 seconds)

async def schedule_checker():
    """Periodically checks and applies scheduled relay operations."""
    global _RELAY_MAP, _SCHEDULES
    print("Starting schedule checker...")

    # --- MANUAL TIME ZONE OFFSET ---
    # For San Francisco (PDT) which is UTC-7
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

        # print(f"Current Local Time: {current_date_str} {current_hour:02d}:{current_minute:02d} ({current_day_name})")

        for pin_tag, schedule_data in _SCHEDULES.items():
            # Ensure pin_tag is correctly typed for map lookup
            if pin_tag != "LED":
                try:
                    pin_tag_typed = int(pin_tag)
                except ValueError:
                    print(f"Skipping schedule for invalid pin_tag format: {pin_tag}")
                    continue
            else:
                pin_tag_typed = pin_tag


            if pin_tag_typed not in _RELAY_MAP:
                print(f"Schedule found for non-existent pin: {pin_tag}. Removing from schedules.")
                del _SCHEDULES[str(pin_tag)] # Clean up invalid schedules
                save_schedules()
                continue

            relay = _RELAY_MAP[pin_tag_typed]

            scheduled_days = schedule_data.get("days", [])
            turn_on_str = schedule_data.get("turn_on_time")
            turn_off_str = schedule_data.get("turn_off_time")
            last_triggered_date = schedule_data.get("last_triggered_date", "")

            if current_day_name in scheduled_days:
                try:
                    on_hour, on_minute = map(int, turn_on_str.split(':'))
                    off_hour, off_minute = map(int, turn_off_str.split(':'))
                except ValueError:
                    print(f"Invalid time format for schedule on {pin_tag_typed}. Skipping.")
                    continue

                # Check for turn ON event
                if current_hour == on_hour and current_minute == on_minute:
                    if last_triggered_date != current_date_str: # Only trigger once per day
                        if relay.status() == "Off":
                            relay.turn_on()
                            _SCHEDULES[str(pin_tag_typed)]["last_triggered_date"] = current_date_str
                            save_schedules()
                            print(f"Scheduled ON for {pin_tag_typed} at {current_date_str} {turn_on_str}")
                # Check for turn OFF event
                elif current_hour == off_hour and current_minute == off_minute:
                    if last_triggered_date != current_date_str: # Only trigger once per day
                        if relay.status() == "On":
                            relay.turn_off()
                            _SCHEDULES[str(pin_tag_typed)]["last_triggered_date"] = current_date_str
                            save_schedules()
                            print(f"Scheduled OFF for {pin_tag_typed} at {current_date_str} {turn_off_str}")

            # Reset last_triggered_date for the next day to allow re-triggering
            # This logic assumes on/off times occur within the same 24-hour period.
            if last_triggered_date == current_date_str:
                # If current time has passed both the on and off times for the current day
                current_minutes_since_midnight = current_hour * 60 + current_minute
                on_minutes_since_midnight = on_hour * 60 + on_minute
                off_minutes_since_midnight = off_hour * 60 + off_minute

                # Consider if the off time is actually on the next day
                if off_minutes_since_midnight < on_minutes_since_midnight: # Schedule spans midnight
                    if current_minutes_since_midnight >= on_minutes_since_midnight or \
                       current_minutes_since_midnight < off_minutes_since_midnight:
                        # Still within the active period or hasn't passed the off time yet for next day's turn off
                        pass # Do nothing, wait for next day or off time
                    else: # Passed off time for this day/cycle
                        _SCHEDULES[str(pin_tag_typed)]["last_triggered_date"] = "" # Reset
                        save_schedules()
                        # print(f"Resetting midnight-spanning schedule for {pin_tag_typed} for next day.")
                else: # Schedule on same day
                    if current_minutes_since_midnight > max(on_minutes_since_midnight, off_minutes_since_midnight):
                        _SCHEDULES[str(pin_tag_typed)]["last_triggered_date"] = "" # Reset
                        save_schedules()
                        # print(f"Resetting same-day schedule for {pin_tag_typed} for next day.")


        await asyncio.sleep(60) # Check every 60 seconds (adjust as needed)

async def main_loop():
    """The main execution loop for the PicoSprinkler application."""
    print("--- PicoSprinkler Bootup Sequence ---")

    # 1. Turn off all relays on bootup
    turn_off_all_relays()

    # 2. Load schedules from file
    load_schedules()

    # 3. Attempt to connect to saved home Wi-Fi first
    saved_ssid, saved_password = load_wifi_credentials()
    if saved_ssid and saved_password:
        print(f"Attempting to connect to saved home Wi-Fi: {saved_ssid}...")
        _WIFI_CONNECTOR.ssid = saved_ssid
        _WIFI_CONNECTOR.password = saved_password
        if _WIFI_CONNECTOR.connect():
            print(f"Connected to saved home WiFi. IP: {_WIFI_CONNECTOR.get_ip_address()}")
            asyncio.create_task(sync_time()) # Sync time only if connected to the internet
        else:
            print("Failed to connect to saved home WiFi. Starting AP mode for initial setup.")
            # If saved connection fails, fall back to AP mode for new setup
            if not _AP_MANAGER.setup_ap_mode():
                print("AP mode setup failed. Exiting.")
                sys.exit() # Critical failure
    else:
        print("No saved home WiFi credentials found. Starting AP mode for initial setup.")
        # No saved credentials, directly start AP mode
        if not _AP_MANAGER.setup_ap_mode():
            print("AP mode setup failed. Exiting.")
            sys.exit() # Critical failure

    print("--- Bootup Sequence Complete. Starting Services ---")

    # Start the async tasks
    asyncio.create_task(schedule_checker()) # Schedule checker runs independently

    # Run the Microdot web server (this will run concurrently)
    app.run(port=5000, debug=True) # 'app' is globally defined

if __name__ == '__main__':
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("Server and tasks stopped by user (KeyboardInterrupt).")
    finally:
        # Clean up or deactivate things if necessary on exit
        _AP_MANAGER.disconnect() # Ensure AP mode is gracefully shut down if active
        turn_off_all_relays()
        print("PicoSprinkler application terminated.")
