#!/usr/bin/env python3
"""
Extract frames from video for training dataset
Usage: python3 extract_frames.py --video footage.mp4 --output frames/ --interval 10
"""

import cv2
import os
import argparse
from pathlib import Path


def extract_frames(video_path, output_dir, interval=10):
    """
    Extract frames from video at specified interval

    Args:
        video_path: Path to video file
        output_dir: Directory to save frames
        interval: Extract every Nth frame (default 10)
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Open video
    video = cv2.VideoCapture(video_path)
    if not video.isOpened():
        print(f"Error: Could not open video {video_path}")
        return

    # Get video properties
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps

    print(f"Video: {video_path}")
    print(f"Total frames: {total_frames}")
    print(f"FPS: {fps:.2f}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Extracting every {interval} frames...")

    frame_count = 0
    saved_count = 0

    while True:
        ret, frame = video.read()
        if not ret:
            break

        # Save frame at interval
        if frame_count % interval == 0:
            filename = output_path / f"frame_{saved_count:06d}.jpg"
            cv2.imwrite(str(filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            saved_count += 1

            if saved_count % 100 == 0:
                print(f"Extracted {saved_count} frames...")

        frame_count += 1

    video.release()
    print(f"\nDone! Extracted {saved_count} frames to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description='Extract frames from video for training')
    parser.add_argument('--video', required=True, help='Input video file')
    parser.add_argument('--output', default='frames/', help='Output directory')
    parser.add_argument('--interval', type=int, default=10,
                       help='Extract every Nth frame (default: 10)')

    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"Error: Video file not found: {args.video}")
        return

    extract_frames(args.video, args.output, args.interval)


if __name__ == '__main__':
    main()
