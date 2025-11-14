// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#include "RobotContainer.h"

#include <frc/controller/PIDController.h>
#include <frc/geometry/Translation2d.h>
#include <frc/smartdashboard/SmartDashboard.h>
#include <frc2/command/InstantCommand.h>
#include <frc2/command/RunCommand.h>
#include <frc2/command/button/JoystickButton.h>
#include <units/angle.h>
#include <units/velocity.h>
#include <cmath>

#include "Constants.h"
#include "subsystems/DriveSubsystem.h"

#include <pathplanner/lib/commands/PathPlannerAuto.h>
#include <pathplanner/lib/auto/NamedCommands.h>

using namespace pathplanner;
using namespace DriveConstants;

RobotContainer::RobotContainer() : fieldRelative(FIELD_RELATIVE) {
  // Register any named commands for PathPlanner
  // Example:
  // NamedCommands::registerCommand("exampleCommand", m_subsystem.ExampleCommand());

  // Configure the button bindings
  ConfigureButtonBindings();

  // Set up default drive command
  // The left stick controls translation of the robot.
  // Turning is controlled by the X axis of the right stick.
  m_drive.SetDefaultCommand(frc2::RunCommand(
      [this] {
        double xSpeed = -frc::ApplyDeadband(
            m_driverController.GetLeftY(), OIConstants::kDriveDeadband);
        double ySpeed = -frc::ApplyDeadband(
            m_driverController.GetLeftX(), OIConstants::kDriveDeadband);
        double rotSpeed = -frc::ApplyDeadband(
            m_driverController.GetRightX(), OIConstants::kDriveDeadband);

        // Drive the robot
        m_drive.Drive(
            units::meters_per_second_t{xSpeed},
            units::meters_per_second_t{ySpeed},
            units::radians_per_second_t{rotSpeed},
            fieldRelative, true);

        // Update LEDs with robot state
        m_leds.SetHeading(m_drive.GetHeading());
        double speed = std::sqrt(xSpeed * xSpeed + ySpeed * ySpeed);
        m_leds.SetSpeed(speed);
        m_leds.SetDriveVector(xSpeed, ySpeed);
      },
      {&m_drive}));
}

VisionTarget RobotContainer::GetTarget() {
  // Simply return the current target from the vision system
  // No filtering needed - the OrangePi vision system will handle target selection
  return m_vision.GetTarget();
}

void RobotContainer::ConfigureButtonBindings() {
  // ==========================================================================
  // DRIVER CONTROLLER BINDINGS
  // ==========================================================================

  // Zero Heading - X button
  frc2::JoystickButton(&m_driverController, frc::XboxController::Button::kX)
      .WhileTrue(new frc2::RunCommand([this] { m_drive.ZeroHeading(); }, {&m_drive}));

  // Field Relative Toggle
  frc2::JoystickButton(&m_driverController, frc::XboxController::Button::kBack)
      .WhileTrue(new frc2::RunCommand([this] { fieldRelative = false; }, {&m_drive}));

  frc2::JoystickButton(&m_driverController, frc::XboxController::Button::kStart)
      .WhileTrue(new frc2::RunCommand([this] { fieldRelative = true; }, {&m_drive}));

  // Vision-Assisted Rotation - Left Bumper
  // Robot auto-rotates to face target with PID, driver controls forward/backward movement
  frc2::JoystickButton(&m_driverController, frc::XboxController::Button::kLeftBumper)
      .WhileTrue(new frc2::RunCommand(
          [this] {
            double xSpeed = -frc::ApplyDeadband(
                m_driverController.GetLeftY(), OIConstants::kDriveDeadband);
            double ySpeed = -frc::ApplyDeadband(
                m_driverController.GetLeftX(), OIConstants::kDriveDeadband);

            VisionTarget target = GetTarget();
            if (target.hasTarget && target.isDataFresh) {
              frc::SmartDashboard::PutNumber("targetYaw", target.yaw);
              frc::SmartDashboard::PutBoolean("visionActive", true);
              // Driver controls movement, robot auto-rotates to face target
              m_drive.PhotonDrive(
                  units::meters_per_second_t{xSpeed},
                  units::meters_per_second_t{ySpeed},
                  units::degree_t(target.yaw));
            } else {
              frc::SmartDashboard::PutBoolean("visionActive", false);
              double rotSpeed = -frc::ApplyDeadband(
                  m_driverController.GetRightX(), OIConstants::kDriveDeadband);
              // Fallback to normal driver control
              m_drive.Drive(
                  units::meters_per_second_t{xSpeed},
                  units::meters_per_second_t{ySpeed},
                  units::radians_per_second_t{rotSpeed},
                  fieldRelative, true);
            }

            // Update LEDs
            m_leds.SetHeading(m_drive.GetHeading());
            double speed = std::sqrt(xSpeed * xSpeed + ySpeed * ySpeed);
            m_leds.SetSpeed(speed);
            m_leds.SetDriveVector(xSpeed, ySpeed);
          },
          {&m_drive}));

  // Full Auto-Drive - Right Bumper
  // Robot auto-rotates AND auto-drives to target with PID control
  frc2::JoystickButton(&m_driverController, frc::XboxController::Button::kRightBumper)
      .WhileTrue(new frc2::RunCommand(
          [this] {
            VisionTarget target = GetTarget();
            if (target.hasTarget && target.isDataFresh) {
              frc::SmartDashboard::PutNumber("targetArea", target.area);
              frc::SmartDashboard::PutNumber("targetDistance", target.distance);
              frc::SmartDashboard::PutNumber("targetYaw", target.yaw);
              frc::SmartDashboard::PutBoolean("visionActive", true);
              // Robot auto-rotates and auto-drives to target
              units::meter_t distance{target.distance};
              m_drive.TractorBeam(distance, false, units::degree_t(target.yaw), target.area);

              // Update LEDs with autonomous drive state
              m_leds.SetHeading(m_drive.GetHeading());
              m_leds.SetSpeed(0.8);  // Show high speed during autonomous
              m_leds.SetDriveVector(0.8, 0.0);  // Forward motion
            } else {
              frc::SmartDashboard::PutBoolean("visionActive", false);
              double xSpeed = -frc::ApplyDeadband(
                  m_driverController.GetLeftY(), OIConstants::kDriveDeadband);
              double ySpeed = -frc::ApplyDeadband(
                  m_driverController.GetLeftX(), OIConstants::kDriveDeadband);
              double rotSpeed = -frc::ApplyDeadband(
                  m_driverController.GetRightX(), OIConstants::kDriveDeadband);
              // Fallback to normal driver control
              m_drive.Drive(
                  units::meters_per_second_t{xSpeed},
                  units::meters_per_second_t{ySpeed},
                  units::radians_per_second_t{rotSpeed},
                  fieldRelative, true);

              // Update LEDs
              m_leds.SetHeading(m_drive.GetHeading());
              double speed = std::sqrt(xSpeed * xSpeed + ySpeed * ySpeed);
              m_leds.SetSpeed(speed);
              m_leds.SetDriveVector(xSpeed, ySpeed);
            }
          },
          {&m_drive}));

  // Vision-assisted Drive - B Button (same as left bumper)
  // Driver controls driving, robot rotates to face target
  frc2::JoystickButton(&m_driverController, frc::XboxController::Button::kB)
      .WhileTrue(new frc2::RunCommand(
          [this] {
            double xSpeed = -frc::ApplyDeadband(
                m_driverController.GetLeftY(), OIConstants::kDriveDeadband);
            double ySpeed = -frc::ApplyDeadband(
                m_driverController.GetLeftX(), OIConstants::kDriveDeadband);

            VisionTarget target = GetTarget();
            if (target.hasTarget && target.isDataFresh) {
              frc::SmartDashboard::PutBoolean("visionActive", true);
              m_drive.PhotonDrive(
                  // driver controls direction of travel, rotation faces target
                  units::meters_per_second_t{xSpeed},
                  units::meters_per_second_t{ySpeed},
                  units::degree_t(target.yaw));
            } else {
              frc::SmartDashboard::PutBoolean("visionActive", false);
              double rotSpeed = -frc::ApplyDeadband(
                  m_driverController.GetRightX(), OIConstants::kDriveDeadband);
              // Fallback to normal driver control
              m_drive.Drive(
                  units::meters_per_second_t{xSpeed},
                  units::meters_per_second_t{ySpeed},
                  units::radians_per_second_t{rotSpeed},
                  fieldRelative, true);
            }

            // Update LEDs
            m_leds.SetHeading(m_drive.GetHeading());
            double speed = std::sqrt(xSpeed * xSpeed + ySpeed * ySpeed);
            m_leds.SetSpeed(speed);
            m_leds.SetDriveVector(xSpeed, ySpeed);
          },
          {&m_drive}));

  // ==========================================================================
  // CO-DRIVER CONTROLLER BINDINGS
  // ==========================================================================

  // Add co-driver bindings for new season mechanisms here
  // Example button bindings:
  //
  // frc2::JoystickButton(&m_coDriverController, frc::XboxController::Button::kA)
  //     .WhileTrue(new frc2::RunCommand([this] { m_mechanism.DoAction(); }, {&m_mechanism}));
  //
  // frc2::JoystickButton(&m_coDriverController, frc::XboxController::Button::kB)
  //     .OnTrue(new frc2::InstantCommand([this] { m_mechanism.Toggle(); }, {&m_mechanism}));
  //
  // POV control example:
  // if (m_coDriverController.GetPOV() == 0) {  // Up on D-pad
  //     m_mechanism.SetPosition(1);
  // }
}

frc2::CommandPtr RobotContainer::GetAutonomousCommand() {
  // Return autonomous command
  // Update with actual auto routine name when configured in PathPlanner
  return PathPlannerAuto("ExampleAuto").ToPtr();
}
