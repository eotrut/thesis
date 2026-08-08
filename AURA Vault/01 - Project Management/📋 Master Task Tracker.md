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
- [x] Wire motors to drivers
- [x] Wire drivers directly to Arduino Mega (no RAMPS) — X-left on pins 3/4/5 bench tested 2026-08-03; X-right and Y pending
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
- [x] Submit draft to adviser
- [x] Revise based on feedback
- [x] Prepare defense presentation
- [x] Conduct mock defense
- [x] Proposal defense (2026-08-08) — accepted, with six follow-up recommendations, see Phase 6 below
- [ ] Final defense

## Phase 6 — Post-Defense Enhancements (Panel Recommendations, 2026-08-08)
> Full context: [[🎯 Post-Defense Recommendations & Action Items]]

- [x] Color module: accept a second reference-image upload, blend its extracted seed with the room's own — **done 2026-08-08** (70/30 LCh blend, circular-mean hue), see [[🎨 Color Recommendation Module]] § As-built record
- [x] Color module: add demographic "for whom" category input with evidence-based LCh bias — **done 2026-08-08** (`CATEGORY_BIAS`, 7 categories, dropdown), see [[🎨 Color Recommendation Module]] and new RRL ([[📚 Literature Review Master]] Theme 7, [[📝 Chapter 2 - Review of Related Literature]] § 2.8b)
- [ ] Color module: eyeball the seven categories against **real** room photos and tune the bias constants — blocked on the `samples/` shoot; only synthetic frames tested so far
- [ ] Camera view: add + erase mask-correction brush on Upload/Playback and Toolpath modes — see [[🔮 Segmentation Model]]
- [ ] Backend: extend `/api/segment`/`/api/toolpath` with the mask-correction payload — see [[🔌 Backend API & Web Integration]] (the `/api/recommend-colors` half of this item shipped 2026-08-08)
- [ ] Hardware: source and mount a load cell + HX711 under the paint reservoir, calibrate, wire a low-paint alert into `/api/status` — see [[💧 Spray System Design]]
- [ ] Hardware: source and mount locking swivel casters + leveling feet — see [[⚙️ Mechanical Design]]
- [ ] Firmware/protocol: add a PWM spray-duty command to the serial protocol and Arduino sketch — see [[💧 Spray System Design]], [[🖥️ Serial Communication Protocol]]
- [ ] Update Chapter 2 RRL in the actual manuscript — **now unblocked**, the demographic-category feature shipped 2026-08-08 — see [[📝 Chapter 2 - Review of Related Literature]] § 2.8b
