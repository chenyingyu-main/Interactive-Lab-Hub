# Chatterboxes
**NAMES OF COLLABORATORS HERE: [Shreya Kethi Reddy](https://github.com/littleredpolkadot/Interactive-Lab-Hub)** 


[![Watch the video](https://user-images.githubusercontent.com/1128669/135009222-111fe522-e6ba-46ad-b6dc-d1633d21129c.png)](https://www.youtube.com/embed/Q8FWzLMobx0?start=19)

In this lab, we want you to design interaction with a speech-enabled device--something that listens and talks to you. This device can do anything *but* control lights (since we already did that in Lab 1).  First, we want you first to storyboard what you imagine the conversational interaction to be like. Then, you will use wizarding techniques to elicit examples of what people might say, ask, or respond.  We then want you to use the examples collected from at least two other people to inform the redesign of the device.

We will focus on **audio** as the main modality for interaction to start; these general techniques can be extended to **video**, **haptics** or other interactive mechanisms in the second part of the Lab.

## Prep for Part 1: Get the Latest Content and Pick up Additional Parts 

✅ Please check instructions in [prep.md](prep.md) and complete the setup before class on Wednesday, Sept 23rd.

<details>
<summary>Click to toggle contents of Lab3 Prep</summary>


### Pick up Web Camera If You Don't Have One

Students who have not already received a web camera will receive their [Logitech C270 Webcam](https://www.amazon.com/Logitech-Desktop-Widescreen-Calling-Recording/dp/B004FHO5Y6/ref=sr_1_3?crid=W5QN79TK8JM7&dib=eyJ2IjoiMSJ9.FB-davgIQ_ciWNvY6RK4yckjgOCrvOWOGAG4IFaH0fczv-OIDHpR7rVTU8xj1iIbn_Aiowl9xMdeQxceQ6AT0Z8Rr5ZP1RocU6X8QSbkeJ4Zs5TYqa4a3C_cnfhZ7_ViooQU20IWibZqkBroF2Hja2xZXoTqZFI8e5YnF_2C0Bn7vtBGpapOYIGCeQoXqnV81r2HypQNUzFQbGPh7VqjqDbzmUoloFA2-QPLa5lOctA.L5ztl0wO7LqzxrIqDku9f96L9QrzYCMftU_YeTEJpGA&dib_tag=se&keywords=webcam%2Bc270&qid=1758416854&sprefix=webcam%2Bc270%2Caps%2C125&sr=8-3&th=1) and bluetooth speaker on Wednesday at the beginning of lab. If you cannot make it to class this week, please contact the TAs to ensure you get these. 

### Get the Latest Content

As always, pull updates from the class Interactive-Lab-Hub to both your Pi and your own GitHub repo. There are 2 ways you can do so:

**\[recommended\]** ✅ Option 1: On the Pi, `cd` to your `Interactive-Lab-Hub`, pull the updates from upstream (class lab-hub) and push the updates back to your own GitHub repo. You will need the *personal access token* for this.

```
pi@ixe00:~$ cd Interactive-Lab-Hub
pi@ixe00:~/Interactive-Lab-Hub $ git pull upstream Fall2025
pi@ixe00:~/Interactive-Lab-Hub $ git add .
pi@ixe00:~/Interactive-Lab-Hub $ git commit -m "get lab3 updates"
pi@ixe00:~/Interactive-Lab-Hub $ git push
```

Option 2: On your your own GitHub repo, [create pull request](https://github.com/FAR-Lab/Developing-and-Designing-Interactive-Devices/blob/2022Fall/readings/Submitting%20Labs.md) to get updates from the class Interactive-Lab-Hub. After you have latest updates online, go on your Pi, `cd` to your `Interactive-Lab-Hub` and use `git pull` to get updates from your own GitHub repo.

</details>


## Part 1.
### Setup 
<details>
<summary>Click to toggle contents of Lab3 Setup (Env and Dependency Installation)</summary>

✅ Activate your virtual environment

```
pi@ixe00:~$ cd Interactive-Lab-Hub
pi@ixe00:~/Interactive-Lab-Hub $ cd Lab\ 3
pi@ixe00:~/Interactive-Lab-Hub/Lab 3 $ python3 -m venv .venv
pi@ixe00:~/Interactive-Lab-Hub $ source .venv/bin/activate
(.venv)pi@ixe00:~/Interactive-Lab-Hub $ 
```

✅ Run the setup script
```(.venv)pi@ixe00:~/Interactive-Lab-Hub $ pip install -r requirements.txt  ```

✅ Next, run the setup script to install additional text-to-speech dependencies:
```
(.venv)pi@ixe00:~/Interactive-Lab-Hub/Lab 3 $ ./setup.sh
```
</details>


### Text to Speech 

✅ In this part of lab, we are going to start peeking into the world of audio on your Pi! 

<details>
<summary>Click to toggle contents of some testing scripts.</summary>
We will be using the microphone and speaker on your webcamera. In the directory is a folder called `speech-scripts` containing several shell scripts. `cd` to the folder and list out all the files by `ls`:

```
pi@ixe00:~/speech-scripts $ ls
Download        festival_demo.sh  GoogleTTS_demo.sh  pico2text_demo.sh
espeak_demo.sh  flite_demo.sh     lookdave.wav
```

✅ You can run these shell files `.sh` by typing `./filename`, for example, typing `./espeak_demo.sh` and see what happens. Take some time to look at each script and see how it works. You can see a script by typing `cat filename`. For instance:

```
pi@ixe00:~/speech-scripts $ cat festival_demo.sh 
#from: https://elinux.org/RPi_Text_to_Speech_(Speech_Synthesis)#Festival_Text_to_Speech
```
✅ You can test the commands by running
```
echo "Just what do you think you're doing, Dave?" | festival --tts
```

Now, you might wonder what exactly is a `.sh` file? 
Typically, a `.sh` file is a shell script which you can execute in a terminal. The example files we offer here are for you to figure out the ways to play with audio on your Pi!

You can also play audio files directly with `aplay filename`. Try typing `aplay lookdave.wav`.

---
Bonus: [Piper](https://github.com/rhasspy/piper) is another fast neural based text to speech package for raspberry pi.

[Piper](https://github.com/rhasspy/piper) is another fast neural based text to speech package for raspberry pi which can be installed easily through python with:
```
pip install piper-tts
```
and used from the command line. Running the command below the first time will download the model, concurrent runs will be faster. 
```
echo 'Welcome to the world of speech synthesis!' | piper \
  --model en_US-lessac-medium \
  --output_file welcome.wav
```
Check the file that was created by running `aplay welcome.wav`. Many more languages are supported and audio can be streamed dirctly to an audio output, rather than into an file by:

```
echo 'This sentence is spoken first. This sentence is synthesized while the first sentence is spoken.' | \
  piper --model en_US-lessac-medium --output-raw | \
  aplay -r 22050 -f S16_LE -t raw -
```
</details>


\*\***Write your own shell file to use your favorite of these TTS engines to have your Pi greet you by name.**\*\*
(This shell file should be saved to your own repo for this lab.)

**REMINDER: Before running any of these scripts, adjust the volume of Pi.**
The following command can set the volume to 30% or control the volume with `pavucontrol`
```
wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.30 
```

Ying Yu:
> Find the code on **speech-scripts/lab3_greet.sh**
>
> The following **two videos** demonstrate different Text-to-Speech (TTS) engines. 
> **Click the image to watch the video.**
>
> * The first video shows the output using espeak and pico2wave.
> * The second video demonstrates speech synthesis with Piper.

<p align="center">
  <a href="https://youtu.be/3vvfNtMkWso">
    <img src="https://img.youtube.com/vi/3vvfNtMkWso/0.jpg" alt="Demo 1" height="300">
  </a>
  &nbsp;&nbsp;&nbsp;
  <a href="https://youtu.be/06EkF5N80uc">
    <img src="https://img.youtube.com/vi/06EkF5N80uc/0.jpg" alt="Demo 2" height="300">
  </a>
</p>

Shreya:
> Code is in speech-scripts/greet_shreya.sh
> 
> The script uses GoogleTTS to greet Shreya
> 
> [Video](https://drive.google.com/file/d/14bAQtoSJ84QoHgKTpH4GYF070SGiDLXs/view?usp=sharing)

  
### Speech to Text
<details>
<summary>Click to toggle contents of Vosk and Whisper</summary>

Next setup speech to text. We are using a speech recognition engine, [Vosk](https://alphacephei.com/vosk/), which is made by researchers at Carnegie Mellon University. Vosk is amazing because it is an offline speech recognition engine; that is, all the processing for the speech recognition is happening onboard the Raspberry Pi. 

Make sure you're running in your virtual environment with the dependencies already installed:
```
source .venv/bin/activate
```

Test if vosk works by transcribing text:

```
vosk-transcriber -i recorded_mono.wav -o test.txt
```

You can use vosk with the microphone by running 
```
python test_microphone.py -m en
```

---
Bonus:
[Whisper](https://openai.com/index/whisper/) is a neural network–based speech-to-text (STT) model developed and open-sourced by OpenAI. Compared to Vosk, Whisper generally achieves higher accuracy, particularly on noisy audio and diverse accents. It is available in multiple model sizes; for edge devices such as the Raspberry Pi 5 used in this class, the tiny.en model runs with reasonable latency even without a GPU.

By contrast, Vosk is more lightweight and optimized for running efficiently on low-power devices like the Raspberry Pi. The choice between Whisper and Vosk depends on your scenario: if you need higher accuracy and can afford slightly more compute, Whisper is preferable; if your priority is minimal resource usage, Vosk may be a better fit.

In this class, we provide two Whisper options: A quantized 8-bit faster-whisper model for speed, and the standard Whisper model. Try them out and compare the trade-offs.

Make sure you're in the Lab 3 directory with your virtual environment activated:
```
cd ~/Interactive-Lab-Hub/Lab\ 3/speech-scripts
source ../.venv/bin/activate
```

Then test the Whisper models:
```
python whisper_try.py
```
and

```
python faster_whisper_try.py
```

</details>

\*\***Write your own shell file that verbally asks for a numerical based input (such as a phone number, zipcode, number of pets, etc) and records the answer the respondent provides.**\*\*

Ying Yu:
> Find the code on 
> * **speech-scripts/lab3_ask_number.sh** 
> * **speech-scripts/lab3_transcribe_number.py**
>
> Below are the demo video and the terminal screenshot from my test run.
> **Click the image to watch the video.**

![zip_code](images/zip_code_test.png)
[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/l5FmxoiRhJA/0.jpg)](https://youtu.be/l5FmxoiRhJA)


Shreya:
> Code is speech-scripts/ask_number_siblings.sh & speech-scripts/ask_num_siblings.py
> 
> The code verbally prompts user for the number of siblings, processes the response, and prints it in the terminal
> 
> [Video](https://drive.google.com/file/d/1pHRaCt3tzJl87oIlbdMygrmKNYHMUe0M/view?usp=sharing)
> 
> As shown in the video, the number one is printed in the terminal as the user responded with a one
> <img width="1403" height="195" alt="image" src="https://github.com/user-attachments/assets/bebee056-1a0a-4b45-bca8-5418fc6bddc2" />


### 🤖 NEW: AI-Powered Conversations with Ollama

Want to add intelligent conversation capabilities to your voice projects? **Ollama** lets you run AI models locally on your Raspberry Pi for sophisticated dialogue without requiring internet connectivity!

<details>
<summary>Click to toggle contents of Ollama.</summary>

#### Quick Start with Ollama

**Installation** (takes ~5 minutes):
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download recommended model for Pi 5
ollama pull phi3:mini

# Install system dependencies for audio (required for pyaudio)
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-dev

# Create separate virtual environment for Ollama (due to pyaudio conflicts)
cd ollama/
python3 -m venv ollama_venv
source ollama_venv/bin/activate

# Install Python dependencies in separate environment
pip install -r ollama_requirements.txt
```
#### Ready-to-Use Scripts

We've created three Ollama integration scripts for different use cases:

**1. ✅ Basic Demo** - Learn how Ollama works:
```bash
python3 ollama_demo.py
```

**2. ✅ Voice Assistant** - Full speech-to-text + AI + text-to-speech:
```bash
python3 ollama_voice_assistant.py
```

**3. Web Interface** - Beautiful web-based chat with voice options:
```bash
python3 ollama_web_app.py
# Then open: http://localhost:5000
```

#### Integration in Your Projects

Simple example to add AI to any project:
```python
import requests

def ask_ai(question):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "phi3:mini", "prompt": question, "stream": False}
    )
    return response.json().get('response', 'No response')

# Use it anywhere!
answer = ask_ai("How should I greet users?")
```

**📖 Complete Setup Guide**: See `OLLAMA_SETUP.md` for detailed instructions, troubleshooting, and advanced usage!

</details>


\*\***Try creating a simple voice interaction that combines speech recognition, Ollama processing, and text-to-speech output. Document what you built and how users responded to it.**\*\*

> Find the code on **ollama/lab3_ollama_food.py**
>
> The following **videos** is the demo for the Food Recommendation Assistant. 
> **Click the image to watch the video.**

[![image](https://img.youtube.com/vi/__usS4v8-7I/0.jpg)](https://youtu.be/__usS4v8-7I)

The screenshots below show the conversation logs for both text-to-speech and speech-to-text. Since there are many warnings when running on the Pi, screenshots make the record clearer.

![food1](images/food1.png)
![food2](images/food2.png)

This flowchart shows the basic workflow of the voice-controlled food recommendation system:

1. Start Program - Initialize the voice assistant
2. Voice Input - Continuously listen for user speech
3. Voice Detection - Check if voice input is detected
  * If no voice detected, continue listening
  * If voice detected, proceed to next step
4. Convert to Text - Transform user speech into text
5. Send to **Ollama AI** - Pass the text to AI for processing
6. Get Food Suggestions - AI analyzes the request and generates food recommendations
7. Speak Response - Convert AI suggestions back to speech and play to user
8. Loop - Return to voice input for next conversation

The system runs in a continuous loop until the user says "quit" to end the program. This follows the typical voice assistant interaction pattern: **Listen → Understand → Process → Respond → Repeat**.
Below is a simplified flowchart of the process:
![food2](images/food3.jpeg)


### Serving Pages

<details>
<summary>Click to toggle contents of webserver.</summary>

In Lab 1, we served a webpage with flask. In this lab, you may find it useful to serve a webpage for the controller on a remote device. Here is a simple example of a webserver.

```
pi@ixe00:~/Interactive-Lab-Hub/Lab 3 $ python server.py
 * Serving Flask app "server" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: on
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 162-573-883
```

</details>

✅ From a remote browser on the same network, check to make sure your webserver is working by going to `http://<YourPiIPAddress>:5000`. You should be able to see "Hello World" on the webpage.

### Storyboard

**Collaborate with [Shreya Kethi Reddy](https://github.com/littleredpolkadot/Interactive-Lab-Hub)**

Storyboard and/or use a Verplank diagram to design a speech-enabled device. (Stuck? Make a device that talks for dogs. If that is too stupid, find an application that is better than that.) 

\*\***Post your storyboard and diagram here.**\*\*

![IMG_561787F51844-1](images/story1.png)


We want to use the answering functionality to create something like a **software engineer’s rubber duck**. The term rubber duck comes from the idea of rubber duck debugging, where programmers explain their code to a simple object to help them reflect on and debug their work.

The rubber duck **doesn’t solve the problem** for the users. Instead, it prompts users to verbalize their thought process, helping users clarify bugs until they reach the solution themselves.

![IMG_561787F51844-1](images/diagram1.png)

---
Write out what you imagine the dialogue to be. Use cards, post-its, or whatever method helps you develop alternatives or group responses. 

\*\***Please describe and document your process.**\*\*

![IMG_561787F51844-1](images/script1.png)


When creating the script, we imagine a process that will let the user work through problems themselves. Thus we imagine scenarios where the duck (which will take the form of some kind of cute stuffed toy and in this process diagram it is a bear) will offer support to the user through means of lending an ear to their frustration and nudging them to take breaks like a supportive friend. The most primary form of interaction is the process where a user will repeatedly interact with the duck as a means to work through a problem and while explaining come to a realization themselves.


### Acting out the dialogue

Find a partner, and *without sharing the script with your partner* try out the dialogue you've designed, where you (as the device designer) act as the device you are designing.  Please record this interaction (for example, using Zoom's record feature).

\*\***Describe if the dialogue seemed different than what you imagined when it was acted out, and how.**\*\*

[Acting out the dialogue video](https://drive.google.com/file/d/1Sy7go3HnWef96RqTYzi3dYmZG9uQ9RM7/view?usp=sharing)

> Shreya designed the script, while Ying Yu acted as the user without knowing the script. We discovered that if the rubber duck keeps giving constant feedback, it can actually become a bit annoying, and the user may also be unsure when the interaction should come to an end.

### Wizarding with the Pi (optional)
In the [demo directory](./demo), you will find an example Wizard of Oz project. In that project, you can see how audio and sensor data is streamed from the Pi to a wizard controller that runs in the browser.  You may use this demo code as a template. By running the `app.py` script, you can see how audio and sensor data (Adafruit MPU-6050 6-DoF Accel and Gyro Sensor) is streamed from the Pi to a wizard controller that runs in the browser `http://<YouPiIPAddress>:5000`. You can control what the system says from the controller as well!

\*\***Describe if the dialogue seemed different than what you imagined, or when acted out, when it was wizarded, and how.**\*\*
> We ran into some issues during this part, especially with Python version compatibility. Because of that, it was difficult for us to properly run the demo and act out the dialogue as intended. We plan to revisit and resolve these technical challenges in Part 2.

# Lab 3 Part 2

For Part 2, you will redesign the interaction with the speech-enabled device using the data collected, as well as feedback from part 1.

## Prep for Part 2

1. What are concrete things that could use improvement in the design of your device? For example: wording, timing, anticipation of misunderstandings...
> * Sometimes, when the user pauses, it means they are thinking, but the bear’s response **interrupts** their thought process. → We plan to add a **recording button** (with a light indicator): when the button is pressed and the light is on, it records; pressing it again turns off the light and stops recording.
> * As seen in Part A of the video, when the user finds the solution, the bear sometimes continues asking questions because it’s unaware of the situation, which can be confusing. → We could add a **button (OFF)** to deactivate the bear, or let it **detect  keywords** (from recording button) such as “Oh, I’m good” to automatically end the session.
> * Starting the interaction too abruptly feels awkward. → We plan to include a **greeting phase**, where the bear first greets the user and confirms what problem they are working on before beginning the conversation.

2. What are other modes of interaction _beyond speech_ that you might also use to clarify how to interact?

> We plan to include **two physical buttons with LED indicators** to make the interaction clearer. One is a **recording button**, which lights up while recording to show that the bear is “listening.” The other is a **OFF button** that allows the user to manually deactivate the bear at any time. These physical controls help users easily understand the system’s current state and reduce confusion during interaction.

3. Make a new storyboard, diagram and/or script based on these reflections.
![IMG_561787F51844-1](images/diagram2.jpg)
![IMG_561787F51844-1](images/story2.jpg)
![script](images/script2.jpeg)


## Prototype your system

The system should:
* ✅ use the Raspberry Pi 
* ✅ use one or more sensors: 2 buttons
* ✅ require participants to speak to it. 

<!-- *Document how the system works*

*Include videos or screencaptures of both the system and the controller.* -->

**Controller Logic Flowchart:**
![control](images/control.jpg)
The start and end of recording are controlled by buttons. Depending on the user’s current task (greeting, describing the problem, or responding whether the interaction was helpful and should continue), the system decides whether to loop back for another recording or end the session.

**System Setup Overview – Wizard Side:**
![system](images/system.jpeg)


**Testing with Users (Video):**
<!-- put the video link here -->


<details>
  <summary><strong>Submission Cleanup Reminder (Click to Expand)</strong></summary>
  
  **Before submitting your README.md:**
  - This readme.md file has a lot of extra text for guidance.
  - Remove all instructional text and example prompts from this file.
  - You may either delete these sections or use the toggle/hide feature in VS Code to collapse them for a cleaner look.
  - Your final submission should be neat, focused on your own work, and easy to read for grading.
  
  This helps ensure your README.md is clear professional and uniquely yours!
</details>

## Test the system
Try to get at least two people to interact with your system. (Ideally, you would inform them that there is a wizard _after_ the interaction, but we recognize that can be hard.)

Answer the following:

### What worked well about the system and what didn't?
\*\**your answer here*\*\*

### What worked well about the controller and what didn't?

\*\**your answer here*\*\*

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?

\*\**your answer here*\*\*


### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?

\*\**your answer here*\*\*








