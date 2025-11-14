#!/usr/bin/env python3
"""
Camera calibration using checkerboard pattern
1. Print checkerboard: https://raw.githubusercontent.com/opencv/opencv/master/doc/pattern.png
2. Take 20+ photos of checkerboard from different angles
3. Run: python3 camera_calibration.py --images calibration/*.jpg

The script will output camera matrix and distortion coefficients
"""

import cv2
import numpy as np
import glob
import argparse
import json


def calibrate_camera(images_path, pattern_size=(9, 6), square_size=0.025):
    """
    Calibrate camera using checkerboard images

    Args:
        images_path: Glob pattern for calibration images
        pattern_size: Checkerboard size (width, height) in inner corners
        square_size: Size of each square in meters

    Returns:
        Camera matrix, distortion coefficients, calibration error
    """
    # Prepare object points
    objp = np.zeros((pattern_size[0] * pattern_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2)
    objp *= square_size

    # Arrays to store object points and image points
    objpoints = []  # 3D points in real world space
    imgpoints = []  # 2D points in image plane

    # Load images
    images = glob.glob(images_path)
    if not images:
        print(f"Error: No images found matching {images_path}")
        return None, None, None

    print(f"Found {len(images)} calibration images")
    print("Processing images...")

    successful = 0
    image_size = None

    for i, fname in enumerate(images):
        img = cv2.imread(fname)
        if img is None:
            print(f"Warning: Could not read {fname}")
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        image_size = gray.shape[::-1]

        # Find checkerboard corners
        ret, corners = cv2.findChessboardCorners(gray, pattern_size, None)

        if ret:
            objpoints.append(objp)

            # Refine corner positions
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)

            successful += 1
            print(f"  [{i+1}/{len(images)}] ✓ {fname}")
        else:
            print(f"  [{i+1}/{len(images)}] ✗ {fname} - Checkerboard not found")

    print(f"\nSuccessfully processed {successful}/{len(images)} images")

    if successful < 10:
        print("Warning: Less than 10 successful images. Results may be inaccurate.")
        print("Try taking more photos from different angles.")

    # Calibrate camera
    print("\nCalibrating camera...")
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, image_size, None, None
    )

    # Calculate reprojection error
    total_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i],
                                          camera_matrix, dist_coeffs)
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        total_error += error

    mean_error = total_error / len(objpoints)

    return camera_matrix, dist_coeffs, mean_error


def save_calibration(camera_matrix, dist_coeffs, output_file='camera_calibration.json'):
    """Save calibration data to JSON file"""
    calibration_data = {
        'camera_matrix': camera_matrix.tolist(),
        'distortion_coefficients': dist_coeffs.tolist()
    }

    with open(output_file, 'w') as f:
        json.dump(calibration_data, f, indent=2)

    print(f"\nCalibration saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Camera calibration using checkerboard')
    parser.add_argument('--images', required=True,
                       help='Glob pattern for calibration images (e.g., "calibration/*.jpg")')
    parser.add_argument('--width', type=int, default=9,
                       help='Checkerboard width (inner corners, default: 9)')
    parser.add_argument('--height', type=int, default=6,
                       help='Checkerboard height (inner corners, default: 6)')
    parser.add_argument('--square', type=float, default=0.025,
                       help='Square size in meters (default: 0.025 = 25mm)')
    parser.add_argument('--output', default='camera_calibration.json',
                       help='Output file (default: camera_calibration.json)')

    args = parser.parse_args()

    # Calibrate
    camera_matrix, dist_coeffs, error = calibrate_camera(
        args.images,
        pattern_size=(args.width, args.height),
        square_size=args.square
    )

    if camera_matrix is None:
        print("\nCalibration failed!")
        return

    # Print results
    print("\n" + "="*60)
    print("CALIBRATION RESULTS")
    print("="*60)
    print("\nCamera Matrix:")
    print(camera_matrix)
    print("\nDistortion Coefficients:")
    print(dist_coeffs)
    print(f"\nMean Reprojection Error: {error:.4f} pixels")

    if error < 0.5:
        print("✓ Excellent calibration!")
    elif error < 1.0:
        print("✓ Good calibration")
    else:
        print("⚠ High error - consider recalibrating with more images")

    # Save calibration
    save_calibration(camera_matrix, dist_coeffs, args.output)

    # Print config.json format
    print("\n" + "="*60)
    print("Copy this to your config.json:")
    print("="*60)
    print('"camera": {')
    print(f'  "matrix": {json.dumps(camera_matrix.tolist(), indent=4).replace("    ", "    ")}')
    print('},')
    print("="*60)


if __name__ == '__main__':
    main()
