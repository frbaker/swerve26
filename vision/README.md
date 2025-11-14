# FRC Vision System - Team 3267

Complete custom vision system for FRC robot using OrangePi, YOLO8, and AprilTag detection.

## Overview

This vision system replaces PhotonVision with a custom solution that:
- ✅ Detects game pieces using YOLO8 (coral and algae)
- ✅ Detects AprilTags for precise positioning
- ✅ Publishes target data to NetworkTables
- ✅ Works with your PhotonDrive and TractorBeam robot code
- ✅ Provides stale data detection (0.5s timeout)
- ✅ Runs autonomously on OrangePi

## How It Works with Your Robot

### NetworkTables Data Flow

```
OrangePi Vision System → NetworkTables → RoboRIO → Robot Actions
```

The vision system publishes these values to `/Vision/` table:

| Key | Type | Robot Usage |
|-----|------|-------------|
| `HasTarget` | boolean | Enables vision-assisted driving |
| `Yaw` | double | **Left Bumper**: Auto-rotate to face target<br>**Right Bumper**: Auto-rotate during approach |
| `Pitch` | double | Future use (elevation targeting) |
| `Distance` | double | **Right Bumper**: Auto-drive to target distance |
| `Area` | double | **Right Bumper**: Target proximity estimation |
| `TargetID` | int | AprilTag ID (if applicable) |
| `FPS` | double | Performance monitoring |

### Robot Controls (from RobotContainer.cpp)

**Left Bumper (Vision-Assisted Rotation)**
```cpp
// Driver controls movement, robot auto-rotates to face target
if (target.hasTarget && target.isDataFresh) {
    m_drive.PhotonDrive(joystick_forward, joystick_strafe, target.yaw);
}
```
- Uses `Yaw` for rotation PID
- Driver controls speed and direction with left joystick
- Fallback to manual if no target or data stale

**Right Bumper (Full Auto-Drive)**
```cpp
// Robot auto-rotates AND auto-drives to target
if (target.hasTarget && target.isDataFresh) {
    m_drive.TractorBeam(target.distance, false, target.yaw, target.area);
}
```
- Uses `Yaw` for rotation PID
- Uses `Distance` for drive PID
- Uses `Area` for proximity estimation
- Fallback to manual if no target or data stale

**B Button (Same as Left Bumper)**
- Vision-assisted rotation only
- Driver controls movement

### Data Freshness Detection

The robot checks if vision data was updated within 0.5 seconds:
- ✅ Fresh data: Vision features active
- ❌ Stale data: Fallback to manual control

This prevents the robot from acting on old/incorrect vision information.

## Files in This Directory

### Core System
- **`vision_system.py`** - Main vision processing script
- **`config.json`** - Configuration (Team 3267 setup)
- **`requirements.txt`** - Python dependencies
- **`frc-vision.service`** - Systemd service for auto-start

### Helper Scripts
- **`test_camera.py`** - Test camera and check FPS
- **`extract_frames.py`** - Extract frames from video for training
- **`camera_calibration.py`** - Calibrate camera for accurate distance

### Documentation
- **`ORANGEPI_SETUP.md`** - Complete OrangePi setup guide
- **`YOLO8_TRAINING.md`** - Train custom YOLO8 model for game pieces
- **`README.md`** - This file

## Quick Start

### 1. Setup OrangePi
Follow **`ORANGEPI_SETUP.md`** for complete setup instructions:
- Install OS and dependencies
- Setup camera
- Install Python packages
- Configure auto-start service

### 2. Test Basic Functionality

```bash
# SSH to OrangePi
ssh pi@10.32.67.50

# Go to vision directory
cd ~/frc-vision

# Test camera
python3 test_camera.py

# Test vision system (AprilTags only, no YOLO yet)
python3 vision_system.py
```

### 3. Train YOLO Model (After Game Reveal)

Follow **`YOLO8_TRAINING.md`** to train a custom model:
1. Collect 500+ images of game pieces
2. Label images in Roboflow
3. Train YOLO8 model on Google Colab
4. Deploy to OrangePi

### 4. Deploy to Robot

```bash
# Enable service
sudo systemctl enable frc-vision.service
sudo systemctl start frc-vision.service

# Check status
sudo systemctl status frc-vision.service

# View logs
sudo journalctl -u frc-vision.service -f
```

## Configuration

Edit `config.json` to adjust:

### Robot Settings
```json
{
  "robot": {
    "team_number": 3267
  }
}
```

### Camera Settings
```json
{
  "camera": {
    "device": 0,
    "width": 640,
    "height": 480,
    "fps": 30
  }
}
```

### Detection Settings
```json
{
  "yolo": {
    "enabled": true,        // false until model trained
    "model_path": "models/game_piece.pt",
    "confidence_threshold": 0.5
  },
  "apriltag": {
    "enabled": true,        // AprilTags always available
    "tag_size": 0.1651      // 6.5 inches in meters
  }
}
```

### Target Priority
```json
{
  "target_priority": "both"  // "yolo", "apriltag", or "both"
}
```

- **"yolo"**: Prioritize game pieces
- **"apriltag"**: Prioritize AprilTags (for precise positioning)
- **"both"**: Detect either (best for versatility)

## Testing

### Test Camera
```bash
python3 test_camera.py
# Press 'q' to quit, 's' to save snapshot
```

### Test Vision System
```bash
# With debug window (local testing)
python3 vision_system.py

# Headless (robot testing)
# Set "debug.show_window": false in config.json
python3 vision_system.py
```

### Test NetworkTables Connection
```bash
# Check if data is publishing
python3 << EOF
from networktables import NetworkTables
import time

NetworkTables.initialize(server='roborio-3267-frc.local')
time.sleep(2)

vision = NetworkTables.getTable('Vision')
print(f"HasTarget: {vision.getBoolean('HasTarget', False)}")
print(f"Yaw: {vision.getNumber('Yaw', 0)}")
print(f"Distance: {vision.getNumber('Distance', 0)}")
print(f"FPS: {vision.getNumber('FPS', 0)}")
EOF
```

### Monitor on SmartDashboard

Add these widgets to SmartDashboard/Shuffleboard:
- **Vision/HasTarget** (Boolean)
- **Vision/Yaw** (Number)
- **Vision/Distance** (Number)
- **Vision/Area** (Number)
- **Vision/FPS** (Number)
- **visionActive** (Boolean) - From robot code

## Performance Tuning

### Target FPS
- ✅ **30+ FPS**: Excellent
- ✅ **20-30 FPS**: Good
- ⚠️  **10-20 FPS**: Acceptable
- ❌ **<10 FPS**: Too slow

### If FPS is Low

1. **Use smaller YOLO model**:
   - yolov8n (nano) - fastest ✅
   - yolov8s (small) - slower
   - yolov8m (medium) - slowest

2. **Reduce camera resolution**:
   ```json
   "camera": {
     "width": 320,
     "height": 240
   }
   ```

3. **Disable debug window**:
   ```json
   "debug": {
     "show_window": false
   }
   ```

4. **Increase confidence threshold**:
   ```json
   "yolo": {
     "confidence_threshold": 0.6
   }
   ```

## Troubleshooting

### No targets detected
- Check `yolo.enabled` is `true` (after training)
- Lower `confidence_threshold` (try 0.3)
- Verify model path is correct
- Check lighting conditions

### NetworkTables not connecting
```bash
# Ping RoboRIO
ping 10.32.67.2

# Check team number in config.json
# Verify RoboRIO is on same network
```

### Camera not working
```bash
# Check camera device
ls -l /dev/video*

# Test with v4l2
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --list-formats-ext

# Try different device number in config.json
```

### Service won't start
```bash
# Check logs
sudo journalctl -u frc-vision.service -n 100

# Test manually
cd ~/frc-vision
source venv/bin/activate
python3 vision_system.py
```

## Competition Checklist

Before competition:
- [ ] OrangePi boots automatically
- [ ] Vision service starts on boot
- [ ] NetworkTables connects to RoboRIO
- [ ] FPS is 20+ consistently
- [ ] Target detection works in field lighting
- [ ] Distance measurements are accurate
- [ ] Stale data detection works (unplug camera, check fallback)
- [ ] All cables secured with zip ties
- [ ] Backup SD card prepared
- [ ] Team knows how to restart service: `sudo systemctl restart frc-vision`

## Development Workflow

### Making Changes

1. Edit files on OrangePi
2. Test manually:
   ```bash
   cd ~/frc-vision
   source venv/bin/activate
   python3 vision_system.py
   ```
3. If working, restart service:
   ```bash
   sudo systemctl restart frc-vision.service
   ```

### Updating Model

```bash
# Copy new model to OrangePi
scp best.pt pi@10.32.67.50:~/frc-vision/models/game_piece.pt

# Restart service
ssh pi@10.32.67.50 "sudo systemctl restart frc-vision.service"
```

### Viewing Logs

```bash
# Follow logs in real-time
sudo journalctl -u frc-vision.service -f

# Last 100 lines
sudo journalctl -u frc-vision.service -n 100

# Logs with timestamps
sudo journalctl -u frc-vision.service --since "10 minutes ago"
```

## How Robot Code Uses Vision Data

### PhotonDrive (Left Bumper & B Button)
```cpp
void DriveSubsystem::PhotonDrive(
    units::meters_per_second_t forward,  // From driver joystick
    units::meters_per_second_t strafe,   // From driver joystick
    units::degree_t yaw                  // From vision system!
) {
    // PID control to rotate robot to face target
    // Driver maintains full control of movement
}
```

### TractorBeam (Right Bumper)
```cpp
void DriveSubsystem::TractorBeam(
    units::meter_t distance,  // From vision system!
    bool left,                // Offset direction
    units::degree_t yaw,      // From vision system!
    double targetArea         // From vision system!
) {
    // PID control for both rotation AND driving
    // Fully autonomous approach to target
}
```

### Stale Data Protection
```cpp
VisionTarget target = GetTarget();
if (target.hasTarget && target.isDataFresh) {
    // Use vision
} else {
    // Fallback to manual
}
```

## Support

- **Documentation**: See ORANGEPI_SETUP.md and YOLO8_TRAINING.md
- **Chief Delphi**: https://www.chiefdelphi.com/
- **FRC Discord**: Computer Vision channel
- **Team 3267**: Contact your programming lead

## License

Based on WPILib and Ultralytics YOLO8 (both GPL-3.0)

---

**Team 3267 - Ready for REEFSCAPE 2025! 🤖🌊**
