// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#pragma once

#include <networktables/NetworkTable.h>
#include <networktables/NetworkTableInstance.h>
#include <units/angle.h>
#include <units/length.h>

/**
 * Structure to hold vision target data from NetworkTables
 */
struct VisionTarget {
    bool hasTarget = false;
    bool isDataFresh = false;   // true if data was updated recently
    double yaw = 0.0;           // degrees
    double pitch = 0.0;         // degrees
    double distance = 0.0;      // meters
    double area = 0.0;          // percentage (0-100)
    int targetID = -1;          // optional ID, -1 if not used
};

/**
 * VisionSystem class to interface with custom vision processing
 * running on an OrangePi (or other coprocessor).
 *
 * The vision system should publish target data to NetworkTables
 * at the following paths:
 * - /Vision/HasTarget (boolean)
 * - /Vision/Yaw (double, degrees)
 * - /Vision/Pitch (double, degrees)
 * - /Vision/Distance (double, meters)
 * - /Vision/Area (double, percentage 0-100)
 * - /Vision/TargetID (int, optional, -1 if not used)
 */
class VisionSystem {
 public:
  VisionSystem();

  /**
   * Get the latest target data from NetworkTables
   * @return VisionTarget struct with current vision data
   */
  VisionTarget GetTarget();

  /**
   * Check if a valid target is currently visible
   * @return true if a target is detected
   */
  bool HasTarget();

  /**
   * Check if vision data is fresh (updated recently)
   * @param maxAge Maximum age in seconds (default 0.5s)
   * @return true if data was updated within maxAge seconds
   */
  bool IsDataFresh(double maxAge = 0.5);

 private:
  std::shared_ptr<nt::NetworkTable> m_visionTable;
  std::shared_ptr<nt::NetworkTableEntry> m_hasTargetEntry;
};
