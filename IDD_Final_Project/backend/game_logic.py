"""
Game Logic - Note hit detection and scoring
"""

import time
import threading
from config import HIT_WINDOW, HOLD_CHECK_INTERVAL, HOLD_GRACE_PERIOD, SOUND_RULES
from audio_manager import should_play

# ============================================================================
# GAME STATE
# ============================================================================

# Thread-safe note tracking
pending_notes = []
pending_lock = threading.Lock()

# Thread-safe sound rules
sound_rules_lock = threading.Lock()


# ============================================================================
# NOTE HIT DETECTION
# ============================================================================

def check_note_hits(utensil, sensor_data, socketio):
    """
    Check if current sensor data hits any pending notes for this utensil.
    Handles both tap notes and hold notes.
    
    Args:
        utensil: The utensil that sent the data
        sensor_data: Dictionary of sensor values
        socketio: SocketIO instance for emitting events
    """
    now = time.time()

    # Get thread-safe copy of pending notes
    with pending_lock:
        notes_copy = list(pending_notes)

    # Check each pending note for this utensil
    for note in notes_copy:
        if note["utensil"] != utensil:  # Wrong instrument
            continue
        if note["hit"] and not note["is_hold"]:  # Tap note already judged
            continue
        if note.get("hold_broken"):  # Hold note already failed
            continue

        # Calculate time difference from expected hit time
        dt = now - note["hit_time"]

        # ==============================================================
        # TAP NOTE LOGIC (duration == 0)
        # ==============================================================
        if not note["is_hold"]:
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
                        "note_type": "tap",
                        "time": now,
                        "scheduled": note["hit_time"],
                        "accuracy_ms": int(dt * 1000)
                    })
                    # Debug: show what direction triggered the hit
                    if utensil == "mixing_bowl":
                        direction = sensor_data.get('direction', 'None')
                        print(f"[TAP HIT] {utensil} target={note['target']} detected_direction={direction} accuracy {int(dt*1000)}ms")
                    else:
                        print(f"[TAP HIT] {utensil} accuracy {int(dt*1000)}ms")

        # ==============================================================
        # HOLD NOTE LOGIC (duration > 0)
        # ==============================================================
        else:
            with sound_rules_lock:
                rule = SOUND_RULES[utensil]
                condition_met = should_play(utensil, sensor_data, note["target"], rule['threshold'])

            # PHASE 1: Starting the hold (within hit window of start time)
            if not note["hold_started"]:
                if dt < -HIT_WINDOW:  # Too early
                    continue
                
                if condition_met:
                    # Successfully started the hold
                    with pending_lock:
                        for n in pending_notes:
                            if (n["utensil"] == note["utensil"] and 
                                n["hit_time"] == note["hit_time"]):
                                n["hold_started"] = True
                                n["hold_active"] = True
                                n["last_check_time"] = now
                                break

                    socketio.emit("note_result", {
                        "utensil": utensil,
                        "instrument": note["instrument"],
                        "result": "hold_start",
                        "note_type": "hold",
                        "time": now,
                        "scheduled": note["hit_time"],
                        "duration": note["duration"],
                        "accuracy_ms": int(dt * 1000)
                    })
                    print(f"[HOLD START] {utensil} accuracy {int(dt*1000)}ms, duration {note['duration']:.2f}s")

            # PHASE 2: Maintaining the hold (after started, before end time)
            elif note["hold_active"] and now < note["hold_end_time"]:
                # Check if enough time has passed since last check
                if note["last_check_time"] and (now - note["last_check_time"]) >= HOLD_CHECK_INTERVAL:
                    if not condition_met:
                        # Broke the hold!
                        with pending_lock:
                            for n in pending_notes:
                                if (n["utensil"] == note["utensil"] and 
                                    n["hit_time"] == note["hit_time"]):
                                    n["hold_active"] = False
                                    n["hold_broken"] = True
                                    break

                        held_duration = now - note["hit_time"]
                        socketio.emit("note_result", {
                            "utensil": utensil,
                            "instrument": note["instrument"],
                            "result": "hold_break",
                            "note_type": "hold",
                            "time": now,
                            "scheduled": note["hit_time"],
                            "expected_duration": note["duration"],
                            "held_duration": held_duration,
                            "completion_percent": int((held_duration / note["duration"]) * 100)
                        })
                        print(f"[HOLD BREAK] {utensil} held {held_duration:.2f}s / {note['duration']:.2f}s")
                    else:
                        # Still holding - update check time
                        with pending_lock:
                            for n in pending_notes:
                                if (n["utensil"] == note["utensil"] and 
                                    n["hit_time"] == note["hit_time"]):
                                    n["last_check_time"] = now
                                    break

            # PHASE 3: Successfully completed the hold
            elif note["hold_active"] and now >= note["hold_end_time"]:
                # Check one final time if condition is still met
                if condition_met or (now - note["hold_end_time"]) < HOLD_GRACE_PERIOD:
                    with pending_lock:
                        for n in pending_notes:
                            if (n["utensil"] == note["utensil"] and 
                                n["hit_time"] == note["hit_time"]):
                                n["hold_active"] = False
                                n["hit"] = True  # Mark as complete
                                break

                    socketio.emit("note_result", {
                        "utensil": utensil,
                        "instrument": note["instrument"],
                        "result": "hold_complete",
                        "note_type": "hold",
                        "time": now,
                        "scheduled": note["hit_time"],
                        "duration": note["duration"]
                    })
                    print(f"[HOLD COMPLETE] {utensil} held for {note['duration']:.2f}s")
                else:
                    # Released too early at the end
                    with pending_lock:
                        for n in pending_notes:
                            if (n["utensil"] == note["utensil"] and 
                                n["hit_time"] == note["hit_time"]):
                                n["hold_active"] = False
                                n["hold_broken"] = True
                                break

                    socketio.emit("note_result", {
                        "utensil": utensil,
                        "instrument": note["instrument"],
                        "result": "hold_break",
                        "note_type": "hold",
                        "time": now,
                        "scheduled": note["hit_time"],
                        "expected_duration": note["duration"],
                        "held_duration": note["duration"],
                        "completion_percent": 99
                    })
                    print(f"[HOLD BREAK] {utensil} released too early at end")

    # Clean up old notes that are past the hit window
    with pending_lock:
        pending_notes[:] = [
            n for n in pending_notes 
            if not (
                # Tap notes that are judged or past window
                (not n["is_hold"] and (n.get("hit") or now > n["hit_time"] + HIT_WINDOW))
                # Hold notes that are complete or broken
                or (n["is_hold"] and (n.get("hit") or n.get("hold_broken")))
            )
        ]


# ============================================================================
# MISS DETECTION
# ============================================================================

def note_miss_checker(socketio, chart_playing_flag):
    """
    Background thread that checks for missed notes.
    
    For TAP notes: Mark as miss if hit window expires without being hit
    For HOLD notes: Mark as miss if never started within the hit window
    
    Args:
        socketio: SocketIO instance for emitting events
        chart_playing_flag: Function that returns True if chart is still playing
    """
    while chart_playing_flag():
        now = time.time()
        
        with pending_lock:
            for note in pending_notes:
                # Skip if already processed
                if note["hit"] or note.get("hold_broken"):
                    continue

                # TAP NOTE: Miss if past the hit window and never hit
                if not note["is_hold"]:
                    if now > note["hit_time"] + HIT_WINDOW:
                        note["hit"] = True
                        
                        socketio.emit("note_result", {
                            "instrument": note["instrument"],
                            "utensil": note["utensil"],
                            "result": "miss",
                            "note_type": "tap",
                            "scheduled": note["hit_time"],
                            "actual_time": now
                        })
                        
                        if note['utensil'] == 'pan':
                            print(f"[TAP MISS] {note['utensil']} missed note at {note['hit_time']}")

                # HOLD NOTE: Miss if never started within the hit window
                elif not note["hold_started"] and now > note["hit_time"] + HIT_WINDOW:
                    note["hold_broken"] = True
                    
                    socketio.emit("note_result", {
                        "instrument": note["instrument"],
                        "utensil": note["utensil"],
                        "result": "miss",
                        "note_type": "hold",
                        "scheduled": note["hit_time"],
                        "actual_time": now,
                        "expected_duration": note["duration"]
                    })
                    
                    if note['utensil'] == 'pan':
                        print(f"[HOLD MISS] {note['utensil']} never started hold at {note['hit_time']}")

        time.sleep(0.01)  # 10ms tick to avoid busy-wait