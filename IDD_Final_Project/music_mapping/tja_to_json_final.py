#!/usr/bin/env python3
"""
TJA to Kitchen Rhythm Game JSON Converter (Final Version)
"""

import json


def parse_tja(tja_file):
    """read TJA file"""
    
    try:
        encodings = ['utf-8', 'utf-8-sig', 'shift-jis', 'cp932']
        lines = None
        
        for encoding in encodings:
            try:
                with open(tja_file, 'r', encoding=encoding) as f:
                    lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue
        
        if lines is None:
            raise Exception("Cannot read the file")
        
    except FileNotFoundError:
        print(f"[ERROR] cannot find the file: {tja_file}")
        return None
    
    # reading metadata
    metadata = {
        'title': 'Unknown',
        'bpm': 120.0,
        'offset': 0.0
    }
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('TITLE:'):
            metadata['title'] = line.replace('TITLE:', '').strip()
        elif line.startswith('BPM:'):
            metadata['bpm'] = float(line.replace('BPM:', '').strip())
        elif line.startswith('OFFSET:'):
            # Fixing 1: if offset is negative, set it to 5 sec, ensure players are ready.
            original_offset = float(line.replace('OFFSET:', '').strip())
            if original_offset < 0:
                metadata['offset'] = 5.0  # start from 5 sec
                print(f"[INFO] OFFSET from {original_offset} to 5.0 sec")
            else:
                metadata['offset'] = original_offset
    
    # Parse the chart
    in_chart = False
    measures = []
    
    for line in lines:
        line = line.strip()
        
        if '#START' in line:
            in_chart = True
            continue
        elif '#END' in line:
            break
        elif in_chart:
            if line.startswith('//') or not line:
                continue
            
            if '//' in line:
                line = line.split('//')[0].strip()
            
            if line.endswith(','):
                measure = line.rstrip(',')
                measures.append(measure)
    
    metadata['measures'] = measures
    return metadata


def tja_to_tracks(tja_data):
    """Convert the TJA score into three instrument tracks."""
    bpm = tja_data['bpm']
    offset = tja_data['offset']
    measures = tja_data['measures']
    
    seconds_per_beat = 60.0 / bpm
    beats_per_measure = 4
    
    pan_notes = []
    knife_notes = []
    bowl_notes = []
    
    current_time = offset
    
    for measure in measures:
        if not measure:
            current_time += beats_per_measure * seconds_per_beat
            continue
        
        notes_in_measure = len(measure)
        time_per_note = (beats_per_measure * seconds_per_beat) / notes_in_measure
        
        for i, note_char in enumerate(measure):
            note_time = current_time + (i * time_per_note)
            
            if note_char == '1':
                note_name = 'C4' if len(pan_notes) % 2 == 0 else 'D4'
                
                # Duration uses actual note intervals.
                pan_notes.append({
                    'time': round(note_time, 3),
                    'name': note_name,
                    'duration': round(time_per_note * 0.8, 3),  # 80% interval
                    'velocity': 0.8
                })
            
            elif note_char == '2':
                note_options = ['A3', 'B3', 'C4']
                note_name = note_options[len(knife_notes) % 3]
                
                knife_notes.append({
                    'time': round(note_time, 3),
                    'name': note_name,
                    'duration': round(time_per_note * 0.8, 3),  # 80% interval
                    'velocity': 0.8
                })
            
            elif note_char == '5':
                # Hold note: Start from 5 and continue counting until the next non-zero number.
                hold_duration = time_per_note
                for j in range(i + 1, len(measure)):
                    if measure[j] == '0':
                        hold_duration += time_per_note
                    else:
                        break
                
                note_options = ['G3', 'F3', 'E3']
                note_name = note_options[len(bowl_notes) % 3]
                
                bowl_notes.append({
                    'time': round(note_time, 3),
                    'name': note_name,
                    'duration': round(hold_duration, 3),
                    'velocity': 0.8
                })
        
        current_time += beats_per_measure * seconds_per_beat
    
    return {
        'bpm': bpm,
        'offset': offset,
        'pan_notes': pan_notes,
        'knife_notes': knife_notes,
        'bowl_notes': bowl_notes
    }


def create_midi_json(tracks_data, title='My Song'):
    """Create a JSON file that conforms to the format of modified_song.json."""
    
    def add_midi_fields(note):
        note_to_midi = {
            'C3': 48, 'D3': 50, 'E3': 52, 'F3': 53, 'G3': 55, 'A3': 57, 'B3': 59,
            'C4': 60, 'D4': 62, 'E4': 64, 'F4': 65, 'G4': 67, 'A4': 69, 'B4': 71,
            'C5': 72
        }
        
        midi_num = note_to_midi.get(note['name'], 60)
        pitch = note['name'][:-1]
        octave = int(note['name'][-1])
        
        return {
            'midi': midi_num,
            'time': note['time'],
            'ticks': 0,
            'durationTicks': 480,
            'name': note['name'],
            'pitch': pitch,
            'octave': octave,
            'velocity': note['velocity'],
            'duration': note['duration']
        }
    
    result = {
        'header': {
            'keySignatures': [],
            'meta': [],
            'name': title,
            'ppq': 480,
            'tempos': [{'bpm': tracks_data['bpm'], 'ticks': 0}],
            'timeSignatures': [{'timeSignature': [4, 4], 'ticks': 0}]
        },
        'tracks': []
    }
    
    if tracks_data['pan_notes']:
        result['tracks'].append({
            'name': 'Instrument 1',
            'channel': 0,
            'pitchBends': [],
            'notes': [add_midi_fields(n) for n in tracks_data['pan_notes']],
            'controlChanges': {},
            'instrument': {
                'number': 0,
                'family': 'piano',
                'name': 'acoustic grand piano',
                'percussion': False
            }
        })
    
    if tracks_data['knife_notes']:
        result['tracks'].append({
            'name': 'Instrument 2',
            'channel': 1,
            'pitchBends': [],
            'notes': [add_midi_fields(n) for n in tracks_data['knife_notes']],
            'controlChanges': {},
            'instrument': {
                'number': 32,
                'family': 'guitar',
                'name': 'acoustic guitar (nylon)',
                'percussion': False
            }
        })
    
    if tracks_data['bowl_notes']:
        result['tracks'].append({
            'name': 'Instrument 3',
            'channel': 2,
            'pitchBends': [],
            'notes': [add_midi_fields(n) for n in tracks_data['bowl_notes']],
            'controlChanges': {},
            'instrument': {
                'number': 48,
                'family': 'strings',
                'name': 'string ensemble 1',
                'percussion': False
            }
        })
    
    return result


def convert_tja_to_json(tja_file, output_file):
    """Main function: Complete TJA → JSON conversion"""
    
    print("=" * 60)
    print("  TJA to Kitchen Rhythm Game Converter (Final)")
    print("=" * 60)
    
    # Step 1: Parsing TJA files
    print(f"\n[1/3] Parsing TJA files: {tja_file}")
    tja_data = parse_tja(tja_file)
    
    if tja_data is None or not tja_data['measures']:
        print("\n[ERROR] Parsing error")
        return
    
    print(f"  ✓ Title Name: {tja_data['title']}")
    print(f"  ✓ BPM: {tja_data['bpm']}")
    print(f"  ✓ Offset: {tja_data['offset']} 秒")
    print(f"  ✓ Number of measures: {len(tja_data['measures'])}")
    
    # Step 2: Converted to three tracks
    print(f"\n[2/3] Converted to three tracks...")
    tracks_data = tja_to_tracks(tja_data)
    print(f"  ✓ Pan notes: {len(tracks_data['pan_notes'])}")
    print(f"  ✓ Knife notes: {len(tracks_data['knife_notes'])}")
    print(f"  ✓ Bowl notes: {len(tracks_data['bowl_notes'])}")
    
    # Display information from the first 3 notes.
    if tracks_data['pan_notes']:
        print(f"\n  [Overview] Pan first 3 notes:")
        for note in tracks_data['pan_notes'][:3]:
            print(f"    TIME {note['time']}s, {note['name']}, LAST {note['duration']}s")
    
    # Step 3: generate JSON
    print(f"\n[3/3] Generating JSON file: {output_file}")
    midi_json = create_midi_json(tracks_data, title=tja_data['title'])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(midi_json, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Parsing Complete！")
    
    # Statitic
    total_notes = (len(tracks_data['pan_notes']) + 
                   len(tracks_data['knife_notes']) + 
                   len(tracks_data['bowl_notes']))
    
    print("\n" + "=" * 60)
    print("  Statistical Information")
    print("=" * 60)
    print(f"  Overall notes: {total_notes}")
    print(f"  BPM: {tracks_data['bpm']}")
    
    if tracks_data['pan_notes']:
        first_note = tracks_data['pan_notes'][0]
        last_pan = tracks_data['pan_notes'][-1]
        duration = last_pan['time'] + last_pan['duration']
        print(f"  Starting Time: {first_note['time']:.1f} sec")
        print(f"  Ending Time: {duration:.1f} sec")
        print(f"  Total Duration: {duration - first_note['time']:.1f} sec")
    
    print("=" * 60)
    print("\n✅ Complete")
    print()


if __name__ == '__main__':
    INPUT_TJA = 'Jingle Bells -Beena Version-.tja'
    OUTPUT_JSON = 'jingle_bells_game.json'
    
    try:
        convert_tja_to_json(INPUT_TJA, OUTPUT_JSON)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
