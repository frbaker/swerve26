// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#pragma once

#include <frc2/command/SubsystemBase.h>
#include <frc/AddressableLED.h>
#include <array>
#include <units/angle.h>
#include <units/velocity.h>

/**
 * LED Subsystem for WS2815 individually addressable LED strip
 *
 * Features:
 * - Direction-based colors (robot heading determines hue)
 * - Speed-based intensity and effects
 * - Front-to-back chase patterns based on movement
 * - Multiple visual modes
 */
class LEDs : public frc2::SubsystemBase {
 public:
  LEDs();

  /**
   * Update LED strip based on robot state
   * Call this periodically from Robot.cpp
   */
  void Periodic() override;

  /**
   * Set the current robot heading for directional colors
   * @param heading Robot heading in degrees (0-360)
   */
  void SetHeading(units::degree_t heading);

  /**
   * Set the current drive speed for intensity effects
   * @param speed Robot speed magnitude (0-1)
   */
  void SetSpeed(double speed);

  /**
   * Set the current drive direction for chase patterns
   * @param xSpeed Forward/backward speed (-1 to 1)
   * @param ySpeed Left/right speed (-1 to 1)
   */
  void SetDriveVector(double xSpeed, double ySpeed);

  /**
   * Enable/disable LEDs
   */
  void SetEnabled(bool enabled);

  /**
   * Set LED mode
   */
  enum class Mode {
    kDirectional,      // Color based on heading, intensity on speed
    kRainbow,          // Rainbow chase pattern
    kTeamColors,       // Solid team colors
    kFire,             // Fire/flame effect (great for edge-lighting!)
    kDisabled          // LEDs off
  };

  void SetMode(Mode mode);

 private:
  frc::AddressableLED m_led;
  std::array<frc::AddressableLED::LEDData, 300> m_ledBuffer;

  units::degree_t m_heading{0};
  double m_speed{0.0};
  double m_xSpeed{0.0};
  double m_ySpeed{0.0};
  bool m_enabled{true};
  Mode m_mode{Mode::kDirectional};

  // Track if robot has been enabled (used for match vs pre-match)
  bool m_hasBeenEnabled{false};

  int m_rainbowFirstPixelHue{0};
  int m_chaseOffset{0};

  // Fire effect heat map (one heat value per LED)
  std::array<uint8_t, 300> m_heat;

  // Helper functions
  void UpdateDirectionalMode();
  void UpdateRainbowMode();
  void UpdateTeamColorsMode();
  void UpdateFireMode();
  void UpdateDisabledMode();

  /**
   * Convert HSV to RGB for LED data
   * @param h Hue (0-180)
   * @param s Saturation (0-255)
   * @param v Value/Brightness (0-255)
   */
  frc::AddressableLED::LEDData HSV(int h, int s, int v);

  /**
   * Get color based on robot heading
   * @return Hue value (0-180) based on heading
   */
  int GetDirectionalHue();

  /**
   * Get brightness based on speed
   * @return Value (0-255) based on speed
   */
  int GetSpeedBrightness();

  /**
   * Convert heat value to fire color
   * @param heat Heat value (0-255)
   * @return LED color (black → red → orange → yellow → white)
   */
  frc::AddressableLED::LEDData HeatToColor(uint8_t heat);
};
