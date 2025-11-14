# OrangePi Vision System Setup Guide

Complete setup instructions for running the FRC vision system on an OrangePi with camera.

## Hardware Requirements

- **OrangePi** (tested on OrangePi 5, but should work on most models)
- **USB Camera** (or CSI camera if supported)
- **MicroSD Card** (32GB+ recommended)
- **Power Supply** (appropriate for your OrangePi model)
- **Ethernet Cable** (for robot network connection)

## Part 1: OrangePi Operating System Setup

### 1. Install Operating System

1. Download the latest **Ubuntu** or **Debian** image for your OrangePi model
2. Flash to MicroSD card using:
   - **Raspberry Pi Imager** (easiest)
   - **Etcher** (cross-platform)
   - `dd` command (Linux)

3. Boot the OrangePi and complete initial setup

### 2. Initial System Configuration

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Set hostname (optional but recommended)
sudo hostnamectl set-hostname orangepi-vision

# Install basic tools
sudo apt install -y git vim curl wget htop
```

### 3. Configure Static IP (Optional but Recommended)

For consistent robot network connection:

```bash
# Edit netplan config (Ubuntu)
sudo nano /etc/netplan/01-netcfg.yaml
```

Add configuration (adjust for your robot network):
```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: no
      addresses:
        - 10.TE.AM.50/24  # Replace TE.AM with your team number
      gateway4: 10.TE.AM.1
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
```

Apply configuration:
```bash
sudo netplan apply
```

## Part 2: Install Python and Dependencies

### 1. Install Python 3.11+

```bash
# Check Python version
python3 --version

# If older than 3.11, install from deadsnakes PPA (Ubuntu)
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Set as default (optional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

### 2. Install System Dependencies

```bash
# OpenCV dependencies
sudo apt install -y \
    libopencv-dev \
    python3-opencv \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    gfortran

# AprilTag dependencies
sudo apt install -y \
    libboost-all-dev \
    libeigen3-dev

# Camera utilities
sudo apt install -y v4l-utils
```

### 3. Setup Python Virtual Environment

```bash
# Create project directory
mkdir -p ~/frc-vision
cd ~/frc-vision

# Copy vision files
# (Transfer vision_system.py, config.json, requirements.txt to this directory)

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r requirements.txt
```

## Part 3: Camera Setup

### 1. Identify Camera Device

```bash
# List video devices
ls -l /dev/video*

# Check camera info
v4l2-ctl --list-devices

# Test camera capabilities
v4l2-ctl -d /dev/video0 --list-formats-ext
```

### 2. Test Camera

```bash
# Activate virtual environment if not already
source ~/frc-vision/venv/bin/activate

# Test camera with Python
python3 << EOF
import cv2
camera = cv2.VideoCapture(0)
ret, frame = camera.read()
if ret:
    print(f"Camera working! Frame shape: {frame.shape}")
else:
    print("Camera NOT working!")
camera.release()
EOF
```

### 3. Optimize Camera Settings

```bash
# Disable auto-exposure for consistent performance
v4l2-ctl -d /dev/video0 --set-ctrl=exposure_auto=1
v4l2-ctl -d /dev/video0 --set-ctrl=exposure_absolute=100

# Disable auto-focus if available
v4l2-ctl -d /dev/video0 --set-ctrl=focus_auto=0

# Set white balance
v4l2-ctl -d /dev/video0 --set-ctrl=white_balance_temperature_auto=0
```

## Part 4: Configure Vision System

### 1. Edit Configuration File

```bash
cd ~/frc-vision
nano config.json
```

Update these critical values:
- `robot.team_number`: Your FRC team number
- `camera.device`: Camera device number (usually 0)
- `camera.width`, `camera.height`, `camera.fps`: Match your camera
- `yolo.enabled`: Set to `false` until you train your model
- `apriltag.enabled`: Set to `true` for AprilTag-only operation
- `debug.show_window`: Set to `false` for headless operation

### 2. Camera Calibration (Important!)

The default camera matrix is approximate. For accurate distance measurements, calibrate your camera:

```bash
# Download calibration script
wget https://raw.githubusercontent.com/opencv/opencv/master/samples/python/calibrate.py

# Print a checkerboard pattern and run calibration
python3 calibrate.py --square_size 0.025 --pattern_width 9 --pattern_height 6

# Update camera.matrix in config.json with the output
```

## Part 5: Test Vision System

### 1. Test with Debug Window

```bash
cd ~/frc-vision
source venv/bin/activate

# Run with debug window (need display)
python3 vision_system.py
```

You should see:
- Camera feed with overlays
- FPS counter
- Target detection (if targets visible)

Press 'q' to quit.

### 2. Test NetworkTables Connection

Make sure:
1. OrangePi is on same network as RoboRIO
2. Update `config.json` with correct team number
3. RoboRIO is powered on

Check NetworkTables connection in the console output.

## Part 6: Auto-Start on Boot

### 1. Create Systemd Service

```bash
sudo nano /etc/systemd/system/frc-vision.service
```

Add this content (adjust paths as needed):

```ini
[Unit]
Description=FRC Vision System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/frc-vision
Environment="PATH=/home/pi/frc-vision/venv/bin"
ExecStart=/home/pi/frc-vision/venv/bin/python3 /home/pi/frc-vision/vision_system.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable frc-vision.service

# Start service now
sudo systemctl start frc-vision.service

# Check status
sudo systemctl status frc-vision.service

# View logs
sudo journalctl -u frc-vision.service -f
```

### 3. Service Management Commands

```bash
# Stop service
sudo systemctl stop frc-vision.service

# Restart service
sudo systemctl restart frc-vision.service

# Disable auto-start
sudo systemctl disable frc-vision.service

# View recent logs
sudo journalctl -u frc-vision.service -n 100
```

## Part 7: Network Configuration for Competition

### For Ethernet Connection (Recommended)

The OrangePi should connect via Ethernet to the robot's network switch.

```bash
# Verify connection
ping 10.TE.AM.2  # RoboRIO address (replace TE.AM with team number)

# Test NetworkTables
python3 << EOF
from networktables import NetworkTables
NetworkTables.initialize(server='roborio-TEAM-frc.local')  # Replace TEAM
import time
time.sleep(2)
print("Connected!" if NetworkTables.isConnected() else "NOT Connected")
EOF
```

### For WiFi Connection (Not Recommended for Competition)

```bash
# Connect to robot WiFi
sudo nmcli device wifi connect "TEAM-Robot" password "your-password"
```

## Part 8: Performance Optimization

### 1. Disable Desktop Environment (Recommended for Headless)

```bash
# Set to boot to console
sudo systemctl set-default multi-user.target

# Reboot
sudo reboot

# To re-enable desktop
sudo systemctl set-default graphical.target
```

### 2. CPU Governor Settings

```bash
# Set to performance mode
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Make permanent
sudo nano /etc/rc.local
```

Add before `exit 0`:
```bash
echo performance > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### 3. Increase Swap (if needed)

```bash
# Check current swap
free -h

# Increase swap to 2GB
sudo swapoff -a
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Troubleshooting

### Camera Not Detected

```bash
# Check if camera is recognized
lsusb  # Should show your USB camera
dmesg | grep video  # Check kernel messages

# Try different USB port
# Check camera power requirements
```

### Low FPS Performance

```bash
# Reduce camera resolution in config.json
# Reduce YOLO confidence threshold
# Disable debug window
# Use lighter YOLO model (yolov8n instead of yolov8m)
```

### NetworkTables Not Connecting

```bash
# Check network connection
ping 10.TE.AM.2

# Check firewall
sudo ufw status

# Check team number in config.json
# Verify RoboRIO is running and has NetworkTables enabled
```

### Service Won't Start

```bash
# Check logs
sudo journalctl -u frc-vision.service -n 50

# Test manually
cd ~/frc-vision
source venv/bin/activate
python3 vision_system.py

# Check file permissions
ls -la vision_system.py
chmod +x vision_system.py
```

## Monitoring and Debugging

### View Real-Time Logs

```bash
# Follow service logs
sudo journalctl -u frc-vision.service -f

# Check system resources
htop

# Monitor network
sudo iftop
```

### Remote Access via SSH

```bash
# From your computer
ssh pi@10.TE.AM.50  # Use configured IP

# Enable SSH if not already
sudo systemctl enable ssh
sudo systemctl start ssh
```

## Competition Day Checklist

- [ ] OrangePi powers on automatically
- [ ] Vision service starts automatically
- [ ] Camera is securely mounted
- [ ] Ethernet cable is connected
- [ ] NetworkTables connects to RoboRIO
- [ ] FPS is stable (>20 fps)
- [ ] Target detection works reliably
- [ ] Distance measurements are accurate
- [ ] All cables are secured with zip ties
- [ ] OrangePi is protected from damage

## Next Steps

After basic setup is complete:
1. See `YOLO8_TRAINING.md` for training your own game piece detector
2. Calibrate camera for accurate distance measurements
3. Tune target selection and tracking parameters
4. Test thoroughly before competition!
