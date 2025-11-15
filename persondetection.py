import cv2
import os
from datetime import datetime

# ---------- CAMERA CONFIG ----------
TAPO_USER = "Tapocam"
TAPO_PASS = "Tapo@1234"
TAPO_IP = "10.239.197.233"  # Update with your camera IP
RTSP_URL = f"rtsp://{TAPO_USER}:{TAPO_PASS}@{TAPO_IP}:554/stream1"

# ---------- SAVE PATH ----------
SAVE_PATH = "./videos"
os.makedirs(SAVE_PATH, exist_ok=True)

# Create a unique filename with timestamp
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = os.path.join(SAVE_PATH, f"tapo_{timestamp}.mp4")

# ---------- HUMAN DETECTION SETUP ----------
# Using HOG (Histogram of Oriented Gradients) for pedestrian detection
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

# ---------- OPEN CAMERA STREAM ----------
print("🔄 Connecting to Tapo camera...")
cap = cv2.VideoCapture(RTSP_URL)

# Reduce buffer size for lower latency
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("❌ Could not open video stream")
    print("💡 Check:")
    print("   - Camera IP is correct")
    print("   - Username/password are correct")
    print("   - Camera is powered on and connected to network")
    exit()

print("✅ Stream connected! Press 'q' to quit.")

# ---------- SETUP VIDEO WRITER ----------
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS)) or 20

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(filename, fourcc, fps, (frame_width, frame_height))

print(f"📹 Recording to: {filename}")
print(f"🎬 Resolution: {frame_width}x{frame_height} @ {fps} FPS")

# ---------- MAIN LOOP ----------
frame_count = 0
person_detected_count = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Stream ended or connection lost.")
            break

        frame_count += 1

        # Detect humans every few frames (for performance)
        if frame_count % 3 == 0:  # Process every 3rd frame
            # Resize frame for faster detection
            detection_frame = cv2.resize(frame, (640, 480))
            
            # Detect people
            boxes, weights = hog.detectMultiScale(
                detection_frame, 
                winStride=(8, 8),
                padding=(4, 4),
                scale=1.05
            )
            
            # Scale boxes back to original frame size
            scale_x = frame_width / 640
            scale_y = frame_height / 480
            
            # Draw bounding boxes around detected people
            for (x, y, w, h) in boxes:
                # Scale coordinates
                x = int(x * scale_x)
                y = int(y * scale_y)
                w = int(w * scale_x)
                h = int(h * scale_y)
                
                # Draw rectangle
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, "Person", (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            if len(boxes) > 0:
                person_detected_count += 1
                # Display welcome message
                cv2.putText(frame, f"👋 {len(boxes)} Person(s) Detected!", 
                           (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                           1, (0, 255, 0), 3)

        # Add timestamp to frame
        time_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, time_text, (10, frame_height - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Write frame to video
        out.write(frame)

        # Display the stream
        cv2.imshow("Tapo CCTV - Human Detection", frame)

        # Quit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n⏹️  Stopping recording...")
            break

except KeyboardInterrupt:
    print("\n⏹️  Recording interrupted by user...")

finally:
    # ---------- CLEANUP ----------
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    print(f"\n📊 Recording Statistics:")
    print(f"   Total frames: {frame_count}")
    print(f"   Detections: {person_detected_count}")
    print(f"🎥 Video saved to: {filename}")