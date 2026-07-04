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
