#!/usr/bin/env python3
"""
Test camera functionality and display feed
Usage: python3 test_camera.py [--device 0]
"""

import cv2
import argparse
import time
import numpy as np


def test_camera(device=0):
    """Test camera and display feed with FPS counter"""
    print(f"Testing camera device {device}...")

    # Open camera
    camera = cv2.VideoCapture(device)

    if not camera.isOpened():
        print(f"Error: Could not open camera device {device}")
        print("Available devices:")
        for i in range(10):
            test_cam = cv2.VideoCapture(i)
            if test_cam.isOpened():
                print(f"  - Device {i}")
                test_cam.release()
        return

    # Get camera properties
    width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = camera.get(cv2.CAP_PROP_FPS)

    print(f"Camera opened successfully!")
    print(f"Resolution: {width}x{height}")
    print(f"FPS: {fps}")
    print("\nPress 'q' to quit, 's' to save snapshot")

    # FPS tracking
    frame_times = []
    snapshot_count = 0

    while True:
        start_time = time.time()

        # Capture frame
        ret, frame = camera.read()
        if not ret:
            print("Error: Failed to capture frame")
            break

        # Calculate FPS
        frame_times.append(time.time() - start_time)
        if len(frame_times) > 30:
            frame_times.pop(0)
        current_fps = len(frame_times) / sum(frame_times)

        # Draw FPS
        cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Draw crosshair
        h, w = frame.shape[:2]
        cv2.line(frame, (w//2 - 20, h//2), (w//2 + 20, h//2), (0, 0, 255), 2)
        cv2.line(frame, (w//2, h//2 - 20), (w//2, h//2 + 20), (0, 0, 255), 2)

        # Show frame
        cv2.imshow('Camera Test', frame)

        # Handle keypresses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f"snapshot_{snapshot_count:03d}.jpg"
            cv2.imwrite(filename, frame)
            print(f"Saved {filename}")
            snapshot_count += 1

    # Cleanup
    camera.release()
    cv2.destroyAllWindows()
    print("\nCamera test completed")


def main():
    parser = argparse.ArgumentParser(description='Test camera functionality')
    parser.add_argument('--device', type=int, default=0,
                       help='Camera device number (default: 0)')

    args = parser.parse_args()
    test_camera(args.device)


if __name__ == '__main__':
    main()
