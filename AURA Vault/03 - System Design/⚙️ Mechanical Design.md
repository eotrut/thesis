---
tags: [system-design, mechanical, gantry]
created: 2026-03-29
status: active
---
# ⚙️ Mechanical Design

> [!info] Related
> [[🔌 Electronics & Wiring]] · [[💧 Spray System Design]] · [[🔧 Assembly Log]] · [[🛒 Bill of Materials]]

## Gantry Configuration — Why Dual X-Axis Motors
The gantry is a **Cartesian XY** frame: a horizontal X-axis carries a vertical Y carriage that holds the spray head. The X-axis is **wide**, so a single motor on one end lets the opposite end lag under acceleration — the beam **racks** (skews out of square), and every commanded coordinate becomes wrong. AURA uses **two NEMA 23 motors on the X-axis**, one at each end, mirrored on the controller so they step in lockstep. This keeps the beam square and is the single most important mechanical decision for painting accuracy. The **Y-axis uses one NEMA 23** — it carries only the lightweight spray head, so racking is not a concern.

> [!warning] Racking is Risk R-02
> Matched belts, matched pulley tooth counts, a square frame, and homing *both* X corners are all required for the dual-motor scheme to actually prevent racking.

## Frame Material — 2040 Aluminum V-Slot Extrusion
| Property | Rationale |
|---|---|
| **Rigidity** | 2040 (20×40mm) resists bending far better than 2020 on the long X span. |
| **Weight** | Aluminum is light enough for NEMA 23 to accelerate without excessive inertia. |
| **Cost** | Widely available in PH; can be cut-to-length locally to save shipping (see [[💰 Budget Tracker]]). |
| **Modularity** | T-nut slots allow bolt-on brackets, motor mounts, and rail carriages without machining. |

## Y-Axis: Single Motor + Linear Motion
The Y carriage rides on a **linear rail + carriage** (or V-Slot wheels for budget) and is driven by a single **GT2 belt** from the Y NEMA 23. It holds the spray head at a fixed **Z standoff (~150mm)** from the wall — there is no active Z axis in the prototype.

## Belt Drive & Steps-per-mm
- **GT2 belt**: 2mm pitch. **Pulley**: 20 teeth → 40mm travel per revolution.
- NEMA 23 = 200 full steps/rev. At **1/8 microstepping** → 1600 steps/rev.
- **Steps per mm** = 1600 / 40 = **40 steps/mm**.
- At **1/16 microstepping** → 3200 / 40 = **80 steps/mm** (finer, slower). Start at 1/8 and tune (see [[🧪 Calibration & Testing Log]]).

```
steps_per_mm = (motor_steps_per_rev * microstep) / (pulley_teeth * belt_pitch)
             = (200 * 8) / (20 * 2) = 40 steps/mm
```

## Estimated Travel Range
| Axis | Range (prototype) | Notes |
|---|---|---|
| X | up to ~2–4 m (frame-dependent) | prototype demo target: 1 m usable |
| Y | up to ~2.5–3 m | prototype demo target: 1 m usable |
| Z | fixed ~150 mm standoff | no active Z |

> Prototype demo works on a **1 m × 1 m** flat board — the frame can be built larger later.

## Carriage & Spray Head Mounting
A printed/bracketed mount fixes the nozzle to the Y carriage, aimed perpendicular to the wall at the ~150mm standoff. Tubing to the pump/reservoir is routed with a small drag chain or zip-tie loops to avoid snagging during motion.

## Assembly Sequence (Order of Operations)
1. Cut and square the X-axis base extrusions; build the outer frame.
2. Mount the two X-axis motors + pulleys/idlers at each end.
3. Install the X gantry beam and its carriages.
4. Mount the Y-axis rail + carriage on the beam; install Y motor + belt.
5. Install limit switches at X (both) and Y home corners.
6. Mount the spray-head carriage and route tubing.
7. Tension all belts evenly; verify frame square with a measurement diagonal.
8. Proceed to wiring ([[🔌 Electronics & Wiring]]).

## Known Mechanical Risks & Mitigations
| Risk | Mitigation |
|---|---|
| Racking (R-02) | Dual-X mirrored motors, matched belts, dual homing |
| Belt slack → lost steps (R-15) | Proper tensioners, GT2 (low stretch), tune steps/mm |
| Frame not square | Measure diagonals, use corner brackets, re-check after tensioning |
| Vibration at speed | Lower acceleration, add feet/damping, brace long spans |
