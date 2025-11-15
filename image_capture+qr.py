"""
Tapo C230 Camera Control Script
Captures 2 images: Max up + left, then Max up + right
Enhanced QR code detection with multiple methods
"""

from onvif import ONVIFCamera
import cv2
import time
from datetime import datetime
import os
import numpy as np

# Camera configuration
CAMERA_IP = "10.239.197.233"
ONVIF_PORT = 2020
USERNAME = "Tapocam"
PASSWORD = "Tapo@1234"  # Replace with actual password

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
        return None, None, None

def move_to_position_onvif(ptz_service, media_profile, pan, tilt):
    """
    Move camera using ONVIF PTZ commands
    Pan: -1 (left) to 1 (right)
    Tilt: -1 (down) to 1 (up)
    """
    try:
        request = ptz_service.create_type('AbsoluteMove')
        request.ProfileToken = media_profile.token
        
        request.Position = {
            'PanTilt': {'x': pan, 'y': tilt},
            'Zoom': {'x': 0}
        }
        
        ptz_service.AbsoluteMove(request)
        print(f"Moving to position - Pan: {pan}, Tilt: {tilt}")
        time.sleep(5)  # Longer wait for precise positioning
        return True
        
    except Exception as e:
        print(f"Error moving camera: {e}")
        return False

def enhance_image_for_qr(image):
    """
    Apply multiple preprocessing techniques to improve QR detection
    """
    enhanced_images = []
    
    # 1. Original image
    enhanced_images.append(("Original", image))
    
    # 2. Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    enhanced_images.append(("Grayscale", gray))
    
    # 3. Adaptive thresholding
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
    enhanced_images.append(("Adaptive", adaptive))
    
    # 4. OTSU thresholding
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    enhanced_images.append(("OTSU", otsu))
    
    # 5. Increase contrast
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    enhanced_images.append(("Contrast", enhanced))
    
    # 6. Sharpened
    kernel = np.array([[-1,-1,-1],
                       [-1, 9,-1],
                       [-1,-1,-1]])
    sharpened = cv2.filter2D(image, -1, kernel)
    enhanced_images.append(("Sharpened", sharpened))
    
    return enhanced_images

def decode_qr_opencv(image, method_name=""):
    """
    Decode QR codes using OpenCV's QRCodeDetector
    """
    qr_codes = []
    
    try:
        # Initialize QR code detector
        qr_detector = cv2.QRCodeDetector()
        
        # Detect and decode
        data, bbox, _ = qr_detector.detectAndDecode(image)
        
        if data:
            qr_codes.append({
                'data': data,
                'bbox': bbox,
                'method': method_name
            })
    except Exception as e:
        pass
    
    return qr_codes

def decode_qr_wechat(image, method_name=""):
    """
    Decode QR codes using OpenCV's WeChat QR detector (more robust)
    """
    qr_codes = []
    
    try:
        # Initialize WeChat QR code detector
        detector = cv2.wechat_qrcode_WeChatQRCode()
        
        # Detect and decode
        data, points = detector.detectAndDecode(image)
        
        if data and len(data) > 0:
            for i, qr_data in enumerate(data):
                if qr_data:
                    qr_codes.append({
                        'data': qr_data,
                        'points': points[i] if i < len(points) else None,
                        'method': method_name
                    })
    except Exception as e:
        pass
    
    return qr_codes

def scan_qr_codes(image_path):
    """
    Comprehensive QR code scanning with multiple methods
    """
    try:
        print(f"  🔍 Scanning for QR codes with enhanced detection...")
        
        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            print(f"  ✗ Could not read image")
            return []
        
        all_qr_codes = []
        
        # Get enhanced versions of the image
        enhanced_images = enhance_image_for_qr(image)
        
        # Try both detection methods on each enhanced image
        for method_name, enhanced_img in enhanced_images:
            # OpenCV standard detector
            qr_codes = decode_qr_opencv(enhanced_img, f"OpenCV-{method_name}")
            all_qr_codes.extend(qr_codes)
            
            # WeChat detector (more robust)
            qr_codes = decode_qr_wechat(enhanced_img, f"WeChat-{method_name}")
            all_qr_codes.extend(qr_codes)
        
        # Remove duplicates based on data
        unique_qr_codes = []
        seen_data = set()
        
        for qr in all_qr_codes:
            if qr['data'] not in seen_data:
                seen_data.add(qr['data'])
                unique_qr_codes.append(qr)
        
        # Display results
        if unique_qr_codes:
            print(f"  📱 Found {len(unique_qr_codes)} unique QR code(s):")
            
            for i, qr in enumerate(unique_qr_codes, 1):
                print(f"     [{i}] Data: {qr['data']}")
                print(f"         Method: {qr['method']}")
                
                # Draw on original image
                if 'bbox' in qr and qr['bbox'] is not None:
                    bbox = qr['bbox'].astype(int)
                    cv2.polylines(image, [bbox], True, (0, 255, 0), 3)
                    x, y = bbox[0][0], bbox[0][1]
                    cv2.putText(image, f"QR {i}", (x, y - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                elif 'points' in qr and qr['points'] is not None:
                    points = qr['points'].astype(int).reshape((-1, 1, 2))
                    cv2.polylines(image, [points], True, (0, 255, 0), 3)
            
            # Save annotated image
            annotated_path = image_path.replace('.jpg', '_qr_detected.jpg')
            cv2.imwrite(annotated_path, image)
            print(f"  ✓ Annotated image saved: {annotated_path}")
            
            return unique_qr_codes
        else:
            print(f"  ℹ No QR codes detected")
            return []
            
    except Exception as e:
        print(f"  ✗ Error scanning QR codes: {e}")
        return []

def capture_image_rtsp(ip, username, password, position_name):
    """
    Capture image from RTSP stream
    """
    try:
        stream_url = f"rtsp://{username}:{password}@{ip}:554/stream1"
        
        print(f"Connecting to RTSP stream...")
        
        cap = cv2.VideoCapture(stream_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if not cap.isOpened():
            print(f"✗ Failed to connect to stream")
            return None
        
        # Discard initial frames and wait for stable image
        for _ in range(15):
            cap.read()
        
        time.sleep(2)
        
        # Capture frame
        ret, frame = cap.read()
        
        if ret and frame is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tapo_{position_name}_{timestamp}.jpg"
            
            os.makedirs("captures", exist_ok=True)
            filepath = os.path.join("captures", filename)
            
            cv2.imwrite(filepath, frame)
            print(f"✓ Image saved: {filepath}")
            
            height, width = frame.shape[:2]
            print(f"  Resolution: {width}x{height}")
            
            cap.release()
            
            # Scan for QR codes
            scan_qr_codes(filepath)
            
            return filepath
        
        cap.release()
        print("✗ Failed to capture frame")
        return None
        
    except Exception as e:
        print(f"✗ Error capturing image: {e}")
        return None

def main():
    """Main function"""
    
    print("=== Tapo C230 Camera - 2 Image Capture with QR Detection ===\n")
    
    # Initialize camera
    camera, ptz_service, media_profile = initialize_camera(
        CAMERA_IP, ONVIF_PORT, USERNAME, PASSWORD
    )
    
    if not ptz_service or not media_profile:
        print("\n✗ Cannot control camera automatically")
        return
    
    # Position 1: Top (Max up) + Left
    print("\n=== Position 1: Top Left (Maximum Up + Slight Left) ===")
    if move_to_position_onvif(ptz_service, media_profile, pan=0.2, tilt=1):
        capture_image_rtsp(CAMERA_IP, USERNAME, PASSWORD, "top_left")
    
    # Return to home center
    print("\n=== Returning to Home/Center Position ===")
    move_to_position_onvif(ptz_service, media_profile, pan=0, tilt=0)
    
    # Position 2: Center + Right
    print("\n=== Position 2: Center Right (Home Position + Slight Right) ===")
    if move_to_position_onvif(ptz_service, media_profile, pan=-0.2, tilt=0):
        capture_image_rtsp(CAMERA_IP, USERNAME, PASSWORD, "center_right")
    
    # Return to home
    print("\n=== Returning to Home Position ===")
    move_to_position_onvif(ptz_service, media_profile, pan=0, tilt=0)
    
    print("\n✓ Operation completed!")
    print(f"Images saved in: ./captures/")

if __name__ == "__main__":
    main()