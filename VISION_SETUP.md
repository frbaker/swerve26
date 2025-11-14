# Custom Vision System Setup

## Overview
This robot code has been updated to work with a custom vision system running on an OrangePi (or similar coprocessor) instead of PhotonVision. The vision system communicates target information via NetworkTables.

## NetworkTables Structure

Your OrangePi vision system must publish the following values to NetworkTables:

| NetworkTables Key | Type | Description | Units/Range |
|-------------------|------|-------------|-------------|
| `/Vision/HasTarget` | boolean | Whether a valid target is detected | true/false |
| `/Vision/Yaw` | double | Horizontal angle to target | degrees (+ = right, - = left) |
| `/Vision/Pitch` | double | Vertical angle to target | degrees (+ = up, - = down) |
| `/Vision/Distance` | double | Distance from robot to target | meters |
| `/Vision/Area` | double | Target area in camera view | percentage (0-100) |
| `/Vision/TargetID` | int | Optional target identifier | integer (-1 if not used) |

## Robot Functionality

The robot uses vision data for the following features:

### 1. Vision-Assisted Rotation (Left Bumper)
- Driver controls forward/backward/strafe movement with left joystick
- Robot automatically rotates to face target using PID control
- Falls back to normal driver control if no target or data is stale
- Uses target `yaw` for rotation

### 2. Full Auto-Drive (Right Bumper)
- Robot automatically rotates AND drives to the target using PID control
- Completely autonomous - no driver input needed
- Falls back to normal driver control if no target or data is stale
- Uses target `yaw`, `distance`, and `area`

### 3. Vision-Assisted Drive (B Button)
- Same as left bumper - driver controls movement, robot auto-rotates
- Uses target `yaw`

### 4. Elevator Safety (Commented Out)
- Optional feature to prevent elevator damage when too close to target
- Uses target `area` to determine proximity

### Data Freshness Detection
The robot checks if vision data is fresh (updated within 0.5 seconds). If data becomes stale or the target is lost, control automatically returns to the driver. This prevents the robot from acting on old vision information.

## OrangePi Setup Requirements

1. **Network Configuration**
   - Connect OrangePi to robot network (same network as RoboRIO)
   - Ensure NetworkTables client is configured to connect to RoboRIO

2. **Vision Processing**
   - Your custom vision code should:
     - Detect targets (game pieces, AprilTags, etc.)
     - Calculate yaw and pitch angles to target
     - Calculate or estimate distance to target
     - Calculate target area percentage
     - Publish all values to NetworkTables at the paths specified above

3. **Update Rate**
   - Recommend publishing at 20-50 Hz for smooth operation
   - **IMPORTANT**: Must publish continuously even when no target is detected
   - Set `HasTarget` to `false` when no valid target is detected
   - Robot checks data freshness - stale data (>0.5s old) will be ignored

## Example Python Code (OrangePi)

```python
from networktables import NetworkTables
import time

# Initialize NetworkTables
NetworkTables.initialize(server='roboRIO-TEAM-frc.local')  # Replace TEAM with your team number
vision_table = NetworkTables.getTable('Vision')

# In your vision processing loop:
def publish_target_data(has_target, yaw, pitch, distance, area, target_id=-1):
    vision_table.putBoolean('HasTarget', has_target)
    vision_table.putNumber('Yaw', yaw)
    vision_table.putNumber('Pitch', pitch)
    vision_table.putNumber('Distance', distance)
    vision_table.putNumber('Area', area)
    vision_table.putNumber('TargetID', target_id)

# Example: No target detected
publish_target_data(False, 0, 0, 0, 0)

# Example: Target detected at 15 degrees right, 2 meters away
publish_target_data(True, 15.0, 5.0, 2.0, 25.0)
```

## Code Changes Made

1. **Removed PhotonVision Dependency**
   - Deleted `vendordeps/photonlib.json`
   - Removed PhotonUtils distance calculations

2. **Created VisionSystem Class**
   - `src/main/include/subsystems/VisionSystem.h`
   - `src/main/cpp/subsystems/VisionSystem.cpp`
   - Simple interface to read from NetworkTables

3. **Updated RobotContainer**
   - Replaced `PhotonCamera` with `VisionSystem`
   - Updated all button bindings to use new vision data structure
   - Removed reef-specific AprilTag filtering (OrangePi handles target selection)

4. **Updated Constants**
   - Commented out reef AprilTag ID array
   - Noted that camera constants are for reference only

## Testing Without Vision

When testing robot code without the OrangePi connected:
- `HasTarget` will default to `false`
- Robot will fall back to normal driver control
- No errors will occur, vision features simply won't activate

## Troubleshooting

### Vision features not working
1. Check NetworkTables connection from OrangePi to RoboRIO
2. Verify all required keys are being published
3. Check SmartDashboard/Shuffleboard for `targetArea` and `targetDistance` values

### Robot behavior seems incorrect
1. Verify yaw angles are correct sign (+ = right, - = left)
2. Verify distance is in meters
3. Check that `HasTarget` is only `true` when target is reliably detected

## Future Enhancements

Consider adding these features to your OrangePi vision system:
- Multiple target tracking (publish best target)
- Target confidence scores
- FPS/latency monitoring
- Camera health monitoring
- LED status indicators
