// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#include "subsystems/VisionSystem.h"

VisionSystem::VisionSystem() {
  // Get the NetworkTables instance and the Vision subtable
  auto inst = nt::NetworkTableInstance::GetDefault();
  m_visionTable = inst.GetTable("Vision");
  m_hasTargetEntry = m_visionTable->GetEntry("HasTarget");
}

VisionTarget VisionSystem::GetTarget() {
  VisionTarget target;

  // Read all vision data from NetworkTables
  target.hasTarget = m_visionTable->GetBoolean("HasTarget", false);
  target.yaw = m_visionTable->GetNumber("Yaw", 0.0);
  target.pitch = m_visionTable->GetNumber("Pitch", 0.0);
  target.distance = m_visionTable->GetNumber("Distance", 0.0);
  target.area = m_visionTable->GetNumber("Area", 0.0);
  target.targetID = m_visionTable->GetNumber("TargetID", -1);
  target.isDataFresh = IsDataFresh();

  return target;
}

bool VisionSystem::HasTarget() {
  return m_visionTable->GetBoolean("HasTarget", false);
}

bool VisionSystem::IsDataFresh(double maxAge) {
  // Get the timestamp of the last update to the HasTarget entry
  auto entry = m_hasTargetEntry->GetEntry();
  uint64_t lastChange = entry.GetLastChange();

  // Get current time in microseconds
  uint64_t currentTime = nt::Now();

  // Calculate age in seconds
  double ageSeconds = (currentTime - lastChange) / 1000000.0;

  return ageSeconds < maxAge;
}
