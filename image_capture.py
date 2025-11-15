"""
Tapo C230 Camera Control Script
Uses ONVIF protocol for camera control and RTSP for image capture
"""

from onvif import ONVIFCamera
import cv2
import time
from datetime import datetime
import os

# Camera configuration
CAMERA_IP = "10.239.197.233"
ONVIF_PORT = 2020  # Default ONVIF port for Tapo cameras
USERNAME = "Tapocam"  # Default username or your Tapo account username
PASSWORD = "Tapo@1234"  # Camera-specific password from Tapo app

def initialize_camera(ip, port, username, password):
    """Initialize ONVIF connection to Tapo camera"""
    try:
        print("Connecting to camera via ONVIF...")
        camera = ONVIFCamera(ip, port, username, password)
        
        # Create media service
        media_service = camera.create_media_service()
        
        # Create PTZ service
        ptz_service = camera.create_ptz_service()
        
        # Get PTZ configuration
        media_profile = media_service.GetProfiles()[0]
        
        print("✓ Camera connected successfully!")
        return camera, ptz_service, media_profile
        
    except Exception as e:
        print(f"✗ Error connecting via ONVIF: {e}")
        print("\nTrying alternative method without ONVIF...")
        return None, None, None

def move_to_position_onvif(ptz_service, media_profile, pan, tilt):
    """
    Move camera using ONVIF PTZ commands
    Values are normalized between -1 and 1
    """
    try:
        request = ptz_service.create_type('AbsoluteMove')
        request.ProfileToken = media_profile.token
        
        # Normalize pan and tilt to -1 to 1 range
        # Pan: -1 (left) to 1 (right)
        # Tilt: -1 (down) to 1 (up)
        request.Position = {
            'PanTilt': {'x': pan, 'y': tilt},
            'Zoom': {'x': 0}
        }
        
        ptz_service.AbsoluteMove(request)
        print(f"Moving to position - Pan: {pan}, Tilt: {tilt}")
        time.sleep(4)  # Wait for movement to complete
        return True
        
    except Exception as e:
        print(f"Error moving camera: {e}")
        return False

def capture_image_rtsp(ip, username, password, position_name):
    """
    Capture image directly from RTSP stream
    This works independently of HTTP/ONVIF
    """
    try:
        # Tapo C230 RTSP URLs
        stream_urls = [
            f"rtsp://{username}:{password}@{ip}:554/stream1",  # High quality
            f"rtsp://{username}:{password}@{ip}:554/stream2",  # Lower quality (fallback)
        ]
        
        for stream_url in stream_urls:
            print(f"Attempting to connect to: rtsp://{username}:***@{ip}:554/stream")
            
            cap = cv2.VideoCapture(stream_url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            if not cap.isOpened():
                print(f"Failed with this stream, trying next...")
                continue
            
            # Discard first few frames to get fresh image
            for _ in range(10):
                cap.read()
            
            time.sleep(1)
            
            # Capture frame
            ret, frame = cap.read()
            
            if ret and frame is not None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tapo_{position_name}_{timestamp}.jpg"
                
                os.makedirs("captures", exist_ok=True)
                filepath = os.path.join("captures", filename)
                
                cv2.imwrite(filepath, frame)
                print(f"✓ Image saved: {filepath}")
                
                # Display image dimensions
                height, width = frame.shape[:2]
                print(f"  Resolution: {width}x{height}")
                
                cap.release()
                return filepath
            
            cap.release()
        
        print("✗ Failed to capture image from all streams")
        return None
        
    except Exception as e:
        print(f"✗ Error capturing image: {e}")
        return None

def manual_camera_control(ip, username, password):
    """
    Manual control using RTSP only (no PTZ control needed)
    User manually moves camera via Tapo app
    """
    print("\n=== MANUAL MODE ===")
    print("Since ONVIF control is not available, please manually control the camera:")
    print("1. Open Tapo app on your phone")
    print("2. Move camera to MAXIMUM TOP position")
    input("3. Press ENTER when ready to capture TOP image...")
    
    capture_image_rtsp(ip, username, password, "top")
    
    print("\n4. Move camera to MAXIMUM BOTTOM position")
    input("5. Press ENTER when ready to capture BOTTOM image...")
    
    capture_image_rtsp(ip, username, password, "bottom")

def main():
    """Main function to control camera and capture images"""
    
    print("=== Tapo C230 Camera Control ===\n")
    
    # Try ONVIF control first
    camera, ptz_service, media_profile = initialize_camera(
        CAMERA_IP, ONVIF_PORT, USERNAME, PASSWORD
    )
    
    if ptz_service and media_profile:
        # ONVIF control available
        print("\n=== Moving to TOP position (Maximum Up) ===")
        if move_to_position_onvif(ptz_service, media_profile, pan=0, tilt=1):
            capture_image_rtsp(CAMERA_IP, USERNAME, PASSWORD, "top")
        
        print("\n=== Moving to BOTTOM position (Maximum Down) ===")
        if move_to_position_onvif(ptz_service, media_profile, pan=0, tilt=-1):
            capture_image_rtsp(CAMERA_IP, USERNAME, PASSWORD, "bottom")
        
        print("\n=== Returning to HOME position ===")
        move_to_position_onvif(ptz_service, media_profile, pan=0, tilt=0)
    
    else:
        # Fallback to manual control
        print("\n⚠ Automatic PTZ control not available")
        print("Switching to manual mode with RTSP capture...\n")
        manual_camera_control(CAMERA_IP, USERNAME, PASSWORD)
    
    print("\n✓ Operation completed!")
    print(f"Check images in: ./captures/")

if __name__ == "__main__":
    main()