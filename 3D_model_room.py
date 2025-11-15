"""
Tapo C230 - 3D Room Scanner (Python 3.13 Compatible)
Creates a 3D point cloud of your room using Structure from Motion (SfM)
Requires: pip install opencv-python numpy matplotlib plotly onvif-zeep
"""

import cv2
import numpy as np
from onvif import ONVIFCamera
import time
import os
from datetime import datetime
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import plotly.graph_objects as go
import json

# Camera configuration
HOST = "10.239.197.233"
PORT = 2020
USER = "Tapocam"
PASSWORD = "Tapo@1234"
RTSP = f"rtsp://{USER}:{PASSWORD}@{HOST}:554/stream1"

# Scanning settings - OPTIMIZED FOR SPEED
NUM_POSITIONS = 6   # Number of camera positions (reduced from 12)
TILT_POSITIONS = 2  # Number of tilt angles (reduced from 3)
CAPTURE_DELAY = 1.5 # Seconds after moving (reduced from 2.5)
CAPTURE_DIR = "3d_scan_captures"
OUTPUT_DIR = "3d_models"
POINT_CLOUD_FILE = "room_pointcloud.npz"
POINT_CLOUD_HTML = "room_3d_model.html"

# Processing settings - SPEED OPTIMIZATIONS
MAX_FEATURES = 500  # Limit features per image (faster processing)
DOWNSAMPLE_FACTOR = 2  # Process smaller images (2x faster)


class Room3DScanner:
    def __init__(self, host, port, user, password, rtsp_url):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.rtsp_url = rtsp_url
        self.camera = None
        self.ptz = None
        self.images = []
        self.camera_poses = []
        
        # Create directories
        for directory in [CAPTURE_DIR, OUTPUT_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"✓ Created directory: {directory}")
    
    def connect(self):
        """Connect to camera via ONVIF"""
        try:
            print(f"Connecting to camera at {self.host}...")
            self.camera = ONVIFCamera(self.host, self.port, self.user, self.password)
            
            media_service = self.camera.create_media_service()
            profiles = media_service.GetProfiles()
            self.media_profile = profiles[0]
            
            self.ptz = self.camera.create_ptz_service()
            print("✓ Camera connected successfully!")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def move_camera(self, pan, tilt):
        """Move camera to specific position"""
        try:
            request = self.ptz.create_type('AbsoluteMove')
            request.ProfileToken = self.media_profile.token
            request.Position = {
                'PanTilt': {'x': pan, 'y': tilt},
                'Zoom': {'x': 0}
            }
            self.ptz.AbsoluteMove(request)
            return True
        except Exception as e:
            print(f"✗ Move failed: {e}")
            return False
    
    def capture_image(self, filename):
        """Capture image from RTSP stream"""
        try:
            cap = cv2.VideoCapture(self.rtsp_url)
            if not cap.isOpened():
                return None
            
            # Skip first few frames
            for _ in range(5):
                ret, frame = cap.read()
            
            if ret and frame is not None:
                filepath = os.path.join(CAPTURE_DIR, filename)
                cv2.imwrite(filepath, frame)
                cap.release()
                return frame
            
            cap.release()
            return None
        except Exception as e:
            print(f"✗ Capture error: {e}")
            return None
    
    def capture_scan_sequence(self):
        """Capture images from multiple positions for 3D reconstruction"""
        print("\n" + "="*60)
        print("📸 CAPTURING 3D SCAN SEQUENCE")
        print("="*60)
        
        self.images = []
        self.camera_poses = []
        image_count = 0
        
        # Tilt angles: low (-0.5), middle (0), high (0.5)
        tilt_angles = np.linspace(-0.5, 0.5, TILT_POSITIONS)
        
        # Pan angles: full 360 rotation
        pan_angles = np.linspace(-1.0, 1.0, NUM_POSITIONS, endpoint=False)
        
        total_images = NUM_POSITIONS * TILT_POSITIONS
        
        print(f"Plan: {NUM_POSITIONS} pan positions × {TILT_POSITIONS} tilt angles = {total_images} images")
        print(f"⚡ Fast Mode: ~{total_images * (CAPTURE_DELAY + 0.5):.0f} seconds for capture\n")
        
        for tilt_idx, tilt in enumerate(tilt_angles):
            print(f"\n--- Tilt Level {tilt_idx + 1}/{TILT_POSITIONS} (tilt={tilt:.2f}) ---")
            
            for pan_idx, pan in enumerate(pan_angles):
                image_count += 1
                print(f"[{image_count}/{total_images}] Pan={pan:.2f}, Tilt={tilt:.2f}")
                
                # Move camera
                print(f"  ➤ Moving camera...")
                self.move_camera(pan, tilt)
                time.sleep(CAPTURE_DELAY)  # Reduced wait time
                
                # Capture image
                filename = f"scan_{image_count:03d}_p{pan:.2f}_t{tilt:.2f}.jpg"
                image = self.capture_image(filename)
                
                if image is not None:
                    self.images.append((os.path.join(CAPTURE_DIR, filename), pan, tilt))
                    print(f"  ✓ Captured")
                else:
                    print(f"  ✗ Failed")
        
        print(f"\n✓ Captured {len(self.images)}/{total_images} images")
        
        # Return to center
        print("\n➤ Returning to center...")
        self.move_camera(0, 0)
        
        return len(self.images) > 0
    
    def extract_features(self):
        """Extract SIFT features from all images - OPTIMIZED"""
        print("\n" + "="*60)
        print("🔍 EXTRACTING FEATURES (Fast Mode)")
        print("="*60)
        
        sift = cv2.SIFT_create(nfeatures=MAX_FEATURES)  # Limit features
        self.keypoints_list = []
        self.descriptors_list = []
        
        for idx, (img_path, pan, tilt) in enumerate(self.images):
            print(f"Processing image {idx + 1}/{len(self.images)}...", end="\r")
            
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            
            # Downsample for faster processing
            if DOWNSAMPLE_FACTOR > 1:
                h, w = img.shape
                img = cv2.resize(img, (w // DOWNSAMPLE_FACTOR, h // DOWNSAMPLE_FACTOR))
            
            keypoints, descriptors = sift.detectAndCompute(img, None)
            
            # Scale keypoints back if downsampled
            if DOWNSAMPLE_FACTOR > 1:
                for kp in keypoints:
                    kp.pt = (kp.pt[0] * DOWNSAMPLE_FACTOR, kp.pt[1] * DOWNSAMPLE_FACTOR)
            
            self.keypoints_list.append(keypoints)
            self.descriptors_list.append(descriptors)
        
        print(f"\n✓ Extracted features from {len(self.images)} images")
    
    def match_features(self):
        """Match features between consecutive images - OPTIMIZED"""
        print("\n" + "="*60)
        print("🔗 MATCHING FEATURES (Fast Mode)")
        print("="*60)
        
        # Use FLANN for faster matching
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)  # Lower checks = faster
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        
        self.matches_list = []
        
        for i in range(len(self.images) - 1):
            print(f"Matching image {i+1} with {i+2}...", end="\r")
            
            if self.descriptors_list[i] is None or self.descriptors_list[i+1] is None:
                self.matches_list.append([])
                continue
            
            # Use FLANN instead of BFMatcher
            matches = flann.knnMatch(self.descriptors_list[i], 
                                    self.descriptors_list[i+1], k=2)
            
            # Apply ratio test
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 0.7 * n.distance:  # More strict = fewer but better matches
                        good_matches.append(m)
            
            self.matches_list.append(good_matches)
        
        total_matches = sum(len(m) for m in self.matches_list)
        print(f"\n✓ Found {total_matches} feature matches")
    
    def create_point_cloud(self):
        """Create 3D point cloud using triangulation"""
        print("\n" + "="*60)
        print("🌐 CREATING 3D POINT CLOUD")
        print("="*60)
        
        points_3d = []
        colors = []
        
        # Estimate camera parameters (simplified)
        img = cv2.imread(self.images[0][0])
        h, w = img.shape[:2]
        focal_length = w  # Rough estimate
        cx, cy = w / 2, h / 2
        
        # Camera intrinsic matrix
        K = np.array([
            [focal_length, 0, cx],
            [0, focal_length, cy],
            [0, 0, 1]
        ])
        
        print("Triangulating points...")
        
        for i in range(len(self.matches_list)):
            if len(self.matches_list[i]) < 10:
                continue
            
            print(f"Processing pair {i+1}/{len(self.matches_list)}...", end="\r")
            
            # Get matched keypoints - with bounds checking
            try:
                pts1 = []
                pts2 = []
                for m in self.matches_list[i]:
                    if m.queryIdx < len(self.keypoints_list[i]) and m.trainIdx < len(self.keypoints_list[i+1]):
                        pts1.append(self.keypoints_list[i][m.queryIdx].pt)
                        pts2.append(self.keypoints_list[i+1][m.trainIdx].pt)
                
                if len(pts1) < 10:
                    continue
                
                pts1 = np.float32(pts1)
                pts2 = np.float32(pts2)
            except Exception as e:
                print(f"\n⚠️ Error processing pair {i+1}: {e}")
                continue
            
            # Estimate essential matrix
            E, mask = cv2.findEssentialMat(pts1, pts2, K, method=cv2.RANSAC, 
                                          prob=0.999, threshold=1.0)
            
            if E is None:
                continue
            
            # Recover pose
            _, R, t, mask = cv2.recoverPose(E, pts1, pts2, K, mask=mask)
            
            # Create projection matrices
            P1 = K @ np.hstack([np.eye(3), np.zeros((3, 1))])
            P2 = K @ np.hstack([R, t])
            
            # Triangulate points
            pts1_h = pts1[mask.ravel() == 1].T
            pts2_h = pts2[mask.ravel() == 1].T
            
            if pts1_h.shape[1] < 4:
                continue
            
            points_4d = cv2.triangulatePoints(P1, P2, pts1_h, pts2_h)
            points_3d_homogeneous = points_4d / points_4d[3]
            
            # Get colors from first image
            img_color = cv2.imread(self.images[i][0])
            for j, pt in enumerate(pts1[mask.ravel() == 1]):
                x, y = int(pt[0]), int(pt[1])
                if 0 <= x < w and 0 <= y < h:
                    color = img_color[y, x] / 255.0  # Normalize to 0-1
                    # Filter out points too far from camera
                    point_3d = points_3d_homogeneous[:3, j]
                    if np.linalg.norm(point_3d) < 50:  # Reasonable distance
                        colors.append([color[2], color[1], color[0]])  # BGR to RGB
                        points_3d.append(point_3d)
        
        print(f"\n✓ Generated {len(points_3d)} 3D points")
        
        if len(points_3d) == 0:
            print("✗ No valid 3D points generated")
            return None, None
        
        points_3d = np.array(points_3d)
        colors = np.array(colors)
        
        # Remove outliers using statistical method
        print("Removing outliers...")
        center = np.mean(points_3d, axis=0)
        distances = np.linalg.norm(points_3d - center, axis=1)
        threshold = np.percentile(distances, 95)
        mask = distances < threshold
        
        points_3d = points_3d[mask]
        colors = colors[mask]
        
        print(f"✓ After filtering: {len(points_3d)} points")
        
        # Save point cloud
        output_path = os.path.join(OUTPUT_DIR, POINT_CLOUD_FILE)
        np.savez(output_path, points=points_3d, colors=colors)
        print(f"✓ Point cloud saved: {output_path}")
        
        return points_3d, colors
    
    def visualize_matplotlib(self, points, colors):
        """Visualize point cloud using matplotlib"""
        print("\n" + "="*60)
        print("📊 CREATING MATPLOTLIB VISUALIZATION")
        print("="*60)
        
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection='3d')
        
        # Downsample for faster rendering
        step = max(1, len(points) // 10000)
        points_sampled = points[::step]
        colors_sampled = colors[::step]
        
        ax.scatter(points_sampled[:, 0], 
                  points_sampled[:, 1], 
                  points_sampled[:, 2],
                  c=colors_sampled,
                  marker='.',
                  s=1)
        
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('3D Room Point Cloud')
        
        # Set equal aspect ratio
        max_range = np.array([points[:, 0].max() - points[:, 0].min(),
                             points[:, 1].max() - points[:, 1].min(),
                             points[:, 2].max() - points[:, 2].min()]).max() / 2.0
        
        mid_x = (points[:, 0].max() + points[:, 0].min()) * 0.5
        mid_y = (points[:, 1].max() + points[:, 1].min()) * 0.5
        mid_z = (points[:, 2].max() + points[:, 2].min()) * 0.5
        
        ax.set_xlim(mid_x - max_range, mid_x + max_range)
        ax.set_ylim(mid_y - max_range, mid_y + max_range)
        ax.set_zlim(mid_z - max_range, mid_z + max_range)
        
        print("✓ Displaying 3D visualization")
        print("  Close the window to continue...")
        plt.show()
    
    def visualize_plotly(self, points, colors):
        """Create interactive 3D visualization using Plotly"""
        print("\n" + "="*60)
        print("🎨 CREATING INTERACTIVE 3D MODEL")
        print("="*60)
        
        # Downsample for web performance
        step = max(1, len(points) // 50000)
        points_sampled = points[::step]
        colors_sampled = colors[::step]
        
        # Convert colors to hex
        colors_hex = ['rgb({},{},{})'.format(
            int(c[0]*255), int(c[1]*255), int(c[2]*255)
        ) for c in colors_sampled]
        
        # Create scatter plot
        scatter = go.Scatter3d(
            x=points_sampled[:, 0],
            y=points_sampled[:, 1],
            z=points_sampled[:, 2],
            mode='markers',
            marker=dict(
                size=2,
                color=colors_hex,
                opacity=0.8
            ),
            text=[f'Point {i}' for i in range(len(points_sampled))],
            hoverinfo='text'
        )
        
        # Create layout
        layout = go.Layout(
            title='3D Room Model - Interactive',
            scene=dict(
                xaxis_title='X',
                yaxis_title='Y',
                zaxis_title='Z',
                aspectmode='data'
            ),
            width=1200,
            height=800
        )
        
        fig = go.Figure(data=[scatter], layout=layout)
        
        # Save as HTML
        output_path = os.path.join(OUTPUT_DIR, POINT_CLOUD_HTML)
        fig.write_html(output_path)
        
        print(f"✓ Interactive 3D model saved: {output_path}")
        print(f"\n📂 To view the 3D model:")
        print(f"   1. Open Finder")
        print(f"   2. Navigate to: {os.path.abspath(output_path)}")
        print(f"   3. Double-click the HTML file")
        print(f"   OR")
        print(f"   4. Run: open {output_path}")
        
        # Try to open in browser
        try:
            import webbrowser
            print("\n➤ Attempting to open in browser...")
            webbrowser.open('file://' + os.path.abspath(output_path))
            print("✓ Check your browser!")
        except Exception as e:
            print(f"⚠️  Couldn't auto-open browser: {e}")
            print(f"   Please manually open: {os.path.abspath(output_path)}")


def main():
    print("\n" + "="*60)
    print("🏠 TAPO C230 3D ROOM SCANNER")
    print("="*60)
    print(f"📹 Camera: {HOST}")
    print(f"📊 Scan positions: {NUM_POSITIONS} × {TILT_POSITIONS}")
    print("="*60)
    
    scanner = Room3DScanner(HOST, PORT, USER, PASSWORD, RTSP)
    
    if not scanner.connect():
        return
    
    print("\nOptions:")
    print("1. Start Full 3D Scan")
    print("2. Process Existing Images")
    print("3. View Saved Model")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        # Capture images
        if scanner.capture_scan_sequence():
            # Extract and match features
            scanner.extract_features()
            scanner.match_features()
            
            # Create 3D model
            points, colors = scanner.create_point_cloud()
            
            if points is not None:
                # Visualize
                scanner.visualize_matplotlib(points, colors)
                scanner.visualize_plotly(points, colors)
                
                print("\n" + "="*60)
                print("✓ 3D SCANNING COMPLETE!")
                print("="*60)
                print(f"📁 Models saved in: {OUTPUT_DIR}/")
                print(f"  - Point cloud data: {POINT_CLOUD_FILE}")
                print(f"  - Interactive HTML: {POINT_CLOUD_HTML}")
                print("="*60 + "\n")
    
    elif choice == "2":
        print("\n⚙️  Processing existing images...")
        if os.path.exists(CAPTURE_DIR):
            files = sorted([f for f in os.listdir(CAPTURE_DIR) if f.endswith('.jpg')])
            scanner.images = [(os.path.join(CAPTURE_DIR, f), 0, 0) for f in files]
            
            if len(scanner.images) > 0:
                scanner.extract_features()
                scanner.match_features()
                points, colors = scanner.create_point_cloud()
                
                if points is not None:
                    scanner.visualize_matplotlib(points, colors)
                    scanner.visualize_plotly(points, colors)
            else:
                print("✗ No images found")
        else:
            print("✗ No capture directory found")
    
    elif choice == "3":
        npz_path = os.path.join(OUTPUT_DIR, POINT_CLOUD_FILE)
        
        if os.path.exists(npz_path):
            print(f"\n📂 Loading model from {OUTPUT_DIR}/")
            data = np.load(npz_path)
            points = data['points']
            colors = data['colors']
            
            print(f"✓ Loaded {len(points)} points")
            scanner.visualize_matplotlib(points, colors)
            scanner.visualize_plotly(points, colors)
        else:
            print("✗ No saved model found. Run a scan first.")
    
    elif choice == "4":
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()