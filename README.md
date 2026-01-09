TAPO-Camera

TAPO-Camera — DC Project
A collection of Python tools and scripts for interacting with TP-Link TAPO cameras (via RTSP/local stream), including image capture, person detection, panorama stitching, QR scanning, audio playback, and more.

📌 Overview

This repository contains Python-based utilities designed to interact with TP-Link TAPO security cameras (e.g., C200, C210, C220 models) using their local video stream. It provides tools to capture images, detect people, scan QR codes, create panoramas, and play audio over RTSP/AUDIO streams.

⚠️ This project uses unofficial methods/APIs for TAPO cameras and is not affiliated with TP-Link or the official TAPO app. Expect differences in behavior across firmware versions (RTSP might need enabling in the TAPO app).

🧠 Key Features
📷 Camera Interaction

Capture single frames or continuous image sequences from the camera.

Use RTSP or local streaming for video feed access.

🧍 Person Detection

Detect people in the camera frame using computer vision.

🔍 QR Code Scanner

Scan QR codes from the camera feed — useful for automation or scanning tags.

🖼️ Image Panorama

Stitch multiple frames into panoramic images.

🔉 Audio Utilities

Play or capture audio from RTSP/AUDIO streams.

🧪 Utilities

Welcome message demo.

Additional helper scripts for camera control workflows.

Note: The scripts are modular and can be integrated into larger automation or surveillance pipelines.

🗂️ Files & Scripts
Script	Purpose
image_capture.py	Capture still frames from camera.
image_capture+qr.py	Capture + QR scanning.
person_detection.py	Detect humans in live feed.
panaroma.py	Create panoramic image from streams.
3D_model_room.py	(Experimental) 3D model generation.
play_rtsp_audio.py	Play audio from RTSP/AUDIO source.
audio.py	Audio utilities.
qrscan.py	Stand-alone QR scanner.
welcome_message.py	Initial demo/intro script.

Adjust this list to match actual functionality if definitions differ.

🚀 Getting Started
🔁 Prerequisites

Make sure you have:

Python 3.9+

Camera with RTSP enabled (via TAPO app: Settings → Third-Party Compatibility → ON)

Local network access to your camera’s IP

Required Python packages (listed below)

🧰 Install Dependencies
pip install -r requirements.txt


If you don’t yet have a requirements.txt file, generate one from installed libs:

pip freeze > requirements.txt

📍 Environment Variables

Set variables for your camera’s credentials and IP:

export TAPO_IP="192.168.1.100"
export TAPO_USER="your_username"
export TAPO_PASS="your_password"


Alternatively, update variables inside the scripts directly.

▶️ Examples
Capture a Frame
python image_capture.py --ip $TAPO_IP --user $TAPO_USER --pass $TAPO_PASS --output frame.jpg

Scan QR in Live Feed
python image_capture+qr.py --ip $TAPO_IP --user $TAPO_USER --pass $TAPO_PASS

Detect Person
python person_detection.py --ip $TAPO_IP --user $TAPO_USER --pass $TAPO_PASS

Create Panorama
python panaroma.py --ip $TAPO_IP --user $TAPO_USER --pass $TAPO_PASS --frames 10

🧩 Integration Ideas

This project can serve as a base for:

Home surveillance systems

Smart notifications on detection

RTSP feeds combined with OpenCV pipelines

QR-based location or tag triggers

📦 Dependencies

Suggested libraries (commonly used):

opencv-python
numpy
pyzbar
ffmpeg/ffmpeg-python
requests


Install them via pip:

pip install opencv-python numpy pyzbar ffmpeg-python requests

❓ Troubleshooting

RTSP not working?
Check that Third-Party Compatibility is enabled in the official TAPO app. Some cameras disable RTSP by default.

Authentication fails?
Ensure correct username/password; sometimes cloud/local credentials can differ. Some integrations require cloud password.

📜 License

This project is MIT Licensed — feel free to modify and distribute.

🤝 Contributing

Contributions are welcome! Whether it’s:

Bug fixes

Feature additions

Packaging & examples

Better documentation

Submit a pull request or open an issue
