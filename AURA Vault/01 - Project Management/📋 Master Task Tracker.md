---
tags: [project-management, tasks, tracker]
created: 2026-03-29
status: active
---
# 📋 Master Task Tracker

> [!info] How to use
> Tasks are grouped by phase. Check items as you complete them. Home dashboard pulls from this note via Dataview. Related: [[📅 Timeline & Milestones]] · [[⚠️ Risk Register]].

## Phase 0 — Planning & Concept Paper
- [x] Concept paper written and submitted (29/03/2026)
- [x] Literature review completed
- [x] System architecture (IPO) defined
- [x] Hardware components identified
- [x] Budget estimated
- [x] Research questions & objectives locked
- [x] Scope and delimitations defined

## Phase 1 — Hardware Procurement & Assembly
- [x] Source and purchase aluminum extrusion rails
- [x] Purchase Arduino Mega ~~+ RAMPS 1.4~~ — **RAMPS bought but not used** (₱380 sunk); the Mega is wired directly to the TB6600s, see [[🔌 Electronics & Wiring]]
- [x] Purchase NEMA 23 motors (×3) — **3 of 3 procured**, both allocated to X (dual-X); Y motor outstanding, planned as a borrowed/spare unit
- [x] Purchase TB6600 drivers (×3) — **3 of 3 procured**; third needed for Y
- [x] Purchase GT2 belts, pulleys, bearings
- [x] Purchase 24V 30A PSU
- [ ] Purchase spray nozzle / airbrush mechanism
- [ ] Purchase pump and solenoid valve (tentative)
- [ ] Assemble X-axis base rail
- [ ] Assemble Y-axis vertical column
- [ ] Wire motors to drivers
- [ ] Wire drivers directly to Arduino Mega (no RAMPS) — X-left on pins 3/4/5 bench tested 2026-08-03; X-right and Y pending
- [x] Test motor movement (no load) — single motor bench tested 2026-08-03 at 3A, 1/32 microstepping, ENA confirmed active-low
- [ ] Calibrate limit switches / homing

## Phase 2 — Firmware & Motion Control
- [ ] Flash Arduino with **custom firmware** (not GRBL — no RAMPS/Marlin in the build). Must drive **both X drivers from one step routine** (R-02 mitigation) and parse the custom command set
- [x] Define G-code command set — `G0` rapid (dry), `G1` paint move, `M3`/`M5` spray on/off, absolute mm at 2 dp. Emitted by `events_to_gcode()`, documented in [[📐 Path Planning & G-code Generation]]. Still to add during tuning: `F` feed rate and a `G21`/`G90` preamble
- [ ] **Decide: translate G-code → custom commands in `serial_ctrl.py`, or replace the emitter.** The toolpath stage emits G-code but the Arduino will not parse it; the two ends do not currently meet. Blocks firmware work — see [[🖥️ Serial Communication Protocol]]
- [ ] Write Python serial controller script
- [ ] Test XY movement to commanded coordinates
- [ ] Measure positional error (motion accuracy test)
- [ ] Tune stepper speed, acceleration, microstepping

## Phase 3 — AI Model Development
- [x] Choose model architecture — **YOLOv8 segmentation** (transfer learning on COCO weights, confirmed with advisor; supersedes earlier MobileNet/DeepLab plan)
- [x] Roboflow: create Instance Segmentation project + lock class list (wall, door, window)
- [x] Roboflow: bootstrap dataset forked — "wall detection" by Meguro (Universe, 480 real photos, classes: wall/door/window/sign/other). Confirmed: annotations are already polygon masks despite Universe listing it as "Object Detection" (that label described the published demo model, not the underlying label data) — usable as-is, no re-annotation needed on this set
- [x] Roboflow: shoot 100–200+ custom photos with actual camera/tripod rig (varied lighting/angle/distance)
- [x] Roboflow: upload custom photos into the (forked) Instance Segmentation project
- [x] Roboflow: annotate custom photos as polygons (Smart Polygon / "Find Objects with AI" tool) — only obstacle classes (door/window/sign/other) strictly need tracing; wall = complement of those
- [x] Roboflow: split (70/20/10) + preprocess (resize 640×640) + augment (flip, ±15° rotation, brightness/exposure, slight blur — no vertical flip)
- [x] Roboflow: generate dataset version
- [x] Roboflow: export as YOLOv8-seg format, save API snippet
- [x] Kaggle: create notebook, attach T4 GPU, pull dataset via Roboflow API snippet
- [x] Kaggle: test zero-shot YOLOv8 COCO weights on real wall photos first
- [x] Kaggle: fine-tune YOLOv8-seg (only if zero-shot insufficient)
- [x] Evaluate segmentation accuracy (IoU / pixel accuracy)
- [x] Download trained `.pt` weights to laptop
- [x] Integrate model inference into Python pipeline
- [x] Connect segmentation output to path planner — **done (2026-08-03)**, see [[📐 Path Planning & G-code Generation]]. Coordinate mapping (homography + uncalibrated fallback), raster toolpath generator with obstacle subtraction, G-code serialization, `/api/toolpath`, and a Toolpath tab on `camera-view.html` with click-to-pick corner calibration. Verified against `best.pt` on the test images; G-code is emitted but nothing sends it yet
- [ ] Validate the homography against a tape-measured test panel — **can be done now**, no gantry needed; table ready in [[🧪 Calibration & Testing Log]] §1b
- [x] Decide envelope-clipping behaviour — **clip, not reject** (2026-08-03). Implemented: clipped against the physical rails (1371.6 × 2743.2 mm less a 50 mm provisional homing margin), not the marker quad, with a soft-limit backstop at G-code emission. See [[📐 Path Planning & G-code Generation]] § Envelope Clipping
- [ ] **Shoot real wall photos into `samples/`** — every coverage figure so far comes from annotated exports, not photographs. Highest priority is a wall with 4 tape-measured corner markers at ~0°/15°/30°: it unblocks [[🧪 Calibration & Testing Log]] §1b and yields real Chapter 4 data **with no gantry needed**. Hold this set out of Roboflow training
- [x] Develop color recommendation module (K-means + harmony rules) — parked, not current focus
- [ ] Test color recommendations with evaluators (qualitative, n≥5)

## Phase 4 — System Integration
- [ ] Connect laptop AI pipeline to Arduino serial
- [ ] Synchronize spray on/off with gantry position
- [ ] Full dry-run test (no paint)
- [ ] First live paint test (single color, simple shape)
- [ ] Multi-color region test
- [ ] Simple mural design test
- [ ] Record all evaluation metrics

## Phase 5 — Thesis Writing & Defense
- [x] Complete Chapter 3 (Methodology)
- [ ] Complete Chapter 4 (Results) — after testing
- [ ] Complete Chapter 5 (Discussion)
- [ ] Compile full references in APA format
- [ ] Internal review / proofreading
- [ ] Submit draft to adviser
- [ ] Revise based on feedback
- [ ] Prepare defense presentation
- [ ] Conduct mock defense
- [ ] Final defense
