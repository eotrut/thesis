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
> This note now reflects the **finalized** architecture used in the manuscript: YOLOv8 (Ultralytics) instance segmentation, not MobileNetV3 + DeepLabV3+; OpenCV-based homography/scaling calibration (not a bare "preprocess" step); and an AI-based color recommendation module framed more broadly than plain K-means. Dual-X motors and TB6600 drivers are unchanged and carry over directly.

> [!important] Build correction (2026-08-04) — RAMPS and G-code are out
> Two things in the sync note above are superseded:
> - **No RAMPS 1.4.** The Arduino Mega 2560 is wired **directly** to the TB6600 drivers ([[🔌 Electronics & Wiring]]). Consequence: nothing mirrors the dual-X step signal in hardware — the **firmware** must pulse both X drivers as one axis, or R-02 (racking) is unmitigated.
> - **No G-code / no Marlin.** The Arduino runs a custom sketch with a custom command set (`MOVE`, `SPRAY ON/OFF`, `HOME`) — see [[🖥️ Serial Communication Protocol]]. `backend/toolpath_generator.py` still emits G-code and the bridge between them is an **open decision**, tracked in that note.
>
> **Dual-X is retained.** 2 of 3 NEMA 23s are procured, both allocated to X; the Y motor is outstanding.

## Input–Process–Output (IPO)

| Input | Process | Output |
|---|---|---|
| Wall image (USB/HD camera) | Image acquisition + preprocessing | Captured wall frame |
| Captured wall frame | YOLOv8 instance segmentation (Ultralytics, CUDA) | Segmented paintable regions |
| Segmentation masks + corner markers | OpenCV homography/scaling calibration | Pixel → millimeter coordinate mapping |
| Calibrated region masks | Raster toolpath generation | Motion + spray-event sequence (mm) |
| User design intent / reference | AI-based color recommendation | Suggested palette + region→color assignment |
| Toolpath + color assignment | Serial command assembly | Command stream (`MOVE`/`SPRAY`/`HOME`) |
| Command stream | pyserial transmission (115200 baud) | Commands received/acknowledged by Arduino Mega |
| Received commands | Arduino Mega 2560 custom firmware (no RAMPS) | Stepper step/direction pulses; solenoid actuation |
| Step/direction pulses | Dual-X motors stepped in lockstep (TB6600) + single-Y motor | Controlled 2-axis gantry motion |
| Actuation signals | Pump + solenoid + nozzle | Applied paint on wall |
| Painted wall | Post-paint capture + evaluation | Motion/segmentation/spray/coverage/color-rec metrics |

## Block Diagram (ASCII)

```
        [USB Camera] ──img──> [ LAPTOP (RTX 3050, CUDA) ]
                                     |
   +---------------------------------+----------------------------------------+
   | Preprocess -> YOLOv8 Segmentation -> OpenCV Homography Calibration ->     |
   | Raster Toolpath Generation -> AI Color Recommendation -> Command Assembly |
   +---------------------------------+----------------------------------------+
                                     | MOVE / SPRAY / HOME (pyserial, USB, 115200 baud)
                                     v
                         [ Arduino Mega 2560 ] (direct wiring, no RAMPS)
                       +-------------+-------------+-------------+
                       |             |             |             |
                    TB6600 #1     TB6600 #2     TB6600 #3    Relay module
                   (X-left)      (X-right)      (Y motor)    (pump+solenoid)
                       |             |          [not procured]      |
                    NEMA23        NEMA23        NEMA23      [Pump]->[Valve]->[Nozzle]
                       \__ dual X, one step stream __/                |
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
5. The **path planner** converts each calibrated region into a raster (boustrophedon) coordinate list, then into serial commands.
6. The laptop streams commands over **USB serial (115200 baud)** via pyserial; the Arduino acknowledges each line with `ok`.
7. The **Arduino** drives the three NEMA 23 motors via TB6600 drivers — the two X motors from a single step stream, plus single-Y — and toggles the **spray relay** synchronized to position.
8. Paint is applied region by region (and color by color, with a nozzle flush between colors); a final image is captured for **evaluation**.

## Separation of Concerns — Laptop vs Arduino

| Laptop (Python, RTX 3050 + CUDA) | Arduino Mega 2560 (direct-wired) |
|---|---|
| Camera capture, preprocessing | Parse custom command lines |
| YOLOv8 instance-segmentation inference | STEP/DIR pulse generation |
| OpenCV homography/scaling calibration | **Dual-X synchronization (was RAMPS' job)** |
| AI-based color recommendation | Limit-switch homing |
| Path planning + command generation | Spray relay on/off |
| Serial command streaming + logging | Acknowledge each command (`ok`) |
| All "thinking" | All real-time actuation |

> [!tip] Why this split?
> The Arduino cannot run a deep-learning segmentation model; the laptop cannot generate precise real-time step pulses over USB. Putting *intelligence on the laptop* and *deterministic timing on the Arduino* plays to each device's strength and keeps the serial interface simple (see [[🖥️ Serial Communication Protocol]]).

## Communication Protocol Overview
- **Transport:** USB serial, **115200 baud**, 8N1.
- **Motion:** `MOVE X{x} Y{y}` (absolute linear move, mm), `HOME`.
- **Spray:** `SPRAY ON` / `SPRAY OFF` → relay.
- **Handshake:** Arduino returns `ok` after each executed line; Python blocks until `ok` or timeout, retries once, then halts + issues `SPRAY OFF` on a second failure (paint/position desync is treated as unsafe to continue).
- Full command table, the superseded G-code design, and the open emitter/protocol gap: [[🖥️ Serial Communication Protocol]].

## Key Architectural Decisions & Why
1. **Dual-X motors** — prevents racking of a wide gantry (the dominant accuracy risk). *Why:* a single X motor lets the far side lag, skewing every coordinate. With RAMPS gone, the lockstep is enforced in firmware rather than by the shield.
2. ~~**G-code over custom protocol**~~ — **reversed 2026-08-03.** The rationale was inheriting mature firmware conventions, which only pays off with Marlin/GRBL underneath. Without RAMPS there is no such firmware to inherit, so a G-code parser would have to be *written* — all of the cost and none of the benefit. A minimal custom command set is now less firmware to write, not more.
3. **2D segmentation, not 3D** — flat walls don't need depth. *Why:* fits a single consumer GPU and a standard USB camera; matches declared scope.
4. **Raster path planning** — simple, robust coverage. *Why:* reliability beats optimality for a prototype (see [[📐 Path Planning & G-code Generation]]).
5. ~~**RAMPS as breakout only**~~ — **removed from the build 2026-08-03.** The concern that drove it (stock RAMPS stepper power paths are under-rated for NEMA 23) is now moot: the Arduino Mega drives the TB6600s directly and the 24V/30A PSU feeds the drivers, exactly as before, just without the shield in between. See [[🔌 Electronics & Wiring]].
6. **YOLOv8, zero-shot-first** — COCO-pretrained weights are evaluated before any custom dataset/fine-tuning effort is spent, since the literature shows COCO-pretrained backbones generalize well enough that fine-tuning is a targeted optimization rather than a prerequisite.
