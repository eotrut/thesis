---
tags: [system-design, architecture, ipo]
created: 2026-03-29
updated: 2026-07-12
status: synced-with-manuscript
---
# 🏗️ System Architecture Overview

> [!info] Sub-designs
> [[⚙️ Mechanical Design]] · [[🔌 Electronics & Wiring]] · [[🧠 AI & Software Design]] · [[💧 Spray System Design]] · [[📐 Path Planning & G-code Generation]] · [[🖥️ Serial Communication Protocol]]

> [!warning] Sync note (2026-07-12)
> This note now reflects the **finalized** architecture used in the manuscript: YOLOv8 (Ultralytics) instance segmentation, not MobileNetV3 + DeepLabV3+; OpenCV-based homography/scaling calibration (not a bare "preprocess" step); and an AI-based color recommendation module framed more broadly than plain K-means. The mechanical/electrical decisions (dual-X motors, TB6600, RAMPS-as-breakout-only) are unchanged and carry over directly.

## Input–Process–Output (IPO)

| Input | Process | Output |
|---|---|---|
| Wall image (USB/HD camera) | Image acquisition + preprocessing | Captured wall frame |
| Captured wall frame | YOLOv8 instance segmentation (Ultralytics, CUDA) | Segmented paintable regions |
| Segmentation masks + corner markers | OpenCV homography/scaling calibration | Pixel → millimeter coordinate mapping |
| Calibrated region masks | Raster toolpath generation | Motion + spray-event sequence (mm) |
| User design intent / reference | AI-based color recommendation | Suggested palette + region→color assignment |
| Toolpath + color assignment | G-code-style command assembly | Command stream (G1/G28/M3/M5) |
| Command stream | pyserial transmission (115200 baud) | Commands received/acknowledged by Arduino Mega |
| Received commands | Arduino Mega + RAMPS 1.4 firmware | Stepper step/direction pulses; solenoid actuation |
| Step/direction pulses | Dual-X mirrored motors (TB6600) + single-Y motor | Controlled 2-axis gantry motion |
| Actuation signals | Pump + solenoid + nozzle | Applied paint on wall |
| Painted wall | Post-paint capture + evaluation | Motion/segmentation/spray/coverage/color-rec metrics |

## Block Diagram (ASCII)

```
        [USB Camera] ──img──> [ LAPTOP (RTX 3050, CUDA) ]
                                     |
   +---------------------------------+----------------------------------------+
   | Preprocess -> YOLOv8 Segmentation -> OpenCV Homography Calibration ->     |
   | Raster Toolpath Generation -> AI Color Recommendation -> G-code Assembly |
   +---------------------------------+----------------------------------------+
                                     | G-code-style commands (pyserial, USB, 115200 baud)
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
1. The **camera** captures the target wall; the frame is preprocessed on the laptop.
2. **YOLOv8** outputs a per-pixel instance-segmentation mask of paintable regions.
3. **OpenCV homography/scaling calibration**, seeded from physical corner markers, converts pixel-space masks into real-world millimeter coordinates.
4. The **color recommendation module** analyzes design intent/reference input and proposes a coherent palette, assigning colors to regions.
5. The **path planner** converts each calibrated region into a raster (boustrophedon) coordinate list, then into G-code-style commands.
6. The laptop streams commands over **USB serial (115200 baud)** via pyserial; the Arduino acknowledges each line with `ok`.
7. The **Arduino** drives the three NEMA 23 motors via TB6600 drivers (dual-X mirrored, single-Y) and toggles the **spray relay** (`M3`/`M5`) synchronized to position.
8. Paint is applied region by region (and color by color, with a nozzle flush between colors); a final image is captured for **evaluation**.

## Separation of Concerns — Laptop vs Arduino

| Laptop (Python, RTX 3050 + CUDA) | Arduino Mega + RAMPS |
|---|---|
| Camera capture, preprocessing | Parse G-code lines |
| YOLOv8 instance-segmentation inference | STEP/DIR pulse generation |
| OpenCV homography/scaling calibration | Dual-X synchronization |
| AI-based color recommendation | Limit-switch homing |
| Path planning + G-code generation | Spray relay on/off (M3/M5) |
| Serial command streaming + logging | Acknowledge each command (`ok`) |
| All "thinking" | All real-time actuation |

> [!tip] Why this split?
> The Arduino cannot run a deep-learning segmentation model; the laptop cannot generate precise real-time step pulses over USB. Putting *intelligence on the laptop* and *deterministic timing on the Arduino* plays to each device's strength and keeps the serial interface simple (see [[🖥️ Serial Communication Protocol]]).

## Communication Protocol Overview
- **Transport:** USB serial, **115200 baud**, 8N1.
- **Motion:** `G1 X{x} Y{y} F{feed}` (linear move), `G28` (home).
- **Spray:** `M3` (spray on), `M5` (spray off) — GRBL-compatible spindle mapping.
- **Dwell:** `G4 P{ms}`.
- **Handshake:** Arduino returns `ok` after each executed line; Python blocks until `ok` or timeout, retries once, then halts + issues `M5` on a second failure (paint/position desync is treated as unsafe to continue).

## Key Architectural Decisions & Why
1. **Dual-X motors** — prevents racking of a wide gantry (the dominant accuracy risk). *Why:* a single X motor lets the far side lag, skewing every coordinate.
2. **G-code over custom protocol** — reuses mature firmware conventions (GRBL-compatible). *Why:* less firmware to write/debug for a solo engineer.
3. **2D segmentation, not 3D** — flat walls don't need depth. *Why:* fits a single consumer GPU and a standard USB camera; matches declared scope.
4. **Raster path planning** — simple, robust coverage. *Why:* reliability beats optimality for a prototype (see [[📐 Path Planning & G-code Generation]]).
5. **RAMPS as breakout only, not a motor power stage** — stock RAMPS stepper power paths are under-rated for the NEMA 23 motors; the 24V/30A PSU feeds the TB6600 drivers directly, and RAMPS only carries STEP/DIR/ENABLE and endstop signals.
6. **YOLOv8, zero-shot-first** — COCO-pretrained weights are evaluated before any custom dataset/fine-tuning effort is spent, since the literature shows COCO-pretrained backbones generalize well enough that fine-tuning is a targeted optimization rather than a prerequisite.
