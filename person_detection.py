"""
Tapo C230 - AI-Powered Person Detection with Alerts
Uses YOLO deep learning model for accurate person detection
Requires: pip install opencv-python numpy ultralytics
"""

import cv2
import numpy as np
from ultralytics import YOLO
import time
from datetime import datetime
import os
from gtts import gTTS
import subprocess
import platform

# Camera configuration
HOST = "10.239.197.233"
USER = "Tapocam"
PASSWORD = "Tapo@1234"
RTSP = f"rtsp://{USER}:{PASSWORD}@{HOST}:554/stream1"

# Detection settings
CONFIDENCE_THRESHOLD = 0.5  # Detection confidence (0.0 to 1.0)
COOLDOWN_SECONDS = 10  # Time between alerts
SAVE_DETECTIONS = True  # Save images with detected persons
DETECTION_DIR = "person_detections"

# Alert settings
ENABLE_AUDIO_ALERT = True
ENABLE_VISUAL_ALERT = True
ENABLE_LOG_FILE = True

# Global variables
last_alert_time = 0
detection_count = 0
log_file = None


def setup_directories():
    """Create necessary directories"""
    if SAVE_DETECTIONS and not os.path.exists(DETECTION_DIR):
        os.makedirs(DETECTION_DIR)
        print(f"✓ Created directory: {DETECTION_DIR}")


def initialize_log():
    """Initialize log file"""
    global log_file
    if ENABLE_LOG_FILE:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"detection_log_{timestamp}.txt"
        log_file = open(log_filename, 'w')
        log_file.write("="*60 + "\n")
        log_file.write("TAPO C230 PERSON DETECTION LOG\n")
        log_file.write("="*60 + "\n")
        log_file.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"Camera: {HOST}\n")
        log_file.write(f"Confidence Threshold: {CONFIDENCE_THRESHOLD}\n")
        log_file.write("="*60 + "\n\n")
        print(f"✓ Log file created: {log_filename}")


def log_detection(person_count, confidence, filename=None):
    """Log detection event"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{timestamp}] DETECTED: {person_count} person(s) | Confidence: {confidence:.2f}"
    if filename:
        message += f" | Saved: {filename}"
    
    print(f"\n🚨 {message}")
    
    if log_file:
        log_file.write(message + "\n")
        log_file.flush()


def play_audio_alert(message="Person detected!"):
    """Play audio alert"""
    try:
        # Generate TTS
        tts = gTTS(text=message, lang='en', slow=False)
        temp_file = "/tmp/alert.mp3"
        tts.save(temp_file)
        
        # Play audio
        if platform.system() == 'Darwin':  # macOS
            subprocess.run(['afplay', temp_file], check=True)
        elif platform.system() == 'Linux':
            subprocess.run(['aplay', temp_file], check=True)
        
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
    except Exception as e:
        print(f"  ⚠️ Audio alert failed: {e}")


def send_alert(person_count, confidence, frame):
    """Send alert when person is detected"""
    global last_alert_time, detection_count
    
    current_time = time.time()
    
    # Check cooldown
    if current_time - last_alert_time < COOLDOWN_SECONDS:
        return
    
    detection_count += 1
    last_alert_time = current_time
    
    # Save detection image
    filename = None
    if SAVE_DETECTIONS:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"detection_{detection_count:04d}_{timestamp}.jpg"
        filepath = os.path.join(DETECTION_DIR, filename)
        cv2.imwrite(filepath, frame)
        filename = filepath
    
    # Log detection
    log_detection(person_count, confidence, filename)
    
    # Audio alert
    if ENABLE_AUDIO_ALERT:
        if person_count == 1:
            message = "Alert! One person detected."
        else:
            message = f"Alert! {person_count} people detected."
        play_audio_alert(message)
    
    # Visual alert (already shown in video window)
    print(f"⏳ Next alert in {COOLDOWN_SECONDS} seconds")


def detect_persons_yolo(rtsp_url):
    """Detect persons using YOLO AI model"""
    global detection_count
    
    print("\n" + "="*60)
    print("🤖 AI-POWERED PERSON DETECTION ACTIVE")
    print("="*60)
    print(f"📹 Camera: {HOST}")
    print(f"🎯 Confidence Threshold: {CONFIDENCE_THRESHOLD}")
    print(f"⏱️  Alert Cooldown: {COOLDOWN_SECONDS}s")
    print(f"💾 Save Detections: {SAVE_DETECTIONS}")
    print(f"🔊 Audio Alerts: {ENABLE_AUDIO_ALERT}")
    print("\nPress 'q' to quit | 's' to save snapshot\n")
    
    # Load YOLO model
    print("Loading YOLO AI model...")
    try:
        model = YOLO('yolov8n.pt')  # Nano model for speed
        # model = YOLO('yolov8s.pt')  # Small model for better accuracy
        print("✓ YOLO model loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load YOLO model: {e}")
        print("  Downloading model (first time only)...")
        try:
            model = YOLO('yolov8n.pt')
            print("✓ Model downloaded and loaded")
        except:
            print("✗ Failed to download model")
            return
    
    # Open video stream
    print(f"\nConnecting to camera stream...")
    cap = cv2.VideoCapture(rtsp_url)
    
    if not cap.isOpened():
        print("✗ Failed to open RTSP stream")
        return
    
    print("✓ Camera stream connected\n")
    print("="*60)
    print("🎥 MONITORING STARTED")
    print("="*60 + "\n")
    
    frame_count = 0
    fps_start_time = time.time()
    fps = 0
    
    try:
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("✗ Failed to read frame")
                break
            
            frame_count += 1
            
            # Calculate FPS
            if frame_count % 30 == 0:
                fps = 30 / (time.time() - fps_start_time)
                fps_start_time = time.time()
            
            # Run YOLO detection
            results = model(frame, conf=CONFIDENCE_THRESHOLD, classes=[0])  # class 0 = person
            
            # Process detections
            person_count = 0
            max_confidence = 0
            
            for result in results:
                boxes = result.boxes
                
                for box in boxes:
                    # Get box coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    confidence = float(box.conf[0])
                    
                    person_count += 1
                    max_confidence = max(max_confidence, confidence)
                    
                    # Draw bounding box
                    color = (0, 255, 0) if confidence > 0.7 else (0, 255, 255)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                    
                    # Draw label
                    label = f"Person {confidence:.2f}"
                    label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                                (x1 + label_size[0], y1), color, -1)
                    cv2.putText(frame, label, (x1, y1 - 5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
            # Send alert if person detected
            if person_count > 0:
                send_alert(person_count, max_confidence, frame)
                
                # Draw alert text
                alert_text = f"PERSON DETECTED! Count: {person_count}"
                cv2.putText(frame, alert_text, (50, 80),
                          cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            
            # Draw status info
            status_text = f"FPS: {fps:.1f} | Detections: {detection_count} | Monitoring..."
            cv2.putText(frame, status_text, (10, 30),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Display frame
            cv2.imshow('AI Person Detection - Tapo C230', frame)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n✓ Monitoring stopped by user")
                break
            elif key == ord('s'):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                snapshot_file = f"snapshot_{timestamp}.jpg"
                cv2.imwrite(snapshot_file, frame)
                print(f"\n📸 Snapshot saved: {snapshot_file}")
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Final statistics
        print("\n" + "="*60)
        print("📊 DETECTION STATISTICS")
        print("="*60)
        print(f"Total Detections: {detection_count}")
        print(f"Frames Processed: {frame_count}")
        if SAVE_DETECTIONS:
            print(f"Images Saved: {DETECTION_DIR}/")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n✓ Monitoring stopped (Ctrl+C)")
    except Exception as e:
        print(f"\n✗ Error during detection: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        if log_file:
            log_file.write(f"\nStopped: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"Total Detections: {detection_count}\n")
            log_file.close()


def test_camera_connection():
    """Test camera connection"""
    print("\n🔍 Testing camera connection...")
    cap = cv2.VideoCapture(RTSP)
    
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"✓ Camera connected successfully")
            print(f"  Resolution: {frame.shape[1]}x{frame.shape[0]}")
            cap.release()
            return True
    
    print("✗ Failed to connect to camera")
    cap.release()
    return False


def main():
    """Main function"""
    print("\n" + "="*60)
    print("🤖 TAPO C230 AI PERSON DETECTION SYSTEM")
    print("="*60)
    print(f"📹 Camera: {HOST}")
    print(f"🧠 AI Model: YOLOv8")
    print("="*60 + "\n")
    
    # Setup
    setup_directories()
    initialize_log()
    
    # Test connection
    if not test_camera_connection():
        return
    
    print("\nOptions:")
    print("1. Start AI Person Detection")
    print("2. Configure Settings")
    print("3. Test Alert System")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        detect_persons_yolo(RTSP)
    
    elif choice == "2":
        print("\n⚙️  Current Settings:")
        print(f"  Confidence Threshold: {CONFIDENCE_THRESHOLD}")
        print(f"  Alert Cooldown: {COOLDOWN_SECONDS}s")
        print(f"  Save Detections: {SAVE_DETECTIONS}")
        print(f"  Audio Alerts: {ENABLE_AUDIO_ALERT}")
        print("\n💡 Edit the script to change these values")
    
    elif choice == "3":
        print("\n🔊 Testing alert system...")
        play_audio_alert("Alert system test. Person detection active.")
        print("✓ Test complete")
    
    elif choice == "4":
        print("\n👋 Goodbye!")
    
    else:
        print("\n✗ Invalid choice")


if __name__ == "__main__":
    main()