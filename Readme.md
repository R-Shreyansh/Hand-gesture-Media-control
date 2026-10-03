# Windows Hand Gesture Media Controller

A computer vision application built with Python and MediaPipe that allows you to control Windows system media (Spotify, YouTube, VLC, etc.) and volume using real-time hand gestures. 

This project utilizes `pyautogui` to simulate native Windows media hardware keys, allowing you to control background applications without needing the target app to be the active window.

## Features & Gestures

Hold your hand upright with your palm facing the webcam to trigger the following controls:

*   **Pinch and Twist (Virtual Knob):** Controls Windows System Volume. 
    *   Bring thumb and index finger together. Twist wrist clockwise to increase volume, counter-clockwise to decrease.
*   **Four Fingers Up:** Play / Pause media.
*   **Index, Middle, and Ring Fingers Up:** Next Track.
*   **Pinky Finger Up:** Previous Track.

## Prerequisites

*   Windows 10 or 11
*   Python 3.11 (MediaPipe currently has compatibility issues with Python 3.12+)
*   A functioning webcam

## Installation

1. Clone this repository:
   ```cmd
   git clone [https://github.com/R-Shreyansh/Hand-gesture-Media-control.git](https://github.com/R-Shreyansh/Hand-gesture-Media-control.git)
   cd gesture-media-controller