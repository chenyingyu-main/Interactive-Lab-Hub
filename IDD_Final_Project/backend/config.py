"""
Configuration and Constants
"""

import pygame

# ============================================================================
# TIMING CONSTANTS
# ============================================================================

LEAD_TIME = 3  # seconds early to show notes visually
HIT_WINDOW = 0.5  # ±150ms window for hitting notes
HOLD_CHECK_INTERVAL = 0.05  # check hold status every 50ms
HOLD_GRACE_PERIOD = 0.1  # 100ms grace before breaking a hold
HOLD_THRESHOLD = 1

# ============================================================================
# MQTT CONFIGURATION
# ============================================================================

MQTT_BROKER = 'farlab.infosci.cornell.edu'
MQTT_PORT = 1883
MQTT_TOPIC = 'IDD/kitchen-instrument'
MQTT_USERNAME = 'idd'
MQTT_PASSWORD = 'device@theFarm'

# ============================================================================
# MESSAGE STORAGE
# ============================================================================

MAX_MESSAGES = 100  # Maximum messages to store in history

# ============================================================================
# AUDIO CONFIGURATION
# ============================================================================

# Initialize pygame mixer once
pygame.mixer.init()
print("[OK] Audio system ready")

# Dedicated audio channels for each utensil (prevents interference)
CHANNELS = {
    'pan': pygame.mixer.Channel(0),
    'cutting_board': pygame.mixer.Channel(1),
    'mixing_bowl': pygame.mixer.Channel(2)
}

# Sound configuration for each utensil
SOUND_RULES = {
    'pan': {
        'file': 'sounds/pan_sizzle.mp3',
        'threshold': 2,
        'target_value': None  # Will be set by chart (e.g., "low" or "high")
    },
    'cutting_board': {
        'file': 'sounds/knife-stab-pull.mp3',
        'threshold': 0,
        'target_value': None  # Will be set by chart (e.g., button ID)
    },
    'mixing_bowl': {
        'file': 'sounds/whisking.mp3',
        'threshold': 0,
        'target_value': None  # Will be set by chart (e.g., acceleration value)
    }
}

# Pan Fire Values
LOW_FIRE = 5
MED_FIRE = 10
HIGH_FIRE = 15