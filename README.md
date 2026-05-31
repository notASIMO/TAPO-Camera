# 🎥 TAPO Camera Toolkit

> A Python-based computer vision and automation toolkit for interacting with **TP-Link TAPO C230 Cameras** through RTSP/local streams.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green)
![RTSP](https://img.shields.io/badge/RTSP-Streaming-orange)

---

## 📖 Overview

The **TAPO Camera Toolkit** is a collection of Python utilities developed to leverage the capabilities of **TP-Link TAPO security cameras** using RTSP-based video streams and computer vision techniques.

The project provides tools for:

* 📷 Capturing images from live camera feeds
* 🧍 Detecting people in real-time
* 🔍 Scanning QR codes from video streams
* 🖼️ Generating panoramic images
* 🔉 Streaming and processing audio feeds
* 🏠 Building automation and surveillance workflows

This repository serves as a foundation for smart surveillance systems, home automation projects, and computer vision experiments.

> ⚠️ **Disclaimer:** This project is not affiliated with or endorsed by TP-Link. It utilizes RTSP/local stream access and may behave differently across camera models and firmware versions.

---

# ✨ Features

## 📷 Camera Feed Access

* Connect to TAPO cameras via RTSP.
* Capture single frames or image sequences.
* Save snapshots automatically.

---

## 🧍 Human Detection

* Detect people in live camera feeds using computer vision techniques.
* Suitable for surveillance and occupancy monitoring.

---

## 🔍 QR Code Recognition

* Real-time QR code detection and decoding.
* Useful for:

  * Inventory tracking
  * Smart home triggers
  * Location-based automation

---

## 🖼️ Panorama Generation

* Capture multiple frames from the stream.
* Stitch images together into panoramic views.

---

## 🔉 Audio Streaming Utilities

* Access and play RTSP audio streams.
* Process audio for custom automation workflows.

---

## 🧪 Experimental Features

* Basic room reconstruction experiments.
* 3D environment modeling research.

---

# 📂 Repository Structure

```text
TAPO-Camera/
│
├── image_capture.py          # Capture images from camera feed
├── image_capture+qr.py       # Capture images and scan QR codes
├── person_detection.py       # Human detection from live feed
├── panorama.py              # Panorama generation
├── qrscan.py                # Standalone QR scanner
├── audio.py                 # Audio utilities
├── play_rtsp_audio.py       # RTSP audio playback
├── 3D_model_room.py         # Experimental 3D room modeling
├── welcome_message.py       # Demo script
│
├── requirements.txt
└── README.md
```

---

# 🚀 Getting Started

## 📋 Prerequisites

Before running the project, ensure you have:

* Python 3.9 or newer
* TP-Link TAPO Camera (tested on C230)
* RTSP enabled in TAPO App
* Local network access to the camera

---

## 🔧 Enable RTSP

In the TAPO mobile application:

```text
Settings
 └── Advanced Settings
      └── Third-Party Compatibility
           └── Enable RTSP
```

---

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/your-username/TAPO-Camera.git

cd TAPO-Camera
```

Install dependencies:

```bash
pip install -r requirements.txt
```

If a requirements file is not available:

```bash
pip install \
opencv-python \
numpy \
pyzbar \
ffmpeg-python \
requests
```

---

# ⚙️ Configuration

Configure your camera credentials using environment variables.

### Linux / macOS

```bash
export TAPO_IP="192.168.1.100"
export TAPO_USER="username"
export TAPO_PASS="password"
```

### Windows

```cmd
set TAPO_IP=192.168.1.100
set TAPO_USER=username
set TAPO_PASS=password
```

---

# ▶️ Usage Examples

## 📸 Capture a Frame

```bash
python image_capture.py \
--ip $TAPO_IP \
--user $TAPO_USER \
--pass $TAPO_PASS \
--output frame.jpg
```

---

## 🔍 Scan QR Codes

```bash
python image_capture+qr.py \
--ip $TAPO_IP \
--user $TAPO_USER \
--pass $TAPO_PASS
```

---

## 🧍 Detect People

```bash
python person_detection.py \
--ip $TAPO_IP \
--user $TAPO_USER \
--pass $TAPO_PASS
```

---

## 🖼️ Create a Panorama

```bash
python panorama.py \
--ip $TAPO_IP \
--user $TAPO_USER \
--pass $TAPO_PASS \
--frames 10
```

---

# 💡 Applications

This toolkit can be integrated into:

### 🏠 Smart Home Systems

* Occupancy detection
* Automated lighting
* Visitor monitoring

### 🎯 Computer Vision Projects

* Object detection
* Scene analysis
* QR-based automation

### 🛡️ Surveillance Solutions

* Motion monitoring
* Human detection alerts
* Security camera analytics

### 🤖 Robotics & Automation

* Vision-based navigation
* Environment monitoring
* Event-triggered actions

---

# 📚 Core Technologies

| Technology | Purpose                |
| ---------- | ---------------------- |
| Python     | Core Development       |
| OpenCV     | Computer Vision        |
| NumPy      | Numerical Computing    |
| RTSP       | Video Streaming        |
| PyZBar     | QR Detection           |
| FFmpeg     | Audio/Video Processing |

---

# 🛠️ Troubleshooting

### RTSP Connection Fails

✅ Verify RTSP is enabled in the TAPO App.

✅ Ensure camera and computer are on the same network.

✅ Confirm IP address is correct.

---

### Authentication Errors

✅ Verify username and password.

✅ Check whether local credentials differ from cloud credentials.

---

### Camera Feed Not Opening

✅ Test the RTSP stream in VLC:

```text
rtsp://username:password@camera_ip:554/stream1
```

---

# 🔮 Future Improvements

* 🚶 Motion detection
* 📱 Mobile notifications
* 🤖 AI-powered object recognition
* 🗺️ Advanced room mapping

---

# 🤝 Contributing

Contributions are welcome!

You can contribute by:

* 🐛 Reporting bugs
* ✨ Adding new features
* 📚 Improving documentation
* ⚡ Optimizing performance

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a Pull Request

