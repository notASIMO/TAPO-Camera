"""
Tapo C230 - 360° Room Viewer (Simplified & Reliable)
Creates a clear, usable 360-degree view of your room
Requires: pip install opencv-python numpy onvif-zeep pillow
"""

import cv2
import numpy as np
from onvif import ONVIFCamera
import time
import os
from PIL import Image

# Camera configuration
HOST = "10.239.197.233"
PORT = 2020
USER = "Tapocam"
PASSWORD = "Tapo@1234"
RTSP = f"rtsp://{USER}:{PASSWORD}@{HOST}:554/stream1"

# Settings
NUM_IMAGES = 12  # 12 images = 30° per image
OUTPUT_DIR = "room_360"


class Room360Viewer:
    def __init__(self, host, port, user, password, rtsp_url):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.rtsp_url = rtsp_url
        self.camera = None
        self.ptz = None
        self.images = []
        
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
    
    def connect(self):
        """Connect to camera"""
        try:
            print(f"Connecting to {self.host}...")
            self.camera = ONVIFCamera(self.host, self.port, self.user, self.password)
            media = self.camera.create_media_service()
            self.media_profile = media.GetProfiles()[0]
            self.ptz = self.camera.create_ptz_service()
            print("✓ Connected!")
            return True
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def move_camera(self, pan, tilt=0):
        """Move camera"""
        try:
            request = self.ptz.create_type('AbsoluteMove')
            request.ProfileToken = self.media_profile.token
            request.Position = {
                'PanTilt': {'x': pan, 'y': tilt},
                'Zoom': {'x': 0}
            }
            self.ptz.AbsoluteMove(request)
            return True
        except:
            return False
    
    def capture_image(self):
        """Capture single frame"""
        cap = cv2.VideoCapture(self.rtsp_url)
        if not cap.isOpened():
            return None
        
        # Skip first few frames
        for _ in range(5):
            ret, frame = cap.read()
        
        cap.release()
        return frame if ret else None
    
    def capture_360_sequence(self):
        """Capture 360° sequence"""
        print("\n" + "="*60)
        print("📸 CAPTURING 360° ROOM VIEW")
        print("="*60)
        print(f"Taking {NUM_IMAGES} photos around the room...")
        
        self.images = []
        angle_step = 2.0 / NUM_IMAGES  # -1 to 1 range
        
        # Start position
        print("\n➤ Moving to start position...")
        self.move_camera(-1.0, 0)
        time.sleep(3)
        
        for i in range(NUM_IMAGES):
            pan = -1.0 + (i * angle_step)
            angle_degrees = ((pan + 1) / 2) * 360
            
            print(f"\n[{i+1}/{NUM_IMAGES}] Angle: {angle_degrees:.0f}°")
            
            # Move
            self.move_camera(pan, 0)
            time.sleep(1.5)
            
            # Capture
            print("  📸 Capturing...", end="")
            frame = self.capture_image()
            
            if frame is not None:
                # Save individual image
                filename = os.path.join(OUTPUT_DIR, f"view_{i+1:02d}_{angle_degrees:.0f}deg.jpg")
                cv2.imwrite(filename, frame)
                self.images.append(frame)
                print(" ✓")
            else:
                print(" ✗ Failed")
        
        print(f"\n✓ Captured {len(self.images)} images")
        
        # Return to center
        self.move_camera(0, 0)
        
        return len(self.images) > 0
    
    def create_contact_sheet(self):
        """Create a grid view of all images"""
        print("\n📊 Creating contact sheet...")
        
        if len(self.images) < 4:
            print("✗ Need at least 4 images")
            return None
        
        # Calculate grid dimensions
        cols = 4
        rows = (len(self.images) + cols - 1) // cols
        
        # Resize images to uniform size
        target_width = 640
        target_height = 360
        
        resized = []
        for img in self.images:
            resized.append(cv2.resize(img, (target_width, target_height)))
        
        # Create canvas
        canvas_width = target_width * cols
        canvas_height = target_height * rows
        canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
        
        # Place images
        for idx, img in enumerate(resized):
            row = idx // cols
            col = idx % cols
            y = row * target_height
            x = col * target_width
            canvas[y:y+target_height, x:x+target_width] = img
            
            # Add label
            angle = (idx / NUM_IMAGES) * 360
            label = f"{angle:.0f}°"
            cv2.putText(canvas, label, (x+10, y+30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Save
        output = os.path.join(OUTPUT_DIR, "room_grid_view.jpg")
        cv2.imwrite(output, canvas)
        print(f"✓ Grid view saved: {output}")
        
        return canvas
    
    def create_horizontal_strip(self):
        """Create simple horizontal strip panorama"""
        print("\n📏 Creating horizontal strip...")
        
        # Resize all to same height
        min_h = min(img.shape[0] for img in self.images)
        resized = []
        
        for img in self.images:
            if img.shape[0] != min_h:
                ratio = min_h / img.shape[0]
                new_w = int(img.shape[1] * ratio)
                resized.append(cv2.resize(img, (new_w, min_h)))
            else:
                resized.append(img)
        
        # Concatenate
        strip = np.hstack(resized)
        
        # Add degree markers
        img_width = strip.shape[1] // len(self.images)
        for i in range(len(self.images)):
            x = i * img_width + 10
            angle = (i / NUM_IMAGES) * 360
            cv2.putText(strip, f"{angle:.0f}°", (x, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Save
        output = os.path.join(OUTPUT_DIR, "room_360_strip.jpg")
        cv2.imwrite(output, strip)
        print(f"✓ Strip saved: {output}")
        print(f"  Size: {strip.shape[1]}x{strip.shape[0]}")
        
        return strip
    
    def create_stitched_panorama(self):
        """Create stitched panorama using OpenCV"""
        print("\n🔗 STITCHING PANORAMA (Advanced)")
        print("="*60)
        print("⚠️  This may take 1-2 minutes and might fail...")
        print("    Stitching works best with overlap between images")
        
        try:
            # Create stitcher with PANORAMA mode
            print("\n➤ Initializing stitcher...")
            stitcher = cv2.Stitcher_create(cv2.Stitcher_PANORAMA)
            
            # Try different strategies
            print("➤ Attempting to stitch...")
            
            # Strategy 1: Use all images
            print("  Strategy 1: Using all images...")
            status, pano = stitcher.stitch(self.images)
            
            if status != cv2.Stitcher_OK:
                # Strategy 2: Use every other image (less overlap needed)
                print("  Strategy 2: Using every other image...")
                subset = self.images[::2]
                status, pano = stitcher.stitch(subset)
            
            if status != cv2.Stitcher_OK:
                # Strategy 3: Use first 8 images only
                print("  Strategy 3: Using first 8 images...")
                subset = self.images[:8]
                status, pano = stitcher.stitch(subset)
            
            if status == cv2.Stitcher_OK:
                # Success!
                output = os.path.join(OUTPUT_DIR, "room_panorama_stitched.jpg")
                cv2.imwrite(output, pano)
                
                h, w = pano.shape[:2]
                print(f"\n✅ SUCCESS! Stitched panorama created!")
                print(f"✓ Saved: {output}")
                print(f"  Resolution: {w}x{h} pixels")
                
                return pano
            else:
                # Failed
                errors = {
                    cv2.Stitcher_ERR_NEED_MORE_IMGS: "Not enough images",
                    cv2.Stitcher_ERR_HOMOGRAPHY_EST_FAIL: "Couldn't find matching features",
                    cv2.Stitcher_ERR_CAMERA_PARAMS_ADJUST_FAIL: "Camera calibration failed"
                }
                error_msg = errors.get(status, f"Error code {status}")
                
                print(f"\n❌ Stitching failed: {error_msg}")
                print("\n💡 Why stitching fails with rotating cameras:")
                print("   • Images need 30-50% overlap")
                print("   • Your camera rotates with gaps between shots")
                print("   • Solution: Use the HTML viewer or grid instead!")
                
                return None
                
        except Exception as e:
            print(f"\n❌ Stitching error: {e}")
            return None
    
    def create_interactive_html(self):
        """Create interactive HTML viewer"""
        print("\n🌐 Creating interactive HTML viewer...")
        
        html = """<!DOCTYPE html>
<html>
<head>
    <title>360° Room View</title>
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: white;
            font-family: Arial, sans-serif;
        }
        h1 {
            text-align: center;
            color: #4CAF50;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .viewer {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .main-image {
            width: 100%;
            border-radius: 5px;
        }
        .controls {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 20px;
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background: #45a049;
        }
        .angle-display {
            text-align: center;
            font-size: 24px;
            margin: 20px;
            color: #4CAF50;
        }
        .thumbnails {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 30px;
        }
        .thumbnail {
            cursor: pointer;
            border: 3px solid transparent;
            border-radius: 5px;
            transition: all 0.3s;
        }
        .thumbnail:hover {
            border-color: #4CAF50;
            transform: scale(1.05);
        }
        .thumbnail.active {
            border-color: #4CAF50;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏠 360° Room View</h1>
        
        <div class="viewer">
            <img id="mainImage" class="main-image" src="view_01_0deg.jpg">
            <div class="angle-display">
                Viewing: <span id="angleDisplay">0°</span>
            </div>
            <div class="controls">
                <button onclick="prevImage()">⬅️ Previous</button>
                <button onclick="autoRotate()">🔄 Auto Rotate</button>
                <button onclick="nextImage()">Next ➡️</button>
            </div>
        </div>
        
        <h2 style="text-align: center;">Click any view:</h2>
        <div class="thumbnails" id="thumbnails"></div>
    </div>
    
    <script>
        const numImages = """ + str(NUM_IMAGES) + """;
        let currentIndex = 0;
        let autoRotating = false;
        let rotateInterval;
        
        // Initialize thumbnails
        for (let i = 0; i < numImages; i++) {
            const angle = Math.round((i / numImages) * 360);
            const img = document.createElement('img');
            img.src = `view_${String(i+1).padStart(2, '0')}_${angle}deg.jpg`;
            img.className = 'thumbnail' + (i === 0 ? ' active' : '');
            img.onclick = () => showImage(i);
            document.getElementById('thumbnails').appendChild(img);
        }
        
        function showImage(index) {
            currentIndex = index % numImages;
            const angle = Math.round((currentIndex / numImages) * 360);
            document.getElementById('mainImage').src = 
                `view_${String(currentIndex+1).padStart(2, '0')}_${angle}deg.jpg`;
            document.getElementById('angleDisplay').textContent = angle + '°';
            
            // Update active thumbnail
            document.querySelectorAll('.thumbnail').forEach((thumb, i) => {
                thumb.classList.toggle('active', i === currentIndex);
            });
        }
        
        function nextImage() {
            showImage(currentIndex + 1);
        }
        
        function prevImage() {
            showImage(currentIndex - 1 + numImages);
        }
        
        function autoRotate() {
            if (autoRotating) {
                clearInterval(rotateInterval);
                autoRotating = false;
            } else {
                autoRotating = true;
                rotateInterval = setInterval(() => {
                    nextImage();
                }, 1000);
            }
        }
        
        // Keyboard controls
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') prevImage();
            if (e.key === 'ArrowRight') nextImage();
            if (e.key === ' ') autoRotate();
        });
    </script>
</body>
</html>"""
        
        # Save HTML
        html_path = os.path.join(OUTPUT_DIR, "room_360_viewer.html")
        with open(html_path, 'w') as f:
            f.write(html)
        
        print(f"✓ Interactive viewer saved: {html_path}")
        print("  Open this file in your browser!")
        
        return html_path
    
    def display_result(self, img, title):
        """Display image"""
        h, w = img.shape[:2]
        if w > 1920:
            scale = 1920 / w
            img = cv2.resize(img, (int(w*scale), int(h*scale)))
        
        cv2.imshow(title, img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def main():
    print("\n" + "="*60)
    print("🏠 360° ROOM VIEWER")
    print("="*60)
    
    viewer = Room360Viewer(HOST, PORT, USER, PASSWORD, RTSP)
    
    if not viewer.connect():
        return
    
    print("\n1. Capture new 360° view")
    print("2. View existing images")
    print("3. Exit")
    
    choice = input("\nChoice: ").strip()
    
    if choice == "1":
        # Capture
        if not viewer.capture_360_sequence():
            print("✗ Capture failed")
            return
        
        # Create outputs
        print("\n" + "="*60)
        print("🎨 CREATING VISUALIZATIONS")
        print("="*60)
        
        # 1. Try stitching first (what you want!)
        stitched = viewer.create_stitched_panorama()
        
        # 2. Grid view
        grid = viewer.create_contact_sheet()
        
        # 3. Strip view
        strip = viewer.create_horizontal_strip()
        
        # 4. Interactive HTML
        html_path = viewer.create_interactive_html()
        
        # Display results
        if stitched is not None:
            print("\n🎉 Showing stitched panorama...")
            viewer.display_result(stitched, "Stitched Panorama - SUCCESS!")
        
        if grid is not None:
            viewer.display_result(grid, "Grid View")
        
        if strip is not None:
            viewer.display_result(strip, "360° Strip")
        
        print("\n" + "="*60)
        print("✅ COMPLETE!")
        print("="*60)
        print(f"\n📁 All files in: {OUTPUT_DIR}/")
        print("\n🌟 OPEN THIS FILE:")
        print(f"   {html_path}")
        print("\n   Click through all 12 views of your room!")
        print("   Use arrow keys or click thumbnails")
        print("="*60 + "\n")
        
        # Try to open HTML
        try:
            import webbrowser
            webbrowser.open('file://' + os.path.abspath(html_path))
        except:
            pass
    
    elif choice == "2":
        # Load existing
        files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.startswith('view_')])
        if files:
            viewer.images = [cv2.imread(os.path.join(OUTPUT_DIR, f)) for f in files]
            print(f"✓ Loaded {len(viewer.images)} images\n")
            
            # Try stitching
            stitched = viewer.create_stitched_panorama()
            
            # Create other views
            grid = viewer.create_contact_sheet()
            strip = viewer.create_horizontal_strip()
            html_path = viewer.create_interactive_html()
            
            # Display
            if stitched is not None:
                viewer.display_result(stitched, "Stitched Panorama")
            if grid is not None:
                viewer.display_result(grid, "Grid View")
            if strip is not None:
                viewer.display_result(strip, "360° Strip")
            
            print(f"\n✅ Files ready in: {OUTPUT_DIR}/")
            print(f"\n🌟 Open: {html_path}")
        else:
            print("✗ No images found")


if __name__ == "__main__":
    main()