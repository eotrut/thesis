---
tags: [system-design, electronics, wiring]
created: 2026-03-29
status: active
---
# 🔌 Electronics & Wiring

> [!info] Related
> [[⚙️ Mechanical Design]] · [[💧 Spray System Design]] · [[🖥️ Serial Communication Protocol]] · [[🛒 Bill of Materials]]

## Component Electrical Specs
| Component | Spec |
|---|---|
| NEMA 23 stepper ×3 | ~2.8–4.5 A/phase, 24 V drive |
| TB6600 driver ×3 | up to 4.0 A, 9–42 V, microstep 1–1/32 |
| Arduino Mega 2560 | 5 V logic, USB-powered from laptop |
| RAMPS 1.4 | interface shield, 12–24 V logic power via VMM (careful: see below) |
| PSU | 24 V DC, 30 A |
| Relay module | 5 V logic, drives pump + solenoid |
| Limit switches ×4 | NO/NC to endstop pins |

> [!warning] RAMPS voltage caution
> Stock RAMPS 1.4 stepper power (D8/D9/D10 MOSFETs, thermistors) is rated for ~12V paths. AURA drives the **NEMA 23 via external TB6600 drivers, NOT RAMPS onboard Pololu sockets** — RAMPS is used only to break out STEP/DIR/ENABLE and endstop pins. The 24V/30A PSU feeds the **TB6600 drivers directly**, not the RAMPS 5A/11A input. This avoids overloading RAMPS traces.

## TB6600 DIP-Switch Configuration (per driver)
For NEMA 23 with the 40 steps/mm calc in [[⚙️ Mechanical Design]]:
- **Microstepping: 1/8** (start here; move to 1/16 if smoother motion needed).
- **Current: ~3.0–4.0 A** set to just below motor rating; start ~3.0A and increase only if steps are lost.

| Setting | S1 | S2 | S3 | S4 | S5 | S6 |
|---|---|---|---|---|---|---|
| Microstep 1/8 (typical) | ON | ON | OFF | — | — | — |
| Current ~3.0A (typical) | — | — | — | ON | OFF | ON |

> [!note] DIP tables vary by TB6600 clone — **always confirm against the label printed on your specific driver** before powering motors.

## RAMPS 1.4 Pinout for 3 External Drivers
Break out from the RAMPS stepper headers (STEP/DIR/EN) to the TB6600 PUL/DIR/ENA inputs:
| Axis | STEP pin | DIR pin | EN pin | TB6600 |
|---|---|---|---|---|
| X1 | 54 (A0) | 55 (A1) | 38 | Driver 1 |
| X2 (mirror) | 60 (A6)/E1 header | 61 (A7) | 56 | Driver 2 |
| Y | 60 (A6) | 61 (A7) | 56 | Driver 3 |

> [!tip] Dual-X mirroring
> In Marlin, set `X2` as a driver on the E1 socket header and enable dual-X, or physically wire both X drivers to the same STEP/DIR (simplest for GRBL). Both X motors must step identically — see [[⚙️ Mechanical Design]] anti-racking.

## 24 V Power Distribution
```
[24V 30A PSU] ──+── TB6600 #1 (X1)  VCC/GND
                +── TB6600 #2 (X2)
                +── TB6600 #3 (Y)
                +── (via buck to 12V if pump/solenoid are 12V)
[Laptop USB] ─────> Arduino Mega (5V logic, USB-B)
```
- Motors get **24 V** from the PSU through the drivers.
- Arduino is powered by **laptop USB** (keeps logic ground referenced to the serial host).
- **Common ground** the PSU 0V with the Arduino/RAMPS logic ground for the STEP/DIR signals.

## Spray Pump & Solenoid Wiring
- A **5V relay module** channel is driven by an Arduino digital pin (e.g., **D9**) mapped to **M3/M5**.
- Relay switches the **pump** (and/or **solenoid valve**) on its own 12/24 V rail.
- Flyback protection: use a relay module with onboard diode/opto-isolation.

## Camera
- **USB directly to the laptop.** Not connected to Arduino. Handled entirely by Python/OpenCV ([[🧠 AI & Software Design]]).

## Limit Switch Wiring
- 4 switches → RAMPS endstop pins: **X-min, X-max (for dual homing), Y-min**, plus one spare.
- Wire NC (normally closed) for fail-safe triggering; enable pull-ups in firmware.

## Serial Link
- **Arduino Mega USB-B → laptop USB-A**, 115200 baud. This is also the power source for the Arduino logic.

## Safety Considerations
> [!danger] Before first power-on
> - **Fuse the 24 V line** (e.g., inline 20–25 A) close to the PSU.
> - **Strain-relieve** all moving cables (drag chain) to prevent fatigue breaks.
> - **Heatsink + fan** the TB6600 drivers; they get hot at 3A+.
> - **Double-check polarity** and common ground before connecting motors.
> - Never hot-plug motor wires while powered — can destroy a driver.

## Wiring Diagram (text)
```
PSU 24V+ ─┬─> TB6600(X1) ─> NEMA23 X1
          ├─> TB6600(X2) ─> NEMA23 X2
          └─> TB6600(Y)  ─> NEMA23 Y
Arduino Mega (USB from laptop)
   D54/55  -> X1 PUL/DIR
   (mirror)-> X2 PUL/DIR
   D60/61  -> Y  PUL/DIR
   D9      -> Relay -> Pump/Solenoid (12/24V rail)
   Endstops-> X-min, X-max, Y-min
Common GND: PSU 0V <-> Arduino GND
```
