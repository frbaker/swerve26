// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#include "subsystems/VisionSystem.h"

VisionSystem::VisionSystem() {
  // Get the NetworkTables instance and the Vision subtable
  auto inst = nt::NetworkTableInstance::GetDefault();
  m_visionTable = inst.GetTable("Vision");
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

  return target;
}

bool VisionSystem::HasTarget() {
  return m_visionTable->GetBoolean("HasTarget", false);
}
