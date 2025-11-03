import time
import pi_servo_hat

# ------------------------------
# Servo configuration
# ------------------------------
SERVO_MIN = 0
SERVO_MAX = 180
# Right arm (keep current)
SERVO1_CH = 0   # Upper servo
SERVO2_CH = 1   # Lower servo
# Left arm (new)
SERVO3_CH = 2   # Upper servo
SERVO4_CH = 3   # Lower servo

# "Straight arm" angles based on your measurements
UPPER_SERVO_STRAIGHT = 75.0
LOWER_SERVO_STRAIGHT = 114.0

# ------------------------------
# Initialize and move servos
# ------------------------------
servo = pi_servo_hat.PiServoHat()
servo.restart()

print("Moving right arm to current position...")
# Right arm (keep current behavior)
servo.move_servo_position(SERVO1_CH, UPPER_SERVO_STRAIGHT)
servo.move_servo_position(SERVO2_CH, LOWER_SERVO_STRAIGHT)

# Left arm (set straight)
print("Moving left arm to straight position...")
servo.move_servo_position(SERVO3_CH, 120-UPPER_SERVO_STRAIGHT)
servo.move_servo_position(SERVO4_CH, 120-LOWER_SERVO_STRAIGHT)

time.sleep(1.0)

print(f"Right upper servo set to {UPPER_SERVO_STRAIGHT}° (channel {SERVO1_CH})")
print(f"Right lower servo set to {LOWER_SERVO_STRAIGHT}° (channel {SERVO2_CH})")
print(f"Left upper servo set to {120-UPPER_SERVO_STRAIGHT}° (channel {SERVO3_CH})")
print(f"Left lower servo set to {120-LOWER_SERVO_STRAIGHT}° (channel {SERVO4_CH})")
print("Right arm kept as is; left arm now straight, ready to physically attach or align pieces.")
