---
tags: [system-design, architecture, ipo]
created: 2026-03-29
status: active
---
# 🏗️ System Architecture Overview

> [!info] Sub-designs
> [[⚙️ Mechanical Design]] · [[🔌 Electronics & Wiring]] · [[🧠 AI & Software Design]] · [[💧 Spray System Design]] · [[📐 Path Planning & G-code Generation]] · [[🖥️ Serial Communication Protocol]]

## Input–Process–Output (IPO)

| Input | Process | Output |
|---|---|---|
| Wall image (camera) | Image acquisition + preprocessing | Segmented wall regions |
| User design/pattern | Deep-learning spatial segmentation | Identified paintable zones |
| Color preferences | AI color recommendation | Suggested color combinations |
| System parameters | Path planning + coordinate generation (XY gantry) | G-code / motion paths |
| — | Motion control via Arduino + stepper motors | Controlled gantry movement |
| Paint supply | Adaptive spray control (pump, valve, nozzle) | Applied paint on wall |
| — | System integration + execution | Fully painted wall output |
| — | Performance evaluation | Accuracy metrics |

## Block Diagram (ASCII)

```
        [USB Camera] ──img──> [ LAPTOP (RTX 3050) ]
                                     |
   +---------------------------------+----------------------------------+
   | Preprocess -> Segmentation(CNN) -> Color Rec(K-means) -> Path Plan  |
   +---------------------------------+----------------------------------+
                                     | G-code / commands (USB serial, 115200)
                                     v
                            [ Arduino Mega 2560 + RAMPS 1.4 ]
                       +-------------+-------------+-------------+
                       |             |             |             |
                    TB6600        TB6600        TB6600       Relay module
                   (X1 motor)    (X2 motor)    (Y motor)    (pump+solenoid)
                       |             |             |             |
                    NEMA23        NEMA23        NEMA23      [Pump]->[Valve]->[Nozzle]
                       \____ dual X (anti-rack) ___/                 |
                                     |                               v
                              [ XY GANTRY ] ---- carries ----> [ SPRAY HEAD ] -> WALL
                                     ^
                              [Limit switches] (homing)
```

## Data Flow Narrative
1. The **camera** captures the target wall; the frame is preprocessed (resize to 512×512, normalize).
2. The **segmentation model** outputs a per-pixel mask of paintable regions.
3. The **color recommendation module** clusters the design/reference image and proposes a harmonious palette, assigning colors to regions.
4. The **path planner** converts each region mask into a raster (lawn-mower) coordinate list, mapped from pixels to millimeters, then to G-code.
5. The laptop streams G-code over **USB serial (115200 baud)**; the Arduino acknowledges each line with `ok`.
6. The **Arduino** drives the three NEMA 23 motors via TB6600 drivers (dual X mirrored, single Y) and toggles the **spray relay** (M3/M5) synchronized to position.
7. Paint is applied; the process repeats per color region. A final image is captured for **evaluation**.

## Separation of Concerns — Laptop vs Arduino

| Laptop (Python, RTX 3050) | Arduino Mega + RAMPS |
|---|---|
| Camera capture, preprocessing | Parse G-code lines |
| Deep-learning segmentation inference | STEP/DIR pulse generation |
| Color recommendation | Dual-X synchronization |
| Path planning + G-code generation | Limit-switch homing |
| Serial command streaming + logging | Spray relay on/off (M3/M5) |
| All "thinking" | All real-time actuation |

> [!tip] Why this split?
> The Arduino cannot run deep learning; the laptop cannot generate precise real-time step pulses over USB. Putting *intelligence on the laptop* and *deterministic timing on the Arduino* plays to each device's strength and keeps the serial interface simple (see [[🖥️ Serial Communication Protocol]]).

## Communication Protocol Overview
- **Transport:** USB serial, **115200 baud**, 8N1.
- **Motion:** `G1 X{x} Y{y} F{feed}` (linear move), `G28` (home).
- **Spray:** `M3` (spray on), `M5` (spray off) — GRBL-compatible spindle mapping.
- **Handshake:** Arduino returns `ok` after each executed line; Python blocks until `ok` or timeout.

## Key Architectural Decisions & Why
1. **Dual-X motors** — prevents racking of a wide gantry (the dominant accuracy risk). *Why:* a single X motor lets the far side lag, skewing every coordinate.
2. **G-code over custom protocol** — reuses mature firmware (GRBL/Marlin) and tooling. *Why:* less firmware to write/debug for a solo engineer.
3. **2D segmentation, not 3D** — flat walls don't need depth. *Why:* fits 4GB VRAM and a hobby camera.
4. **Raster path planning** — simple, robust coverage. *Why:* reliability beats optimality for a prototype (see [[📐 Path Planning & G-code Generation]]).
