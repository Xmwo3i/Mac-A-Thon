import cv2
import mediapipe as mp
import yarppg
import numpy as np
import warnings
import os
import threading
import time
from collections import deque

# Suppress all Deprecation Warnings from libraries (e.g., OpenCV, MediaPipe) to keep output clean
warnings.filterwarnings("ignore", category=DeprecationWarning)
# Silences MediaPipe logging noise
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


class BiometricsMonitor:
    """
    A thread-safe biometrics monitor that tracks heart rate and blink rate
    in a separate thread using webcam and MediaPipe/yarPPG.
    """
    
    def __init__(self, camera_index=0, fps=30, blink_window_seconds=60, show_ui=False):
        """
        Initialize the biometrics monitor.
        
        Args:
            camera_index: Camera device index (default 0)
            fps: Expected camera FPS for HR calculation
            blink_window_seconds: Time window for calculating blinks per minute
            show_ui: Whether to show the UI window (default False)
        """
        self.camera_index = camera_index
        self.fps = fps
        self.blink_window_seconds = blink_window_seconds
        self.show_ui = show_ui
        
        # Thread-safe data storage
        self._lock = threading.Lock()
        self._heart_rate = 0.0
        self._blinks_per_minute = 0.0
        self._blink_count = 0
        self._latest_frame = None
        
        # Blink timing tracking for rate calculation
        self._blink_timestamps = deque()
        
        # Thread control
        self._running = False
        self._thread = None
        self._eye_closed = False
        
        # Initialize yarPPG and MediaPipe
        self.rppg = yarppg.Rppg()
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(refine_landmarks=True)
        
    def start(self):
        """Start the biometrics monitoring thread."""
        if self._running:
            print("BiometricsMonitor is already running")
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print("BiometricsMonitor started")
        
    def stop(self):
        """Stop the biometrics monitoring thread."""
        if not self._running:
            return
            
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        print("BiometricsMonitor stopped")
        
    def get_metrics(self):
        """
        Get current biometric metrics in a thread-safe manner.
        
        Returns:
            tuple: (heart_rate, blinks_per_minute)
        """
        with self._lock:
            return self._heart_rate, self._blinks_per_minute
    
    def get_blink_count(self):
        """
        Get total blink count.
        
        Returns:
            int: Total number of blinks detected
        """
        with self._lock:
            return self._blink_count
            
    def _update_blinks_per_minute(self):
        """Calculate blinks per minute based on recent blink timestamps."""
        current_time = time.time()
        cutoff_time = current_time - self.blink_window_seconds
        
        # Remove old timestamps outside the window
        while self._blink_timestamps and self._blink_timestamps[0] < cutoff_time:
            self._blink_timestamps.popleft()
        
        # Calculate rate (blinks per minute)
        num_blinks = len(self._blink_timestamps)
        if num_blinks > 0:
            time_span = current_time - self._blink_timestamps[0]
            if time_span > 0:
                self._blinks_per_minute = (num_blinks / time_span) * 60
            else:
                self._blinks_per_minute = 0.0
        else:
            self._blinks_per_minute = 0.0
    
    def _monitor_loop(self):
        """Main monitoring loop that runs in a separate thread."""
        cap = cv2.VideoCapture(self.camera_index)
        
        if not cap.isOpened():
            print("Error: Could not open camera")
            self._running = False
            return
        
        print(f"Camera opened successfully. Starting biometrics monitoring...")
        frame_count = 0
        
        try:
            while self._running:
                success, frame = cap.read()
                if not success:
                    continue
                
                frame_count += 1
                
                # --- HEART RATE LOGIC ---
                result = self.rppg.process_frame(frame)
                hr_raw = result.hr if not np.isnan(result.hr) else 0
                
                # Convert from frames per beat to BPM
                if hr_raw > 0:
                    hr = (self.fps / hr_raw) * 60
                else:
                    hr = 0
                
                # Debug output every 30 frames
                if frame_count % 30 == 0:
                    print(f"Frame {frame_count}: HR raw={hr_raw:.2f}, HR BPM={hr:.1f}")
                
                # --- BLINK LOGIC ---
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_mesh.process(rgb_frame)
                
                ear = 0  # Default EAR value
                if results.multi_face_landmarks:
                    landmarks = results.multi_face_landmarks[0].landmark
                    
                    # Eye landmarks for EAR calculation
                    left_eye_top, left_eye_bot = landmarks[159].y, landmarks[145].y
                    right_eye_top, right_eye_bot = landmarks[386].y, landmarks[374].y
                    
                    ear = ((left_eye_bot - left_eye_top) + (right_eye_bot - right_eye_top)) / 2.0
                    
                    if ear < 0.012:  # Eye closed threshold
                        if not self._eye_closed:
                            current_time = time.time()
                            with self._lock:
                                self._blink_count += 1
                                self._blink_timestamps.append(current_time)
                                self._update_blinks_per_minute()
                            self._eye_closed = True
                            print(f"Blink detected! Total: {self._blink_count}, EAR: {ear:.4f}")
                    else:
                        self._eye_closed = False
                else:
                    if frame_count % 30 == 0:
                        print("Warning: No face detected")
                
                # Update heart rate and frame in thread-safe manner
                with self._lock:
                    self._heart_rate = hr
                    if self.show_ui:
                        self._latest_frame = frame.copy()
                
                # Show UI if requested
                if self.show_ui and self._latest_frame is not None:
                    display_frame = self._latest_frame.copy()
                    
                    # Get current metrics for display
                    hr_display, bpm_display = self._heart_rate, self._blinks_per_minute
                    blink_count_display = self._blink_count
                    
                    # --- UI DASHBOARD ---
                    hr_color = (0, 255, 0) if hr_display > 0 else (0, 0, 255)
                    cv2.putText(display_frame, f"Heart Rate: {hr_display:.1f} BPM", (30, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, hr_color, 2)
                    
                    cv2.putText(display_frame, f"Blinks: {blink_count_display}", (30, 100), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                    
                    cv2.putText(display_frame, f"Blinks/min: {bpm_display:.1f}", (30, 150), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                    
                    cv2.imshow('Hackathon Biometrics', display_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self._running = False
                        break
                
                # Small sleep to prevent excessive CPU usage (only if not showing UI)
                if not self.show_ui:
                    time.sleep(0.01)
                
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print(f"Monitor stopped. Total frames processed: {frame_count}")


# Demo/test function to show the monitor with UI
def run_with_ui():
    """Run the biometrics monitor with a visual UI display."""
    monitor = BiometricsMonitor(show_ui=True)
    monitor.start()
    
    print("Biometrics monitor running with UI. Press 'q' in the window to quit.")
    
    try:
        # Keep main thread alive while monitor runs
        while monitor._running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        monitor.stop()


if __name__ == "__main__":
    run_with_ui()