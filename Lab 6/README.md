# Distributed Interaction

**NAMES OF COLLABORATORS HERE** [Amanda Lu](https://github.com/amandazlu/Interactive-Lab-Hub/tree/Fall2025/Lab%206), [Shreya Kethi Reddy](https://github.com/littleredpolkadot/Interactive-Lab-Hub/tree/Fall2025/Lab%206), [Miriam Alex](https://github.com/miriam-alex/Interactive-Lab-Hub/tree/Fall2025/Lab%206)

For submission, replace this section with your documentation!

---

## Prep

1. Pull the new changes
2. Read: [The Presence Table](https://dl.acm.org/doi/10.1145/1935701.1935800) ([video](https://vimeo.com/15932020))

## Overview

Build interactive systems where **multiple devices communicate over a network** using MQTT messaging. Work in teams of 3+ with Raspberry Pis.

**Parts:**
- ✅ A: Learn MQTT messaging
- ✅ B: Try collaborative pixel grid demo  
- C: Build your own distributed system

---

## Part A: MQTT Messaging

MQTT = lightweight messaging for IoT. Publish/subscribe model with central broker.

<details>

**Concepts:**
- **Broker**: `farlab.infosci.cornell.edu:1883`
- **Topic**: Like `IDD/bedroom/temperature` (use `#` wildcard)
- **Publish/Subscribe**: Send and receive messages

**Install MQTT tools on your Pi:**
```bash
sudo apt-get update
sudo apt-get install -y mosquitto-clients
```

**Test it:**

**Subscribe to messages (listener):**
```bash
mosquitto_sub -h farlab.infosci.cornell.edu -p 1883 -t 'IDD/#' -u idd -P 'device@theFarm'
```

**Publish a message (sender):**
```bash
mosquitto_pub -h farlab.infosci.cornell.edu -p 1883 -t 'IDD/test/yourname' -m 'Hello!' -u idd -P 'device@theFarm'
```

> **💡 Tips:**
> - Replace `yourname` with your actual name in the topic
> - Use single quotes around the password: `'device@theFarm'`

**🔧 Debug Tool:** View all MQTT messages in real-time at `http://farlab.infosci.cornell.edu:5001`

![MQTT Explorer showing messages](imgs/MQTT-explorer.png)

</details>

**Screen shot for MQTT Messaging**
From Ying Yu's Pi
![image](imgs/parta1.png)
![image](imgs/parta2.png)

**💡 Brainstorm 5 ideas for messaging between devices**
> 1. **Collaborative Gaming Status:** Enable a cooperative game (like an escape room, building an object, or a collaborative puzzle) where multiple users control different items or characters. Devices publish the status of their controlled element in real-time.
> 2. **Home Monitoring Dashboard:** Create a single, unified view (like a dashboard on a tablet or web page) that displays real-time environmental data collected from various sensors and allows control of actuators. All sensors and control devices publish their status, and the dashboard subscribes to everything.
> 3. **Security Guard and Alert System:** Use door/window contact sensors to monitor entry points. When a sensor's state changes (e.g., from closed to open), the device publishes an alert. A central security hub subscribes and triggers an immediate audible alarm or sends a notification.
> 4. **Competitive Gaming (something like Sumo):** Design a competitive game (like robot sumo wrestling) where the playing area itself can detect boundaries. Use capacity or pressure sensors to define a "ring." When a character/robot is pushed outside the defined area, the ring sensor publishes the event, and the game server determines the winner.
> 5. **Social Media Collaborative Story Game:** Create a "story chain" game where each participating device/user adds the next line or paragraph to a story. When a user finishes their contribution, their device publishes the updated story fragment. All other devices subscribe to receive the latest complete story.

---

## Part B: Collaborative Pixel Grid

Each Pi = one pixel, controlled by RGB sensor, displayed in real-time grid.

<details>

**Architecture:** `Pi (sensor) → MQTT → Server → Web Browser`

**Setup:**

1. **Sensor**

#### Light/Proximity/Gesture sensor (APDS-9960)
We use this sensor [Adafruit APDS-9960](https://www.adafruit.com/product/3595) for this exmaple to detect light (also RGB)
 
<img src="https://cdn-shop.adafruit.com/970x728/3595-06.jpg" width=200>

Connect it to your pi with Qwiic connector


<img src="imgs/IMG_0270.jpg" height="200" />
We need to use the screen to display the color detection, so we need to stop the running piscreen.service to make your screen available again

```bash
# stop the screen service
sudo systemctl stop piscreen.service
```

if you want to restart the screen service
```bash
# start the screen service
sudo systemctl start piscreen.service
```
 
2. **Server** (one person on laptop):
```bash
cd "Lab 6"  
source .venv/bin/activate
pip install -r requirements-server.txt
python app.py
```

2. **View in browser:**
   - Grid: `http://farlab.infosci.cornell.edu:5000`
   - Controller: `http://farlab.infosci.cornell.edu:5000/controller`

3. **Pi publisher** (everyone on their Pi):
```bash
# First time setup - create virtual environment
cd "Lab 6"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-pi.txt

# Run the publisher
python pixel_grid_publisher.py
```

Hold colored objects near sensor to change your pixel!

![Pixel grid with two devices](imgs/two-devices-grid.png)


</details>

**📸 Include: Screenshot of grid + photo of your Pi setup**

🎥 See the testing video from Ying Yu below.

[![youtube](https://img.youtube.com/vi/zrZQ_2HXI1o/0.jpg)](https://youtube.com/shorts/zrZQ_2HXI1o)

---

## Part C: Make Your Own

**Requirements:**
- **✅ 3+ people, 3+ Pis:** We will use 4 Pis; one designated as the Viewer/Scorekeeper, and three others acting as Publishers (Players).
- **✅ Each Pi contributes sensor input via MQTT:** The three Player Pis will act as sensors/publishers, reporting the status of their assigned "kitchen appliance/ utensils."
- **✅ Meaningful or fun interaction:** The interaction is a rhythm-based musical game integrated with a kitchen theme.

**Ideas:**
<details><summary> Click to see some brilliant ideas :)</summary>

**Sensor Fortune Teller**
- Each Pi sends 0-255 from different sensor
- Server generates fortunes from combined values

**Frankenstories**
- Sensor events → story elements (not text!)
- Red = danger, gesture up = climbed, distance <10cm = suddenly

**Distributed Instrument**
- Each Pi = one musical parameter
- Only works together

**Others:** Games, presence display, mood ring

</details>


### Deliverables

Replace this README with your documentation:

**1. Project Description**
- What does it do? Why interesting? User experience
> The project is the detection of coordination from three different sensors on different pis which serves as the foundation for oour multiplayer cooking-themed rhythm game. Each Pi represents a different player's kitchen utensil whcih are the following:
> - A "knife/cutting-board" where a user must chops on specific places on a board
> - A "mixing bowl" where a user use a dowel to mix around the bowl at a certain speed
> - A "pan" where a user has to both manage the heat of the stove and when the take the pan off the heat
> It's interesting since it is the basis of a synchronized collaborative physical cooking experiencethat is both great as a game-mechanic as well as an experience to uniquely collaborate through the cooking motions.
> Upon the synchronizatin of the physical actions (when the "knife" hits the board, "mixing bowl" is strirred, and the "pan" stove is off and "pan" is off the sove all at the same time, the system plays a victory sound)  


**2. Architecture Diagram**
- Hardware, connections, data flow
- Label input/computation/output
![graph](/Lab%206/imgs/grapph.jpg)

**3. Build Documentation**
- Photos of each Pi + sensors
- MQTT topics used
- Code snippets with explanations

>> **Action Viewer**
> 
> The Action Viewer acts as the central game server and display. Its primary role is to subscribe to all incoming instrument status data from the Player Publishers (Pan, Mixing Bowl, Cutting Board). This component handles all received data, executes the game logic, provides feedback, and broadcasts updates to any web clients.
>
> **MQTT Messaging Details (Listener):** 
> * Broker: farlab.infosci.cornell.edu:1883
> * Subscribed Topic: IDD/kitchen-instrument
> * Data Format: Received data is expected to be in JSON format, containing the status information for the various kitchen instruments.
> **Code:** Lab 6/mqtt_viewer_instrument.py
> 
> The Viewer randomly generates a set of required Target Values for the Pan, Mixing Bowl, and Cutting Board instruments (e.g., a specific X range for the Mixing Bowl, a specific distance value for the Pan).
> 
> When new data is received via MQTT (identify by the utensil label), the Viewer parses the JSON message to extract the current instrument values. It then checks if the transmitted values conform to the currently active Target Values.
>
> If the received values meet the required targets, the Viewer plays the corresponding audio tone or sound effect (via speaker output); then immediately generates a new set of random Target Values, prompting the players to perform the next action in the rhythm game.

>> **Knife/ Cutting Board**
>
> ![image](imgs/cutting.jpg)
>
> This component simulates the action of chopping ingredients on a Cutting Board using a capacitive sensor. The sensor is segmented into multiple channels. The device's primary function is to continuously detect which channel is being touched and transmit this channel status data via MQTT. This simulates chopping on the correct section of the board.
> 
> **MQTT Messaging Details:** 
> * Data Source: Capacitive Sensor Channels (Channels 0–11).
> * Target Broker: farlab.infosci.cornell.edu:1883
> * Topic: IDD/kitchen-instrument
> 
> **Code:** Lab 6/instrument_knife_publisher.py
> The main loop reads the status of the capacitive sensor's channels (typically channels 0 through 11).
> The current channel status is formatted into a JSON object (similar to a hashmap) where the key is the channel number and the value is its state (typically 1 for touched/active, 0 for untouched/inactive). 

>> **Pan**
>
> ![image](imgs/pan.jpg)
> 
> This component simulates the action of stir-frying or cooking by using a Distance Sensor to detect the pan's proximity to a simulated "heat source" or a fixed reference point. The device's primary function is to continuously capture the distance value and transmit it via MQTT to simulate the chef controlling the pan's height.
>
> **MQTT Messaging Details:** 
> * Data Source: Distance Sensor (Numerical Value).
>     * Interpretation: A large value (e.g., $2000+$) indicates the pan is very close to the sensor/heat source. A very small value ($0, 1, 2$) indicates the pan is far away (almost nothing detected).
> * Target Broker: farlab.infosci.cornell.edu:1883
> * Topic: IDD/kitchen-instrument
>
> **Code:** /Lab 6/instrument_pan_publisher.py
> 
> The main loop repeatedly reads the raw numerical output from the distance sensor. The current distance value is formatted into a message (e.g., a simple numerical string or a JSON object containing the value) and published to the shared topic.


>> **Mixing Bowl**
> 
> ![image](imgs/mixing.jpg)
>
> This component simulates the action of mixing ingredients in a Mixing Bowl using a joystick as the sensor input. The device's primary function is to continuously capture the joystick's X and Y coordinates and transmit this data via MQTT.
>
> **MQTT Messaging Details:** 
> * Data Source: Joystick (X and Y axis values).
> * Target Broker: farlab.infosci.cornell.edu:1883
> * Topic: IDD/kitchen-instrument
> * Publish Frequency: 20 Hz (once 0.05 sec)
> **Code:** Lab 6/mixing_bowl_publisher.py
> 
> The core logic resides within the main loop. This loop reads the current X and Y values from the connected joystick.
> The X and Y values are formatted into a message (e.g., a simple string or JSON object) and published to the specified topic at a high frequency of 20 Hz to ensure near real-time tracking of the mixing motion.

**4. User Testing**
- **Test with 2+ people NOT on your team**
- Photos/video of use
- What did they think before trying?
- What surprised them?
- What would they change?

**5. Reflection**
- What worked well?
- Challenges with distributed interaction?
- How did sensor events work?
- What would you improve?

**🎥 Video**
* [Test with the MQTT Messaging](https://youtu.be/gWVzn_YbFjk)
* [Sound Integrated](https://youtube.com/shorts/l5_PfEa0vT8)

---

<details><summary>Click for information: Code Files, Debugging Tools, Troubleshooting </summary>


## Code Files

**Server files:**
- `app.py` - Pixel grid server (Flask + WebSocket + MQTT)
- `mqtt_viewer.py` - MQTT message viewer for debugging
- `mqtt_bridge.py` - MQTT → WebSocket bridge
- `requirements-server.txt` - Server dependencies

**Pi files:**
- `pixel_grid_publisher.py` - Example (RGB sensor → MQTT)
- `requirements-pi.txt` - Pi dependencies

**Web interface:**
- `templates/grid.html` - Pixel grid display
- `templates/controller.html` - Color picker
- `templates/mqtt_viewer.html` - Message viewer

---

## Debugging Tools

**MQTT Message Viewer:** `http://farlab.infosci.cornell.edu:5001`
- See all MQTT messages in real-time
- View topics and payloads
- Helpful for debugging your own projects

**Command line:**
```bash
# See all IDD messages
mosquitto_sub -h farlab.infosci.cornell.edu -p 1883 -t "IDD/#" -u idd -P "device@theFarm"
```

---

## Troubleshooting

**MQTT:** Broker `farlab.infosci.cornell.edu:1883`, user `idd`, pass `device@theFarm`

**Sensor:** Check `i2cdetect -y 1`, APDS-9960 at `0x39`

**Grid:** Verify server running, check MQTT in console, test with web controller

**Pi venv:** Make sure to activate: `source .venv/bin/activate`


</details>



---

## Submission Checklist

Before submitting:
- [x] Delete prep/instructions above
- [x] Add YOUR project documentation
- [x] Include photos/videos/diagrams  
- [ ] Document user testing with non-team members
- [ ] Add reflection on learnings
- [x] List team names at top

**Your README = story of what YOU built!**

---

Resources: [MQTT Guide](https://www.hivemq.com/mqtt-essentials/) | [Paho Python](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php) | [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
