# IDD_Final_Project

## Set-up 

One pi must host. The other Pis can act as instruments.

First-time set up:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-pi.txt
```

For the hosting Pi:
1. Set up Bluetooth speaker (can connect via VNC Viewer)
2. We use the class server. We can set up our viewer by running `python mqtt_viewer_instrument.py`

For the instrument Pis:
1. Run the corresponding publisher (`python <instrument_name>_publisher.py`)

## Generating Rhythm Charts
We're planning to use Tone.js to generate sounds. Please use `modified_song.json` as a reference.

Currently, for each track, we support the following action -> sound mapping (in `notes_to_utensil.json`)
- Tracks named "Instrument 1" map to the pan. 
    - Low flame ->  C4
    - Medium flame -> D4
    - High flame -> E4
- Tracks named "Instrument 2" map to the cutting board. 
    - Cutting object 1 -> A3
    - Cutting object 2 -> B3
    - Cutting object 3 -> C4
- Tracks named "Instrument 3" map to the mixing bowl. 
    - Right now, we just ensure the mixing bowl is moving when any note appears


## TO DO LIST:

- add more notes for mixing bowl (ellen) 
- change pan notes (amanda)
- change pan flip to a separate note (amanda)
- get rid of ready to cook words on ui (miriam)
- Add logo to UI (miriam)
- add sound effects (miriam)
- change timing so that perfect lines up (shreya)
- Update Instructions (shreya)
- Record
- Make mixing bowl (ellen)

- make it fun to play

- sound design
- frontend: show instruments movement with real actions - animation
- change the note UI to demonstrate the different actions
- instructions modal on the screen and help button

- start our report

## DONE
- restart button on the screen
- 3-2-1 countdown
- add knob to stove that indicates higher/lower and also restricts the movement past a specific rotation
- hinge to restrict pan from moving upwards
- make the knifeboard stronger
