#!/usr/bin/env python3
"""
Training Data Collection Tool for FRC Vision System
Capture images directly from camera for YOLO8 training

Usage:
    # Collect coral images
    python3 collect_training_data.py --class coral --output training_data/

    # Collect algae images
    python3 collect_training_data.py --class algae --output training_data/

    # Collect negative examples (background/no game pieces)
    python3 collect_training_data.py --class negative --output training_data/

    # Collect with specific lighting condition
    python3 collect_training_data.py --class coral --lighting bright --output training_data/

Controls:
    SPACE   - Capture image
    C       - Toggle crosshair
    G       - Toggle grid overlay
    E       - Toggle exposure info
    +/-     - Adjust exposure (if supported)
    Q       - Quit
"""

import cv2
import argparse
import time
import os
from pathlib import Path
from datetime import datetime
import json


class TrainingDataCollector:
    def __init__(self, class_name, output_dir, camera_device=0, lighting=None):
        self.class_name = class_name
        self.output_dir = Path(output_dir)
        self.lighting = lighting
        self.camera_device = camera_device

        # Create output directories
        self.setup_directories()

        # Setup camera
        self.camera = self.setup_camera()

        # UI state
        self.show_crosshair = True
        self.show_grid = True
        self.show_exposure = True
        self.capture_count = 0

        # Load existing metadata
        self.metadata = self.load_metadata()

    def setup_directories(self):
        """Create directory structure for training data"""
        # Main class directory
        self.class_dir = self.output_dir / self.class_name
        self.class_dir.mkdir(parents=True, exist_ok=True)

        # Lighting subdirectory if specified
        if self.lighting:
            self.save_dir = self.class_dir / self.lighting
        else:
            self.save_dir = self.class_dir

        self.save_dir.mkdir(parents=True, exist_ok=True)

        print(f"Saving images to: {self.save_dir}")

    def setup_camera(self):
        """Initialize camera"""
        camera = cv2.VideoCapture(self.camera_device)

        if not camera.isOpened():
            raise RuntimeError(f"Failed to open camera device {self.camera_device}")

        # Set camera properties
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Try to set autofocus off (not all cameras support this)
        try:
            camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        except:
            pass

        print(f"Camera initialized: {camera.get(cv2.CAP_PROP_FRAME_WIDTH)}x{camera.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
        return camera

    def load_metadata(self):
        """Load existing metadata file"""
        metadata_file = self.output_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return {
            "collection_sessions": [],
            "classes": {},
            "total_images": 0
        }

    def save_metadata(self):
        """Save metadata to file"""
        metadata_file = self.output_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def update_metadata(self, session_captures):
        """Update metadata with session information"""
        session_info = {
            "timestamp": datetime.now().isoformat(),
            "class": self.class_name,
            "lighting": self.lighting,
            "captures": session_captures,
            "camera_device": self.camera_device
        }

        self.metadata["collection_sessions"].append(session_info)

        # Update class counts
        if self.class_name not in self.metadata["classes"]:
            self.metadata["classes"][self.class_name] = 0
        self.metadata["classes"][self.class_name] += session_captures

        self.metadata["total_images"] += session_captures

        self.save_metadata()

    def get_exposure_info(self):
        """Get camera exposure settings"""
        try:
            exposure = self.camera.get(cv2.CAP_PROP_EXPOSURE)
            brightness = self.camera.get(cv2.CAP_PROP_BRIGHTNESS)
            return exposure, brightness
        except:
            return None, None

    def adjust_exposure(self, increase=True):
        """Adjust camera exposure"""
        try:
            current = self.camera.get(cv2.CAP_PROP_EXPOSURE)
            if increase:
                new_value = current + 5
            else:
                new_value = current - 5
            self.camera.set(cv2.CAP_PROP_EXPOSURE, new_value)
            print(f"Exposure: {current:.1f} → {new_value:.1f}")
        except Exception as e:
            print(f"Could not adjust exposure: {e}")

    def draw_crosshair(self, frame):
        """Draw center crosshair"""
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2

        # Horizontal line
        cv2.line(frame, (cx - 30, cy), (cx + 30, cy), (0, 255, 0), 2)
        # Vertical line
        cv2.line(frame, (cx, cy - 30), (cx, cy + 30), (0, 255, 0), 2)
        # Center dot
        cv2.circle(frame, (cx, cy), 3, (0, 255, 0), -1)

    def draw_grid(self, frame):
        """Draw rule of thirds grid"""
        h, w = frame.shape[:2]

        # Vertical lines
        for x in [w // 3, 2 * w // 3]:
            cv2.line(frame, (x, 0), (x, h), (255, 255, 255), 1)

        # Horizontal lines
        for y in [h // 3, 2 * h // 3]:
            cv2.line(frame, (0, y), (w, y), (255, 255, 255), 1)

    def draw_info(self, frame):
        """Draw information overlay"""
        h, w = frame.shape[:2]

        # Semi-transparent background for text
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 100), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)

        # Class and count
        text = f"Class: {self.class_name}"
        cv2.putText(frame, text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        text = f"Captured: {self.capture_count}"
        cv2.putText(frame, text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        if self.lighting:
            text = f"Lighting: {self.lighting}"
            cv2.putText(frame, text, (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Exposure info
        if self.show_exposure:
            exposure, brightness = self.get_exposure_info()
            if exposure is not None:
                text = f"Exp: {exposure:.1f}"
                cv2.putText(frame, text, (w - 120, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Average brightness
            avg_brightness = frame.mean()
            text = f"Bright: {avg_brightness:.0f}"
            cv2.putText(frame, text, (w - 120, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Controls
        controls = [
            "SPACE: Capture",
            "C: Crosshair",
            "G: Grid",
            "Q: Quit"
        ]
        y_offset = h - 80
        for control in controls:
            cv2.putText(frame, control, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            y_offset += 15

        return frame

    def save_image(self, frame):
        """Save captured image with metadata"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{self.class_name}_{timestamp}.jpg"
        filepath = self.save_dir / filename

        # Save with high quality
        cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])

        self.capture_count += 1
        print(f"Captured: {filename}")

        return filename

    def show_capture_feedback(self, frame):
        """Show visual feedback when image is captured"""
        # Flash white overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (255, 255, 255), -1)
        flash = cv2.addWeighted(overlay, 0.5, frame, 0.5, 0)
        cv2.imshow('Training Data Collection', flash)
        cv2.waitKey(100)

    def run(self):
        """Main collection loop"""
        print("\n" + "="*60)
        print("TRAINING DATA COLLECTION")
        print("="*60)
        print(f"Class: {self.class_name}")
        print(f"Output: {self.save_dir}")
        print(f"Lighting: {self.lighting or 'unspecified'}")
        print("\nControls:")
        print("  SPACE  - Capture image")
        print("  C      - Toggle crosshair")
        print("  G      - Toggle grid")
        print("  E      - Toggle exposure info")
        print("  +/-    - Adjust exposure")
        print("  Q      - Quit")
        print("="*60 + "\n")

        session_start_count = self.capture_count

        try:
            while True:
                ret, frame = self.camera.read()
                if not ret:
                    print("Failed to capture frame")
                    break

                # Draw overlays
                display_frame = frame.copy()

                if self.show_grid:
                    self.draw_grid(display_frame)

                if self.show_crosshair:
                    self.draw_crosshair(display_frame)

                display_frame = self.draw_info(display_frame)

                # Show frame
                cv2.imshow('Training Data Collection', display_frame)

                # Handle key presses
                key = cv2.waitKey(1) & 0xFF

                if key == ord(' '):
                    # Capture image
                    self.save_image(frame)
                    self.show_capture_feedback(display_frame)

                elif key == ord('c'):
                    # Toggle crosshair
                    self.show_crosshair = not self.show_crosshair
                    print(f"Crosshair: {'ON' if self.show_crosshair else 'OFF'}")

                elif key == ord('g'):
                    # Toggle grid
                    self.show_grid = not self.show_grid
                    print(f"Grid: {'ON' if self.show_grid else 'OFF'}")

                elif key == ord('e'):
                    # Toggle exposure info
                    self.show_exposure = not self.show_exposure
                    print(f"Exposure info: {'ON' if self.show_exposure else 'OFF'}")

                elif key == ord('+') or key == ord('='):
                    # Increase exposure
                    self.adjust_exposure(increase=True)

                elif key == ord('-') or key == ord('_'):
                    # Decrease exposure
                    self.adjust_exposure(increase=False)

                elif key == ord('q'):
                    # Quit
                    break

        except KeyboardInterrupt:
            print("\nCollection interrupted by user")

        finally:
            self.cleanup(session_start_count)

    def cleanup(self, session_start_count):
        """Cleanup and save session info"""
        session_captures = self.capture_count - session_start_count

        self.camera.release()
        cv2.destroyAllWindows()

        # Update metadata
        if session_captures > 0:
            self.update_metadata(session_captures)

        print("\n" + "="*60)
        print("SESSION SUMMARY")
        print("="*60)
        print(f"Images captured this session: {session_captures}")
        print(f"Total images for '{self.class_name}': {self.metadata['classes'].get(self.class_name, 0)}")
        print(f"Total images all classes: {self.metadata['total_images']}")
        print(f"Saved to: {self.save_dir}")
        print("="*60 + "\n")


def print_collection_stats(output_dir):
    """Print statistics about collected data"""
    metadata_file = Path(output_dir) / "metadata.json"
    if not metadata_file.exists():
        print("No training data collected yet")
        return

    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    print("\n" + "="*60)
    print("TRAINING DATA STATISTICS")
    print("="*60)
    print(f"Total images: {metadata['total_images']}")
    print(f"Total sessions: {len(metadata['collection_sessions'])}")
    print("\nImages per class:")
    for class_name, count in metadata['classes'].items():
        print(f"  {class_name}: {count}")
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Collect training data for YOLO8',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect coral images
  python3 collect_training_data.py --class coral

  # Collect algae images with lighting condition
  python3 collect_training_data.py --class algae --lighting indoor

  # Collect negative examples (backgrounds)
  python3 collect_training_data.py --class negative

  # View statistics
  python3 collect_training_data.py --stats

Recommended classes:
  - coral: Orange coral game pieces
  - algae: Yellow/green algae game pieces
  - negative: Backgrounds without game pieces
  - mixed: Multiple game pieces together

Recommended lighting conditions:
  - bright: Bright indoor or outdoor
  - indoor: Typical indoor field lighting
  - dim: Low light conditions
  - outdoor: Outdoor sunlight
        """
    )

    parser.add_argument('--class', dest='class_name', required=False,
                       help='Class name (coral, algae, negative, etc.)')
    parser.add_argument('--output', default='training_data',
                       help='Output directory (default: training_data)')
    parser.add_argument('--camera', type=int, default=0,
                       help='Camera device number (default: 0)')
    parser.add_argument('--lighting',
                       choices=['bright', 'indoor', 'dim', 'outdoor'],
                       help='Lighting condition label')
    parser.add_argument('--stats', action='store_true',
                       help='Show collection statistics and exit')

    args = parser.parse_args()

    # Show stats if requested
    if args.stats:
        print_collection_stats(args.output)
        return

    # Validate class name
    if not args.class_name:
        parser.error("--class is required (unless using --stats)")

    # Run collector
    collector = TrainingDataCollector(
        class_name=args.class_name,
        output_dir=args.output,
        camera_device=args.camera,
        lighting=args.lighting
    )

    collector.run()


if __name__ == '__main__':
    main()
