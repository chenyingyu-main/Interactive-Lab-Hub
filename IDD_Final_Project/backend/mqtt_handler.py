"""
MQTT Handler - Message receiving and processing
"""

import paho.mqtt.client as mqtt
from datetime import datetime
import json
import threading
import math

from config import (MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, 
                    MQTT_USERNAME, MQTT_PASSWORD, SOUND_RULES)
from audio_manager import should_play, play_sound, stop_sound, playing_state
from game_logic import check_note_hits, sound_rules_lock

# ============================================================================
# MQTT CLIENT
# ============================================================================

mqtt_client = None
_socketio = None
_recent_messages = None

# ============================================================================
# MIXING BOWL DIRECTION TRACKING
# ============================================================================

# Track last position for direction detection
mixing_bowl_state = {
    'direction': None  # Current direction based on x position
}

CENTER_X = 519
CENTER_Y = 517

def detect_mixing_direction(x, y):
    """
    Detect direction based on x position.
    Left half = counterclockwise, Right half = clockwise
    Returns: 'clockwise', 'counterclockwise', or None
    """
    global mixing_bowl_state
    
    # Determine direction based on which side of center
    if x < CENTER_X:
        # Left half = counterclockwise
        mixing_bowl_state['direction'] = 'counterclockwise'
        return 'counterclockwise'
    elif x > CENTER_X:
        # Right half = clockwise
        mixing_bowl_state['direction'] = 'clockwise'
        return 'clockwise'
    else:
        # Exactly at center
        return mixing_bowl_state['direction']  # Keep last direction


def broadcast_to_web_client(message, topic):
    """Send message to all connected web clients via WebSocket."""
    if _recent_messages is not None:
        _recent_messages.append(message)
    if _socketio:
        _socketio.emit(topic, message, namespace='/')


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
        # MIXING BOWL: Detect rotation direction from x, y coordinates
        # ====================================================================
        if utensil == 'mixing_bowl':
            x = sensor_data.get('x', CENTER_X)
            y = sensor_data.get('y', CENTER_Y)
            direction = detect_mixing_direction(x, y)
            sensor_data['direction'] = direction
            # Debug: show direction and position
            if direction:
                side = "LEFT" if x < CENTER_X else "RIGHT"
                # print(f"[MIXING BOWL] Direction: {direction}, side: {side}, x={x}")
        
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
        if _socketio:
            check_note_hits(utensil, sensor_data, _socketio)
                
    except Exception as e:
        print(f'Error processing message: {e}')


def start_mqtt_client(socketio, recent_messages):
    """
    Initialize and start MQTT client connection.
    
    Args:
        socketio: SocketIO instance for sending events to frontend
        recent_messages: Deque for storing recent messages
    """
    global mqtt_client, _socketio, _recent_messages
    
    _socketio = socketio
    _recent_messages = recent_messages
    
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