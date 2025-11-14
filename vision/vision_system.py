#!/usr/bin/env python3
"""
FRC Vision System for OrangePi
Uses YOLO8 for object detection and AprilTag detection
Publishes target data to NetworkTables for robot control
"""

import cv2
import numpy as np
from ultralytics import YOLO
import time
import json
import argparse
from networktables import NetworkTables
from dt_apriltags import Detector
import logging

class VisionSystem:
    def __init__(self, config_path='config.json'):
        """Initialize the vision system"""
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Initialize NetworkTables
        self.setup_networktables()

        # Initialize camera
        self.camera = self.setup_camera()

        # Initialize YOLO model for game piece detection
        self.yolo_model = None
        if self.config['yolo']['enabled']:
            try:
                self.yolo_model = YOLO(self.config['yolo']['model_path'])
                self.logger.info(f"YOLO model loaded: {self.config['yolo']['model_path']}")
            except Exception as e:
                self.logger.warning(f"YOLO model not loaded: {e}")

        # Initialize AprilTag detector
        self.apriltag_detector = None
        if self.config['apriltag']['enabled']:
            self.apriltag_detector = Detector(
                families=self.config['apriltag']['family'],
                nthreads=self.config['apriltag']['threads'],
                quad_decimate=self.config['apriltag']['quad_decimate'],
                quad_sigma=self.config['apriltag']['quad_sigma'],
                refine_edges=self.config['apriltag']['refine_edges'],
                decode_sharpening=self.config['apriltag']['decode_sharpening']
            )
            self.logger.info("AprilTag detector initialized")

        # Camera calibration (you'll need to calibrate your specific camera)
        self.camera_matrix = np.array(self.config['camera']['matrix'])
        self.camera_params = (
            self.camera_matrix[0, 0],  # fx
            self.camera_matrix[1, 1],  # fy
            self.camera_matrix[0, 2],  # cx
            self.camera_matrix[1, 2]   # cy
        )

        # Target selection preferences
        self.target_priority = self.config['target_priority']

        # FPS tracking
        self.fps_start_time = time.time()
        self.fps_counter = 0
        self.current_fps = 0

    def setup_networktables(self):
        """Initialize NetworkTables connection to RoboRIO"""
        team_number = self.config['robot']['team_number']
        NetworkTables.initialize(server=f'roborio-{team_number}-frc.local')

        # Wait for connection
        timeout = 10
        start_time = time.time()
        while not NetworkTables.isConnected():
            if time.time() - start_time > timeout:
                self.logger.warning("NetworkTables connection timeout - continuing anyway")
                break
            time.sleep(0.1)

        if NetworkTables.isConnected():
            self.logger.info("Connected to NetworkTables")

        # Get vision table
        self.vision_table = NetworkTables.getTable('Vision')

        # Initialize all values
        self.publish_target(has_target=False)

    def setup_camera(self):
        """Initialize camera with configuration"""
        camera = cv2.VideoCapture(self.config['camera']['device'])

        # Set camera properties
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.config['camera']['width'])
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config['camera']['height'])
        camera.set(cv2.CAP_PROP_FPS, self.config['camera']['fps'])

        # Additional settings for better performance
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce latency

        if not camera.isOpened():
            self.logger.error("Failed to open camera")
            raise RuntimeError("Camera not accessible")

        self.logger.info(f"Camera opened: {self.config['camera']['width']}x{self.config['camera']['height']} @ {self.config['camera']['fps']}fps")
        return camera

    def detect_yolo_targets(self, frame):
        """Detect game pieces using YOLO"""
        if self.yolo_model is None:
            return []

        results = self.yolo_model(
            frame,
            conf=self.config['yolo']['confidence_threshold'],
            verbose=False
        )

        targets = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = result.names[class_id]

                # Calculate center and size
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                width = x2 - x1
                height = y2 - y1

                targets.append({
                    'type': 'yolo',
                    'class': class_name,
                    'confidence': confidence,
                    'center': (cx, cy),
                    'bbox': (x1, y1, x2, y2),
                    'width': width,
                    'height': height
                })

        return targets

    def detect_apriltags(self, frame):
        """Detect AprilTags in the frame"""
        if self.apriltag_detector is None:
            return []

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect tags
        tags = self.apriltag_detector.detect(
            gray,
            estimate_tag_pose=True,
            camera_params=self.camera_params,
            tag_size=self.config['apriltag']['tag_size']
        )

        targets = []
        for tag in tags:
            # Get center
            center = tag.center

            # Get corners for bounding box
            corners = tag.corners
            x1 = min(corners[:, 0])
            y1 = min(corners[:, 1])
            x2 = max(corners[:, 0])
            y2 = max(corners[:, 1])

            # Calculate pose if available
            distance = None
            if tag.pose_t is not None:
                # Distance is the Z component (forward)
                distance = float(tag.pose_t[2][0])

            targets.append({
                'type': 'apriltag',
                'id': tag.tag_id,
                'confidence': tag.decision_margin,
                'center': (center[0], center[1]),
                'bbox': (x1, y1, x2, y2),
                'distance': distance,
                'pose_R': tag.pose_R,
                'pose_t': tag.pose_t
            })

        return targets

    def select_best_target(self, yolo_targets, apriltag_targets, frame_shape):
        """Select the best target based on priority and position"""
        all_targets = []

        # Add YOLO targets
        if self.target_priority == 'yolo' or self.target_priority == 'both':
            all_targets.extend(yolo_targets)

        # Add AprilTag targets
        if self.target_priority == 'apriltag' or self.target_priority == 'both':
            all_targets.extend(apriltag_targets)

        if not all_targets:
            return None

        # Score targets based on:
        # 1. Proximity to center of frame
        # 2. Size (larger is better)
        # 3. Type priority

        frame_center_x = frame_shape[1] / 2
        frame_center_y = frame_shape[0] / 2

        best_target = None
        best_score = -float('inf')

        for target in all_targets:
            cx, cy = target['center']

            # Distance from center (normalized)
            dist_from_center = np.sqrt(
                ((cx - frame_center_x) / frame_shape[1]) ** 2 +
                ((cy - frame_center_y) / frame_shape[0]) ** 2
            )

            # Size score
            if 'width' in target and 'height' in target:
                size_score = (target['width'] * target['height']) / (frame_shape[0] * frame_shape[1])
            else:
                x1, y1, x2, y2 = target['bbox']
                size_score = ((x2 - x1) * (y2 - y1)) / (frame_shape[0] * frame_shape[1])

            # Type priority
            type_score = 1.0
            if self.target_priority == 'apriltag' and target['type'] == 'apriltag':
                type_score = 2.0
            elif self.target_priority == 'yolo' and target['type'] == 'yolo':
                type_score = 2.0

            # Combined score
            score = (
                type_score * 2.0 +
                (1.0 - dist_from_center) * 1.5 +
                size_score * 1.0
            )

            if score > best_score:
                best_score = score
                best_target = target

        return best_target

    def calculate_target_data(self, target, frame_shape):
        """Calculate yaw, pitch, distance, and area for target"""
        if target is None:
            return None

        # Get frame center
        frame_center_x = frame_shape[1] / 2
        frame_center_y = frame_shape[0] / 2

        # Get target center
        cx, cy = target['center']

        # Calculate yaw (horizontal angle)
        # Positive = right, Negative = left
        pixel_offset_x = cx - frame_center_x
        yaw = np.degrees(np.arctan2(
            pixel_offset_x,
            self.camera_matrix[0, 0]  # focal length
        ))

        # Calculate pitch (vertical angle)
        # Positive = up, Negative = down
        pixel_offset_y = cy - frame_center_y
        pitch = np.degrees(np.arctan2(
            pixel_offset_y,
            self.camera_matrix[1, 1]  # focal length
        ))

        # Calculate area (percentage of frame)
        x1, y1, x2, y2 = target['bbox']
        target_area = (x2 - x1) * (y2 - y1)
        frame_area = frame_shape[0] * frame_shape[1]
        area_percent = (target_area / frame_area) * 100.0

        # Distance estimation
        distance = 0.0
        if target['type'] == 'apriltag' and target.get('distance') is not None:
            # AprilTag provides accurate distance
            distance = target['distance']
        else:
            # Estimate distance based on target size
            # This is a rough approximation - calibrate for your specific targets
            known_width = self.config['target']['known_width_meters']
            focal_length = self.camera_matrix[0, 0]
            pixel_width = x2 - x1
            if pixel_width > 0:
                distance = (known_width * focal_length) / pixel_width

        # Get target ID
        target_id = -1
        if target['type'] == 'apriltag':
            target_id = target['id']

        return {
            'yaw': yaw,
            'pitch': pitch,
            'distance': distance,
            'area': area_percent,
            'target_id': target_id,
            'type': target['type']
        }

    def publish_target(self, has_target=False, data=None):
        """Publish target data to NetworkTables"""
        self.vision_table.putBoolean('HasTarget', has_target)

        if has_target and data is not None:
            self.vision_table.putNumber('Yaw', data['yaw'])
            self.vision_table.putNumber('Pitch', data['pitch'])
            self.vision_table.putNumber('Distance', data['distance'])
            self.vision_table.putNumber('Area', data['area'])
            self.vision_table.putNumber('TargetID', data['target_id'])
        else:
            self.vision_table.putNumber('Yaw', 0.0)
            self.vision_table.putNumber('Pitch', 0.0)
            self.vision_table.putNumber('Distance', 0.0)
            self.vision_table.putNumber('Area', 0.0)
            self.vision_table.putNumber('TargetID', -1)

        # Publish FPS for monitoring
        self.vision_table.putNumber('FPS', self.current_fps)

    def draw_overlays(self, frame, yolo_targets, apriltag_targets, selected_target, target_data):
        """Draw detection overlays on frame for debugging"""
        # Draw all YOLO detections
        for target in yolo_targets:
            x1, y1, x2, y2 = target['bbox']
            color = (0, 255, 0) if target == selected_target else (0, 255, 255)
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            label = f"{target['class']} {target['confidence']:.2f}"
            cv2.putText(frame, label, (int(x1), int(y1) - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Draw all AprilTag detections
        for target in apriltag_targets:
            x1, y1, x2, y2 = target['bbox']
            color = (255, 0, 0) if target == selected_target else (255, 0, 255)
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            label = f"Tag {target['id']}"
            if target['distance'] is not None:
                label += f" {target['distance']:.2f}m"
            cv2.putText(frame, label, (int(x1), int(y1) - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Draw crosshair
        h, w = frame.shape[:2]
        cv2.line(frame, (w//2 - 20, h//2), (w//2 + 20, h//2), (0, 0, 255), 2)
        cv2.line(frame, (w//2, h//2 - 20), (w//2, h//2 + 20), (0, 0, 255), 2)

        # Draw target info
        if target_data is not None:
            info_text = [
                f"Target: {target_data['type']}",
                f"Yaw: {target_data['yaw']:.1f}deg",
                f"Pitch: {target_data['pitch']:.1f}deg",
                f"Dist: {target_data['distance']:.2f}m",
                f"Area: {target_data['area']:.1f}%"
            ]
            y_offset = 30
            for text in info_text:
                cv2.putText(frame, text, (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                y_offset += 25

        # Draw FPS
        cv2.putText(frame, f"FPS: {self.current_fps:.1f}", (10, frame.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return frame

    def update_fps(self):
        """Update FPS counter"""
        self.fps_counter += 1
        if self.fps_counter >= 30:
            end_time = time.time()
            self.current_fps = self.fps_counter / (end_time - self.fps_start_time)
            self.fps_counter = 0
            self.fps_start_time = time.time()

    def run(self):
        """Main processing loop"""
        self.logger.info("Vision system started")

        try:
            while True:
                # Capture frame
                ret, frame = self.camera.read()
                if not ret:
                    self.logger.error("Failed to capture frame")
                    time.sleep(0.1)
                    continue

                # Detect targets
                yolo_targets = self.detect_yolo_targets(frame) if self.config['yolo']['enabled'] else []
                apriltag_targets = self.detect_apriltags(frame) if self.config['apriltag']['enabled'] else []

                # Select best target
                selected_target = self.select_best_target(yolo_targets, apriltag_targets, frame.shape)

                # Calculate target data
                target_data = None
                has_target = False
                if selected_target is not None:
                    target_data = self.calculate_target_data(selected_target, frame.shape)
                    has_target = True

                # Publish to NetworkTables
                self.publish_target(has_target, target_data)

                # Display debug window if enabled
                if self.config['debug']['show_window']:
                    debug_frame = self.draw_overlays(
                        frame.copy(),
                        yolo_targets,
                        apriltag_targets,
                        selected_target,
                        target_data
                    )
                    cv2.imshow('Vision System', debug_frame)

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                # Update FPS
                self.update_fps()

        except KeyboardInterrupt:
            self.logger.info("Vision system stopped by user")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up...")
        self.camera.release()
        cv2.destroyAllWindows()
        self.publish_target(has_target=False)


def main():
    parser = argparse.ArgumentParser(description='FRC Vision System')
    parser.add_argument('--config', default='config.json', help='Path to config file')
    args = parser.parse_args()

    vision = VisionSystem(config_path=args.config)
    vision.run()


if __name__ == '__main__':
    main()
