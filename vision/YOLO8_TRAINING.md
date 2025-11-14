# YOLO8 Training Guide for FRC Game Pieces

Complete guide for training a custom YOLO8 model to detect game pieces for any FRC season.

## Overview

YOLO8 (You Only Look Once version 8) is a state-of-the-art object detection model that's fast enough for real-time robotics applications. This guide will help you train a custom model to detect whatever game pieces are used in the current season.

## Training Workflow

This system is designed to be retrained each season with new game pieces:
1. **Collect images** directly from OrangePi camera
2. **Label images** in Roboflow
3. **Train model** on Google Colab
4. **Deploy to robot** and test
5. **Retrain as needed** for different lighting/conditions

## Prerequisites

### Hardware for Training
- Computer with NVIDIA GPU (recommended, or use Google Colab)
- At least 8GB RAM
- 50GB free disk space

### Software
- Python 3.8+
- CUDA (if using local GPU)
- Roboflow account (free) for dataset management

## Part 1: Collect Training Data

### Option A: Direct Collection from OrangePi (Recommended)

**Best method** - Collect images directly from the robot's camera in real competition conditions!

1. **SSH to OrangePi**:
   ```bash
   ssh pi@10.32.67.50
   cd ~/frc-vision
   ```

2. **Collect images for each game piece class**:
   ```bash
   # Start collection for first game piece
   python3 collect_training_data.py --class gamepiece1 --lighting indoor

   # Press SPACE to capture images
   # Move game piece to different positions/angles
   # Press Q when done

   # Collect for second game piece
   python3 collect_training_data.py --class gamepiece2 --lighting indoor

   # Collect negative examples (backgrounds without game pieces)
   python3 collect_training_data.py --class negative --lighting indoor
   ```

3. **Collect in different lighting conditions**:
   ```bash
   # Bright lighting
   python3 collect_training_data.py --class gamepiece1 --lighting bright

   # Dim lighting
   python3 collect_training_data.py --class gamepiece1 --lighting dim

   # Outdoor (if applicable)
   python3 collect_training_data.py --class gamepiece1 --lighting outdoor
   ```

4. **View collection statistics**:
   ```bash
   python3 collect_training_data.py --stats
   ```

5. **Prepare dataset for training**:
   ```bash
   # Organize images into train/val/test splits
   python3 prepare_dataset.py --input training_data --output dataset

   # This creates dataset.zip for transfer
   ```

6. **Transfer to your computer**:
   ```bash
   # From your computer
   scp pi@10.32.67.50:~/frc-vision/dataset_*imgs.zip ~/Downloads/
   ```

**Collection Tips:**
- Collect 100-200 images per game piece minimum (500+ ideal)
- Capture at different angles (front, side, top, tilted)
- Include partial occlusions (pieces half-visible)
- Vary distances (close, medium, far)
- Include multiple pieces in same frame
- Add motion blur (move piece while capturing)
- Collect negative examples (field without game pieces)

### Option B: Record Video at Events/Practice

1. **Record video footage**:
   ```bash
   # Mount camera on robot
   # Record at different:
   # - Lighting conditions (bright, dim, outdoor)
   # - Angles (floor level, elevated, different rotations)
   # - Distances (close, far, medium)
   # - Backgrounds (field carpet, walls, people)
   ```

2. **Extract frames from video**:
   ```bash
   # Use provided script
   python3 extract_frames.py --video footage.mp4 --output frames/ --interval 10

   # Or use ffmpeg
   ffmpeg -i footage.mp4 -vf fps=3 frames/frame_%04d.jpg
   ```

### Option C: Download Existing Datasets

Check FRC community resources:
- Chief Delphi forums
- FRC Discord servers
- Team websites
- Current season datasets from other teams

**Note:** Each season has different game pieces, so datasets from previous seasons won't work directly. You'll need to collect new data for each season's unique game pieces.

### Data Collection Best Practices

Collect **500-1000 images minimum** with:
- ✅ Various lighting conditions (bright field, dim pit, outdoor)
- ✅ Different angles and orientations (all sides of game piece)
- ✅ Partial occlusions (pieces half-visible behind robots/field elements)
- ✅ Multiple pieces in frame (realistic game scenarios)
- ✅ Different distances (close-up to far away)
- ✅ Motion blur (move pieces while capturing for realistic robot movement)
- ✅ Different field locations (carpet, walls, scoring positions)
- ✅ Varied backgrounds (with/without robots, people, other game elements)

**Pro Tip:** Use `collect_training_data.py` at practice, competitions, and build sessions to continuously improve your dataset!

## Part 2: Label Your Dataset

### Using Roboflow (Recommended - Easy)

1. **Create Roboflow Account**:
   - Go to https://roboflow.com
   - Sign up for free account

2. **Create New Project**:
   - Project type: "Object Detection"
   - Name: "FRC 2025 Game Pieces"
   - Classes: `coral`, `algae`

3. **Upload Images**:
   - Drag and drop your collected images
   - Roboflow will organize them

4. **Label Images**:
   - Click "Annotate"
   - Draw bounding boxes around each game piece
   - Assign correct class (coral or algae)
   - Keyboard shortcuts: `1` for coral, `2` for algae
   - Aim for 500+ labeled images

5. **Dataset Split**:
   - Training: 70%
   - Validation: 20%
   - Testing: 10%

6. **Augmentation** (Roboflow does this automatically):
   - Rotation: ±15°
   - Brightness: ±25%
   - Noise: Up to 2%
   - Blur: Up to 1px

7. **Generate Dataset**:
   - Format: "YOLO v8"
   - Click "Generate"
   - Download or get API code

### Using Label Studio (Alternative - Self-Hosted)

```bash
# Install Label Studio
pip install label-studio

# Start server
label-studio start

# Open browser to http://localhost:8080
# Create project, upload images, label bounding boxes
```

### Using Roboflow Annotate (Alternative - Desktop)

Download from https://roboflow.com/annotate

## Part 3: Train YOLO8 Model

### Option A: Google Colab (Free GPU) - Recommended

1. **Open Google Colab**:
   - Go to https://colab.research.google.com
   - File → New Notebook

2. **Enable GPU**:
   - Runtime → Change runtime type
   - Hardware accelerator: GPU (T4)

3. **Training Code**:

```python
# Install Ultralytics
!pip install ultralytics roboflow

# Import libraries
from ultralytics import YOLO
from roboflow import Roboflow
import os

# Download dataset from Roboflow
rf = Roboflow(api_key="YOUR_API_KEY")  # Get from Roboflow
project = rf.workspace("YOUR_WORKSPACE").project("frc-2025-game-pieces")
dataset = project.version(1).download("yolov8")

# Initialize model
# Options: yolov8n (nano - fastest), yolov8s (small), yolov8m (medium)
# For OrangePi, use yolov8n for best performance
model = YOLO('yolov8n.pt')

# Train model
results = model.train(
    data=f'{dataset.location}/data.yaml',
    epochs=100,  # More epochs = better accuracy, but slower training
    imgsz=640,   # Image size
    batch=16,    # Adjust based on GPU memory
    name='frc_game_pieces',
    patience=20, # Early stopping if no improvement
    save=True,
    plots=True
)

# Validate model
metrics = model.val()
print(f"mAP50: {metrics.box.map50}")
print(f"mAP50-95: {metrics.box.map}")

# Export model
model.export(format='onnx')  # Optional: smaller file size
```

4. **Download Trained Model**:
   - After training completes, download `best.pt` from Colab
   - This is your trained model!

### Option B: Local Training (If you have NVIDIA GPU)

```bash
# Install CUDA and PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install Ultralytics
pip install ultralytics

# Download your dataset (from Roboflow or local)
# Train model
yolo train data=dataset/data.yaml model=yolov8n.pt epochs=100 imgsz=640
```

### Training Tips

- **Start with yolov8n.pt** (nano) for OrangePi - it's fastest
- **Use more epochs** (100-200) for better accuracy
- **Monitor validation loss** - should decrease over time
- **Early stopping** - training will stop if no improvement
- **Augmentation helps** - more varied training data = better generalization

## Part 4: Evaluate Your Model

### Check Training Metrics

Look at the results folder:
```
runs/detect/frc_game_pieces/
├── confusion_matrix.png     # How often model confuses classes
├── results.png               # Loss and mAP over epochs
├── val_batch0_pred.png      # Sample predictions
└── weights/
    ├── best.pt              # Best model weights (use this!)
    └── last.pt              # Final epoch weights
```

**Good metrics:**
- mAP50 > 0.90 (90% accuracy at 50% IoU threshold)
- mAP50-95 > 0.70
- Low confusion between coral and algae

### Test on New Images

```python
from ultralytics import YOLO

# Load your trained model
model = YOLO('runs/detect/frc_game_pieces/weights/best.pt')

# Test on new image
results = model.predict('test_image.jpg', conf=0.5)

# Display results
results[0].show()

# Save results
results[0].save('result.jpg')
```

### Test Performance on OrangePi

```bash
# Transfer model to OrangePi
scp best.pt pi@10.32.67.50:~/frc-vision/models/game_piece.pt

# SSH to OrangePi
ssh pi@10.32.67.50

# Test FPS
cd ~/frc-vision
source venv/bin/activate
python3 << EOF
from ultralytics import YOLO
import cv2
import time

model = YOLO('models/game_piece.pt')
camera = cv2.VideoCapture(0)

# Test FPS
start = time.time()
frames = 0
for i in range(100):
    ret, frame = camera.read()
    if ret:
        results = model(frame, conf=0.5, verbose=False)
        frames += 1

fps = frames / (time.time() - start)
print(f"FPS: {fps:.1f}")
camera.release()
EOF
```

**Target FPS:**
- ✅ 20+ FPS: Excellent
- ⚠️  10-20 FPS: Acceptable
- ❌ <10 FPS: Too slow, use smaller model

## Part 5: Deploy Model

### 1. Copy Model to OrangePi

```bash
# From your computer
scp best.pt pi@10.32.67.50:~/frc-vision/models/game_piece.pt
```

### 2. Update Configuration

```bash
# SSH to OrangePi
ssh pi@10.32.67.50

# Edit config
cd ~/frc-vision
nano config.json
```

Update:
```json
{
  "yolo": {
    "enabled": true,
    "model_path": "models/game_piece.pt",
    "confidence_threshold": 0.5
  }
}
```

### 3. Test Vision System

```bash
# Test with debug window
cd ~/frc-vision
source venv/bin/activate
python3 vision_system.py

# Should detect coral and algae pieces!
```

### 4. Restart Service

```bash
sudo systemctl restart frc-vision.service
sudo systemctl status frc-vision.service
```

## Part 6: Improve Your Model

### If Model Has Poor Accuracy

1. **Collect more data** (aim for 1000+ images)
2. **Balance classes** (equal images for each game piece type)
3. **Add difficult examples** (partial occlusions, poor lighting)
4. **Increase training epochs** (try 200)
5. **Try larger model** (yolov8s instead of yolov8n)
6. **Check labels** (incorrect labels = poor results)

### If Model is Too Slow

1. **Use smaller model** (yolov8n is smallest)
2. **Reduce image size** (try 416x416 instead of 640x640)
3. **Increase confidence threshold** (0.6 or 0.7)
4. **Consider ONNX export** for faster inference

### Continuous Improvement Workflow

**After each competition/practice:**

1. **Collect missed detections**:
   ```bash
   # SSH to OrangePi
   ssh pi@10.32.67.50
   cd ~/frc-vision

   # Collect images of cases where detection failed
   python3 collect_training_data.py --class gamepiece1 --lighting competition
   ```

2. **Add to dataset and retrain**:
   ```bash
   # Prepare updated dataset
   python3 prepare_dataset.py --input training_data --output dataset_v2

   # Transfer to computer
   scp dataset_v2_*imgs.zip user@yourcomputer:~/

   # Retrain on Google Colab with new data
   # Compare v1 vs v2 model performance
   ```

3. **A/B test models**:
   ```bash
   # Keep both models on OrangePi
   # models/game_piece_v1.pt
   # models/game_piece_v2.pt

   # Update config.json to switch between them
   nano config.json
   # Change "model_path" to test different versions
   ```

4. **Deploy best model**:
   ```bash
   # Copy winning model as primary
   cp models/game_piece_v2.pt models/game_piece.pt
   sudo systemctl restart frc-vision.service
   ```

### Retraining for New Season

**When new game pieces are revealed:**

1. **Clear old data** (optional - or keep for reference):
   ```bash
   mv training_data training_data_2025
   mkdir training_data
   ```

2. **Collect new game piece data**:
   ```bash
   # Collect 500+ images per new game piece
   python3 collect_training_data.py --class newpiece1
   python3 collect_training_data.py --class newpiece2
   python3 collect_training_data.py --class negative
   ```

3. **Prepare and train**:
   ```bash
   python3 prepare_dataset.py
   # Upload to Roboflow, label, and train
   ```

4. **Deploy new model**:
   ```bash
   scp new_model.pt pi@10.32.67.50:~/frc-vision/models/game_piece.pt
   ssh pi@10.32.67.50 "sudo systemctl restart frc-vision.service"
   ```

### Lighting-Specific Models (Advanced)

If one model doesn't work well in all conditions:

1. **Collect separate datasets**:
   ```bash
   python3 collect_training_data.py --class gamepiece1 --lighting bright
   python3 collect_training_data.py --class gamepiece1 --lighting dim
   ```

2. **Train separate models**:
   - `game_piece_bright.pt`
   - `game_piece_dim.pt`

3. **Auto-switch in code** (modify vision_system.py):
   ```python
   avg_brightness = frame.mean()
   model_path = "models/game_piece_bright.pt" if avg_brightness > 100 else "models/game_piece_dim.pt"
   ```

## Part 7: Advanced Techniques

### Multi-Model Strategy

Train separate models for different conditions:
```python
# Day model (bright lighting)
model_day = YOLO('models/game_piece_day.pt')

# Night model (indoor/dim lighting)
model_night = YOLO('models/game_piece_night.pt')

# Auto-select based on brightness
avg_brightness = frame.mean()
model = model_day if avg_brightness > 100 else model_night
```

### Tracking (Reduce Jitter)

```python
from ultralytics import YOLO

# Enable tracking
model = YOLO('models/game_piece.pt')
results = model.track(frame, persist=True)

# Track IDs stay consistent frame-to-frame
```

### TensorRT Optimization (Advanced)

For maximum speed on OrangePi with NVIDIA Jetson:
```python
# Export to TensorRT
model.export(format='engine', device=0)

# Load TensorRT model
model_trt = YOLO('game_piece.engine')
```

## Resources

### Datasets
- Roboflow Universe: Search "FRC" for existing datasets
- Chief Delphi: https://www.chiefdelphi.com/
- FRC Discord: Computer Vision channel

### Tools
- Roboflow: https://roboflow.com
- Label Studio: https://labelstud.io
- Ultralytics YOLO8: https://github.com/ultralytics/ultralytics

### Tutorials
- YOLO8 Documentation: https://docs.ultralytics.com
- Roboflow Training Guide: https://blog.roboflow.com/train-yolov8
- FRC Vision Guide: https://docs.wpilib.org/en/stable/docs/software/vision-processing/

## Troubleshooting

### "CUDA out of memory"
- Reduce batch size (try 8 or 4)
- Use smaller images (416 instead of 640)
- Use Google Colab with free GPU

### "Model not detecting anything"
- Lower confidence threshold (0.3 or 0.4)
- Check if classes match (coral, algae)
- Verify model file path is correct
- Test on training images first

### "Low FPS on OrangePi"
- Use yolov8n (not yolov8s or yolov8m)
- Reduce camera resolution (320x240)
- Disable debug window
- Check CPU usage with `htop`

## Competition Checklist

Before competition:
- [ ] Model detects both coral and algae reliably
- [ ] FPS is 20+ on OrangePi
- [ ] False positive rate is low (<5%)
- [ ] Works in competition field lighting
- [ ] Works at all expected distances
- [ ] Backup model saved and tested
- [ ] Team knows how to restart vision service
- [ ] NetworkTables data is accurate

Good luck at competition! 🤖
