---
tags: [system-design, spray, mechanical]
created: 2026-03-29
status: active
---
# 💧 Spray System Design

> [!danger] Highest-risk subsystem
> Spray timing, dripping, and clogging are AURA's hardest calibration problems (Risks R-01, R-14). Treat every design choice here as accuracy-critical. Related: [[⚙️ Mechanical Design]] · [[🔌 Electronics & Wiring]].

## Why Airbrush/Spray Nozzle (not brush or roller)
A spray head applies paint **without contacting the wall**, so it needs no force control or surface compliance — ideal for a lightweight gantry carriage. Brushes/rollers require pressure regulation and leave stroke marks; spray gives **even, controllable coverage** and works naturally with on/off (solenoid) control synchronized to motion.

## Pump Choice — Peristaltic vs Diaphragm
| | Peristaltic | Diaphragm |
|---|---|---|
| Flow precision | **High** (volumetric) | Medium |
| Cleaning | **Easy** (paint only touches tubing) | Harder (internal chambers) |
| Pressure | Lower | **Higher** (better atomization) |
| Cost | Higher | **Cheaper** |
| **AURA choice** | **Preferred** for precise, clean flow | Fallback if atomization/pressure inadequate |

> [!note] Decision
> Start with a **peristaltic pump** for flow precision and easy cleaning (paint contacts only the tube). If atomization is too weak for even coverage, switch to a **diaphragm pump** and add a small pressure buffer.

## Solenoid Valve Role
The **solenoid valve** provides fast **on/off** control of paint flow, toggled by the Arduino relay via **M3/M5** synchronized to gantry position. Placing the solenoid **close to the nozzle** minimizes dribble after shut-off (dead-volume in the line keeps flowing otherwise).

## Flow Rate & Calibration
- Calibrate by spraying a **fixed-time burst** onto paper at the standoff distance and measuring covered area / weight.
- Match flow to **gantry feedrate**: coverage per pass = flow_rate ÷ travel_speed. Tune both together in [[🧪 Calibration & Testing Log]].

## Paint Viscosity
> [!tip] Use **water-based acrylic**, thinned for spray.
> Water-based acrylic cleans up with water (protects the pump/nozzle), is low-odor, and thins predictably. Strain paint before use to avoid nozzle clogs (R-14).

## Tubing & Standoff
- Short tubing from reservoir → pump → solenoid → nozzle; keep runs short to reduce lag and dead volume.
- **Nozzle-to-wall standoff ~100–200 mm** — far enough for a spread pattern, close enough to limit overspray.

## Drip & Clog Mitigation
| Problem | Mitigation |
|---|---|
| Nozzle drip after M5 | Solenoid near nozzle; brief reverse/relief; cap between runs |
| Paint drying in nozzle | Flush with water after every run; keep capped |
| Pump air-lock | Prime before run; keep reservoir above pump if gravity-assist helps |
| Clog mid-run (R-14) | Strain paint, spare nozzle on hand, purge cycle before start |
| Overspray | Correct standoff, mask edges during tests, tune flow vs speed |

## Spray Test Protocol (Coverage Uniformity)
1. Prime and purge until steady stream.
2. Command a **single filled rectangle** (e.g., 100×100 mm) at a fixed feedrate.
3. Photograph under even lighting; analyze pixel intensity variance across the region.
4. Record **coverage %** and **uniformity** in [[🧪 Calibration & Testing Log]].
5. Adjust flow, standoff, overlap (10–20%) and repeat.

## Known Risks
- Paint drying in nozzle (R-14) · pump air-lock · overspray · post-M5 dribble. All logged in [[⚠️ Risk Register]].

---

## 🪫 Planned: Paint-Level Monitoring (2026-08-08)

> [!info] Panel recommendation, not yet implemented
> Full context and option comparison: [[🎯 Post-Defense Recommendations & Action Items]] § Paint-Level Indicator.

**Recommended: load cell + HX711 amplifier** under the reservoir, not an optical/ultrasonic or float-switch alternative — short version: a load cell doesn't care that the fluid is opaque pigmented paint, and it reuses the weight-based measurement principle the flow-rate calibration protocol above already relies on (§ Flow Rate & Calibration).

**Design sketch:**
- Mount: reservoir sits on (or hangs from) a small platform bearing on the load cell — needs to happen after the reservoir/mount is finalized, so this is blocked on that mechanical decision.
- Calibration: tare with an empty reservoir, single-point calibration against a known paint mass (or volume × density, water-based acrylic ≈1.2–1.3 g/mL).
- Thresholds: two levels — a **low-paint warning** (placeholder 20%) surfaced as a dashboard/toast notice, and a **critical** level (placeholder 5%) that should probably pause the run rather than just notify, given a dry-nozzle run risks R-14 (clogging). Exact thresholds are a tuning call once real flow-rate numbers exist.
- Noise: a gantry in motion vibrates — smooth the raw reading (moving average) before it drives a threshold, or a transient dip during a spray pass could false-trigger.
- API surface: `/api/status` gains a `paint_level_pct` field — see [[🔌 Backend API & Web Integration]] § Planned endpoint changes.

**BOM impact:** load cell (e.g. a small bar-type cell, ≤5–10 kg range) + HX711 breakout — see [[🛒 Bill of Materials]].

## 🎛️ Planned: Adaptive Spray Control — PWM (2026-08-08)

> [!info] Panel recommendation, not yet implemented
> Full context: [[🎯 Post-Defense Recommendations & Action Items]] § Adaptive Spray Control. Current "adaptive" behaviour is binary: the solenoid above is switched fully on/off, timed to gantry position (§ Solenoid Valve Role). The panel wants genuine flow-rate modulation, not just positional on/off.

**Decided direction: PWM time-proportioning on the existing solenoid.** No new hardware — rapidly pulse the same 12/24V solenoid at a duty cycle within a short fixed cycle period (well above any visible flutter or droplet-pattern artifact) to approximate a continuous average flow rate. This is the same principle precision-agriculture PWM spray-nozzle controllers use to vary flow at constant pressure.

**What this touches:**
- **Serial protocol:** the current custom command set (`MOVE` / `SPRAY ON` / `SPRAY OFF` / `HOME`, see [[🖥️ Serial Communication Protocol]]) needs a duty-cycle-capable spray command, e.g. `SPRAY PWM {0-100}`, alongside or replacing the binary `SPRAY ON/OFF`. This is an *additive* change to a protocol that already has one open, undecided item (the G-code ↔ custom-command bridge) — land it wherever that decision lands.
- **Firmware:** the Arduino sketch needs to generate the pulse train on the solenoid pin — well within Arduino timer/PWM capability at solenoid-appropriate switching frequencies.
- **Toolpath generator:** `toolpath_generator.py` would need to compute a duty-cycle value per segment rather than a flat on/off flag. Simplest starting point: uniform full duty during normal passes (functionally identical to today's on/off), with the real "adaptive" payoff as a natural follow-on — reduced duty near obstacle-adjacent rows to cut overspray (the spray-width-tapering idea Kurt flagged as not yet decided). Building PWM support makes that tapering nearly free to add once the base case works.

**Not yet decided:** whether edge-tapering ships alongside the PWM base case or as a later pass — see [[🎯 Post-Defense Recommendations & Action Items]].
