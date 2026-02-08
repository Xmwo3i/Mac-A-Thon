import cv2
import mediapipe as mp
import yarppg
import numpy as np
import warnings
import os

# Suppress all Deprecation Warnings from libraries (e.g., OpenCV, MediaPipe) to keep output clean
warnings.filterwarnings("ignore", category=DeprecationWarning)
# Silences MediaPipe logging noise
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Initialize yarPPG
rppg = yarppg.Rppg()

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

cap = cv2.VideoCapture(0)
blink_count = 0
eye_closed = False
frame_count = 0

while cap.isOpened():
    
    success, frame = cap.read()
    if not success: break

    frame_count += 1

    # --- HEART RATE LOGIC ---
    # process_frame returns an RppgResult object with HR calculated
    result = rppg.process_frame(frame)
    
    # Extract HR from result (in beats per minute)
    # yarPPG needs a buffer of frames to calculate HR
    hr = result.hr if not np.isnan(result.hr) else 0
    
    # Convert from frames per beat to BPM (multiply by FPS and divide by 60)
    if hr > 0:
        hr = (30/hr) * 60  # Assuming 30 FPS camera


    # --- BLINK LOGIC ---
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    
    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark
        
        # Eye landmarks for EAR calculation
        # Simplified: vertical distance between eyelid landmarks
        left_eye_top, left_eye_bot = landmarks[159].y, landmarks[145].y
        right_eye_top, right_eye_bot = landmarks[386].y, landmarks[374].y
        
        ear = ((left_eye_bot - left_eye_top) + (right_eye_bot - right_eye_top)) / 2.0
        
        if ear < 0.012: # Tune this threshold if blinks aren't registering
            if not eye_closed:
                blink_count += 1
                eye_closed = True
        else:
            eye_closed = False

    # --- UI DASHBOARD ---
    # Heart Rate (Green if stable, Red if 0)
    hr_color = (0, 255, 0) if hr > 0 else (0, 0, 255)
    cv2.putText(frame, f"Heart Rate: {hr:.1f} BPM", (30, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, hr_color, 2)
    
    # Blinks
    cv2.putText(frame, f"Blinks: {blink_count}", (30, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    cv2.imshow('Hackathon Biometrics', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()