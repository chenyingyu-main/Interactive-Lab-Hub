import os
import json

def parse_midi_to_rhythm(file_path, output_path="./rhythm_charts/rhythm_chart.json"):
    """Parse MIDI JSON into rhythm game events."""

    MAPPING_PATH = "./rhythm_charts/notes_to_utensil.json"
    
    if not os.path.exists(file_path):
        print(f"[ERROR] MIDI file not found: {file_path}")
        return None

    if not os.path.exists(MAPPING_PATH):
        print(f"[ERROR] Mapping file not found: {file_path}")
        return None

    try:
        with open(file_path, "r") as f:
            midi_data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load MIDI file: {e}")
        return None

    try:
        with open(MAPPING_PATH, "r") as f:
            mapping_data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load mapping file: {e}")
        return None

    # Extract BPM from header
    bpm = midi_data["header"]["tempos"][0]["bpm"]
    
    # Collect all notes from all tracks as events
    events = []
    
    for track in midi_data["tracks"]:
        track_name = track["name"]
        instrument_name = track["instrument"]["name"]
        channel = track["channel"]

        utensil = mapping_data[track_name]
        utensil_name = utensil["name"]
        utensil_targets = utensil["targets"]
        print(utensil_targets)
        
        for note in track["notes"]:
            # Create event for each note
            note_name = note["name"]
            curr_utensil_target = utensil_targets[note_name] if note_name in utensil_targets else None

            event = {
                "time": note["time"],
                "type": "note",
                "track": track_name,
                "utensil": utensil_name,
                "channel": channel,
                "instrument": instrument_name,
                "midi": note["midi"],
                "note_name": note["name"],
                "pitch": note["pitch"],
                "octave": note["octave"],
                "velocity": note["velocity"],
                "duration": note["duration"],
                "target" : curr_utensil_target
            }
            events.append(event)
    
    # Sort events by time
    events = sorted(events, key=lambda e: e["time"])
    
    # Create rhythm chart data
    chart_data = {
        "bpm": bpm,
        "offset": 0.0,
        "total_duration": max(e["time"] + e["duration"] for e in events) if events else 0,
        "num_tracks": len(midi_data["tracks"]),
        "events": events
    }
    
    # Save to output file
    try:
        with open(output_path, "w") as f:
            json.dump(chart_data, f, indent=2)
        print(f"[SUCCESS] Rhythm chart saved to: {output_path}")
        print(f"[INFO] {len(events)} events loaded")
        print(f"[INFO] BPM: {bpm}")
        print(f"[INFO] Duration: {chart_data['total_duration']:.2f}s")
    except Exception as e:
        print(f"[ERROR] Failed to save rhythm chart: {e}")
        return None
    
    return chart_data


def load_rhythm_chart(file_path="./rhythm_chart.json"):
    """Load a parsed rhythm chart for gameplay."""
    
    if not os.path.exists(file_path):
        print(f"[ERROR] Chart file not found: {file_path}")
        return None

    try:
        with open(file_path, "r") as f:
            chart = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load chart: {e}")
        return None

    print(f"[CHART LOADED] {len(chart['events'])} events ready")
    return chart


# Example usage
if __name__ == "__main__":
    # Parse MIDI JSON to rhythm chart
    chart = parse_midi_to_rhythm(file_path="./rhythm_charts/modified_song.json")
    
    if chart:
        print("\n[PREVIEW] First 5 events:")
        for event in chart["events"][:5]:
            print(f"  Time {event['time']:>5.2f}s: {event['note_name']} on {event['track']}")