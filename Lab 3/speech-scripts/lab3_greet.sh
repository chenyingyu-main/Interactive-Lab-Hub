wpctl set-volume @DEFAULT_AUDIO_SINK@ 0.30
# adjust the volume as needed

TEXT=${1:-"Hello, Ying Yu Chen!"}
TEXT_2=${2:-"Welcome back to Lab three!"}
TEXT_3=${3:-"Now Ying Yu is testing Text to Speech."}

# from https://elinux.org/RPi_Text_to_Speech_(Speech_Synthesis)
espeak -ven+f2 -k5 -s150 --stdout  "$TEXT" | aplay
echo "$TEXT_2" | festival --tts
pico2wave -w hi_yingyu.wav "$TEXT_3" && aplay hi_yingyu.wav

