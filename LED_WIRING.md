# WS2815 LED Strip Wiring Guide

## Overview

This guide covers wiring the BTF-LIGHTING WS2815 16.4ft (300 pixel) LED strip to the RoboRIO.

**LED Strip Specifications:**
- Model: WS2815 (Upgraded WS2812B)
- Length: 16.4ft (5 meters)
- LEDs: 300 pixels
- Voltage: DC 12V
- Data: Dual signal lines (backup line for reliability)
- Type: Individually addressable RGB
- Control: Digital PWM signal

## Components Required

### From Kit
- [ ] WS2815 LED strip (300 LEDs)
- [ ] 12V power supply (see power requirements below)
- [ ] RoboRIO (PWM output)

### Additional Components
- [ ] Power Distribution Panel (PDP) or Power Distribution Hub (PDH)
- [ ] Wire (16-18 AWG for power, 22-24 AWG for signal)
- [ ] 470Ω resistor (for data line protection)
- [ ] 1000µF capacitor (for power smoothing, recommended)
- [ ] Connectors (Anderson Powerpole, XT60, or similar)
- [ ] Heat shrink tubing
- [ ] Zip ties for cable management

## Power Requirements

### Calculating Power Needs

**Maximum Power (all LEDs at full white):**
- Each WS2815 pixel: ~60mA at full brightness
- 300 LEDs × 60mA = 18A at 12V
- Power: 18A × 12V = **216W maximum**

**Typical Power (normal operation):**
- With effects and colors: ~30-50% of maximum
- Expected: **6-9A at 12V (72-108W)**

**Recommended Power Supply:**
- Minimum: 10A at 12V (120W)
- Recommended: 15A at 12V (180W)
- Maximum safe: 20A at 12V (240W)

**Important Notes:**
- Use the robot's 12V power system (from PDP/PDH)
- Ensure adequate circuit breaker rating (15-20A)
- LEDs can be brightness-limited in code to reduce power draw

## Wiring Diagram

### Full System Wiring

```
                    ROBORIO
                  ┌─────────────┐
                  │   PWM 0     │────────┐
                  │             │        │ Signal (Yellow/White)
                  │   GND       │────┐   │
                  └─────────────┘    │   │
                                     │   │
    ┌────────────────────────────────┼───┼──────────────────┐
    │                                │   │                  │
    │  POWER DISTRIBUTION (PDP/PDH)  │   │                  │
    │                                │   │                  │
    │  12V OUT ──────────────────────┼───┼────┐ +12V (Red)  │
    │  GND ──────────────────────────┼───┼──┐ │             │
    │  (15-20A Breaker)              │   │  │ │             │
    └────────────────────────────────┼───┼──┼─┼─────────────┘
                                     │   │  │ │
                                     │   │  │ │
                      ┌──────────────┴───┼──┼─┼─────────┐
                      │   CAPACITOR      │  │ │         │
                      │   1000µF 16V+    │  │ │         │
                      │   + ─────────────┼──┘ │         │
                      │   - ─────────────┼────┘         │
                      └──────────────────┼──────────────┘
                                         │
                      ┌──────────────────┼──────────────┐
                      │  470Ω RESISTOR   │              │
                      │                  │              │
                      └──────────────────┼──────────────┘
                                         │
                      ┌──────────────────┼──────────────┐
                      │   WS2815 STRIP   │              │
                      │                  │              │
                      │  DI (Data In) ◄──┘              │
                      │  BI (Backup)  ◄── (Optional)    │
                      │  12V ◄──────────────────────────┘
                      │  GND ◄──────────────────────────┐
                      │                                 │
                      │  [LED][LED][LED]...[LED] (300x) │
                      │                                 │
                      │  DO (Data Out) (not used)       │
                      │  BO (Backup Out) (not used)     │
                      └─────────────────────────────────┘
```

### LED Strip Connector Pinout

WS2815 strips typically have 4 wires:

```
INPUT CONNECTOR (from controller):
┌─────────────────┐
│ 🔴 RED    = 12V  │
│ ⚪ WHITE  = DI   │  (Data In - connect to RoboRIO PWM)
│ 🟢 GREEN  = BI   │  (Backup Data In - optional)
│ ⚫ BLACK  = GND  │
└─────────────────┘

OUTPUT CONNECTOR (to next strip - not used):
┌─────────────────┐
│ 🔴 RED    = 12V  │
│ 🟡 YELLOW = DO   │  (Data Out)
│ 🔵 BLUE   = BO   │  (Backup Data Out)
│ ⚫ BLACK  = GND  │
└─────────────────┘
```

## Step-by-Step Wiring Instructions

### 1. Power Wiring (12V System)

```
PDP/PDH 12V Terminal
      │
      ├─[15-20A Breaker]─┐
      │                  │
      └─────────────┐    │
                    │    │
               GND  │    │ +12V
                    │    │
                    │    │
         ┌──────────┴────┴──────────┐
         │  1000µF Capacitor        │
         │  (+ to 12V, - to GND)    │
         └──────────┬────┬──────────┘
                    │    │
                    │    └──────────► LED Strip RED (12V)
                    │
                    └───────────────► LED Strip BLACK (GND)
```

**Instructions:**
1. Install 15-20A circuit breaker on PDP/PDH for LED circuit
2. Connect +12V from PDP/PDH through breaker to LED strip RED wire
3. Connect GND from PDP/PDH to LED strip BLACK wire
4. Solder 1000µF capacitor across +12V and GND near LED strip connection
   - Observe polarity! Long leg (+) to +12V, short leg (-) to GND
   - Use capacitor rated for at least 16V

### 2. Signal Wiring (PWM to RoboRIO)

```
RoboRIO PWM 0
     │
     ├── Signal Pin ──[470Ω Resistor]──► LED Strip WHITE (DI)
     │
     └── GND Pin ─────────────────────► LED Strip BLACK (GND)
```

**Instructions:**
1. Cut and strip a 3-wire servo cable or use individual wires
2. Connect RoboRIO PWM 0 signal pin through 470Ω resistor to LED strip WHITE wire (DI)
3. Connect RoboRIO PWM 0 ground pin to LED strip BLACK wire (shared with power ground)
4. Secure resistor with heat shrink tubing
5. **Important:** Do NOT connect RoboRIO PWM +5V to LED strip!

### 3. Optional Backup Signal (WS2815 Feature)

WS2815 has a backup data line for improved reliability:

```
RoboRIO PWM 1 (optional)
     │
     └── Signal Pin ──[470Ω Resistor]──► LED Strip GREEN (BI)
```

**To use backup line:**
1. Connect second PWM channel (PWM 1) to LED strip GREEN wire (BI)
2. Update `LEDConstants::kPWMPort` to use both channels (requires code modification)
3. This provides redundancy - if one data line fails, the other keeps working

**Note:** Basic setup uses only the primary data line (WHITE). Backup is optional.

## Common Wiring Mistakes to Avoid

### ❌ **NEVER DO THIS:**

1. **Powering LEDs from RoboRIO 5V/6V:**
   - WS2815 requires 12V, not 5V
   - RoboRIO cannot supply enough current
   - Will damage RoboRIO

2. **Connecting PWM +5V to LED strip:**
   - Only connect PWM signal and ground
   - LED strip has separate 12V power supply
   - Connecting 5V to 12V LED will cause issues

3. **No resistor on data line:**
   - Data line spike can damage first LED
   - Use 470Ω resistor between PWM and DI

4. **Missing capacitor:**
   - Power spikes can damage LEDs or cause flickering
   - Use 1000µF capacitor across power supply

5. **Inadequate power supply:**
   - Insufficient current causes brownouts
   - Use properly rated breaker (15-20A)

6. **Long data wire without shielding:**
   - Keep data wire short (<1 meter if possible)
   - Use shielded/twisted pair for longer runs

## Physical Installation

### LED Strip Mounting

```
Robot Frame
    │
    ├── LED Strip (adhesive backing)
    │   └── Additional zip ties every 6 inches
    │
    └── Cable routing along frame
```

**Installation Steps:**
1. Clean mounting surface with isopropyl alcohol
2. Plan strip layout to avoid sharp bends (<90°)
3. Apply strip using adhesive backing
4. Add zip ties every 6 inches for vibration resistance
5. Route power and signal cables along frame
6. Use cable management to prevent snagging
7. Ensure strip doesn't interfere with mechanisms

### Cable Routing Best Practices

- Keep power and signal cables separate where possible
- Secure all cables with zip ties
- Avoid routing near motors (electrical noise)
- Leave slack for robot movement
- Protect cables from pinch points
- Label all connections

## Testing Procedure

### 1. Power Test (Before Connecting Signal)

1. Measure voltage at LED strip connector:
   - RED to BLACK should read 12V ± 0.5V
   - If incorrect, check breaker and wiring

2. Verify polarity with multimeter
   - Incorrect polarity can damage LEDs

3. Look for smoke or unusual smells
   - Immediately disconnect if detected

### 2. Initial Signal Test

1. Deploy code to RoboRIO
2. Enable robot
3. Observe LED strip:
   - Should display directional colors
   - Check for flickering (indicates power/signal issues)
   - Verify colors change with robot heading

### 3. Full Function Test

1. Test all LED modes:
   - Directional mode (default)
   - Rainbow mode
   - Team colors mode

2. Test drive integration:
   - LEDs should brighten with joystick input
   - Wave pattern should move when driving

3. Monitor current draw:
   - Check PDP/PDH current reading
   - Should be <10A during normal operation

## Troubleshooting

### No LEDs Lighting Up

**Check:**
- [ ] 12V power connected and breaker not tripped
- [ ] Voltage at LED strip (should be 12V)
- [ ] PWM cable connected to correct port (PWM 0)
- [ ] Ground connection between RoboRIO and LEDs
- [ ] LED code deployed and robot enabled

### Only First Few LEDs Work

**Causes:**
- Voltage drop along strip (insufficient power)
- Data signal degraded

**Solutions:**
- Add power injection mid-strip (12V + GND)
- Reduce brightness in code
- Check data wire connections

### LEDs Flicker or Random Colors

**Causes:**
- Insufficient power
- Noisy data signal
- Missing capacitor
- Poor ground connection

**Solutions:**
- Add/check 1000µF capacitor
- Shorten data wire
- Verify all ground connections
- Move data wire away from motors

### LEDs Don't Match Robot State

**Check:**
- [ ] Code deployed correctly
- [ ] `m_leds.Periodic()` being called
- [ ] `SetHeading()` receiving correct gyro data
- [ ] PWM port matches `kPWMPort` constant

### LEDs Work in Test, Fail in Match

**Common cause:** Voltage drop under load

**Solutions:**
- Reduce brightness: edit `kMaxBrightness` in LEDs.cpp
- Add power injection
- Use higher capacity power supply
- Check all power connections

## Configuration Options

### Adjusting Brightness (Power Saving)

Edit `src/main/cpp/subsystems/LEDs.cpp`:

```cpp
int LEDs::GetSpeedBrightness() {
  constexpr int kMinBrightness = 10;   // Lower = dimmer when stopped
  constexpr int kMaxBrightness = 128;  // Lower = dimmer at full speed (was 255)
  ...
}
```

**Power reduction:**
- 50% brightness (128) = ~25% power (1/4 of max)
- 25% brightness (64) = ~6% power

### Changing PWM Port

Edit `src/main/include/Constants.h`:

```cpp
namespace LEDConstants {
    constexpr int kPWMPort = 0;  // Change to desired PWM port (0-9)
    ...
}
```

### Adjusting Strip Length

If using a different length LED strip, edit `src/main/include/Constants.h`:

```cpp
namespace LEDConstants {
    constexpr int kStripLength = 300;  // Change to actual LED count
    ...
}
```

**And** update `src/main/include/subsystems/LEDs.h`:

```cpp
std::array<frc::AddressableLED::LEDData, 300> m_ledBuffer;  // Change 300 to match
```

### Team Colors

Customize colors in `src/main/include/Constants.h`:

```cpp
namespace LEDConstants {
    // Color 1 - Example: Blue
    constexpr int kTeamColor1_R = 0;
    constexpr int kTeamColor1_G = 0;
    constexpr int kTeamColor1_B = 255;

    // Color 2 - Example: Gold
    constexpr int kTeamColor2_R = 255;
    constexpr int kTeamColor2_G = 215;
    constexpr int kTeamColor2_B = 0;
}
```

## Safety Notes

⚠️ **Important Safety Information:**

1. **Electrical Safety:**
   - Always disconnect battery before wiring
   - Use properly rated circuit breakers
   - Insulate all connections with heat shrink
   - Check for shorts before powering on

2. **Current Draw:**
   - Monitor current with PDP/PDH
   - LEDs can draw significant current at full brightness
   - Consider brightness limiting for battery life

3. **Thermal Management:**
   - LEDs generate heat at high brightness
   - Ensure adequate airflow
   - Check strip temperature during testing

4. **Mechanical Safety:**
   - Secure all cables to prevent entanglement
   - Keep LEDs away from moving parts
   - Protect strip from impact damage

## Competition Checklist

Before competition:
- [ ] All connections secured with heat shrink and zip ties
- [ ] No exposed wire or solder joints
- [ ] Breaker rated correctly (15-20A for 12V)
- [ ] Tested all LED modes (directional, rainbow, team colors)
- [ ] Verified current draw <10A typical, <15A maximum
- [ ] Backup power cable prepared
- [ ] Team knows how to disable LEDs if needed
- [ ] Inspection-ready wiring (neat and labeled)

## Additional Resources

- **WPILib AddressableLED Documentation:**
  https://docs.wpilib.org/en/stable/docs/software/hardware-apis/misc/addressable-leds.html

- **WS2815 Datasheet:**
  Search for "WS2815 datasheet" for detailed specifications

- **FRC Power Distribution:**
  https://docs.wpilib.org/en/stable/docs/hardware/hardware-basics/preemptive-troubleshooting.html

## Support

For issues or questions:
- Check Chief Delphi: https://www.chiefdelphi.com/
- FRC Discord: #programming channel
- Team 3267 programming lead

---

**Good luck with your LED installation! 🤖💡**
