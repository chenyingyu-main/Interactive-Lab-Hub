"""
MQTT Kitchen Rhythm Game
Physical cooking utensils as rhythm game controllers via MQTT
"""

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
from datetime import datetime
from collections import deque
import json
import pygame
import os
from functools import lru_cache
import heapq
import itertools
import threading
import time

from parser import parse_midi_to_rhythm

# ============================================================================
# GLOBAL STATE & CONFIGURATION
# ============================================================================

counter = itertools.count()  # unique ID generator for heap queue

# Chart data and playback control
chart_data = None
chart_thread = None
chart_playing = False
miss_checker_thread = None

# Timing constants (in seconds)
LEAD_TIME = 3  # how early to show notes visually
HIT_WINDOW = 5  # ±150ms window for hitting notes

# Thread-safe note tracking
pending_notes = []
pending_lock = threading.Lock()

# Thread-safe sound rules
sound_rules_lock = threading.Lock()

# Audio initialization
pygame.mixer.init()
print("[OK] Audio system ready")

# Dedicated audio channels for each utensil (prevents interference)
CHANNELS = {
    'pan': pygame.mixer.Channel(0),
    'cutting_board': pygame.mixer.Channel(1),
    'mixing_bowl': pygame.mixer.Channel(2)
}

# Track which utensils are currently playing sounds
playing_state = {
    'pan': False,
    'cutting_board': False,
    'mixing_bowl': False
}

# Sound configuration for each utensil
SOUND_RULES = {
    'pan': {
        'file': 'sounds/pan_sizzle.mp3',
        'threshold': 5,
        'target_value': None  # Will be set by chart (e.g., "low" or "high")
    },
    'cutting_board': {
        'file': 'sounds/knife-stab-pull.mp3',
        'threshold': 0,
        'target_value': None  # Will be set by chart (e.g., button ID)
    },
    'mixing_bowl': {
        'file': 'sounds/whisking.mp3',
        'threshold': 0,
        'target_value': None  # Will be set by chart (e.g., acceleration value)
    }
}

# Flask/SocketIO setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mqtt-viewer-2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Store recent messages for new clients
MAX_MESSAGES = 100
recent_messages = deque(maxlen=MAX_MESSAGES)

# MQTT Configuration
MQTT_BROKER = 'farlab.infosci.cornell.edu'
MQTT_PORT = 1883
MQTT_TOPIC = 'IDD/kitchen-instrument'
MQTT_USERNAME = 'idd'
MQTT_PASSWORD = 'device@theFarm'

mqtt_client = None


# ============================================================================
# SOUND CONDITION CHECKING
# ============================================================================

def should_play(utensil, sensor_data, target, threshold):
    """
    Check if the current sensor data meets the target condition for this utensil.
    
    Args:
        utensil: 'pan', 'cutting_board', or 'mixing_bowl'
        sensor_data: dict of sensor values from MQTT
        target: the target value from the chart (e.g., "low", "high", button ID)
        threshold: numeric threshold for comparison
    
    Returns:
        bool: True if condition is met, False otherwise
    """
    if target is None:
        return False

    if utensil == 'pan':
        # Pan uses rotation sensor
        curr_val = sensor_data.get('rotation', 0)
        if target == "low":
            return curr_val < threshold
        elif target == "high":
            return curr_val > threshold
        # Can add "medium" range if needed
        
    elif utensil == "cutting_board":
        # Cutting board uses button presses
        button_id = str(target)
        return sensor_data.get(button_id, 0) == 1
    
    elif utensil == "mixing_bowl":
        # Mixing bowl uses accelerometer
        return sensor_data.get('x', 0) > target
    
    return False


# ============================================================================
# AUDIO PLAYBACK
# ============================================================================

@lru_cache(maxsize=10)
def load_sound(file_path):
    """Cache loaded sound objects to avoid reloading."""
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return None
    try:
        return pygame.mixer.Sound(file_path)
    except pygame.error as e:
        print(f"[ERROR] Cannot load sound file: {e}")
        return None


def play_sound(utensil, file_path, loop=False):
    """Play a sound for a specific utensil on its dedicated channel."""
    sound = load_sound(file_path)
    if not sound:
        return

    channel = CHANNELS.get(utensil)
    if channel:
        channel.play(sound, loops=-1 if loop else 0)
        print(f"[PLAYING] {utensil}: {file_path}")
    else:
        print(f"[WARN] No channel for utensil '{utensil}'")


def stop_sound(utensil):
    """Stop sound for a specific utensil."""
    channel = CHANNELS.get(utensil)
    if channel:
        channel.stop()
        print(f"[STOPPED] {utensil}")


def close_audio():
    """Cleanly shut down the audio system."""
    pygame.mixer.quit()
    print("[CLOSED] Audio system shut down")


# ============================================================================
# MQTT MESSAGE HANDLING
# ============================================================================

def broadcast_to_web_client(message, topic):
    """Send message to all connected web clients via WebSocket."""
    recent_messages.append(message)
    socketio.emit(topic, message, namespace='/')


def on_connect(client, userdata, flags, rc):
    """MQTT connection callback."""
    if rc == 0:
        print(f'MQTT connected to {MQTT_BROKER}:{MQTT_PORT}')
        client.subscribe(MQTT_TOPIC)
        print(f'Subscribed to {MQTT_TOPIC}')
    else:
        print(f'MQTT connection failed: {rc}')


def on_message(client, userdata, msg):
    """
    MQTT message received - main game logic happens here.
    
    Flow:
    1. Parse MQTT message
    2. Broadcast to frontend for debugging
    3. Check if sensor data triggers sound playback
    4. Check if sensor data hits any pending rhythm game notes
    """
    global playing_state
    
    try:
        # Parse payload as JSON
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            payload_str = json.dumps(payload, indent=2)
            is_json = True
        except:
            payload_str = msg.payload.decode('utf-8', errors='replace')
            is_json = False
        
        # Create message object for frontend debugging
        message = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'topic': msg.topic,
            'payload': payload_str,
            'is_json': is_json
        }
        broadcast_to_web_client(message, 'mqtt_message')

        if not is_json:
            return

        # Extract utensil and sensor data
        utensil = payload.get('utensil', 'unknown')
        sensor_data = payload.get('data', {})
        
        # ====================================================================
        # SOUND PLAYBACK: Check if sensor data triggers sound for this utensil
        # ====================================================================
        with sound_rules_lock:
            rule = SOUND_RULES.get(utensil)
            if rule and rule['target_value'] is not None:
                condition_met = should_play(
                    utensil, 
                    sensor_data, 
                    rule['target_value'], 
                    rule['threshold']
                )
                sound_file = rule['file']

                # Start sound if condition just became true
                if condition_met and not playing_state[utensil]:
                    loop = (utensil == 'pan')  # Pan sizzle loops, others are one-shots
                    play_sound(utensil, sound_file, loop=loop)
                    playing_state[utensil] = True

                # Stop sound if condition is no longer met
                elif not condition_met and playing_state[utensil]:
                    stop_sound(utensil)
                    playing_state[utensil] = False

        # ====================================================================
        # RHYTHM GAME: Check if this sensor reading hits any pending notes
        # ====================================================================
        now = time.time()

        # Get thread-safe copy of pending notes
        with pending_lock:
            notes_copy = list(pending_notes)

        # Check each pending note for this utensil
        for note in notes_copy:
            if note["utensil"] != utensil:  # Wrong instrument
                continue
            if note["hit"]:  # Already judged
                continue

            # Calculate time difference from expected hit time
            dt = now - note["hit_time"]

            # Too early to judge yet
            if dt < -HIT_WINDOW:
                continue

            # Within hit window - check if sensor condition is met
            with sound_rules_lock:
                rule = SOUND_RULES[utensil]
                if should_play(utensil, sensor_data, note["target"], rule['threshold']):
                    # SUCCESS! Mark as hit
                    with pending_lock:
                        for n in pending_notes:
                            if (n["utensil"] == note["utensil"] and 
                                n["hit_time"] == note["hit_time"] and 
                                not n["hit"]):
                                n["hit"] = True
                                break

                    # Send hit result to frontend
                    socketio.emit("note_result", {
                        "utensil": utensil,
                        "instrument": note["instrument"],
                        "result": "hit",
                        "time": now,
                        "scheduled": note["hit_time"],
                        "accuracy_ms": int(dt * 1000)
                    })
                    print(f"[HIT] {utensil} accuracy {int(dt*1000)}ms")
        
        # Clean up old notes that are past the hit window
        with pending_lock:
            pending_notes[:] = [
                n for n in pending_notes 
                if not n.get("hit") and (now <= n["hit_time"] + HIT_WINDOW)
            ]
                
    except Exception as e:
        print(f'Error processing message: {e}')


# ============================================================================
# MISS DETECTION (runs in separate thread)
# ============================================================================

def note_miss_checker():
    """
    Background thread that checks for missed notes.
    If a note's hit window expires without being hit, mark it as a miss.
    """
    while chart_playing:
        now = time.time()
        
        with pending_lock:
            for note in pending_notes:
                if note["hit"]:
                    continue  # Already judged

                # Note's hit window has expired
                if now > note["hit_time"] + HIT_WINDOW:
                    note["hit"] = True
                    
                    # Send miss result to frontend
                    socketio.emit("note_result", {
                        "instrument": note["instrument"],
                        "utensil": note["utensil"],
                        "result": "miss",
                        "scheduled": note["hit_time"],
                        "actual_time": now
                    })
                    
                    if note['utensil'] == 'pan':  # Debug logging for pan
                        print(f"[MISS] {note['utensil']} missed note at {note['hit_time']}")

        time.sleep(0.01)  # 10ms tick to avoid busy-wait


# ============================================================================
# CHART PLAYBACK (runs in separate thread)
# ============================================================================

def start_chart_playback():
    """Start playing the rhythm chart in a background thread."""
    global chart_thread, chart_playing, miss_checker_thread

    if chart_data is None:
        print("[ERROR] No chart loaded. Call parse_midi_to_rhythm() first.")
        return

    if chart_thread and chart_thread.is_alive():
        print("[WARN] Chart already running.")
        return

    chart_playing = True
    
    # Start chart playback thread
    chart_thread = threading.Thread(target=_chart_loop, daemon=True)
    chart_thread.start()

    # Start miss detection thread
    miss_checker_thread = threading.Thread(target=note_miss_checker, daemon=True)
    miss_checker_thread.start()


def stop_chart_playback():
    """Stop an in-progress chart."""
    global chart_playing
    chart_playing = False
    print("[CHART] Stop requested")


def _chart_loop():
    """
    Main chart playback loop. Manages two priority queues:
    
    1. Visual Queue: Sends notes to frontend LEAD_TIME seconds early
    2. Activation Queue: Activates target values at the exact beat time
    
    Timeline for a note at beat 5.0 seconds:
    - t=2.0s: Visual event sent to frontend (note appears on screen)
    - t=5.0s: Target activated (backend starts listening for this action)
    - t=5.0s-5.15s: Hit window (player can successfully hit the note)
    - t=5.15s+: Miss if not hit
    """
    global chart_playing, pending_notes
    
    # Initial countdown before chart starts
    time.sleep(5)

    events = chart_data["events"]
    start_time = time.time() + chart_data["offset"]

    # Two priority queues for scheduling events
    visual_queue = []      # (visual_time, unique_id, event)
    activation_queue = []  # (activation_time, unique_id, event)

    # Build both queues and populate pending notes
    with pending_lock:
        for evt in events:
            hit_time = start_time + float(evt["time"])
            visual_time = hit_time - LEAD_TIME
            
            # Add to visual queue (shows note on screen early)
            heapq.heappush(visual_queue, (visual_time, next(counter), evt))
            
            # Add to activation queue (activates target at exact time)
            heapq.heappush(activation_queue, (hit_time, next(counter), evt))

            # Track as pending note for hit detection
            pending_notes.append({
                "utensil": evt["utensil"],
                "instrument": evt["instrument"],
                "target": evt["target"],
                "hit_time": hit_time,
                "hit": False
            })

    print(f"[CHART] Playback started - {len(events)} events loaded")

    # Main playback loop
    while chart_playing and (visual_queue or activation_queue):
        now = time.time()

        # Process all visual events that should be shown now
        while visual_queue and visual_queue[0][0] <= now:
            _, _, evt = heapq.heappop(visual_queue)
            hit_time = start_time + evt["time"]

            # Send to frontend for visual display
            socketio.emit("chart_event", {
                "instrument": evt["instrument"],
                "target": evt["target"],
                "event_time": hit_time,
                "server_time": now
            })
            
            print(f"[VISUAL] {evt['utensil']} (target={evt['target']})")

        # Process all activation events that should be active now
        while activation_queue and activation_queue[0][0] <= now:
            _, _, evt = heapq.heappop(activation_queue)

            # Set target value in sound rules (backend starts listening)
            with sound_rules_lock:
                SOUND_RULES[evt["utensil"]]["target_value"] = evt["target"]

            # Inform frontend that target is now active
            socketio.emit("target_active", {
                "utensil": evt["utensil"],
                "instrument": evt["instrument"],
                "target": evt["target"],
                "event_time": now
            })

            print(f"[ACTIVE] {evt['utensil']} = {evt['target']}")
        
        time.sleep(0.01)  # 10ms tick

    chart_playing = False
    print("[CHART] Playback finished")


# ============================================================================
# MQTT CLIENT SETUP
# ============================================================================

def start_mqtt_client():
    """Initialize and start MQTT client connection."""
    global mqtt_client
    
    try:
        import uuid
        mqtt_client = mqtt.Client(str(uuid.uuid1()))
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        
        mqtt_client.connect(MQTT_BROKER, port=MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()
        
        print('MQTT client started successfully')
        return True
        
    except Exception as e:
        print(f'[ERR] MQTT client failed: {e}')
        return False


# ============================================================================
# FLASK ROUTES & SOCKETIO HANDLERS
# ============================================================================

@app.route('/')
def index():
    """Main viewer page."""
    return render_template('kitchen.html')


@socketio.on('connect')
def handle_connect():
    """Client connected - send recent message history."""
    print('Web client connected')
    for msg in recent_messages:
        emit('mqtt_message', msg)


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected."""
    print('Web client disconnected')


@socketio.on('clear_messages')
def handle_clear():
    """Clear message history."""
    recent_messages.clear()
    emit('messages_cleared', broadcast=True)
    print('Messages cleared')


@socketio.on('update_filter')
def handle_filter(data):
    """Update topic filter settings (filtering happens client-side)."""
    print(f'Filter updated: {data}')
    emit('filter_updated', data)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("  Kitchen Rhythm Game - MQTT Viewer")
    print("=" * 60)
    print(f"  Viewer URL:  http://0.0.0.0:5001")
    print(f"  Monitoring:  {MQTT_TOPIC} on {MQTT_BROKER}")
    print("=" * 60)

    # Load rhythm chart
    chart_data = parse_midi_to_rhythm(file_path="./rhythm_charts/modified_song.json")
    print(f"[CHART LOADED] {len(chart_data['events'])} events loaded")
    
    # Start MQTT client
    start_mqtt_client()
    
    print("=" * 60)
    print()

    # Start chart playback
    start_chart_playback()
    
    # Run Flask app
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)