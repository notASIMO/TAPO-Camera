"""
Tapo C230 - Welcome Message on Person Detection (ONVIF Version)
Requires: pip install opencv-python numpy gtts onvif-zeep
"""

import cv2
import time
from gtts import gTTS
import os
import tempfile
import subprocess
import platform
from datetime import datetime

# Camera configuration (same as your working image_capture.py)
HOST = "10.239.197.233"
USER = "Tapocam"
PASSWORD = "Tapo@1234"
RTSP = f"rtsp://{USER}:{PASSWORD}@{HOST}:554/stream1"

# Detection settings
COOLDOWN_SECONDS = 30  # Wait 30 seconds before saying welcome again
last_welcome_time = 0


def play_audio_file(audio_file):
    """Play audio file using native system command"""
    try:
        if platform.system() == 'Darwin':  # macOS
            subprocess.run(['afplay', audio_file], check=True)
        elif platform.system() == 'Linux':
            subprocess.run(['aplay', audio_file], check=True)
        elif platform.system() == 'Windows':
            subprocess.run(['powershell', '-c', 
                          f'(New-Object Media.SoundPlayer "{audio_file}").PlaySync()'], 
                          check=True)
        print("✓ Audio played successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to play audio: {e}")
        return False


def generate_welcome_audio(message="Welcome!", language='en'):
    """Generate welcome audio using text-to-speech"""
    try:
        tts = gTTS(text=message, lang=language, slow=False)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        tts.save(temp_file.name)
        print(f"✓ Generated audio: {message}")
        return temp_file.name
    except Exception as e:
        print(f"✗ Failed to generate audio: {e}")
        return None


def play_welcome_message(audio_file):
    """Play welcome message"""
    if audio_file and os.path.exists(audio_file):
        print("🔊 Playing welcome message...")
        play_audio_file(audio_file)
    else:
        print("✗ No audio file available")


def detect_person_opencv(rtsp_url):
    """Monitor stream and detect persons using OpenCV"""
    global last_welcome_time
    
    print("\n" + "="*50)
    print("🎥 PERSON DETECTION ACTIVE")
    print("="*50)
    print(f"📹 Monitoring: {HOST}")
    print(f"⏱️  Cooldown: {COOLDOWN_SECONDS} seconds")
    print(f"🎤 Welcome message ready")
    print("\nPress 'q' to quit\n")
    
    # Load pre-trained person detector (HOG)
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    # Generate welcome audio file once
    welcome_messages = [
        "Welcome! Have a great day!",
        "Hello! Welcome home!",
        "Welcome! Nice to see you!",
    ]
    
    message_index = 0
    welcome_audio = generate_welcome_audio(welcome_messages[message_index])
    
    if not welcome_audio:
        print("✗ Could not generate welcome audio")
        return
    
    try:
        print(f"Attempting to connect to: {rtsp_url.replace(PASSWORD, '***')}")
        cap = cv2.VideoCapture(rtsp_url)
        
        if not cap.isOpened():
            print("✗ Failed to open RTSP stream")
            print("Make sure camera is online and credentials are correct")
            return
        
        print("✓ Camera stream opened successfully\n")
        
        frame_skip = 0
        detection_count = 0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("✗ Failed to read frame")
                break
            
            # Process every 15th frame to reduce CPU usage
            frame_skip += 1
            if frame_skip % 15 != 0:
                cv2.imshow('Tapo C230 - Person Detection', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue
            
            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (640, 360))
            
            # Detect people
            boxes, weights = hog.detectMultiScale(
                small_frame, 
                winStride=(8, 8),
                padding=(4, 4),
                scale=1.05
            )
            
            # Draw boxes around detected people
            display_frame = frame.copy()
            person_detected = False
            
            for (x, y, w, h) in boxes:
                # Scale coordinates back to original frame size
                scale_x = frame.shape[1] / 640
                scale_y = frame.shape[0] / 360
                
                x_scaled = int(x * scale_x)
                y_scaled = int(y * scale_y)
                w_scaled = int(w * scale_x)
                h_scaled = int(h * scale_y)
                
                cv2.rectangle(display_frame, 
                            (x_scaled, y_scaled), 
                            (x_scaled + w_scaled, y_scaled + h_scaled), 
                            (0, 255, 0), 3)
                cv2.putText(display_frame, 'PERSON DETECTED', 
                          (x_scaled, y_scaled - 10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                person_detected = True
            
            # If person detected and cooldown expired
            if person_detected:
                current_time = time.time()
                if current_time - last_welcome_time > COOLDOWN_SECONDS:
                    detection_count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    print(f"\n{'='*50}")
                    print(f"👤 PERSON DETECTED #{detection_count}")
                    print(f"⏰ Time: {timestamp}")
                    print(f"{'='*50}")
                    
                    # Display welcome text on frame
                    cv2.putText(display_frame, 'WELCOME!', 
                              (50, 100), 
                              cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 5)
                    cv2.imshow('Tapo C230 - Person Detection', display_frame)
                    cv2.waitKey(1)
                    
                    # Play welcome message
                    play_welcome_message(welcome_audio)
                    
                    # Cycle through different welcome messages
                    message_index = (message_index + 1) % len(welcome_messages)
                    if welcome_audio and os.path.exists(welcome_audio):
                        os.remove(welcome_audio)
                    welcome_audio = generate_welcome_audio(welcome_messages[message_index])
                    
                    last_welcome_time = current_time
                    print(f"⏳ Next detection possible in {COOLDOWN_SECONDS} seconds\n")
            
            # Add status info to frame
            status_text = f"Monitoring | Detections: {detection_count}"
            cv2.putText(display_frame, status_text, 
                       (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Display frame
            cv2.imshow('Tapo C230 - Person Detection', display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        print(f"\n{'='*50}")
        print(f"✓ Detection session ended")
        print(f"📊 Total detections: {detection_count}")
        print(f"{'='*50}\n")
        
        # Cleanup
        if welcome_audio and os.path.exists(welcome_audio):
            os.remove(welcome_audio)
            
    except Exception as e:
        print(f"✗ Detection error: {e}")
    finally:
        cv2.destroyAllWindows()


def test_audio():
    """Test audio playback"""
    print("\n=== Testing Audio System ===\n")
    test_audio = generate_welcome_audio("Testing audio. If you can hear this, the system is working.")
    if test_audio:
        play_audio_file(test_audio)
        os.remove(test_audio)
        return True
    return False


def main():
    """Main function"""
    print("\n" + "="*50)
    print("🏠 TAPO C230 WELCOME SYSTEM")
    print("="*50)
    print(f"📹 Camera: {HOST}")
    print(f"👤 User: {USER}")
    print("="*50 + "\n")
    
    print("Choose an option:")
    print("1. Start Person Detection with Welcome Messages")
    print("2. Test Audio System")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        detect_person_opencv(RTSP)
    elif choice == "2":
        if test_audio():
            print("\n✓ Audio test completed successfully!")
        else:
            print("\n✗ Audio test failed")
    elif choice == "3":
        print("\n👋 Goodbye!")
    else:
        print("\n✗ Invalid choice")


if __name__ == "__main__":
    main()