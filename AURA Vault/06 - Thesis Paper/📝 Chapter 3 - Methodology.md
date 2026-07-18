---
tags: [thesis, chapter-3, methodology]
created: 2026-03-29
updated: 2026-07-18
status: synced-with-manuscript
---
# 📝 Chapter 3 — Methodology

> [!info] Sync note (2026-07-18)
> Updated to match the finalized manuscript: YOLOv8 (not MobileNetV3+DeepLabV3+), OpenCV homography calibration, pyserial G-code bridge, and evaluation against **external standards** rather than internal thresholds. Color reproduction (ΔE\*) removed — see [[📝 Chapter 1 - Introduction]] scope note. **ASTM correction:** the two previously-cited designations, ASTM D4147 and ASTM D3270, were both found during the full reference audit to be real but entirely unrelated standards (D4147 = coil-coating drawdown bars; D3270 = fluoride content of atmosphere/plant tissues). Both spray-consistency and coverage-uniformity rows below are now benchmarked against the single correct standard, **ASTM D823** ("Standard Practices for Producing Films of Uniform Thickness of Paint, Coatings and Related Products on Test Panels"). See [[🔍 Reference Audit 2026-07 - Concept Paper]] for the full audit.

## 3.1 Research Design
**Developmental-experimental** design: developmental component covers iterative design/construction/integration of the AURA prototype; experimental component covers controlled evaluation against defined metrics.

## 3.2 Development Approach
**Iterative prototyping** through mechanical → electronic → firmware → AI → integration stages, testing after each. Target: reliably paint a simple multi-color design on a flat test board.

## 3.3 System Architecture
Full detail in [[🏗️ System Architecture Overview]]. Summary: camera → YOLOv8 segmentation → OpenCV homography calibration → raster toolpath generation → AI color recommendation → G-code assembly → pyserial (115200 baud) → Arduino Mega + RAMPS 1.4 → dual-X/single-Y NEMA 23 motors (TB6600) + relay-driven pump/solenoid/nozzle. All intelligence runs on the RTX 3050 laptop; the Arduino executes motion + spray only.

## 3.4 Participants
Minimum **five (5) evaluators** rate recommended color palettes on a 1–5 scale (visual coherence + suitability), per ISO/IEC 25010:2011 usability/satisfaction sub-characteristics. Evaluators drawn from students/faculty familiar with design aesthetics.

## 3.5 Instruments
**Hardware:** 2040 aluminum extrusion frame, 3× NEMA 23 (dual-X mirrored + single-Y), 3× TB6600 drivers, Arduino Mega 2560 + RAMPS 1.4 (signal breakout only — does not power motors), 24V/30A PSU, GT2 belts/pulleys, linear rails, USB/HD camera, peristaltic pump (diaphragm fallback), solenoid valve, spray nozzle, limit switches. Full list: [[🛒 Bill of Materials]].

**Software:** Python, PyTorch, Ultralytics YOLOv8, OpenCV (homography/scaling calibration), a raster toolpath generator, an AI-based color recommendation module (color-harmony rules + optional deep-learning palette recommender), and a pyserial motion controller.

**Motion system parameters** (derived, not assumed): steps/mm = (motor steps/rev × microstep) / (pulley teeth × belt pitch) = (200 × 8) / (20 × 2) = **40 steps/mm** at 1/8 microstepping. TB6600 current set to ~3.0–4.0 A per driver (confirmed against each unit's DIP label). RAMPS breaks out STEP/DIR/ENABLE + endstops only; the 24V/30A PSU feeds the TB6600 drivers directly, not RAMPS' onboard motor headers.

## 3.6 Development Procedure
1. **Mechanical** — assemble XY gantry per [[⚙️ Mechanical Design]]; verify squareness, dual-X sync.
2. **Camera + Calibration** — mount USB/HD camera; affix corner markers; compute OpenCV homography/scaling transform (pixel → mm).
3. **AI Integration — zero-shot baseline** — deploy YOLOv8 (Ultralytics, CUDA) with COCO-pretrained weights; evaluate via IoU/mAP (COCO protocol).
4. **Optional fine-tuning** — only if zero-shot underperforms: Roboflow-labeled custom dataset → Kaggle Tesla T4 fine-tune → redeploy on RTX 3050 → re-evaluate on the same test set.
5. **Toolpath generation** — raster (boustrophedon) scan per region, calibrated to mm, 10–20% pass overlap.
6. **Color recommendation module** — harmony-rule-based (+ optional deep-learning) palette generation; evaluated by the participant group.
7. **Arduino firmware** — GRBL-compatible command set (`G1`, `G28`, `M3`/`M5`, `G4`) → step/direction pulses + relay control; tested standalone before integration.
8. **pyserial bridge** — 115200 baud, blocking handshake (`ok` per line); one retry on timeout, then halt + spray-off on second failure.
9. **System integration & test runs** — full pipeline on a physical wall; motion, segmentation, spray consistency, and coverage uniformity measured.
10. **Mural / multi-region tests** — extended trials with multiple color regions if end-to-end tests pass.

## 3.7 Evaluation Framework (external standards, not internal thresholds)

| Metric | Type | Reference Standard | Method | Indicator |
|---|---|---|---|---|
| Motion (Positional) Accuracy | Quantitative | ISO 9283:1998 | Commanded vs. measured pose (mm) | Lower error/spread = better |
| Segmentation Accuracy | Quantitative | COCO protocol / Ultralytics YOLOv8 eval | IoU, mAP @ IoU ≥ 0.50 | Higher = better |
| Spray Consistency | Quantitative | ASTM D823 | Uniformity of applied coating across test panels/wall regions | More uniform = better |
| Coverage Uniformity | Quantitative | ASTM D823 | % area evenly coated, no gaps/excess overlap | Higher = better |
| Color Recommendation Quality | Qualitative | ISO/IEC 25010:2011 | 5-point Likert (coherence, suitability, satisfaction) | Higher mean = better |
| Overall System Integration | Qualitative | IEEE 1872-2015 | Structured end-to-end integration assessment | Higher = better |

> [!warning] Removed row
> "Color Reproduction Accuracy (CIE ΔE\*)" has been **removed** from this table. AURA does not mix/synthesize paint color, so there is no way to instrument a comparison between recommended and applied color. Only recommendation *quality* (the palette itself) is evaluated.

> [!tip] Standards references (for the Reference list)
> ISO 9283:1998 — Manipulating industrial robots — Performance criteria and related test methods (ISO, 1998). COCO evaluation protocol (Lin et al., 2014); Ultralytics YOLOv8 eval (Jocher et al., 2023). **ASTM D823-18(2022)** — Standard Practices for Producing Films of Uniform Thickness of Paint, Coatings and Related Products on Test Panels (ASTM International, 2022). ISO/IEC 25010:2011 — Systems and software Quality Requirements and Evaluation (SQuaRE) (ISO/IEC, 2011). IEEE 1872-2015 — IEEE Standard Ontologies for Robotics and Automation (IEEE, 2015).

## 3.8 Data Analysis
Quantitative metrics: descriptive statistics (means, SDs) and error metrics (mean positional error mm, mean IoU/mAP). Qualitative ratings: descriptive summary (mean, distribution). Results interpreted against **H₀/H₁** from [[📝 Chapter 1 - Introduction]]. Any deviations feed back into the next prototyping iteration.
