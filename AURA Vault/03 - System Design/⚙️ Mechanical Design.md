---
tags: [system-design, mechanical, gantry]
created: 2026-03-29
status: active
---
# ⚙️ Mechanical Design

> [!info] Related
> [[🔌 Electronics & Wiring]] · [[💧 Spray System Design]] · [[🔧 Assembly Log]] · [[🛒 Bill of Materials]]

## Gantry Configuration — Why Dual X-Axis Motors
The gantry is a **Cartesian XY** frame: a horizontal X-axis carries a vertical Y carriage that holds the spray head. The X-axis is **wide**, so a single motor on one end lets the opposite end lag under acceleration — the beam **racks** (skews out of square), and every commanded coordinate becomes wrong. AURA uses **two NEMA 23 motors on the X-axis**, one at each end, stepped in lockstep so the beam stays square. This is the single most important mechanical decision for painting accuracy. The **Y-axis uses one NEMA 23** — it carries only the lightweight spray head, so racking is not a concern.

> [!warning] Racking is Risk R-02
> Matched belts, matched pulley tooth counts, a square frame, and homing *both* X corners are all required for the dual-motor scheme to actually prevent racking.

> [!important] Mirroring is now a **firmware** responsibility (2026-08-04)
> The earlier design mirrored the two X motors on a RAMPS shield. **RAMPS is not in the build** — the Arduino Mega drives the TB6600s directly ([[🔌 Electronics & Wiring]]) — so nothing mirrors the step signal in hardware any more. The Arduino sketch must pulse both X drivers from a single step routine and treat them as one axis. If they are ever driven as two independent axes, R-02 is unmitigated and the dual-motor scheme buys nothing.

> [!note] Procurement status
> 2 of the 3 NEMA 23 motors are procured, **both allocated to X**. The Y motor is outstanding and is planned as a borrowed/spare unit for initial testing — see [[💰 Budget Tracker]] and [[🔌 Electronics & Wiring]].

## Frame Material — 2040 Aluminum V-Slot Extrusion
| Property | Rationale |
|---|---|
| **Rigidity** | 2040 (20×40mm) resists bending far better than 2020 on the long X span. |
| **Weight** | Aluminum is light enough for NEMA 23 to accelerate without excessive inertia. |
| **Cost** | Widely available in PH; can be cut-to-length locally to save shipping (see [[💰 Budget Tracker]]). |
| **Modularity** | T-nut slots allow bolt-on brackets, motor mounts, and rail carriages without machining. |

## Bottom Axis Rail Config — DECIDED: Dual V-Slot (2026-08-04)
Debate was single V-slot rail (center, bottom axis) vs. two rails (one on each side). **Decided: dual rails** — better load distribution and racking resistance on the bottom axis, at the cost of extra alignment work and hardware. Assembly begins once all parts (including any rail-specific hardware still incoming) have arrived — see [[🔧 Assembly Log]].

## Y-Axis: Single Motor + Linear Motion
The Y carriage rides on a **linear rail + carriage** (or V-Slot wheels for budget) and is driven by a single **GT2 belt** from the Y NEMA 23. It holds the spray head at a fixed **Z standoff (~150mm)** from the wall — there is no active Z axis in the prototype.

## Belt Drive & Steps-per-mm

> [!important] Superseded by the 2026-08-03 bench test — microstepping is **1/32**, not 1/8
> The TB6600 was bench tested at **32 microsteps / 6400 pulses per revolution** at 3 A ([[🔌 Electronics & Wiring]]). That is the confirmed hardware setting, so the 40 steps/mm figure below is **wrong by a factor of 4**. Anything quoting 40 steps/mm — including [[📝 Chapter 3 - Methodology]] — needs the corrected value.

- **GT2 belt**: 2mm pitch. **Pulley**: 20 teeth → 40mm travel per revolution.
- NEMA 23 = 200 full steps/rev. At **1/32 microstepping** → **6400 steps/rev** (bench confirmed).
- **Steps per mm** = 6400 / 40 = **160 steps/mm**.

```
steps_per_mm = (motor_steps_per_rev * microstep) / (pulley_teeth * belt_pitch)
             = (200 * 32) / (20 * 2) = 160 steps/mm
```

| Microstepping | Steps/rev | Steps/mm | Note |
|---|---|---|---|
| 1/8 | 1600 | 40 | Original plan — **not what the driver is set to** |
| 1/16 | 3200 | 80 | — |
| **1/32** | **6400** | **160** | ✅ Bench confirmed 2026-08-03 |

> [!note] Finer microstepping is not free resolution
> 1/32 gives a smaller commanded increment, but step *accuracy* is still bounded by belt stretch, pulley runout and motor detent — not by the microstep count. Treat 160 steps/mm as the command scaling, and let the ISO 9283 positional-accuracy measurement ([[🧪 Calibration & Testing Log]]) say what the real resolution is. It also raises the pulse rate 4× for the same feed, so check the Arduino can sustain the step frequency before assuming the speed budget still holds.

## Travel Range — Locked (2026-08-03)
| Axis | Rail length | mm | Notes |
|---|---|---|---|
| X (horizontal) | 4.5 ft | 1371.6 mm | full wall width covered by **repositioning the gantry**, not a longer rail |
| Y (vertical) | 9 ft | 2743.2 mm | |
| Z | fixed ~150 mm standoff | | no active Z |

> [!info] Multi-position painting is the plan, not a fallback
> The frame's X-axis is intentionally shorter than most wall widths. For any wall wider than 4.5 ft, the gantry is physically slid over and re-calibrated (new corner markers) to paint the next section — each `/api/toolpath` run covers exactly one gantry position. This is why **envelope clipping** (clip the toolpath to what this position can actually reach, report the leftover area) is the correct software behavior rather than an edge case — see [[📐 Path Planning & G-code Generation]] § Envelope Clipping.

> The actual reachable envelope for toolpath clipping is the rail length **minus a safety margin** for homing/limit-switch clearance (placeholder: 50 mm per end until measured on the built frame) — not the full 1371.6 × 2743.2 mm rail length.

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
| Racking (R-02) | Dual-X motors stepped in lockstep **in firmware** (no RAMPS), matched belts, dual homing |
| Belt slack → lost steps (R-15) | Proper tensioners, GT2 (low stretch), tune steps/mm |
| Frame not square | Measure diagonals, use corner brackets, re-check after tensioning |
| Vibration at speed | Lower acceleration, add feet/damping, brace long spans |

---

## 🛞 Planned: Mobility — Casters & Leveling Feet (2026-08-08)

> [!info] Panel recommendation, not yet implemented
> Full context and the R-17 scope-creep distinction: [[🎯 Post-Defense Recommendations & Action Items]] § Gantry Mobility.

**Recommended:** locking **swivel casters**, load-rated for the assembled frame weight (not yet measured — needs weighing once the frame is built, see [[🔧 Assembly Log]]), **plus separate drop-down leveling feet**. Casters carry the frame only in transit; the leveling feet drop down and bear the actual load once the gantry is positioned, so the frame sits rigid and square while painting rather than resting on four unlocked wheels. This matters specifically because of **R-02 (racking)** — the dual-X-motor lockstep scheme depends on a square, stable frame, and an accelerating gantry sitting on unloaded casters would reintroduce exactly the wobble that scheme exists to prevent.

**Ties into the existing multi-position workflow, not a new one:** the X-axis rail is intentionally shorter than most walls (§ Travel Range — Locked, above); AURA already plans to physically slide the gantry to a new position and re-calibrate for wider walls. Casters + leveling feet just make that already-planned manual reposition easier — they don't turn AURA into a self-propelled or continuously-mobile system. See the R-17 clarification linked above.

**Not yet decided:** exact caster count/placement and load rating — blocked on the frame's actual assembled weight. **BOM impact:** see [[🛒 Bill of Materials]].
