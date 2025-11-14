# Camera Streaming to Driver Station

The vision system can stream live camera feed with detection overlays to your driver station, allowing you to see what the vision system sees in real-time.

## What You See in the Stream

The camera stream includes:
- ✅ Live camera feed
- ✅ Bounding boxes around detected game pieces (YOLO)
- ✅ AprilTag detection markers
- ✅ Selected target highlighted
- ✅ Target information overlays (yaw, distance, FPS)
- ✅ Crosshairs and reference markers

## Configuration

### Enable Streaming

Edit `config.json`:

```json
{
  "streaming": {
    "enabled": true,
    "port": 1181,
    "quality": 80
  }
}
```

**Settings:**
- `enabled`: Set to `true` to enable streaming
- `port`: Port number (1181-1190 recommended for FRC)
- `quality`: JPEG quality 0-100 (80 = good balance of quality/bandwidth)

### Adjust Quality vs Bandwidth

**High quality** (more bandwidth):
```json
"quality": 90
```

**Low bandwidth** (lower quality):
```json
"quality": 60
```

**Competition recommendation**: 70-80 for balance

## Viewing the Stream

### Option 1: Shuffleboard (Recommended)

1. **Add Camera Widget**:
   - Sources → CameraServer → Vision System
   - Drag to your layout

2. **Alternative Method**:
   - Widgets → Add Widget → Camera Stream
   - Properties → Camera: "Vision System"

3. **Layout**:
   - Place alongside NetworkTables data (Yaw, Distance, etc.)
   - Resize as needed

### Option 2: SmartDashboard

1. **Add Camera Feed**:
   - View → Add → Camera Stream
   - Select "Vision System"

### Option 3: Web Browser

Navigate to:
```
http://10.TE.AM.50:1181/?action=stream
```

**For Team 3267**:
```
http://10.32.67.50:1181/?action=stream
```

Replace `TE.AM` with your team number in format:
- Team 254 → `10.2.54.50:1181`
- Team 1234 → `10.12.34.50:1181`

### Option 4: Dashboard Cameras Tab

In FRC Driver Station:
- Cameras tab should auto-detect the stream
- May require manual configuration with IP:port

## Stream URL Format

The standard MJPEG stream URL is:
```
http://<orangepi-ip>:<port>/?action=stream
```

For default configuration:
```
http://10.32.67.50:1181/?action=stream
```

## Troubleshooting

### No Stream Visible

**Check if streaming is enabled:**
```bash
ssh orangepi@10.32.67.50
cat ~/frc-vision/config.json | grep -A 5 streaming
```

Should show:
```json
"streaming": {
  "enabled": true,
  ...
}
```

**Check if vision service is running:**
```bash
sudo systemctl status frc-vision.service
```

**Check logs for streaming errors:**
```bash
sudo journalctl -u frc-vision.service -n 50 | grep -i stream
```

Should see:
```
Camera stream started on port 1181
View stream at: http://10.32.67.50:1181/?action=stream
```

### Stream Stutters or Lags

**Reduce quality:**
```json
"streaming": {
  "quality": 60
}
```

**Reduce resolution:**
```json
"camera": {
  "width": 320,
  "height": 240
}
```

**Check network bandwidth:**
```bash
# On OrangePi
ping 10.32.67.5  # Driver station
# Should have <5ms latency, no packet loss
```

### "cscore not available" Error

If you see this in logs:

```bash
ssh orangepi@10.32.67.50
cd ~/frc-vision
source venv/bin/activate
pip install robotpy-cscore

# Restart service
sudo systemctl restart frc-vision.service
```

### Stream Works Locally but Not on Robot

**Check firewall (if enabled):**
```bash
sudo ufw status
# If active, allow port:
sudo ufw allow 1181/tcp
```

**Check network connection:**
```bash
# From driver station computer
ping 10.32.67.50

# From OrangePi
ping 10.32.67.5  # or your driver station IP
```

**Verify port number:**
```bash
# Check what ports are listening
sudo netstat -tlnp | grep 1181
```

### Multiple Streams (Advanced)

If you want multiple camera streams:

```json
"streaming": {
  "enabled": true,
  "port": 1181,
  "quality": 80
}
```

Then in vision_system.py, you could create multiple streams on different ports (requires code modification).

## Performance Impact

### Bandwidth Usage

Approximate bandwidth per resolution/quality:

| Resolution | Quality | Bandwidth | FPS Impact |
|-----------|---------|-----------|------------|
| 320x240   | 60      | ~500 KB/s | Minimal    |
| 640x480   | 60      | ~1.5 MB/s | Low        |
| 640x480   | 80      | ~2.5 MB/s | Low        |
| 640x480   | 90      | ~3.5 MB/s | Medium     |

**Robot bandwidth budget**: FRC allows ~7 Mbps total

### CPU Impact

Streaming adds ~5-10% CPU usage for JPEG compression.

**Monitor CPU usage:**
```bash
ssh orangepi@10.32.67.50
htop
# Look for vision_system.py process
```

If CPU usage is >80%, consider:
- Reducing resolution
- Reducing quality
- Reducing FPS

### Recommended Settings for Competition

**Balanced** (recommended for most teams):
```json
{
  "camera": {
    "width": 640,
    "height": 480,
    "fps": 30
  },
  "streaming": {
    "enabled": true,
    "port": 1181,
    "quality": 75
  }
}
```

**Low bandwidth** (congested network):
```json
{
  "camera": {
    "width": 320,
    "height": 240,
    "fps": 20
  },
  "streaming": {
    "enabled": true,
    "port": 1181,
    "quality": 60
  }
}
```

**High quality** (practice/debugging):
```json
{
  "camera": {
    "width": 640,
    "height": 480,
    "fps": 30
  },
  "streaming": {
    "enabled": true,
    "port": 1181,
    "quality": 90
  }
}
```

## Disabling Stream (Save Bandwidth/CPU)

If you don't need the camera stream during competition:

```json
{
  "streaming": {
    "enabled": false
  }
}
```

Then restart:
```bash
sudo systemctl restart frc-vision.service
```

Vision system will still publish target data to NetworkTables, just without video stream.

## Using Stream for Debugging

### View Detection Overlays

The stream shows:
- **Green boxes**: Detected game pieces (YOLO)
- **Blue markers**: AprilTags
- **Yellow box**: Selected target (being tracked)
- **Crosshair**: Center of frame
- **Text overlays**: FPS, target info, distance, yaw

### Record Stream for Analysis

From your computer:

```bash
# Using ffmpeg
ffmpeg -i http://10.32.67.50:1181/?action=stream -t 60 recording.mp4

# Record 60 seconds
```

### Compare Camera View vs Driver View

Split screen on driver station:
- Left: Camera stream (what vision system sees)
- Right: Robot controls/NetworkTables data

This helps debug:
- Why robot isn't seeing targets
- If camera angle needs adjustment
- If lighting is affecting detection

## Integration with Robot Code

The stream is **independent** from NetworkTables data:
- Stream = visual feedback for humans
- NetworkTables = data for robot code

Both run simultaneously. Disabling stream does NOT affect robot vision control.

## Advanced: Custom Stream Overlays

To modify what's shown in the stream, edit `vision_system.py`:

```python
def draw_overlays(self, frame, yolo_targets, apriltag_targets, selected_target, target_data):
    """Draw detection overlays on frame"""

    # Your custom drawing code here
    # Example: Add team logo
    # cv2.putText(frame, "Team 3267", (10, 30), ...)

    return frame
```

## FAQ

**Q: Does streaming affect vision performance?**
A: Minimal impact (~5-10% CPU). Target detection still runs at full speed.

**Q: Can I stream to multiple viewers?**
A: Yes! Multiple devices can view the same stream simultaneously.

**Q: Stream works at home but not at competition?**
A: Check network configuration. Must use robot radio network (10.TE.AM.X). Firewall or wrong IP can block stream.

**Q: Can I change port number?**
A: Yes, edit `config.json`. Recommended range: 1181-1190 to avoid conflicts.

**Q: Stream shows old/cached frames?**
A: Check FPS counter. If very low, camera or processing is bottlenecked. Reduce resolution/quality.

**Q: Can I stream raw camera without overlays?**
A: Yes, modify `vision_system.py` to stream `frame` instead of `annotated_frame`.

---

## Summary

Camera streaming provides:
- ✅ Real-time visual feedback
- ✅ Detection verification
- ✅ Debugging assistance
- ✅ Driver awareness

**Quick Start:**
1. Ensure `"streaming.enabled": true` in config.json
2. Open Shuffleboard → Add Camera Stream → "Vision System"
3. See live annotated camera feed!

**Recommended for:**
- Testing and debugging
- Driver station monitoring
- Competition (if bandwidth allows)

**Disable if:**
- Network congestion issues
- CPU usage too high
- Don't need visual feedback

---

**Team 3267 - See what your robot sees! 🤖👁️**
