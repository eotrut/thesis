---
tags: [system-design, electronics, wiring]
created: 2026-03-29
updated: 2026-08-04
status: active
---
# 🔌 Electronics & Wiring

> [!info] Related
> [[⚙️ Mechanical Design]] · [[💧 Spray System Design]] · [[🖥️ Serial Communication Protocol]] · [[🛒 Bill of Materials]]

> [!warning] Build correction (2026-08-03)
> **RAMPS 1.4 is NOT part of the current build.** Early design assumed RAMPS as a breakout shield, but the actual hardware is Arduino Mega 2560 wired **directly** to TB6600 drivers. All RAMPS-specific pinouts and Marlin references below are superseded by the direct-wiring section. The serial communication protocol is also **custom** (not standard G-code/Marlin) — see [[🖥️ Serial Communication Protocol]].

## Component Electrical Specs

> [!important] The build needs **3** motors and **3** drivers; 2 of each are procured
> Dual-X is retained — see [[⚙️ Mechanical Design]]. The two procured NEMA 23s are **both for the X-axis** (mirrored, anti-racking). The Y-axis motor and its driver are still outstanding; the budget plan is to borrow/reuse a spare for initial Y testing ([[💰 Budget Tracker]]).

| Component | Spec | Status |
|---|---|---|
| NEMA 23 stepper ×3 | 3A/phase, 24V drive | ⚠️ 2 of 3 procured (both X) |
| TB6600 driver ×3 | up to 4.0A, 9–42V, microstep 1–1/32 | ⚠️ 2 of 3 procured |
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

> [!note] The bench test above drove **one** motor
> Pins 3/4/5 are the confirmed pattern for a single driver. The axis assignments below extend that pattern; they are not yet bench tested.

### Remaining drivers — pins TBD during gantry wiring
| Driver | Axis | Suggested pins (PUL+ / DIR+ / ENA+) | Status |
|---|---|---|---|
| TB6600 #1 | X-left | 3 / 4 / 5 | ✅ Bench tested |
| TB6600 #2 | X-right (mirrored) | 6 / 7 / 8 | Procured, unwired |
| TB6600 #3 | Y | 9 / 10 / 11 | ❌ Not procured |
| Relay | Pump/solenoid | 12 | Pending |

> [!danger] Both X drivers must receive the **same** STEP stream
> Dual-X only prevents racking if the two motors step in lockstep (Risk **R-02**). With no RAMPS to mirror the signal in hardware, this is now the firmware's job: the sketch must pulse both X drivers from one step routine, never as two independent axes. DIR on one side is inverted if the motors face opposite directions — confirm rotation per motor before belting up.

## 24V Power Distribution

> [!important] PSU terminal / branch assignment — DECIDED (2026-08-04)
> The procured PSU (24V/30A "power supply jaring" style metal-box unit) has **3 pairs** of DC output screw terminals (3×"-V", 3×"+V"), plus AC input and grounding. These 3 pairs are **not 3 isolated outputs** — they're all internally tied to the same single 24V rail, just broken out onto multiple screws so high total current can be spread across more than one mechanical connection. Confirmed decision on how the 3 pairs are used:
> - **Pair 1 → both X-axis TB6600 drivers** (X-left + X-right, mirrored). These two always run together, so combining them on one branch reflects the real load — worst case ~3A + 3A = **6A** on this branch.
> - **Pair 2 → Y-axis TB6600 driver.** ~3A.
> - **Pair 3 → spray subsystem** (pump/solenoid, via relay), instead of dedicating a 4th pair that doesn't exist. Typically <2A.
> - Combined worst case ≈ 11A against a 30A-rated supply — comfortable headroom even before accounting for motors rarely drawing full rated current continuously.
> - **This is parallel wiring, not series** — two loads landing on the same +/- pair are just two parallel taps off the same rail, not a chain. Series would incorrectly split the 24V across the two loads and starve both drivers.
> - **Wire gauge:** currently using 14–16 AWG stock. Decision: use **14 AWG** on the shared X branch (carries the highest combined current, ~6A) and 16 AWG is fine for Y and spray. Both gauges have solid margin at these currents for short, open-air robot wiring.
> - **Fusing (still pending, see Safety Considerations below):** recommend fusing each branch separately rather than one fuse for the whole PSU — suggested ~7–8A on the shared X branch, ~4A on Y, and sized to the actual pump/solenoid nameplate draw on the spray branch — so a fault on one branch doesn't take out the others.

```
[24V 30A PSU, terminal pair 1] ──+── TB6600 #1 (X-left)  VCC/GND ──> NEMA23 X-left
                                 └── TB6600 #2 (X-right) VCC/GND ──> NEMA23 X-right   (same pair, parallel — not series)
[24V 30A PSU, terminal pair 2] ───── TB6600 #3 (Y)       VCC/GND ──> NEMA23 Y   [not procured]
[24V 30A PSU, terminal pair 3] ───── Relay ──> Pump/Solenoid (spray subsystem)
[Laptop USB] ─────> Arduino Mega 2560 (5V logic, USB-B)
Common GND: PSU 0V <─────────────> Arduino GND (signal ground)
```
- Motors get **24V** from PSU through drivers.
- Arduino powered by **laptop USB** (keeps logic ground referenced to the serial host).
- **Common ground** the PSU 0V with Arduino GND — required for STEP/DIR signals to work.
- Spray subsystem now shares the same PSU as the motors (see decision above) rather than needing a separate supply.

## Serial Communication (Python → Arduino)
- **USB-B cable: Arduino Mega → laptop**, 115200 baud.
- Python (`serial_ctrl.py` via `pyserial`) sends custom text commands; Arduino replies `ok` after each move completes.
- **No G-code / no Marlin** — custom protocol. See [[🖥️ Serial Communication Protocol]] for command format.

## Spray Pump & Solenoid Wiring
- A **5V relay module** driven by an Arduino digital pin (**Pin 12** — moved off Pin 9, which is now the Y-axis step pin) switches the pump on/off.
- Relay switches pump on its own 12/24V rail.
- Use relay module with onboard opto-isolation/flyback diode.

## Camera
- **USB directly to the laptop.** Not connected to Arduino. Handled entirely by Python/OpenCV ([[🧠 AI & Software Design]]).

## Limit Switch Wiring
- 4 switches → Arduino digital pins directly (with pull-ups enabled in firmware): X-min, X-max, Y-min, spare.
- Wire NC (normally closed) for fail-safe triggering.

## Wiring Diagram (text) — updated
```
PSU 24V+ ─┬─> TB6600 #1 VCC  ──> NEMA23 (X-left)
           ├─> TB6600 #2 VCC  ──> NEMA23 (X-right, mirrored)
           └─> TB6600 #3 VCC  ──> NEMA23 (Y)          [not procured]
PSU GND   ─┬─> TB6600 #1 GND
            ├─> TB6600 #2 GND
            ├─> TB6600 #3 GND
            └─> Arduino GND  (common ground)

Arduino Mega (USB from laptop)
   Pin 3  ──> TB6600 #1 PUL+   (X-left step)     [bench tested]
   Pin 4  ──> TB6600 #1 DIR+   (X-left dir)      [bench tested]
   Pin 5  ──> TB6600 #1 ENA+   (X-left enable, active-low)
   Pin 6  ──> TB6600 #2 PUL+   (X-right step, mirrored — same pulse train as Pin 3)
   Pin 7  ──> TB6600 #2 DIR+   (X-right dir, invert if motor is mounted facing opposite)
   Pin 8  ──> TB6600 #2 ENA+   (X-right enable)
   Pin 9  ──> TB6600 #3 PUL+   (Y step, TBD)
   Pin 10 ──> TB6600 #3 DIR+   (Y dir, TBD)
   Pin 11 ──> TB6600 #3 ENA+   (Y enable, TBD)
   Pin 12 ──> Relay ──> Pump/Solenoid
   Endstop pins ──> limit switches (X-min, X-max, Y-min)
```

> [!note] Homing both X corners
> R-02 mitigation calls for homing *both* X ends, so X-min and X-max are both required — they are not a redundant pair. A skew is detected when the two switches do not trigger within tolerance of each other.

## Safety Considerations
> [!danger] Before first power-on
> - **Fuse each branch separately** — ~7–8A on the shared X branch, ~4A on Y, and sized to the spray subsystem's actual draw — rather than one fuse for the whole 24V line (see PSU terminal/branch decision above).
> - **Strain-relieve** all moving cables (drag chain) to prevent fatigue breaks.
> - **Heatsink + fan** the TB6600 drivers — they get hot at 3A+.
> - **Double-check polarity** and common ground before connecting motors.
> - Never hot-plug motor wires while powered — can destroy a driver instantly.
