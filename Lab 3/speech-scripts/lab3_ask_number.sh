# Ask a question with TTS, record user speech, transcribe with Whisper

# ask a question with TTS
QUESTION="Please say your zip code after the beep."
espeak -ven+f2 -k5 -s150 --stdout  "$QUESTION" | aplay

# Beep sound
espeak -ven+f2 -k5 -s150 --stdout "beep" | aplay

# record user speech (5 seconds, 16kHz, mono)
arecord -D pulse -d 5 -r 16000 -f S16_LE -c 1 lab3_answer.wav

# fast whisper transcription
python3 lab3_transcribe_number.py lab3_answer.wav
