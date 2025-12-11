"""
Audio Manager - Sound loading and playback
"""

import pygame
import os
from functools import lru_cache
from config import CHANNELS, LOW_FIRE, HIGH_FIRE, MED_FIRE

# Magic Numbers


# ============================================================================
# PLAYBACK STATE
# ============================================================================

# Track which utensils are currently playing sounds
playing_state = {
    'pan': False,
    'cutting_board': False,
    'mixing_bowl': False
}

# ============================================================================
# SOUND CONDITION CHECKING
# ============================================================================

def should_play(utensil, sensor_data, target, threshold):
    """
    Check if the current sensor data meets the target condition for this utensil.
    
    Args:
        utensil: 'pan', 'cutting_board', or 'mixing_bowl'
        sensor_data: dict of sensor values from MQTT
        target: the target value from the chart (e.g., "low", "high", button ID)
        threshold: numeric threshold for comparison
    
    Returns:
        bool: True if condition is met, False otherwise
    """
    
    if target is None:
        return False

    if utensil == 'pan':
        # Pan uses rotation sensor AND button state (on/off)
        button_held = sensor_data.get('distance', False)
        
        # # Determine stove state based on target
        # if "off" in str(target):
        #     stove_on = (button_held == False)  # OFF means button NOT held
        # elif "on" in str(target):
        #     stove_on = (button_held == True)   # ON means button held
        # else:
        #     stove_on = True  # Legacy: assume stove is on
        
        # Then check rotation threshold
        curr_val = sensor_data.get('rotation', 0)
        if "low" in str(target):
            return curr_val <= LOW_FIRE + threshold and curr_val >= LOW_FIRE - threshold 
        elif "med" in str(target):
            return curr_val <= MED_FIRE + threshold and curr_val >= MED_FIRE - threshold 
        elif "high" in str(target):
            return curr_val <= HIGH_FIRE + threshold and curr_val >= HIGH_FIRE - threshold 
        elif "flip" in str(target):
            return button_held 
        
        return False

        
        
    elif utensil == "cutting_board":
        # Cutting board uses button presses
        button_id = str(target)
        return sensor_data.get(button_id, 0) == 1
    
    elif utensil == "mixing_bowl":
        # Mixing Bowl: up down right left
        x = sensor_data.get('x', 512)  # center
        y = sensor_data.get('y', 512)
        
        # threshold
        EDGE_THRESHOLD = 256  # dist from the center
        CENTER = 512
        
        if target == "up":
            # up: y = close to 0
            return y < (CENTER - EDGE_THRESHOLD)
        
        elif target == "down":
            # down: y = close to 1023
            return y > (CENTER + EDGE_THRESHOLD)
        
        elif target == "left":
            # left: x close to 0
            return x < (CENTER - EDGE_THRESHOLD)
        
        elif target == "right":
            # right: x close to 1023
            return x > (CENTER + EDGE_THRESHOLD)
        
        # elif target == "low":
        #     return sensor_data.get('speed', 0) < 400
        # elif target == "high":
        #     return sensor_data.get('speed', 0) > 400
    
    return False


# ============================================================================
# AUDIO PLAYBACK
# ============================================================================

@lru_cache(maxsize=10)
def load_sound(file_path):
    """Cache loaded sound objects to avoid reloading."""
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return None
    try:
        return pygame.mixer.Sound(file_path)
    except pygame.error as e:
        print(f"[ERROR] Cannot load sound file: {e}")
        return None


def play_sound(utensil, file_path, loop=False):
    """Play a sound for a specific utensil on its dedicated channel."""
    sound = load_sound(file_path)
    if not sound:
        return

    channel = CHANNELS.get(utensil)
    if channel:
        channel.play(sound, loops=-1 if loop else 0)
        print(f"[PLAYING] {utensil}: {file_path}")
    else:
        print(f"[WARN] No channel for utensil '{utensil}'")


def stop_sound(utensil):
    """Stop sound for a specific utensil."""
    channel = CHANNELS.get(utensil)
    if channel:
        channel.stop()
        print(f"[STOPPED] {utensil}")


def close_audio():
    """Cleanly shut down the audio system."""
    pygame.mixer.quit()
    print("[CLOSED] Audio system shut down")