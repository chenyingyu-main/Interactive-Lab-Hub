"""
Chart Manager - Rhythm chart playback and scheduling
"""

import time
import threading
import heapq
import itertools

from config import LEAD_TIME, SOUND_RULES, HOLD_THRESHOLD
from game_logic import pending_notes, pending_lock, sound_rules_lock, note_miss_checker

# ============================================================================
# CHART PLAYBACK STATE
# ============================================================================

counter = itertools.count()  # unique ID generator for heap queue

chart_data = None
chart_thread = None
chart_playing = False
miss_checker_thread = None


# ============================================================================
# CHART PLAYBACK CONTROL
# ============================================================================

def start_chart_playback(socketio, loaded_chart_data):
    """
    Start playing the rhythm chart in a background thread.
    
    Args:
        socketio: SocketIO instance for sending events to frontend
        loaded_chart_data: Parsed chart data from parse_midi_to_rhythm()
    """
    global chart_thread, chart_playing, miss_checker_thread, chart_data

    chart_data = loaded_chart_data

    if chart_data is None:
        print("[ERROR] No chart loaded.")
        return

    if chart_thread and chart_thread.is_alive():
        print("[WARN] Chart already running.")
        return

    chart_playing = True
    
    # Start chart playback thread
    chart_thread = threading.Thread(target=_chart_loop, args=(socketio,), daemon=True)
    chart_thread.start()

    # Start miss detection thread
    miss_checker_thread = threading.Thread(
        target=note_miss_checker, 
        args=(socketio, lambda: chart_playing), 
        daemon=True
    )
    miss_checker_thread.start()


def stop_chart_playback():
    """Stop an in-progress chart."""
    global chart_playing
    chart_playing = False
    print("[CHART] Stop requested")


def restart_chart_playback(socketio, loaded_chart_data):
    """
    Restart the rhythm chart from the beginning by resetting all state.
    
    This function:
    1. Stops the current chart playback
    2. Clears all pending notes
    3. Resets sound rules to default state
    4. Waits for threads to finish
    5. Starts a fresh chart playback
    
    Args:
        socketio: SocketIO instance for sending events to frontend
        loaded_chart_data: Parsed chart data from parse_midi_to_rhythm()
    """
    global chart_playing, chart_thread, miss_checker_thread
    
    print("[RESTART] Stopping current chart...")
    
    # Stop current chart playback
    chart_playing = False
    
    # Wait for threads to finish
    if chart_thread and chart_thread.is_alive():
        chart_thread.join(timeout=2.0)
        print("[RESTART] Chart thread stopped")
    
    if miss_checker_thread and miss_checker_thread.is_alive():
        miss_checker_thread.join(timeout=2.0)
        print("[RESTART] Miss checker thread stopped")
    
    # Clear all pending notes
    with pending_lock:
        pending_notes.clear()
        print("[RESTART] Cleared pending notes")
    
    # Reset sound rules to default target values
    with sound_rules_lock:
        for utensil in SOUND_RULES:
            SOUND_RULES[utensil]["target_value"] = None
        print("[RESTART] Reset sound rules")
    
    # Small delay to ensure clean state
    time.sleep(0.1)
    
    # Start fresh chart playback
    print("[RESTART] Starting fresh chart playback...")
    start_chart_playback(socketio, loaded_chart_data)


def _chart_loop(socketio):
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
    global chart_playing
    
    # 3-2-1 countdown before chart starts
    print("[COUNTDOWN] Starting countdown...")
    for count in [3, 2, 1]:
        print(f"[COUNTDOWN] {count}...")
        socketio.emit("countdown", {"count": count})
        time.sleep(1)
    
    print("[COUNTDOWN] GO!")
    socketio.emit("countdown", {"count": "GO"})
    time.sleep(1)

    if chart_data and "music_file" in chart_data:
        socketio.emit("play_music", {
            "music_file": chart_data["music_file"],
            "start_time": time.time()
        })
        print(f"[MUSIC] Sent play command: {chart_data['music_file']}")

    time.sleep(1)

    events = chart_data["events"]
    manual_offset = chart_data.get("offset", 0)
    start_time = time.time() + manual_offset

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
            duration = evt.get("duration", 0)  # 0 means tap note
            pending_notes.append({
                "utensil": evt["utensil"],
                "instrument": evt["instrument"],
                "target": evt["target"],
                "hit_time": hit_time,
                "duration": duration,
                "is_hold": duration > HOLD_THRESHOLD,
                "hit": False,
                "hold_started": False,
                "hold_active": False,
                "hold_broken": False,
                "hold_end_time": hit_time + duration,
                "last_check_time": None
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
                "utensil": evt["utensil"],
                "target": evt["target"],
                "event_time": hit_time,
                "server_time": now,
                "duration": evt.get("duration", 0),
                "is_hold": evt.get("duration", 0) > HOLD_THRESHOLD
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
    
    # Emit game over event to frontend
    socketio.emit("game_over", {
        "message": "Song completed!",
        "timestamp": time.time()
    })
    print("[CHART] Game over event sent to frontend")