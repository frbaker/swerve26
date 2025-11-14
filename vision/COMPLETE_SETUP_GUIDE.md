# Complete OrangePi Vision System Setup Guide
## From Zero to Fully Operational

This guide takes you through the complete process of setting up your OrangePi vision system from unboxing to running autonomously on your robot.

**Estimated Time**: 2-4 hours for initial setup + training time

---

## Table of Contents
1. [Hardware Setup](#part-1-hardware-setup)
2. [Operating System Installation](#part-2-operating-system-installation)
3. [System Configuration](#part-3-system-configuration)
4. [Python & Dependencies](#part-4-python--dependencies)
5. [Camera Setup & Testing](#part-5-camera-setup--testing)
6. [Vision System Installation](#part-6-vision-system-installation)
7. [Initial Testing](#part-7-initial-testing)
8. [Data Collection & Model Training](#part-8-data-collection--model-training)
9. [Auto-Start Configuration](#part-9-auto-start-configuration)
10. [Robot Integration](#part-10-robot-integration)
11. [Competition Preparation](#part-11-competition-preparation)

---

## Part 1: Hardware Setup

### What You Need
- **OrangePi** (OrangePi 5 recommended, but works on most models)
- **MicroSD Card** (32GB+ Class 10 or better)
- **USB Camera** (or CSI camera if supported)
- **Power Supply** (appropriate for your OrangePi model)
- **Ethernet Cable** (for robot network)
- **MicroSD Card Reader** (for flashing OS)
- **Computer** (for setup and training)
- **Monitor + HDMI Cable** (for initial setup, optional)
- **USB Keyboard** (for initial setup, optional)

### Physical Setup
1. Insert MicroSD card into your computer
2. Keep OrangePi unpowered for now
3. Have camera ready for testing

---

## Part 2: Operating System Installation

### 1. Download OS Image

**Recommended**: Ubuntu 22.04 LTS for OrangePi

- OrangePi 5: http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/service-and-support/Orange-Pi-5.html
- Other models: http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/index.html

### 2. Flash MicroSD Card

**Using Raspberry Pi Imager (Easiest)**:
```bash
# Download from: https://www.raspberrypi.com/software/
# 1. Open Raspberry Pi Imager
# 2. Choose OS → Use custom → Select downloaded image
# 3. Choose Storage → Select your MicroSD card
# 4. Click Write
```

**Using Etcher (Alternative)**:
```bash
# Download from: https://www.balena.io/etcher/
# 1. Open Etcher
# 2. Select image file
# 3. Select target (MicroSD card)
# 4. Flash!
```

**Using dd (Linux)**:
```bash
# Find device name
lsblk

# Flash image (CAREFUL - verify /dev/sdX is your MicroSD card!)
sudo dd if=orangepi_ubuntu.img of=/dev/sdX bs=4M status=progress
sudo sync
```

### 3. First Boot

1. Insert MicroSD card into OrangePi
2. Connect monitor and keyboard (or SSH if headless)
3. Connect ethernet cable to your network
4. Power on OrangePi
5. Complete initial setup wizard (create user, set password)

**Default credentials** (if prompted):
- Username: `orangepi` or `pi`
- Password: `orangepi` or `orangepi`

**⚠️ IMPORTANT**: Change default password immediately!

---

## Part 3: System Configuration

### 1. Initial Login

```bash
# If using monitor/keyboard, login with credentials

# If using SSH (find IP with router or: sudo arp-scan --localnet)
ssh orangepi@<IP_ADDRESS>
# Default password: orangepi
```

### 2. Change Password & Update System

```bash
# Change password
passwd

# Update system
sudo apt update
sudo apt upgrade -y

# Install basic tools
sudo apt install -y git vim curl wget htop net-tools
```

### 3. Set Hostname

```bash
# Set recognizable hostname
sudo hostnamectl set-hostname orangepi-vision

# Verify
hostname
```

### 4. Configure Static IP (Important!)

For reliable robot network connection:

```bash
# Check current network interface name
ip addr
# Look for interface like 'eth0' or 'enp1s0'

# Edit netplan config (Ubuntu)
sudo nano /etc/netplan/01-netcfg.yaml
```

**For Team 3267**, add this configuration (replace with YOUR team number):
```yaml
network:
  version: 2
  ethernets:
    eth0:  # Replace with your interface name if different
      dhcp4: no
      addresses:
        - 10.32.67.50/24  # 10.TE.AM.50 format
      routes:
        - to: default
          via: 10.32.67.1
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
```

**For your team**, use format `10.TE.AM.50`:
- Team 3267 → `10.32.67.50`
- Team 254 → `10.2.54.50`
- Team 1234 → `10.12.34.50`

Apply configuration:
```bash
sudo netplan apply

# Verify new IP
ip addr show eth0
```

### 5. Enable SSH (if not already enabled)

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
sudo systemctl status ssh
```

From now on, you can SSH from your computer:
```bash
ssh orangepi@10.32.67.50  # Use your team's IP
```

---

## Part 4: Python & Dependencies

### 1. Check Python Version

```bash
python3 --version
# Need 3.8 or higher, 3.11+ recommended
```

If older than 3.8:
```bash
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
```

### 2. Install System Dependencies

```bash
# OpenCV and camera dependencies
sudo apt install -y \
    python3-opencv \
    libopencv-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    gfortran \
    v4l-utils

# This may take 5-10 minutes
```

---

## Part 5: Camera Setup & Testing

### 1. Connect Camera

- Plug USB camera into OrangePi USB port
- Or connect CSI camera to CSI port

### 2. Verify Camera Detection

```bash
# List video devices
ls -l /dev/video*
# Should show /dev/video0 (or video1, video2, etc.)

# Check camera info
v4l2-ctl --list-devices

# Check supported formats
v4l2-ctl -d /dev/video0 --list-formats-ext
```

If no camera detected:
- Try different USB port
- Check camera LED (if present)
- Run `dmesg | grep -i video` to check for errors
- Verify camera works on another computer

### 3. Test Camera with Python

**Note**: This test uses system Python (not venv), which has `python3-opencv` from Part 4.

```bash
python3 << 'EOF'
import cv2

print("Opening camera...")
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("❌ FAILED: Camera not accessible")
    exit(1)

ret, frame = camera.read()
if ret:
    print(f"✅ SUCCESS: Camera working!")
    print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
    print(f"   Channels: {frame.shape[2]}")
else:
    print("❌ FAILED: Could not read frame")

camera.release()
EOF
```

You should see: `✅ SUCCESS: Camera working!`

**If you get `ModuleNotFoundError: No module named 'cv2'`**:
```bash
# Verify python3-opencv is installed
sudo apt install -y python3-opencv
# Then retry the test above
```

---

## Part 6: Vision System Installation

### 1. Create Project Directory

```bash
mkdir -p ~/frc-vision
cd ~/frc-vision
```

### 2. Transfer Vision Files from Repository

**Option A: Clone Repository (if you have it on GitHub)**:
```bash
cd ~/frc-vision
# Clone your repo (adjust URL)
git clone https://github.com/frbaker/swerve26.git temp
mv temp/vision/* .
rm -rf temp
```

**Option B: Copy Files Manually**:
```bash
# From your computer, copy vision files to OrangePi:
scp -r vision/* orangepi@10.32.67.50:~/frc-vision/

# Files you need:
# - vision_system.py
# - config.json
# - requirements.txt
# - collect_training_data.py
# - prepare_dataset.py
# - test_camera.py
# - camera_calibration.py
# - frc-vision.service
```

**Option C: Download Individual Files**:
```bash
cd ~/frc-vision

# Download each file from your repository
# (Adjust URLs to match your repo)
wget https://raw.githubusercontent.com/frbaker/swerve26/main/vision/vision_system.py
wget https://raw.githubusercontent.com/frbaker/swerve26/main/vision/config.json
wget https://raw.githubusercontent.com/frbaker/swerve26/main/vision/requirements.txt
wget https://raw.githubusercontent.com/frbaker/swerve26/main/vision/collect_training_data.py
wget https://raw.githubusercontent.com/frbaker/swerve26/main/vision/prepare_dataset.py
wget https://raw.githubusercontent.com/frbaker/swerve26/main/vision/test_camera.py
wget https://raw.githubusercontent.com/frbaker/swerve26/main/vision/frc-vision.service

# Make scripts executable
chmod +x *.py
```

### 3. Create Python Virtual Environment

```bash
cd ~/frc-vision

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### 4. Install Python Dependencies

```bash
# Still in activated venv
pip install -r requirements.txt

# This installs:
# - ultralytics (YOLO8)
# - opencv-python
# - numpy
# - pynetworktables
# - dt-apriltags
# This may take 10-20 minutes on OrangePi
```

**⚠️ Note on OpenCV for ARM devices:**

If `opencv-python` installation fails or takes too long (>30 minutes), you have two options:

**Option A: Use system OpenCV (Recommended for OrangePi)**

```bash
# Exit and recreate venv with system site-packages access
deactivate
rm -rf venv
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Install requirements (will skip system opencv)
pip install ultralytics numpy pynetworktables dt-apriltags Pillow
```

**Option B: Install OpenCV headless version**

```bash
# If Option A doesn't work, try headless version
pip uninstall opencv-python
pip install opencv-python-headless
```

### 4a. Verify OpenCV Installation

**CRITICAL**: Test that cv2 works before proceeding:

```bash
# Should still be in activated venv
python3 << 'EOF'
import cv2
print(f"✅ OpenCV version: {cv2.__version__}")
print(f"   Build info: {cv2.getBuildInformation().split()[0]}")
EOF
```

Expected output:
```
✅ OpenCV version: 4.x.x
   Build info: ...
```

If you see `ModuleNotFoundError: No module named 'cv2'`, go back and try Option A or B above.

### 5. Create Models Directory

```bash
mkdir -p ~/frc-vision/models
```

### 6. Configure for Your Team

```bash
nano ~/frc-vision/config.json
```

Update these critical values:
```json
{
  "robot": {
    "team_number": 3267  // ← CHANGE TO YOUR TEAM NUMBER
  },
  "camera": {
    "device": 0,  // Check with v4l2-ctl if camera is /dev/video0
    "width": 640,
    "height": 480,
    "fps": 30
  },
  "yolo": {
    "enabled": false,  // ← Keep false until you train your model
    "model_path": "models/game_piece.pt",
    "confidence_threshold": 0.5
  },
  "apriltag": {
    "enabled": true,  // ← Keep true for AprilTag detection
    "tag_size": 0.1651
  },
  "debug": {
    "show_window": false  // ← false for headless operation
  }
}
```

Save and exit (`Ctrl+X`, `Y`, `Enter`)

---

## Part 7: Initial Testing

### 1. Test Camera Script

```bash
cd ~/frc-vision
source venv/bin/activate

python3 test_camera.py
```

You should see:
- Camera resolution
- FPS counter
- "Press 'q' to quit, 's' to save snapshot"

Press `q` to quit.

### 2. Test Vision System (AprilTag Only)

```bash
# Make sure config.json has:
# - "yolo.enabled": false
# - "apriltag.enabled": true
# - "debug.show_window": false (if headless)

python3 vision_system.py
```

You should see output like:
```
Starting FRC Vision System...
Team: 3267
Camera: 640x480 @ 30fps
YOLO: Disabled
AprilTag: Enabled
NetworkTables: Connecting to roborio-3267-frc.local...
FPS: 28.5 | Targets: 0 | NT: Disconnected
```

**If NetworkTables shows "Disconnected"**: That's OK for now (RoboRIO might not be on network). The vision system will still work.

**Test with AprilTag**:
- Print an AprilTag from: https://april.eecs.umich.edu/software/apriltag
- Hold it in front of camera
- You should see "Targets: 1" in the output

Press `Ctrl+C` to stop.

### 3. Verify Files Are Correct

```bash
cd ~/frc-vision
ls -la

# You should see:
# - vision_system.py
# - config.json
# - requirements.txt
# - collect_training_data.py
# - prepare_dataset.py
# - test_camera.py
# - venv/ (directory)
# - models/ (directory)
```

✅ **Checkpoint**: At this point, you have a working vision system that can detect AprilTags!

---

## Part 8: Data Collection & Model Training

Now we'll train a custom YOLO model to detect game pieces.

### Phase 1: Collect Training Images

```bash
cd ~/frc-vision
source venv/bin/activate

# Create training data directory
mkdir -p training_data
```

#### Collect Images for Each Game Piece Class

**For REEFSCAPE 2025** (adjust class names for your season):

```bash
# Collect coral images
python3 collect_training_data.py --class coral --lighting indoor

# Controls:
# - SPACE: Capture image
# - C: Toggle crosshair
# - G: Toggle grid
# - Q: Quit

# Tips while collecting:
# - Move piece around to different positions
# - Rotate to show different angles
# - Vary distance (close, medium, far)
# - Aim for 100-200 images minimum
```

Repeat for each class:
```bash
# Collect algae images
python3 collect_training_data.py --class algae --lighting indoor

# Collect negative examples (background without game pieces)
python3 collect_training_data.py --class negative --lighting indoor
```

#### Collect in Different Lighting Conditions

```bash
# Bright lighting
python3 collect_training_data.py --class coral --lighting bright
python3 collect_training_data.py --class algae --lighting bright

# Dim lighting
python3 collect_training_data.py --class coral --lighting dim
python3 collect_training_data.py --class algae --lighting dim

# Outdoor (if applicable)
python3 collect_training_data.py --class coral --lighting outdoor
python3 collect_training_data.py --class algae --lighting outdoor
```

**Goal**: 500-1000 total images (200-300 per game piece class)

#### Check Collection Statistics

```bash
python3 collect_training_data.py --stats
```

### Phase 2: Prepare Dataset

```bash
cd ~/frc-vision

# Organize images into train/val/test splits
python3 prepare_dataset.py --input training_data --output dataset

# This creates dataset.zip and shows summary
```

### Phase 3: Transfer Dataset to Computer

```bash
# From your computer (not on OrangePi):
scp orangepi@10.32.67.50:~/frc-vision/dataset_*.zip ~/Downloads/

# Unzip it:
cd ~/Downloads
unzip dataset_*.zip
```

### Phase 4: Label Images in Roboflow

1. **Create Roboflow Account**:
   - Go to https://roboflow.com
   - Sign up (free account)

2. **Create New Project**:
   - Click "Create New Project"
   - Project Type: **Object Detection**
   - Project Name: `FRC 2025 Game Pieces` (or your season)
   - Annotation Group: `Bounding Box`

3. **Upload Images**:
   - Click "Upload" → "Folder"
   - Select your `dataset/images` folder
   - Upload all images

4. **Assign Classes**:
   - Add classes: `coral`, `algae` (or your game pieces)
   - Click "Assign"

5. **Label Images** (Most time-consuming part):
   - Click "Annotate" on each image
   - Draw bounding box around each game piece
   - Assign correct class
   - Keyboard shortcuts:
     - `1` = first class (coral)
     - `2` = second class (algae)
     - `S` = save and next
   - Aim for at least 300-500 labeled images

6. **Generate Dataset**:
   - Click "Generate" → "New Version"
   - Preprocessing:
     - Auto-Orient: ✅
     - Resize: 640x640
   - Augmentation (creates more training data):
     - Flip: Horizontal ✅
     - Rotate: ±15°
     - Brightness: ±25%
     - Blur: Up to 1px
   - Split:
     - Train: 70%
     - Valid: 20%
     - Test: 10%
   - Click "Generate"

7. **Get Dataset Code**:
   - Format: **YOLOv8**
   - Copy the code snippet (you'll need it for training)

### Phase 5: Train Model on Google Colab

1. **Open Google Colab**:
   - Go to https://colab.research.google.com
   - Sign in with Google account
   - File → New Notebook

2. **Enable GPU**:
   - Runtime → Change runtime type
   - Hardware accelerator: **GPU** (T4)
   - Save

3. **Training Code**:

Create a new cell and paste:

```python
# Install dependencies
!pip install ultralytics roboflow

# Import libraries
from ultralytics import YOLO
from roboflow import Roboflow
import os

# Download dataset from Roboflow
# Get API key from: https://app.roboflow.com/settings/api
rf = Roboflow(api_key="YOUR_API_KEY_HERE")

# Get your workspace and project names from Roboflow URL
project = rf.workspace("YOUR_WORKSPACE").project("frc-2025-game-pieces")
dataset = project.version(1).download("yolov8")

# Print dataset location
print(f"Dataset downloaded to: {dataset.location}")
```

Run this cell (`Shift+Enter`)

Create another cell:

```python
# Initialize YOLO model
# yolov8n.pt = nano (fastest, best for OrangePi)
model = YOLO('yolov8n.pt')

# Train the model
results = model.train(
    data=f'{dataset.location}/data.yaml',
    epochs=100,           # More epochs = better accuracy
    imgsz=640,            # Image size
    batch=16,             # Adjust if GPU memory issues
    name='frc_game_pieces',
    patience=20,          # Early stopping
    save=True,
    plots=True,
    device=0              # Use GPU
)

print("Training complete!")
```

Run this cell - **Training will take 1-3 hours**

When done, create another cell:

```python
# Validate the model
metrics = model.val()
print(f"mAP50: {metrics.box.map50:.3f}")
print(f"mAP50-95: {metrics.box.map:.3f}")

# Test on a sample image
import glob
test_images = glob.glob(f'{dataset.location}/test/images/*.jpg')
if test_images:
    results = model.predict(test_images[0], conf=0.5)
    results[0].show()
```

4. **Download Trained Model**:
   - In Colab, click folder icon (left sidebar)
   - Navigate to: `runs/detect/frc_game_pieces/weights/`
   - Right-click `best.pt` → Download
   - This is your trained model!

### Phase 6: Deploy Model to OrangePi

```bash
# From your computer, copy model to OrangePi:
scp ~/Downloads/best.pt orangepi@10.32.67.50:~/frc-vision/models/game_piece.pt
```

On OrangePi, enable YOLO:
```bash
ssh orangepi@10.32.67.50
cd ~/frc-vision
nano config.json
```

Change:
```json
{
  "yolo": {
    "enabled": true,  // ← Change to true
    "model_path": "models/game_piece.pt",
    "confidence_threshold": 0.5
  }
}
```

### Phase 7: Test Your Model

```bash
cd ~/frc-vision
source venv/bin/activate

# Test vision system with your model
python3 vision_system.py

# Hold game pieces in front of camera
# Should see "Targets: 1" when detected
```

✅ **Checkpoint**: You now have a working vision system with custom game piece detection!

---

## Part 9: Auto-Start Configuration

Make the vision system start automatically when OrangePi boots.

### 1. Update Service File

```bash
cd ~/frc-vision
nano frc-vision.service
```

Verify it looks like this (adjust username if not `orangepi`):
```ini
[Unit]
Description=FRC Vision System
After=network.target

[Service]
Type=simple
User=orangepi
WorkingDirectory=/home/orangepi/frc-vision
Environment="PATH=/home/orangepi/frc-vision/venv/bin"
ExecStart=/home/orangepi/frc-vision/venv/bin/python3 /home/orangepi/frc-vision/vision_system.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 2. Install Service

```bash
# Copy service file to systemd
sudo cp frc-vision.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable frc-vision.service

# Start service now
sudo systemctl start frc-vision.service
```

### 3. Verify Service is Running

```bash
# Check status
sudo systemctl status frc-vision.service

# Should show:
# Active: active (running)

# View live logs
sudo journalctl -u frc-vision.service -f

# Press Ctrl+C to stop viewing logs
```

### 4. Test Auto-Start

```bash
# Reboot OrangePi
sudo reboot

# Wait for boot (~30 seconds)

# SSH back in
ssh orangepi@10.32.67.50

# Check if service started automatically
sudo systemctl status frc-vision.service
```

### 5. Service Management Commands

```bash
# Stop service
sudo systemctl stop frc-vision.service

# Start service
sudo systemctl start frc-vision.service

# Restart service (after config changes)
sudo systemctl restart frc-vision.service

# Disable auto-start
sudo systemctl disable frc-vision.service

# View recent logs
sudo journalctl -u frc-vision.service -n 100

# View live logs
sudo journalctl -u frc-vision.service -f
```

---

## Part 10: Robot Integration

### 1. Physical Installation

1. **Mount OrangePi on robot**:
   - Use vibration-damping mounting
   - Keep away from high-current components
   - Ensure good airflow

2. **Mount camera**:
   - Front-center of robot (best field of view)
   - Secure mounting (no wobble)
   - Protect lens from damage
   - Consider camera angle for game piece detection

3. **Connect cables**:
   - USB camera to OrangePi
   - Ethernet from OrangePi to robot network switch
   - Power to OrangePi (from robot PDP/PDH)
   - Secure all cables with zip ties

### 2. Network Configuration

The OrangePi should be on the robot's network:
- **Static IP**: `10.TE.AM.50` (already configured in Part 3)
- **Connected to**: Robot network switch (same network as RoboRIO)
- **RoboRIO IP**: `10.TE.AM.2`

### 3. Test NetworkTables Connection

```bash
# Power on robot
# SSH to OrangePi
ssh orangepi@10.32.67.50

# Check if vision service is running
sudo systemctl status frc-vision.service

# View logs - should show NetworkTables connected
sudo journalctl -u frc-vision.service -n 50 | grep NetworkTables

# Should see: "NetworkTables: Connected to roborio-XXXX-frc.local"
```

### 4. Verify Data on Driver Station

On your driver station computer:

**Using SmartDashboard**:
1. Connect to robot
2. View → Add → Choose Widget → Boolean Box
3. Properties → NetworkTables Key: `/Vision/HasTarget`
4. Repeat for:
   - `/Vision/Yaw` (Number)
   - `/Vision/Distance` (Number)
   - `/Vision/Area` (Number)
   - `/Vision/FPS` (Number)
   - `/Vision/TargetID` (Number)

**Using Shuffleboard**:
1. Sources tab → NetworkTables → Vision
2. Drag values to layout

**Test it**:
- Hold game piece in front of camera
- `HasTarget` should turn true
- `Yaw`, `Distance`, `Area` should show values
- `FPS` should be 20+

### 5. Test Robot Control

With robot code running:

**Left Bumper (Vision-Assisted Rotation)**:
- Hold game piece in view
- Press left bumper
- Drive with left stick
- Robot should auto-rotate to face target

**Right Bumper (Auto-Drive to Target)**:
- Hold game piece in view
- Press right bumper
- Robot should drive to target and rotate

**Test stale data protection**:
- Unplug camera
- Vision features should disable (fallback to manual)
- Plug camera back in
- Vision features should re-enable

---

## Part 11: Competition Preparation

### Pre-Competition Checklist

#### Hardware
- [ ] OrangePi powers on when robot is powered
- [ ] Camera is securely mounted (no wobble)
- [ ] All cables are secured with zip ties
- [ ] Ethernet cable is connected to robot network
- [ ] Camera lens is clean
- [ ] OrangePi has adequate cooling/airflow
- [ ] All mounting is vibration-resistant
- [ ] Camera field of view covers target area

#### Software
- [ ] Vision service starts automatically on boot
- [ ] YOLO detection works in competition lighting
- [ ] AprilTag detection works
- [ ] NetworkTables connects to RoboRIO reliably
- [ ] FPS is consistently 20+ during testing
- [ ] Distance measurements are accurate (±2 inches)
- [ ] No false positives from field elements
- [ ] Stale data timeout works (unplug camera test)

#### Network
- [ ] OrangePi has static IP configured
- [ ] Can ping RoboRIO from OrangePi
- [ ] NetworkTables data visible on driver station
- [ ] No network conflicts with other devices

#### Team Preparation
- [ ] Team knows how to restart vision service
- [ ] Team knows how to view logs
- [ ] Backup MicroSD card prepared and tested
- [ ] Printed troubleshooting guide
- [ ] Monitor setup for pit testing

### Emergency Procedures

**If vision system stops working**:

1. **Check service status**:
   ```bash
   ssh orangepi@10.32.67.50
   sudo systemctl status frc-vision.service
   ```

2. **Restart service**:
   ```bash
   sudo systemctl restart frc-vision.service
   ```

3. **View error logs**:
   ```bash
   sudo journalctl -u frc-vision.service -n 100
   ```

4. **Common issues**:
   - Camera disconnected: Check USB cable
   - Low FPS: Reduce resolution or confidence threshold
   - NetworkTables disconnected: Check ethernet cable
   - No detections: Check lighting, adjust confidence threshold

**Quick restart procedure** (tell team):
```bash
ssh orangepi@10.32.67.50
sudo systemctl restart frc-vision.service
```

### Backup & Recovery

**Create backup SD card**:
```bash
# On your computer (Linux)
# Insert OrangePi SD card
sudo dd if=/dev/sdX of=~/orangepi-backup.img bs=4M status=progress
sudo gzip ~/orangepi-backup.img

# Store orangepi-backup.img.gz safely
```

**Restore from backup**:
```bash
# Flash backup to new SD card
sudo gunzip -c ~/orangepi-backup.img.gz | sudo dd of=/dev/sdX bs=4M status=progress
```

### Performance Optimization

If FPS is low (<20):

1. **Reduce camera resolution**:
   ```json
   "camera": {
     "width": 320,
     "height": 240
   }
   ```

2. **Increase confidence threshold**:
   ```json
   "yolo": {
     "confidence_threshold": 0.6
   }
   ```

3. **Disable debug window** (should already be off):
   ```json
   "debug": {
     "show_window": false
   }
   ```

4. **Check CPU usage**:
   ```bash
   ssh orangepi@10.32.67.50
   htop
   # vision_system.py should be <80% CPU
   ```

### Competition Day Workflow

**Morning Setup**:
1. Power on robot
2. Verify vision service is running
3. Check FPS and detection on SmartDashboard
4. Test robot control with vision features
5. Note any issues for adjustment

**Between Matches**:
1. Quick visual check of camera (clean lens if needed)
2. Glance at SmartDashboard to verify FPS/targets
3. No changes unless critical issue

**After Competition**:
1. Collect feedback from drivers
2. Note any missed detections or false positives
3. Collect more training data if needed
4. Retrain model if necessary

---

## Continuous Improvement

### After Each Competition/Practice

**Collect more data for cases where detection failed**:
```bash
ssh orangepi@10.32.67.50
cd ~/frc-vision
source venv/bin/activate

# Collect images where detection was poor
python3 collect_training_data.py --class coral --lighting competition
python3 collect_training_data.py --class algae --lighting competition
```

**Retrain with new data**:
1. Prepare updated dataset: `python3 prepare_dataset.py`
2. Transfer to computer
3. Add to Roboflow project
4. Retrain on Google Colab
5. Deploy new `best.pt` model
6. Test and compare performance

### Model Versioning

Keep multiple model versions:
```bash
cd ~/frc-vision/models

# Backup current model
cp game_piece.pt game_piece_v1.pt

# Deploy new model
# (copy new best.pt as game_piece.pt)

# Test new model
# If worse, revert:
cp game_piece_v1.pt game_piece.pt
sudo systemctl restart frc-vision.service
```

---

## Troubleshooting

### Camera Issues

**Camera not detected**:
```bash
# Check USB connection
lsusb

# Check video devices
ls -l /dev/video*

# Check kernel logs
dmesg | grep -i video

# Try different USB port
```

**Low FPS**:
- Reduce resolution
- Use lighter YOLO model (yolov8n)
- Increase confidence threshold
- Check CPU usage with `htop`

### OpenCV Installation Issues

**`ModuleNotFoundError: No module named 'cv2'` in virtual environment**:
```bash
cd ~/frc-vision
source venv/bin/activate

# Test if opencv is available
python3 -c "import cv2; print(cv2.__version__)"

# If it fails, try using system site-packages:
deactivate
rm -rf venv
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install ultralytics numpy pynetworktables dt-apriltags Pillow

# Test again
python3 -c "import cv2; print(cv2.__version__)"
```

**`pip install opencv-python` takes forever or fails on ARM**:
```bash
# Option 1: Use system opencv (recommended)
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Option 2: Use headless version
pip install opencv-python-headless

# Option 3: Install prebuilt wheel (if available for your platform)
pip install opencv-contrib-python
```

**OpenCV works with system Python but not in venv**:
```bash
# Recreate venv with system site-packages
cd ~/frc-vision
deactivate
rm -rf venv
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install -r requirements.txt
```

### NetworkTables Issues

**Can't connect to RoboRIO**:
```bash
# Ping RoboRIO
ping 10.32.67.2

# Check ethernet cable
ip addr show eth0

# Verify team number in config.json
cat config.json | grep team_number
```

### Service Issues

**Service won't start**:
```bash
# Check logs for errors
sudo journalctl -u frc-vision.service -n 100

# Test manually
cd ~/frc-vision
source venv/bin/activate
python3 vision_system.py
# Look for error messages
```

**Service crashes**:
```bash
# View crash logs
sudo journalctl -u frc-vision.service | grep -i error

# Common issues:
# - Missing dependencies: pip install -r requirements.txt
# - Wrong camera device: update config.json
# - Model not found: check models/ directory
```

### Detection Issues

**No detections**:
- Check YOLO enabled: `"yolo.enabled": true`
- Lower confidence: `"confidence_threshold": 0.3`
- Verify model exists: `ls -la models/game_piece.pt`
- Check lighting conditions
- Test with training images

**False positives**:
- Increase confidence: `"confidence_threshold": 0.6`
- Collect negative examples and retrain
- Check model quality metrics (mAP50)

**Inconsistent detections**:
- Collect more diverse training data
- Add motion blur examples
- Train for more epochs

---

## Next Season

When new game pieces are revealed:

1. **Clear old data** (optional):
   ```bash
   mv training_data training_data_2025
   mkdir training_data
   ```

2. **Collect new game piece images**:
   ```bash
   python3 collect_training_data.py --class newpiece1
   python3 collect_training_data.py --class newpiece2
   ```

3. **Follow training steps** (Part 8)

4. **Deploy new model**

5. **Update documentation** with new class names

---

## Summary

You now have a complete, autonomous vision system running on OrangePi!

**What it does**:
- ✅ Detects game pieces using custom YOLO8 model
- ✅ Detects AprilTags for positioning
- ✅ Publishes target data to NetworkTables
- ✅ Enables vision-assisted driving on robot
- ✅ Runs autonomously on robot startup
- ✅ Provides stale data protection

**Key files**:
- `~/frc-vision/vision_system.py` - Main vision processor
- `~/frc-vision/config.json` - Configuration
- `~/frc-vision/models/game_piece.pt` - Your trained model
- `/etc/systemd/system/frc-vision.service` - Auto-start service

**Key commands**:
```bash
# Restart vision service
sudo systemctl restart frc-vision.service

# View logs
sudo journalctl -u frc-vision.service -f

# Collect more training data
cd ~/frc-vision && source venv/bin/activate
python3 collect_training_data.py --class gamepiece

# SSH to OrangePi
ssh orangepi@10.32.67.50
```

**Good luck at competition!** 🤖🏆
