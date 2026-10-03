"""
Hand Gesture Media Controller
-----------------------------
Uses your webcam to detect hand gestures and sends media keys
(play/pause, next, previous, volume) to your PC.

Gestures (palm facing camera, hand upright, thumb ignored):
  4 fingers up           -> Play / Pause
  Thumb+index "knob"     -> Turn clockwise = volume up, anticlockwise = down
  Index + middle + ring  -> Next track
  Pinky only             -> Previous track
  Fist                   -> Nothing

Press 'q' in the camera window to quit.
"""

import math
import time

import cv2
import mediapipe as mp
import pyautogui

# ---------------- Settings you can tweak ----------------
CAMERA_INDEX = 0        # try 1 if your webcam isn't found
HOLD_FRAMES = 5         # gesture must be held this many frames to count
COOLDOWN = {            # seconds to wait before an action can fire again
    "playpause": 1.5,
    "nexttrack": 1.5,
    "prevtrack": 1.5,
}

# Knob (volume dial) settings
DEGREES_PER_STEP = 8     # turn this many degrees = 1 volume key press (2% on Windows)
KNOB_MIN_OPENNESS = 0.45 # thumb-index gap must be this big (relative to hand size)

# Finger pattern (index, middle, ring, pinky) -> (action key, label to show)
GESTURES = {
    (1, 1, 1, 1): ("playpause", "Play / Pause"),
    (1, 1, 1, 0): ("nexttrack", "Next Track"),
    (0, 0, 0, 1): ("prevtrack", "Previous Track"),
}

# MediaPipe landmark numbers: (fingertip, lower joint) for each finger
FINGERS = [(8, 6), (12, 10), (16, 14), (20, 18)]

pyautogui.PAUSE = 0  # no built-in delay after each key press

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


def get_finger_pattern(hand_landmarks):
    """Return a tuple like (1, 0, 0, 0): 1 = finger up, 0 = finger down."""
    lm = hand_landmarks.landmark
    # Finger is "up" if its tip is higher on screen (smaller y) than its joint
    return tuple(1 if lm[tip].y < lm[joint].y else 0 for tip, joint in FINGERS)


def dist(a, b):
    """Distance between two landmarks."""
    return math.hypot(a.x - b.x, a.y - b.y)


def is_knob_pose(lm):
    """Middle, ring, pinky folded + thumb and index spread apart."""
    wrist = lm[0]
    # A finger is folded if its tip is closer to the wrist than its middle joint
    # (this works even when your hand is tilted or rotated)
    folded = all(dist(wrist, lm[tip]) < dist(wrist, lm[joint])
                 for tip, joint in [(12, 10), (16, 14), (20, 18)])
    hand_size = dist(lm[0], lm[9])  # wrist to middle-finger base
    openness = dist(lm[4], lm[8]) / hand_size if hand_size else 0
    return folded and openness > KNOB_MIN_OPENNESS


def knob_angle(lm, w, h):
    """Angle (degrees) of the line from thumb tip to index tip on screen.
    Because screen y points down, an increasing angle = clockwise turn."""
    dx = (lm[8].x - lm[4].x) * w
    dy = (lm[8].y - lm[4].y) * h
    return math.degrees(math.atan2(dy, dx))


def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("Could not open the webcam. Try changing CAMERA_INDEX.")
        return

    last_fired = {}          # action key -> time it last fired
    current_gesture = None   # gesture currently being held
    held_count = 0           # how many frames in a row it has been held
    status_text = "Show a gesture"
    prev_angle = None        # knob angle in the previous frame
    angle_total = 0          # degrees turned but not yet converted to key presses

    with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    ) as hands:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            frame = cv2.flip(frame, 1)  # mirror view so it feels natural
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            detected = None
            knob_mode = False
            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]
                mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
                lm = hand.landmark
                h, w, _ = frame.shape

                if is_knob_pose(lm):
                    knob_mode = True
                    angle = knob_angle(lm, w, h)
                    if prev_angle is not None:
                        # Smallest turn between frames, handles the -180/+180 wrap
                        delta = (angle - prev_angle + 180) % 360 - 180
                        angle_total += delta
                        while angle_total >= DEGREES_PER_STEP:      # clockwise
                            pyautogui.press("volumeup")
                            angle_total -= DEGREES_PER_STEP
                            status_text = "Volume Up"
                        while angle_total <= -DEGREES_PER_STEP:     # anticlockwise
                            pyautogui.press("volumedown")
                            angle_total += DEGREES_PER_STEP
                            status_text = "Volume Down"
                    prev_angle = angle
                    # Draw a line between thumb and index so you can see the "knob"
                    p1 = (int(lm[4].x * w), int(lm[4].y * h))
                    p2 = (int(lm[8].x * w), int(lm[8].y * h))
                    cv2.line(frame, p1, p2, (0, 255, 255), 4)
                else:
                    detected = GESTURES.get(get_finger_pattern(hand))

            if not knob_mode:
                prev_angle = None   # reset so the next knob use starts fresh
                angle_total = 0

            # Count how long the same gesture has been held
            if detected and detected == current_gesture:
                held_count += 1
            else:
                current_gesture = detected
                held_count = 1 if detected else 0

            # Fire the action if held long enough and cooldown has passed
            if current_gesture and held_count >= HOLD_FRAMES:
                key, label = current_gesture
                now = time.time()
                if now - last_fired.get(key, 0) >= COOLDOWN[key]:
                    pyautogui.press(key)
                    last_fired[key] = now
                    status_text = label

            cv2.putText(frame, f"Last action: {status_text}", (10, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            cv2.putText(frame, "Press 'q' to quit", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.imshow("Gesture Media Controller", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()