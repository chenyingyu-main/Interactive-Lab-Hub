#!/usr/bin/env python3
"""
Simple Raspberry Pi Sound Player
Plays audio files (MP3, WAV, OGG) through default audio output.
"""

import pygame
import sys
import os
from time import sleep

# Initialize once when the module loads
pygame.mixer.init()
print("[OK] Audio system ready")

def play_sound(file_path):
    """Play a sound file using pygame mixer."""
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        sys.exit(1)

    # Load the sound file
    try:
        pygame.mixer.music.load(file_path)
        print(f"[OK] Loaded file: {file_path}")
    except pygame.error as e:
        print(f"[ERROR] Cannot load sound file: {e}")
        sys.exit(1)

    # Play the sound
    pygame.mixer.music.play()
    print(f"[PLAYING] {file_path}")

    # Wait until playback finishes
    while pygame.mixer.music.get_busy():
        sleep(0.1)

    print("[DONE] Playback finished.")

def stop_sound():
    """Stop current playback."""
    pygame.mixer.music.stop()
    print("[STOPPED] Playback interrupted")

def close_audio():
    """Cleanly shut down the audio system."""
    pygame.mixer.quit()
    print("[CLOSED] Audio system shut down")


if __name__ == "__main__":
    sound_file = "welcome.wav"
    
    while True:

        play_sound(sound_file)
        sleep(5)


    close_audio()
