import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
import numpy as np
import time
import pi_servo_hat
import math

# Set up servo: For most 9g micro servos (like SG90, MS18, SER0048), safe range is 0-120 degrees
SERVO_MIN = 0
SERVO_MAX = 120
SERVO1_CH = 0  
SERVO2_CH = 1

SERVO3_CH = 2  
SERVO4_CH = 3

servo = pi_servo_hat.PiServoHat()
servo.restart()




def draw_landmarks_on_image(rgb_image, detection_result):
  pose_landmarks_list = detection_result.pose_landmarks
  annotated_image = np.copy(rgb_image)

  for idx in range(len(pose_landmarks_list)):
    pose_landmarks = pose_landmarks_list[idx]

    pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
    pose_landmarks_proto.landmark.extend([
      landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in pose_landmarks
    ])
    solutions.drawing_utils.draw_landmarks(
      annotated_image,
      pose_landmarks_proto,
      solutions.pose.POSE_CONNECTIONS,
      solutions.drawing_styles.get_default_pose_landmarks_style())
  return annotated_image

def print_parsed_landmarks(detection_result):
    pose_landmarks_list = detection_result.pose_landmarks

    # parts we care about
    part_dict = {
        "left_shoulder": 11,
        "right_shoulder": 12,
        "left_elbow": 13,
        "right_elbow": 14,
        "left_wrist": 15,
        "right_wrist": 16
    }

    for part_name, part_index in part_dict.items():
        for idx in range(len(pose_landmarks_list)):
            pose_landmarks = pose_landmarks_list[idx]
            landmark = pose_landmarks[part_index]
            if landmark.visibility > 0.9:
                print(f"Pose {idx + 1} {part_name}: x={landmark.x}, y={landmark.y}, z={landmark.z}")


def angle_2d_from_points(p1, p2, invert_y=False, invert_x=False):
    x1, y1 = p1
    x2, y2 = p2
    if invert_y:
        y1, y2 = -y1, -y2
    if invert_x:
        x1, x2 = -x1, -x2

    dx = x2 - x1
    dy = y2 - y1
    angle = math.degrees(math.atan2(dy, dx))
    angle = (angle + 360) % 360  # wrap into 0?360

    # # optional: convert to 0?180 if servo only moves one direction
    # if angle > 180:
    #     angle = 360 - angle

    return angle

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

# poselandmarker init
base_options = python.BaseOptions(model_asset_path='pose_landmarker_lite.task')
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    output_segmentation_masks=False,
    running_mode=vision.RunningMode.IMAGE  # synchronous frame processing
)
detector = vision.PoseLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open webcam")
    exit()

curr_r_upper_angle = 0
curr_r_lower_angle = 0
curr_l_upper_angle = 0
curr_l_lower_angle = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame,1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)



    detection_result = detector.detect(mp_image)

    annotated_image = draw_landmarks_on_image(rgb_frame, detection_result)
    # print_parsed_landmarks(detection_result)

    pose_landmarks_list = detection_result.pose_landmarks
    if pose_landmarks_list is not None and len(pose_landmarks_list) > 0:
        pose_landmarks = pose_landmarks_list[0]  # first detected person
        shoulder_r = pose_landmarks[12]
        elbow_r = pose_landmarks[14]
        wrist_r = pose_landmarks[16]

        shoulder_l = pose_landmarks[11]
        elbow_l = pose_landmarks[13]
        wrist_l = pose_landmarks[15]
        
        shoulder_point_r = (shoulder_r.x, shoulder_r.y)
        elbow_point_r = (elbow_r.x, elbow_r.y)
        wrist_point_r = (wrist_r.x, wrist_r.y)


        # calculate angles
        upper_r_angle_deg = angle_2d_from_points(shoulder_point_r, elbow_point_r, invert_y=True)
        lower_r_angle_deg = angle_2d_from_points(elbow_point_r, wrist_point_r, invert_y=True)
        upper_r_servo_angle= clamp(upper_r_angle_deg-120, SERVO_MIN, SERVO_MAX)
        lower_r_servo_angle= clamp(lower_r_angle_deg-60, SERVO_MIN, SERVO_MAX)

        # Mirror over Y-axis
        shoulder_point_l = (shoulder_l.x, shoulder_l.y)
        elbow_point_l = (elbow_l.x, elbow_l.y)
        wrist_point_l = (wrist_l.x, wrist_l.y)

        # Compute angles
        upper_l_angle_deg = angle_2d_from_points(shoulder_point_l, elbow_point_l, invert_x=True)
        lower_l_angle_deg = angle_2d_from_points(elbow_point_l, wrist_point_l, invert_x=True)
        upper_l_servo_angle = clamp((upper_l_angle_deg-125), SERVO_MIN, SERVO_MAX)
        lower_l_servo_angle = clamp((lower_l_angle_deg-165), SERVO_MIN, SERVO_MAX)
                
        
        # alpha = 0.2  # smoothing factor (0 = frozen, 1 = instant)
        # upper_l_servo_angle = curr_l_upper_angle + alpha * (upper_l_servo_angle - curr_l_upper_angle)
        # lower_l_servo_angle = curr_l_lower_angle + alpha * (lower_l_servo_angle - curr_l_lower_angle)

        print(f"Right Upper: {upper_r_angle_deg:.2f} -> Servo: {upper_r_servo_angle:.2f}")
        print(f"Right Lower: {lower_r_angle_deg:.2f} -> Servo: {lower_r_servo_angle:.2f}")
        print(f"Left Upper: {upper_l_angle_deg:.2f} -> Servo: {upper_l_servo_angle:.2f}")
        print(f"Left Lower: {lower_l_angle_deg:.2f} -> Servo: {lower_l_servo_angle:.2f}")

        # Mmve right arm servos
        if abs(curr_r_upper_angle - upper_r_servo_angle) > 5:
           curr_r_upper_angle = upper_r_servo_angle
           servo.move_servo_position(SERVO1_CH, upper_r_servo_angle)
        if abs(curr_r_lower_angle - lower_r_servo_angle) > 2:
           curr_r_lower_angle = lower_r_servo_angle
           servo.move_servo_position(SERVO2_CH, lower_r_servo_angle)

        # move left arm servos (inverted)
        if abs(curr_l_upper_angle - upper_l_servo_angle) > 5:
            curr_l_upper_angle = upper_l_servo_angle
            servo.move_servo_position(SERVO3_CH, upper_l_servo_angle)
        if abs(curr_l_lower_angle - lower_l_servo_angle) > 2:
            curr_l_lower_angle = lower_l_servo_angle
            servo.move_servo_position(SERVO4_CH, lower_l_servo_angle)
  
    cv2.imshow('Pose Landmarks', cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()