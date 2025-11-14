// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#pragma once

#include <frc/XboxController.h>
#include <frc/controller/PIDController.h>
#include <frc/controller/ProfiledPIDController.h>
#include <frc/smartdashboard/SendableChooser.h>
#include <frc2/command/Command.h>
#include <frc2/command/InstantCommand.h>
#include <frc2/command/PIDCommand.h>
#include <frc2/command/ParallelRaceGroup.h>
#include <frc2/command/RunCommand.h>
#include <frc2/command/CommandPtr.h>
#include <rev/SparkMax.h>
#include <rev/SparkLowLevel.h>
#include "Constants.h"
#include "subsystems/VisionSystem.h"
#include "subsystems/DriveSubsystem.h"
/**
 * This class is where the bulk of the robot should be declared.  Since
 * Command-based is a "declarative" paradigm, very little robot logic should
 * actually be handled in the {@link Robot} periodic methods (other than the
 * scheduler calls).  Instead, the structure of the robot (including subsystems,
 * commands, and button mappings) should be declared here.
 */
class RobotContainer {
 public:
  RobotContainer();

  frc2::CommandPtr GetAutonomousCommand();

 private:
  // Controllers
  frc::XboxController m_driverController{OIConstants::kDriverControllerPort};
  frc::XboxController m_coDriverController{OIConstants::kCoDriverControllerPort};

  // The robot's subsystems
  DriveSubsystem m_drive;
  VisionSystem m_vision;

  // Autonomous chooser
  frc::SendableChooser<frc2::Command*> m_chooser;

  // Helper methods
  void ConfigureButtonBindings();
  VisionTarget GetTarget();

  // Drive control state
  bool fieldRelative;
};