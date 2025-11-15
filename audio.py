"""
Tapo C230 Camera Audio Features Script
Requires: pip install pytapo opencv-python numpy
"""

from pytapo import Tapo
import cv2
import time
import numpy as np

# Camera configuration
HOST = "10.239.197.233"
USER = "b24me1066"
PASSWORD = "Tapo@1234"
RTSP = f"rtsp://{USER}:{PASSWORD}@{HOST}:554/stream1"


def connect_camera(host, username, password):
    """Connect to the Tapo camera"""
    try:
        camera = Tapo(host, username, password)
        print(f"✓ Connected to camera at {host}")
        return camera
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return None


def play_audio_alert(camera):
    """Play the camera's built-in alarm sound"""
    try:
        camera.setAlarm(True, "sound")
        print("✓ Audio alert activated")
        time.sleep(3)  # Play for 3 seconds
        camera.setAlarm(False, "sound")
        print("✓ Audio alert stopped")
    except Exception as e:
        print(f"✗ Failed to play audio alert: {e}")


def get_audio_status(camera):
    """Get current audio configuration"""
    try:
        audio_config = camera.getAudioConfig()
        print("\n--- Audio Status ---")
        print(f"Audio Enabled: {audio_config.get('enabled', 'Unknown')}")
        print(f"Audio Type: {audio_config.get('type', 'Unknown')}")
        print(f"Volume: {audio_config.get('volume', 'Unknown')}")
        return audio_config
    except Exception as e:
        print(f"✗ Failed to get audio status: {e}")
        return None


def set_audio_volume(camera, volume):
    """Set speaker volume (0-100)"""
    try:
        if 0 <= volume <= 100:
            camera.setAudioConfig(volume=volume)
            print(f"✓ Volume set to {volume}%")
        else:
            print("✗ Volume must be between 0 and 100")
    except Exception as e:
        print(f"✗ Failed to set volume: {e}")


def enable_sound_detection(camera):
    """Enable sound detection alerts"""
    try:
        # Enable sound detection in motion detection settings
        camera.setMotionDetection(enabled=True)
        print("✓ Motion/Sound detection enabled")
    except Exception as e:
        print(f"✗ Failed to enable sound detection: {e}")


def stream_audio_video(rtsp_url, duration=10):
    """Stream video and audio from RTSP"""
    print(f"\n--- Starting RTSP Stream ---")
    print(f"Streaming from: {rtsp_url}")
    print(f"Duration: {duration} seconds")
    print("Press 'q' to quit early\n")
    
    try:
        # Open RTSP stream
        cap = cv2.VideoCapture(rtsp_url)
        
        if not cap.isOpened():
            print("✗ Failed to open RTSP stream")
            return
        
        print("✓ RTSP stream opened successfully")
        
        start_time = time.time()
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                print("✗ Failed to read frame")
                break
            
            frame_count += 1
            
            # Display frame
            cv2.imshow('Tapo C230 Live Stream', frame)
            
            # Check if duration exceeded
            if time.time() - start_time > duration:
                print(f"\n✓ Streamed {frame_count} frames in {duration} seconds")
                break
            
            # Press 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n✓ Stream stopped by user")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"✗ Streaming error: {e}")


def get_camera_info(camera):
    """Get basic camera information"""
    try:
        print("\n--- Camera Information ---")
        device_info = camera.getDeviceInfo()
        print(f"Model: {device_info.get('device_model', 'Unknown')}")
        print(f"Hardware Version: {device_info.get('hw_version', 'Unknown')}")
        print(f"Software Version: {device_info.get('sw_version', 'Unknown')}")
    except Exception as e:
        print(f"✗ Failed to get camera info: {e}")


def main():
    """Main function demonstrating audio features"""
    print("=== Tapo C230 Audio Control ===\n")
    
    # Connect to camera
    camera = connect_camera(HOST, USER, PASSWORD)
    
    if not camera:
        print("\nTrying RTSP stream only...")
        stream_audio_video(RTSP, duration=15)
        return
    
    # Get camera information
    get_camera_info(camera)
    
    # Get current audio status
    get_audio_status(camera)
    
    # Demo: Set volume
    print("\n--- Setting Volume ---")
    set_audio_volume(camera, 80)
    
    # Demo: Play audio alert
    print("\n--- Playing Audio Alert ---")
    play_audio_alert(camera)
    
    # Demo: Enable sound detection
    print("\n--- Enabling Detection ---")
    enable_sound_detection(camera)
    
    # Demo: Stream video (includes audio in stream)
    print("\n--- Starting Live Stream ---")
    stream_audio_video(RTSP, duration=15)
    
    print("\n✓ Audio features demo completed!")


if __name__ == "__main__":
    main()