---
tags: [system-design, electronics, wiring]
created: 2026-03-29
updated: 2026-08-03
status: active
---
# 🔌 Electronics & Wiring

> [!info] Related
> [[⚙️ Mechanical Design]] · [[💧 Spray System Design]] · [[🖥️ Serial Communication Protocol]] · [[🛒 Bill of Materials]]

> [!warning] Build correction (2026-08-03)
> **RAMPS 1.4 is NOT part of the current build.** Early design assumed RAMPS as a breakout shield, but the actual hardware is Arduino Mega 2560 wired **directly** to TB6600 drivers. All RAMPS-specific pinouts and Marlin references below are superseded by the direct-wiring section. The serial communication protocol is also **custom** (not standard G-code/Marlin) — see [[🖥️ Serial Communication Protocol]].

## Component Electrical Specs
| Component | Spec | Status |
|---|---|---|
| NEMA 23 stepper ×2 | 3A/phase, 24V drive | ✅ Procured |
| TB6600 driver ×2 | up to 4.0A, 9–42V, microstep 1–1/32 | ✅ Procured |
| Arduino Mega 2560 | 5V logic, USB-powered from laptop | ✅ Procured |
| ~~RAMPS 1.4~~ | ~~interface shield~~ | ❌ Not in build |
| PSU | 24V DC, 30A | ✅ Procured |
| Relay module | 5V logic, drives pump + solenoid | Pending |
| Limit switches ×4 | NO/NC to endstop pins | Pending |

## TB6600 DIP-Switch Configuration (per driver)

> [!note] Confirmed settings (2026-08-03 bench test)
> Tested at 32 microsteps / 6400 pulses per revolution. Motor runs smoothly at 3A. These are the actual confirmed settings — update if changed during gantry integration.

| Setting | Description | Result |
|---|---|---|
| All microstep switches OFF | 32 microsteps | 6400 pulses/rev |
| Current switches | 3A | Matched to NEMA23 spec |

> [!note] DIP tables vary by TB6600 clone — **always confirm against the label printed on your specific driver** before powering motors.

## Direct Arduino Mega 2560 → TB6600 Wiring (No RAMPS)

### Confirmed pin assignments (bench tested 2026-08-03)
| Signal | TB6600 Pin | Arduino Mega Pin | Notes |
|---|---|---|---|
| Step pulse | PUL+ | Pin 3 | 5V logic |
| Direction | DIR+ | Pin 4 | HIGH = CW, LOW = CCW |
| Enable | ENA+ | Pin 5 | **Active-low** — LOW = enabled, HIGH = disabled |
| Common GND | PUL−, DIR−, ENA− | GND rail | All three share one GND rail |

> [!danger] ENA is active-low on this TB6600 unit
> Tying ENA+ to 5V **disables** the driver. Confirmed during 2026-08-03 bench test. Code must pull ENA LOW to enable the motor. Motor de-energizes (free to spin) when ENA is HIGH — use this for idle periods to reduce heat.

### For second motor (Y-axis) — pins TBD during gantry wiring
Suggested: PUL+ → Pin 6, DIR+ → Pin 7, ENA+ → Pin 8 (same wiring pattern, different pins).

## 24V Power Distribution
```
[24V 30A PSU] ──+── TB6600 #1 (X-axis) VCC/GND ──> NEMA23 X
                └── TB6600 #2 (Y-axis) VCC/GND ──> NEMA23 Y
[Laptop USB] ─────> Arduino Mega 2560 (5V logic, USB-B)
Common GND: PSU 0V <─────────────> Arduino GND (signal ground)
```
- Motors get **24V** from PSU through drivers.
- Arduino powered by **laptop USB** (keeps logic ground referenced to the serial host).
- **Common ground** the PSU 0V with Arduino GND — required for STEP/DIR signals to work.

## Serial Communication (Python → Arduino)
- **USB-B cable: Arduino Mega → laptop**, 115200 baud.
- Python (`serial_ctrl.py` via `pyserial`) sends custom text commands; Arduino replies `ok` after each move completes.
- **No G-code / no Marlin** — custom protocol. See [[🖥️ Serial Communication Protocol]] for command format.

## Spray Pump & Solenoid Wiring
- A **5V relay module** driven by an Arduino digital pin (e.g., **Pin 9**) switches the pump on/off.
- Relay switches pump on its own 12/24V rail.
- Use relay module with onboard opto-isolation/flyback diode.

## Camera
- **USB directly to the laptop.** Not connected to Arduino. Handled entirely by Python/OpenCV ([[🧠 AI & Software Design]]).

## Limit Switch Wiring
- 4 switches → Arduino digital pins directly (with pull-ups enabled in firmware): X-min, X-max, Y-min, spare.
- Wire NC (normally closed) for fail-safe triggering.

## Wiring Diagram (text) — updated
```
PSU 24V+ ─┬─> TB6600 #1 VCC  ──> NEMA23 (X-axis)
           └─> TB6600 #2 VCC  ──> NEMA23 (Y-axis)
PSU GND   ─┬─> TB6600 #1 GND
            ├─> TB6600 #2 GND
            └─> Arduino GND  (common ground)

Arduino Mega (USB from laptop)
   Pin 3  ──> TB6600 #1 PUL+   (X step)
   Pin 4  ──> TB6600 #1 DIR+   (X dir)
   Pin 5  ──> TB6600 #1 ENA+   (X enable, active-low)
   Pin 6  ──> TB6600 #2 PUL+   (Y step, TBD)
   Pin 7  ──> TB6600 #2 DIR+   (Y dir, TBD)
   Pin 8  ──> TB6600 #2 ENA+   (Y enable, TBD)
   Pin 9  ──> Relay ──> Pump/Solenoid
   Endstop pins ──> limit switches (X-min, X-max, Y-min)
```

## Safety Considerations
> [!danger] Before first power-on
> - **Fuse the 24V line** (e.g., inline 20–25A) close to the PSU.
> - **Strain-relieve** all moving cables (drag chain) to prevent fatigue breaks.
> - **Heatsink + fan** the TB6600 drivers — they get hot at 3A+.
> - **Double-check polarity** and common ground before connecting motors.
> - Never hot-plug motor wires while powered — can destroy a driver instantly.
