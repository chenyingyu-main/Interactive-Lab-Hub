#!/usr/bin/env python3
"""
Pixel Grid Pi Publisher
Reads RGB color sensor and publishes to collaborative pixel grid
Each Pi is identified by MAC address and gets a stable position in the grid
"""

import board
import busio
import adafruit_apds9960.apds9960
import time
import paho.mqtt.client as mqtt
import uuid
import signal
import ssl
import json
import socket
import subprocess
import math


# for joystick
import qwiic_joystick
import time
import sys



# Optional: Display support (comment out if no display)
try:
    import digitalio
    from PIL import Image, ImageDraw, ImageFont
    import adafruit_rgb_display.st7789 as st7789
    DISPLAY_AVAILABLE = True
except ImportError:
    DISPLAY_AVAILABLE = False
    print("Display libraries not available - running in headless mode")


# MQTT Configuration
MQTT_BROKER = 'farlab.infosci.cornell.edu'
MQTT_PORT = 1883  # Changed to non-TLS port
MQTT_TOPIC = 'IDD/kitchen-instrument'
MQTT_USERNAME = 'idd'
MQTT_PASSWORD = 'device@theFarm'

# Publishing interval (seconds)
PUBLISH_INTERVAL = 0.1

# Joystick center position (calibrate based on your joystick)
CENTER_X = 519
CENTER_Y = 517

# Minimum radius to consider as "stirring" (not just resting at center)
MIN_RADIUS = 200  # Adjust this based on how far from center you move

class CircleDetector:
    """Detects when joystick completes a full circle"""
    
    def __init__(self):
        self.last_angle = None
        self.accumulated_angle = 0
        self.circles_completed = 0
        self.in_motion = False

        # [New] track timing for speed calculation
        self.circle_start_time = None
        self.last_circle_duration = 0   # time (sec) for last completed circle
        self.last_circle_speed = 0      # average speed (degrees/sec) for last completed circle

        # [NEW] real-time speed calculation
        self.angle_history = []  # store the history of (time, angle change)
        self.history_window = 0.5  # use 0.5 seconds window to calculate speed
        self.current_speed = 0  # real-time angle speed (degrees/sec)
        
    def get_angle(self, x, y):
        """Calculate angle from center (-180 to 180 degrees)"""
        dx = x - CENTER_X
        dy = y - CENTER_Y
        
        # Check if we're far enough from center
        radius = math.sqrt(dx*dx + dy*dy)
        if radius < MIN_RADIUS:
            return None, radius
        
        # Calculate angle in degrees
        angle = math.degrees(math.atan2(dy, dx))
        return angle, radius
    
    def update(self, x, y):
        """Update with new position and return if circle completed"""
        current_time = time.time()
        angle, radius = self.get_angle(x, y)
        
        # Not moving enough to count
        # don't forget to return to IDLE state
        if angle is None:
            self.current_speed = 0 
            self.in_motion = False
            return False, 0, "IDLE"
        
        self.in_motion = True

        # [New] start timing for the new circle
        if self.circle_start_time is None:
            self.circle_start_time = time.time()
        
        # First valid reading the angle
        if self.last_angle is None:
            self.last_angle = angle
            return False, radius, "IDLE"
        
        # Calculate angle difference
        diff = angle - self.last_angle
        
        # Handle wraparound (-180 to 180 boundary)
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360


        # [NEW] record the angle change to history
        self.angle_history.append((current_time, diff))
        
        # [NEW] clear old data (beyond history_window)
        self.angle_history = [(t, d) for t, d in self.angle_history 
                              if current_time - t <= self.history_window]
        
        # [NEW] calculate real-time speed (average angular speed over recent time window)
        if len(self.angle_history) >= 2:
            total_angle = sum(d for _, d in self.angle_history)
            time_span = current_time - self.angle_history[0][0]
            if time_span > 0:
                self.current_speed = abs(total_angle / time_span)  # degrees/sec

        
        # Accumulate the angle change
        self.accumulated_angle += diff
        self.last_angle = angle


        # [NEW] identify the speed state based on current speed
        if self.current_speed < 200:  
            # adjust threshold as needed 
            # (but if we just want to send the speed, there's no necessity to classify)
            speed_state = "SLOW"
        else:
            speed_state = "FAST"
        
        # Check if completed a full circle (360 degrees in either direction)
        circle_completed = False
        if abs(self.accumulated_angle) >= 360:
            self.circles_completed += 1
            circle_completed = True
            # Reset but keep the remainder
            self.accumulated_angle = self.accumulated_angle % 360
            print(f"\n HIT!! Circle #{self.circles_completed} completed! \n")


            # [New] calculate speed
            current_time = time.time()
            self.last_circle_duration = current_time - self.circle_start_time
            self.last_circle_speed = 360 / self.last_circle_duration  # degrees per second
            print(f"   Duration: {self.last_circle_duration:.2f}s")
            print(f"   Speed: {self.last_circle_speed:.1f} degree/s")
            print(f"   RPM: {(60/self.last_circle_duration):.1f}\n")
            # [New] reset circle timer
            self.circle_start_time = current_time
        
        return circle_completed, radius, speed_state


def get_mac_address():
    """Get the MAC address of the primary network interface"""
    try:
        # Try to get MAC from eth0 or wlan0
        result = subprocess.run(['cat', '/sys/class/net/eth0/address'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        
        result = subprocess.run(['cat', '/sys/class/net/wlan0/address'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"Error getting MAC address: {e}")
    
    # Fallback to UUID if MAC can't be determined
    return str(uuid.uuid1())


def get_ip_address():
    """Get the IP address of this device"""
    try:
        # Connect to external host to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


def setup_display():
    """Setup the MiniPiTFT display if available"""
    if not DISPLAY_AVAILABLE:
        return None, None, None, None, None
    
    try:
        # Configuration for CS and DC pins
        # Use GPIO5 instead of CE0 to avoid SPI conflicts
        cs_pin = digitalio.DigitalInOut(board.D5)   # GPIO5 (PIN 29)
        dc_pin = digitalio.DigitalInOut(board.D25)  # GPIO25 (PIN 22)
        reset_pin = None

        # Config for display baudrate
        BAUDRATE = 64000000

        backlight = digitalio.DigitalInOut(board.D22)
        backlight.switch_to_output()
        backlight.value = True
        
        # Buttons with pull-ups (active LOW when pressed)
        buttonA = digitalio.DigitalInOut(board.D23)
        buttonB = digitalio.DigitalInOut(board.D24)
        buttonA.switch_to_input(pull=digitalio.Pull.UP)
        buttonB.switch_to_input(pull=digitalio.Pull.UP)

        # Setup SPI bus using hardware SPI
        spi = board.SPI()

        # Create the ST7789 display
        disp = st7789.ST7789(
            spi,
            cs=cs_pin,
            dc=dc_pin,
            rst=reset_pin,
            baudrate=BAUDRATE,
            width=135,
            height=240,
            x_offset=53,
            y_offset=40,
            rotation=90  # Rotate 90 degrees for vertical orientation
        )

        # After rotation, width and height are swapped
        width = 240
        height = 135
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)
        
        print("[OK] Display initialized (240x135 rotated)")

        return disp, draw, image, buttonA, buttonB
    except Exception as e:
        print(f"Error setting up display: {e}")
        return None, None, None, None, None


def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        print(f"[OK] Connected to MQTT broker: {MQTT_BROKER}")
    else:
        print(f"[ERROR] Connection failed with code {rc}")

def runExample_joystick():
    #? This is the joystick example from Lab 4

	print("\nSparkFun qwiic Joystick   Example 1\n")
	myJoystick = qwiic_joystick.QwiicJoystick()

	if myJoystick.connected == False:
		print("The Qwiic Joystick device isn't connected to the system. Please check your connection", \
			file=sys.stderr)
		return

	myJoystick.begin()

	print("Initialized. Firmware Version: %s" % myJoystick.version)

	while True:

		print("X: %d, Y: %d, Button: %d" % ( \
					myJoystick.horizontal, \
					myJoystick.vertical, \
					myJoystick.button))

		time.sleep(.5)

def main():
    print("=" * 50)
    print("  Kitchen Instrument - Pi Publisher")
    print("=" * 50)
    
    # Get device identifiers
    mac_address = get_mac_address()
    ip_address = get_ip_address()
    
    print(f"MAC Address: {mac_address}")
    print(f"IP Address: {ip_address}")
    print(f"MQTT Topic: {MQTT_TOPIC}")
    print()

    # Setup Joystick
    print("Initializing joystick...")
    myJoystick = qwiic_joystick.QwiicJoystick()
    
    if myJoystick.connected == False:
        print("[ERROR] The Qwiic Joystick device isn't connected to the system. Please check your connection", 
            file=sys.stderr)
        return
    
    myJoystick.begin()
    print(f"[OK] Joystick initialized. Firmware Version: {myJoystick.version}")

    # Setup Circle Detector
    detector = CircleDetector()
    
    # Setup MQTT client
    print("Connecting to MQTT broker...")
    client = mqtt.Client(str(uuid.uuid1()))
    # Remove TLS for non-encrypted connection
    # client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    
    try:
        client.connect(MQTT_BROKER, port=MQTT_PORT, keepalive=60)
        client.loop_start()
        # Wait a bit for connection to establish
        time.sleep(2)
        
        # Check if connected
        if client.is_connected():
            print(f"[OK] MQTT connected and ready")
        else:
            print("[WARNING] MQTT connection pending...")
    except Exception as e:
        print(f"[ERROR] Failed to connect to MQTT broker: {e}")
        return
    
    # Graceful exit handler
    def signal_handler(signum, frame):
        print("\nShutting down gracefully...")
        client.loop_stop()
        client.disconnect()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\n" + "=" * 50)
    print("Streaming kitchen instrument data...")
    print(f"Update frequency: {PUBLISH_INTERVAL}s ({1/PUBLISH_INTERVAL:.1f} updates/sec)")
    print("Press Ctrl+C to exit")
    print("=" * 50 + "\n")
    
    last_publish_time = 0
    
    # Main loop
    while True:
        try:
            #! Get current time (don't call multiple times!!!!)
            current_time = time.time()

            # Read joystick values
            x = myJoystick.horizontal
            y = myJoystick.vertical
            button = myJoystick.button

            utensil = 'mixing_bowl'

            #? ----------------------------------------------------
            #? this is the detecting hit part, 
            #? if the joystick makes a full circle, we will return hit
            
            # Update circle detector
            hit, radius, speed_state = detector.update(x, y)
            # Calculate progress percentage (0-100%)
            progress = (abs(detector.accumulated_angle) / 360.0) * 100
            
            # Display status in terminal
            if current_time - last_publish_time >= PUBLISH_INTERVAL:
                status = "STIRRING" if detector.in_motion else "IDLE"
                print(f"{status} [{speed_state}] | X:{x:4d} Y:{y:4d} | "
                    f"Speed:{detector.current_speed:.1f} degree/s | "
                    f"Progress:{progress:5.1f}% | Circles:{detector.circles_completed}")
                
                # last_publish_time = current_time
                #! we will update last_publish_time after publishing to MQTT
            
            # time.sleep(0.05)  # 20Hz update rate
            #! don't sleep here, we will control the publishing rate later

            #? end of detecting hit part
            #? ----------------------------------------------------

            
            # Publish to MQTT at specified interval
            if current_time - last_publish_time >= PUBLISH_INTERVAL:
                # Re-create compact payload for MQTT (without indentation)
                mqtt_payload = json.dumps({
                    'mac': mac_address,
                    'ip': ip_address,
                    'utensil': utensil,
                    'data': {
                        'x': x,
                        'y': y,
                        'speed': round(detector.current_speed, 1),  # send the speed 
                        'radius': round(radius, 1),  # optional: send radius
                    },
                    # 'mixing': {
                    #     'speed_state': speed_state,  # "IDLE", "SLOW", "MEDIUM", "FAST"
                    #     'current_speed': round(detector.current_speed, 1),  # degrees/sec
                    #     'circles': detector.circles_completed,
                    #     'progress': round(progress, 1)
                    # },
                    'timestamp': int(current_time)
                })
                
                # Publish to MQTT
                result = client.publish(MQTT_TOPIC, mqtt_payload)
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    # print(f"[OK] Streaming: RGB({r:3d}, {g:3d}, {b:3d}) | {mac_address[:17]} | rc:{result.rc} mid:{result.mid}")
                    print(f"     Payload: {mqtt_payload}")
                else:
                    print(f"[ERROR] Publish failed: rc={result.rc}")
                    if not client.is_connected():
                        print("[ERROR] MQTT client disconnected! Attempting to reconnect...")
                        try:
                            client.reconnect()
                        except Exception as e:
                            print(f"[ERROR] Reconnect failed: {e}")
                
                last_publish_time = current_time
            
            # Small sleep to prevent CPU spinning (shorter than both intervals)
            time.sleep(0.05)  # 20Hz main loop
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)


if __name__ == '__main__':
    main()
