"""
Tapo C230 Continuous QR Scanner
Captures one image every X seconds from RTSP stream (home position only)
Uses multiple QR detection methods for maximum reliability
"""

import cv2
import os
import time
from datetime import datetime
import numpy as np
from pyzbar import pyzbar

# --- Camera Configuration ---
CAMERA_IP = "10.254.8.233"
USERNAME = "Depasa"
PASSWORD = "tapo1234"
CAPTURE_INTERVAL = 5  # seconds between scans

# --- Image Enhancements ---
def enhance_image_for_qr(image):
    """Create multiple enhanced versions of the image to improve detection"""
    enhanced_images = []
    enhanced_images.append(("Original", image))

    # Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    enhanced_images.append(("Grayscale", gray))

    # Adaptive threshold
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
    enhanced_images.append(("Adaptive", adaptive))

    # OTSU
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    enhanced_images.append(("OTSU", otsu))

    # CLAHE contrast enhancement
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    merged = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    enhanced_images.append(("Contrast", enhanced))

    # Sharpen
    kernel = np.array([[-1, -1, -1],
                       [-1, 9, -1],
                       [-1, -1, -1]])
    sharpened = cv2.filter2D(image, -1, kernel)
    enhanced_images.append(("Sharpened", sharpened))

    return enhanced_images


# --- QR Decoding Methods ---
def decode_qr_opencv(image, method_name="OpenCV"):
    """Decode using OpenCV QRCodeDetector"""
    results = []
    try:
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(image)
        if data:
            results.append({"data": data, "method": method_name})
    except:
        pass
    return results


def decode_qr_wechat(image, method_name="WeChat"):
    """Decode using WeChat QR detector (requires opencv-contrib-python)"""
    results = []
    try:
        detector = cv2.wechat_qrcode_WeChatQRCode()
        data, points = detector.detectAndDecode(image)
        if data:
            for d in data:
                if d:
                    results.append({"data": d, "method": method_name})
    except:
        pass
    return results


def decode_qr_pyzbar(image, method_name="pyzbar"):
    """Decode using pyzbar (very reliable)"""
    results = []
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        barcodes = pyzbar.decode(gray)
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            results.append({"data": barcode_data, "method": method_name})
    except:
        pass
    return results

def preprocess_for_qr(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Denoise slightly (helps reduce compression noise)
    gray = cv2.fastNlMeansDenoising(gray, h=10)

    # Increase contrast aggressively
    gray = cv2.convertScaleAbs(gray, alpha=1.7, beta=-40)

    # Sharpen edges
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    sharpened = cv2.filter2D(gray, -1, kernel)

    # Optional: adaptive threshold to isolate dark squares
    thresh = cv2.adaptiveThreshold(
        sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 15, 5
    )
    return thresh


def scan_qr_codes(image_path):
    """Run enhanced QR code scanning on an image"""
    print(f"🔍 Scanning for QR codes in {os.path.basename(image_path)}...")
    image = cv2.imread(image_path)
    if image is None:
        print("✗ Could not read image")
        return []

    all_results = []
    enhanced_versions = enhance_image_for_qr(image)
    enhanced_versions = [("Preprocessed", preprocess_for_qr(image))]


    for label, img in enhanced_versions:
        all_results.extend(decode_qr_opencv(img, f"OpenCV-{label}"))
        all_results.extend(decode_qr_wechat(img, f"WeChat-{label}"))
        all_results.extend(decode_qr_pyzbar(img, f"pyzbar-{label}"))

    # Remove duplicates
    seen = set()
    unique = []
    for res in all_results:
        if res["data"] not in seen:
            seen.add(res["data"])
            unique.append(res)

    if unique:
        print(f"✅ Found {len(unique)} QR code(s):")
        for i, qr in enumerate(unique, 1):
            print(f"   [{i}] {qr['data']}  ({qr['method']})")
    else:
        print("ℹ No QR codes detected")

    return unique


# --- Capture from RTSP ---
def capture_image_rtsp(ip, username, password):
    """Capture single frame from RTSP stream"""
    stream_url = f"rtsp://{username}:{password}@{ip}:554/stream1"
    cap = cv2.VideoCapture(stream_url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("✗ Could not open RTSP stream")
        return None

    # Let it stabilize
    for _ in range(10):
        cap.read()
    time.sleep(1)

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print("✗ Failed to capture frame")
        return None

    os.makedirs("captures", exist_ok=True)
    filename = f"tapo_qr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = os.path.join("captures", filename)
    cv2.imwrite(filepath, frame)
    print(f"📸 Image saved: {filepath}")
    return filepath


# --- Main Loop ---
def main():
    print("=== Tapo C230 Continuous QR Scanner (Home Position) ===\n")

    while True:
        img_path = capture_image_rtsp(CAMERA_IP, USERNAME, PASSWORD)
        if img_path:
            scan_qr_codes(img_path)
        else:
            print("⚠️ Skipping scan due to capture failure.")

        print(f"\n⏳ Waiting {CAPTURE_INTERVAL} seconds before next scan...\n")
        time.sleep(CAPTURE_INTERVAL)


if __name__ == "__main__":
    main()
