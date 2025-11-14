// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#include "subsystems/LEDs.h"
#include "Constants.h"
#include <frc/DriverStation.h>
#include <frc/smartdashboard/SmartDashboard.h>
#include <algorithm>
#include <cmath>
#include <cstdlib>

LEDs::LEDs() : m_led(LEDConstants::kPWMPort) {
  // Set LED strip length
  m_led.SetLength(m_ledBuffer.size());

  // Initialize buffer to off
  for (auto& led : m_ledBuffer) {
    led.SetRGB(0, 0, 0);
  }

  // Initialize heat map to zero
  for (auto& heat : m_heat) {
    heat = 0;
  }

  // Set data
  m_led.SetData(m_ledBuffer);

  // Start output
  m_led.Start();
}

void LEDs::Periodic() {
  // If LEDs are manually disabled, turn them off
  if (!m_enabled) {
    UpdateDisabledMode();
    m_led.SetData(m_ledBuffer);
    frc::SmartDashboard::PutString("LED Mode", "Disabled (Manual)");
    return;
  }

  // Track if robot has been enabled (for post-match fire effect)
  if (!frc::DriverStation::IsDisabled()) {
    m_hasBeenEnabled = true;
  }

  // When robot is disabled
  if (frc::DriverStation::IsDisabled()) {
    // Before match (never been enabled): No LEDs
    if (!m_hasBeenEnabled) {
      UpdateDisabledMode();
      m_led.SetData(m_ledBuffer);
      frc::SmartDashboard::PutString("LED Mode", "Off (Pre-Match)");
      return;
    }
    // After match (has been enabled): Fire effect
    else {
      UpdateFireMode();
      m_led.SetData(m_ledBuffer);
      frc::SmartDashboard::PutString("LED Mode", "Fire (Post-Match)");
      return;
    }
  }

  // When robot is enabled, use selected mode
  switch (m_mode) {
    case Mode::kDirectional:
      UpdateDirectionalMode();
      frc::SmartDashboard::PutString("LED Mode", "Directional");
      break;
    case Mode::kRainbow:
      UpdateRainbowMode();
      frc::SmartDashboard::PutString("LED Mode", "Rainbow");
      break;
    case Mode::kTeamColors:
      UpdateTeamColorsMode();
      frc::SmartDashboard::PutString("LED Mode", "Team Colors");
      break;
    case Mode::kFire:
      UpdateFireMode();
      frc::SmartDashboard::PutString("LED Mode", "Fire");
      break;
    case Mode::kDisabled:
      UpdateDisabledMode();
      frc::SmartDashboard::PutString("LED Mode", "Disabled");
      break;
  }

  // Publish debug data to SmartDashboard
  frc::SmartDashboard::PutNumber("LED Heading", m_heading.value());
  frc::SmartDashboard::PutNumber("LED Speed", m_speed);
  frc::SmartDashboard::PutBoolean("LED Has Been Enabled", m_hasBeenEnabled);

  // Update the LED strip
  m_led.SetData(m_ledBuffer);
}

void LEDs::SetHeading(units::degree_t heading) {
  m_heading = heading;
}

void LEDs::SetSpeed(double speed) {
  m_speed = std::clamp(speed, 0.0, 1.0);
}

void LEDs::SetDriveVector(double xSpeed, double ySpeed) {
  m_xSpeed = std::clamp(xSpeed, -1.0, 1.0);
  m_ySpeed = std::clamp(ySpeed, -1.0, 1.0);
}

void LEDs::SetEnabled(bool enabled) {
  m_enabled = enabled;
}

void LEDs::SetMode(Mode mode) {
  m_mode = mode;
}

void LEDs::UpdateDirectionalMode() {
  int hue = GetDirectionalHue();
  int brightness = GetSpeedBrightness();

  // Calculate chase pattern based on drive direction
  double driveAngle = std::atan2(m_ySpeed, m_xSpeed);
  int numLEDs = m_ledBuffer.size();

  // Front-to-back chase effect when driving
  if (m_speed > 0.1) {
    m_chaseOffset = (m_chaseOffset + 1) % numLEDs;

    for (int i = 0; i < numLEDs; i++) {
      // Create wave pattern that moves based on drive direction
      int wavePosition = (i + m_chaseOffset) % numLEDs;
      double wave = std::sin(wavePosition * 2.0 * M_PI / 20.0);  // 20 LED wave period

      // Adjust brightness with wave
      int ledBrightness = brightness * (0.5 + 0.5 * wave);
      ledBrightness = std::clamp(ledBrightness, 20, 255);  // Minimum brightness

      m_ledBuffer[i] = HSV(hue, 255, ledBrightness);
    }
  } else {
    // Solid color when stationary
    for (auto& led : m_ledBuffer) {
      led = HSV(hue, 255, std::max(20, brightness));
    }
  }
}

void LEDs::UpdateRainbowMode() {
  // Rainbow chase pattern
  int numLEDs = m_ledBuffer.size();

  for (int i = 0; i < numLEDs; i++) {
    // Calculate hue based on position and time
    int hue = ((m_rainbowFirstPixelHue + (i * 180 / numLEDs)) % 180);
    m_ledBuffer[i] = HSV(hue, 255, 128);
  }

  // Increment for animation
  m_rainbowFirstPixelHue = (m_rainbowFirstPixelHue + 3) % 180;
}

void LEDs::UpdateTeamColorsMode() {
  // Solid team colors - customize for your team
  // Example: Split strip in half with two colors
  int halfLength = m_ledBuffer.size() / 2;

  for (int i = 0; i < halfLength; i++) {
    m_ledBuffer[i].SetRGB(
        LEDConstants::kTeamColor1_R,
        LEDConstants::kTeamColor1_G,
        LEDConstants::kTeamColor1_B);
  }

  for (int i = halfLength; i < static_cast<int>(m_ledBuffer.size()); i++) {
    m_ledBuffer[i].SetRGB(
        LEDConstants::kTeamColor2_R,
        LEDConstants::kTeamColor2_G,
        LEDConstants::kTeamColor2_B);
  }
}

void LEDs::UpdateFireMode() {
  // Fire effect inspired by FastLED's Fire2012
  // Perfect for edge-lighting - looks like flames rising!

  int numLEDs = m_ledBuffer.size();

  // Step 1: Cool down every LED slightly
  for (int i = 0; i < numLEDs; i++) {
    // Cooling rate: Higher = faster cooling (dimmer fire)
    // Random cooling between 0-20 creates flickering effect
    int cooling = std::rand() % 20;
    int cooldown = (cooling > m_heat[i]) ? 0 : (m_heat[i] - cooling);
    m_heat[i] = cooldown;
  }

  // Step 2: Heat diffuses upward (heat rises like real fire)
  for (int k = numLEDs - 1; k >= 2; k--) {
    m_heat[k] = (m_heat[k - 1] + m_heat[k - 2] + m_heat[k - 2]) / 3;
  }

  // Step 3: Randomly ignite new "sparks" at the bottom
  // Sparking rate: Higher = more frequent sparks (more intense fire)
  if (std::rand() % 100 < 80) {  // 80% chance of spark
    int sparkPos = std::rand() % 7;  // Sparks in bottom 7 LEDs
    m_heat[sparkPos] = std::min(255, m_heat[sparkPos] + std::rand() % (255 - 160) + 160);
  }

  // Step 4: Convert heat to LED colors
  for (int j = 0; j < numLEDs; j++) {
    m_ledBuffer[j] = HeatToColor(m_heat[j]);
  }
}

void LEDs::UpdateDisabledMode() {
  // Turn off all LEDs
  for (auto& led : m_ledBuffer) {
    led.SetRGB(0, 0, 0);
  }
}

frc::AddressableLED::LEDData LEDs::HSV(int h, int s, int v) {
  // Convert HSV to RGB
  // H: 0-180 (WPILib uses half the standard 0-360 range)
  // S: 0-255
  // V: 0-255

  frc::AddressableLED::LEDData led;

  if (s == 0) {
    // Grayscale
    led.SetRGB(v, v, v);
    return led;
  }

  int region = h / 30;
  int remainder = (h - (region * 30)) * 6;

  int p = (v * (255 - s)) >> 8;
  int q = (v * (255 - ((s * remainder) >> 8))) >> 8;
  int t = (v * (255 - ((s * (255 - remainder)) >> 8))) >> 8;

  switch (region) {
    case 0:
      led.SetRGB(v, t, p);
      break;
    case 1:
      led.SetRGB(q, v, p);
      break;
    case 2:
      led.SetRGB(p, v, t);
      break;
    case 3:
      led.SetRGB(p, q, v);
      break;
    case 4:
      led.SetRGB(t, p, v);
      break;
    default:
      led.SetRGB(v, p, q);
      break;
  }

  return led;
}

int LEDs::GetDirectionalHue() {
  // Convert heading (0-360 degrees) to hue (0-180)
  // This creates a color wheel effect where different headings = different colors
  double degrees = m_heading.value();

  // Normalize to 0-360
  while (degrees < 0) degrees += 360;
  while (degrees >= 360) degrees -= 360;

  // Map to 0-180 hue range
  int hue = static_cast<int>(degrees / 2.0);

  return hue;
}

int LEDs::GetSpeedBrightness() {
  // Map speed (0-1) to brightness (min to max)
  constexpr int kMinBrightness = 20;   // Dim when stopped
  constexpr int kMaxBrightness = 255;  // Full brightness at max speed

  int brightness = kMinBrightness +
                   static_cast<int>(m_speed * (kMaxBrightness - kMinBrightness));

  return std::clamp(brightness, kMinBrightness, kMaxBrightness);
}

frc::AddressableLED::LEDData LEDs::HeatToColor(uint8_t heat) {
  // Convert heat value to fire color palette
  // Heat scale: 0 (black) → 255 (white hot)
  // Color progression: Black → Red → Orange → Yellow → White

  frc::AddressableLED::LEDData color;

  // Cool colors (0-85): Black → Dark Red → Red
  if (heat < 85) {
    int red = heat * 3;  // 0 → 255
    color.SetRGB(red, 0, 0);
  }
  // Medium heat (85-170): Red → Orange → Yellow
  else if (heat < 170) {
    int red = 255;
    int green = (heat - 85) * 3;  // 0 → 255
    color.SetRGB(red, green, 0);
  }
  // Hot (170-255): Yellow → White
  else {
    int red = 255;
    int green = 255;
    int blue = (heat - 170) * 3;  // 0 → 255
    color.SetRGB(red, green, blue);
  }

  return color;
}
