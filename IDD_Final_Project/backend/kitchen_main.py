"""
Kitchen Rhythm Game - Main Application Entry Point
Physical cooking utensils as rhythm game controllers via MQTT
"""
import time

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from collections import deque

from config import *
from mqtt_handler import start_mqtt_client
from audio_manager import close_audio
from chart_manager import start_chart_playback
from parser import parse_midi_to_rhythm

# Flask/SocketIO setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mqtt-viewer-2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Store recent messages for new clients
recent_messages = deque(maxlen=MAX_MESSAGES)

# Store loaded chart data for restart functionality
chart_data = None


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


@socketio.on('restart_chart')
def handle_restart_chart():
    """Restart the rhythm chart from the beginning."""
    print('[RESTART] Chart restart requested')
    socketio.emit('chart_restarted')
    from chart_manager import restart_chart_playback
    restart_chart_playback(socketio, chart_data)
    emit('chart_restarted', broadcast=True)
    print('[RESTART] Chart restarted successfully')


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("  Kitchen Rhythm Game - MQTT Viewer")
    print("=" * 60)
    print(f"  Viewer URL:  http://0.0.0.0:5002")
    print(f"  Monitoring:  {MQTT_TOPIC} on {MQTT_BROKER}")
    print("=" * 60)

    # Load rhythm chart
    MUSIC_FILE = "/static/music/Jingle Bells -Beena Version.ogg" 
    chart_data = parse_midi_to_rhythm(file_path="./rhythm_charts/jingle_bells_game_beena.json")
    print(f"[CHART LOADED] {len(chart_data['events'])} events loaded")

    chart_data['music_file'] = MUSIC_FILE
    chart_data['offset'] = -0.2
    
    # Start MQTT client
    from mqtt_handler import mqtt_client
    start_mqtt_client(socketio, recent_messages)
    
    print("=" * 60)
    print()

    # Start chart playback
    start_chart_playback(socketio, chart_data)
    
    # Run Flask app
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
    
    # Cleanup
    close_audio()