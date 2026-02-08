import cv2
import mediapipe as mp
import numpy as np
import warnings
import os
import threading
import time
from collections import deque

# Suppress warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


class SimpleRPPG:
    """Simple rPPG implementation using green channel FFT"""
    def __init__(self, buffer_size=150, fps=30):
        self.buffer_size = buffer_size
        self.fps = fps
        self.green_values = deque(maxlen=buffer_size)
        self.timestamps = deque(maxlen=buffer_size)
        
    def process_frame(self, frame, face_roi=None):
        """Extract green channel average from face region"""
        try:
            if face_roi is not None:
                x, y, w, h = face_roi
                face_region = frame[y:y+h, x:x+w]
            else:
                h, w = frame.shape[:2]
                face_region = frame[h//4:3*h//4, w//4:3*w//4]
            
            green_channel = face_region[:, :, 1]
            green_avg = np.mean(green_channel)
            
            self.green_values.append(green_avg)
            self.timestamps.append(time.time())
            
            if len(self.green_values) >= self.buffer_size:
                return self.calculate_heart_rate()
            
            return 0
            
        except Exception as e:
            return 0
    
    def calculate_heart_rate(self):
        """Calculate heart rate from green channel signal using FFT"""
        try:
            if len(self.green_values) < 60:
                return 0
                
            signal = np.array(list(self.green_values))
            signal = signal - np.mean(signal)
            
            fft = np.fft.fft(signal)
            freqs = np.fft.fftfreq(len(signal), 1/self.fps)
            
            valid_idx = np.where((freqs >= 0.8) & (freqs <= 3.0))[0]
            
            if len(valid_idx) == 0:
                return 0
            
            fft_abs = np.abs(fft[valid_idx])
            peak_idx = valid_idx[np.argmax(fft_abs)]
            peak_freq = abs(freqs[peak_idx])
            
            hr = peak_freq * 60
            
            if 45 <= hr <= 180:
                return hr
            return 0
            
        except Exception as e:
            return 0


class BiometricsMonitor:
    """Thread-safe biometrics monitor using webcam and MediaPipe"""
    
    def __init__(self, camera_index=0, fps=30, blink_window_seconds=60, show_ui=False):
        self.camera_index = camera_index
        self.fps = fps
        self.blink_window_seconds = blink_window_seconds
        self.show_ui = show_ui
        
        self._lock = threading.Lock()
        self._heart_rate = 0.0
        self._blinks_per_minute = 0.0
        self._blink_count = 0
        self._latest_frame = None
        
        self._blink_timestamps = deque()
        
        self._running = False
        self._thread = None
        self._eye_closed = False
        
        # Initialize custom rPPG
        self.rppg = SimpleRPPG(buffer_size=150, fps=fps)
        
        # Initialize MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(min_detection_confidence=0.5)
        
    def start(self):
        """Start monitoring thread"""
        if self._running:
            print("BiometricsMonitor already running")
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print("BiometricsMonitor started")
        
    def stop(self):
        """Stop monitoring thread"""
        if not self._running:
            return
            
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        print("BiometricsMonitor stopped")
        
    def get_metrics(self):
        """Get current biometric metrics (thread-safe)"""
        with self._lock:
            return self._heart_rate, self._blinks_per_minute
    
    def get_blink_count(self):
        """Get total blink count"""
        with self._lock:
            return self._blink_count
            
    def _update_blinks_per_minute(self):
        """Calculate blinks per minute"""
        current_time = time.time()
        cutoff_time = current_time - self.blink_window_seconds
        
        while self._blink_timestamps and self._blink_timestamps[0] < cutoff_time:
            self._blink_timestamps.popleft()
        
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
        """Main monitoring loop"""
        cap = cv2.VideoCapture(self.camera_index)
        
        if not cap.isOpened():
            print("❌ ERROR: Could not open camera!")
            self._running = False
            return
        
        print("✅ Camera opened successfully. Starting biometrics monitoring...")
        frame_count = 0
        
        try:
            while self._running:
                success, frame = cap.read()
                if not success:
                    continue
                
                frame_count += 1
                
                # Get face ROI
                face_roi = None
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_results = self.face_detection.process(rgb_frame)
                
                if face_results.detections:
                    detection = face_results.detections[0]
                    bbox = detection.location_data.relative_bounding_box
                    h, w = frame.shape[:2]
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    face_roi = (max(0, x), max(0, y), width, height)
                
                # Heart rate processing
                hr = self.rppg.process_frame(frame, face_roi)
                
                if hr > 0:
                    with self._lock:
                        self._heart_rate = round(hr, 1)
                
                # Blink detection
                mesh_results = self.face_mesh.process(rgb_frame)
                
                if mesh_results.multi_face_landmarks:
                    landmarks = mesh_results.multi_face_landmarks[0].landmark
                    
                    left_eye_top = landmarks[159].y
                    left_eye_bot = landmarks[145].y
                    right_eye_top = landmarks[386].y
                    right_eye_bot = landmarks[374].y
                    
                    ear = ((left_eye_bot - left_eye_top) + (right_eye_bot - right_eye_top)) / 2.0
                    
                    if ear < 0.012:
                        if not self._eye_closed:
                            current_time = time.time()
                            with self._lock:
                                self._blink_count += 1
                                self._blink_timestamps.append(current_time)
                                self._update_blinks_per_minute()
                            self._eye_closed = True
                    else:
                        self._eye_closed = False
                
                # Debug output every 30 frames
                if frame_count % 30 == 0:
                    hr_display, bpm_display = self.get_metrics()
                    print(f"📊 Frame {frame_count}: HR={hr_display:.1f} BPM, Blinks/min={bpm_display:.1f}, Total blinks={self._blink_count}")
                
                if self.show_ui and self._latest_frame is not None:
                    display_frame = frame.copy()
                    hr_display, bpm_display = self.get_metrics()
                    
                    hr_color = (0, 255, 0) if hr_display > 0 else (0, 0, 255)
                    cv2.putText(display_frame, f"Heart Rate: {hr_display:.1f} BPM", (30, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, hr_color, 2)
                    cv2.putText(display_frame, f"Blinks: {self._blink_count}", (30, 100), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                    cv2.putText(display_frame, f"Blinks/min: {bpm_display:.1f}", (30, 150), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                    
                    cv2.imshow('Biometrics', display_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self._running = False
                        break
                
                time.sleep(0.01)
                
        except Exception as e:
            print(f"❌ Monitor loop error: {e}")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print(f"✅ Monitor stopped. Total frames: {frame_count}")


# Test function
def run_with_ui():
    """Run with visual UI"""
    monitor = BiometricsMonitor(show_ui=True)
    monitor.start()
    
    print("Biometrics monitor running. Press 'q' in window to quit.")
    
    try:
        while monitor._running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        monitor.stop()


if __name__ == "__main__":
    run_with_ui()