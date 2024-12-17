import network
import socket
import time

# WiFi credentials
SSID = 'DALEWOOD_5G'
PASSWORD = 'F@RG0000'

# Connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

print("Connecting to WiFi...")
while not wlan.isconnected() and wlan.status() >= 0:
    print(".", end="")
    time.sleep(1)

print("\nConnected to WiFi!")
print("IP Address:", wlan.ifconfig()[0])

# HTML response
html = """\
HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html>
<head>
    <title>Pico W Web Server</title>
</head>
<body>
    <h1>Hello, World!</h1>
    <p>This is a web server running on Raspberry Pi Pico W.</p>
</body>
</html>
"""

# Setup socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

print("Listening on", addr)

# Listen for connections
while True:
    try:
        conn, addr = s.accept()
        print("Client connected from", addr)
        request = conn.recv(1024)
        print("Request:", request)

        conn.send(html)
        conn.close()

    except Exception as e:
        print("Error:", e)
        conn.close()
