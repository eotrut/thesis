---
tags: [thesis, chapter-3, methodology]
created: 2026-03-29
status: draft-complete
---
# 📝 Chapter 3 — Methodology

## 3.1 Research Design
This study employs a **developmental-experimental** design. The developmental component covers the iterative design, construction, and integration of the AURA prototype; the experimental component covers the controlled evaluation of its performance against defined metrics. This dual design is appropriate because the study both *builds* a novel artifact and *measures* its effectiveness.

## 3.2 Development Approach
An **iterative prototyping** approach is used, progressing through mechanical, electronic, firmware, AI, and integration stages, with testing after each stage to surface defects early. Each iteration refines the prototype toward the target capability: reliably painting a simple two-color design on a 1 m × 1 m flat board.

## 3.3 System Architecture
AURA follows the Input–Process–Output model detailed in [[🏗️ System Architecture Overview]]. A camera captures the wall; a deep-learning model segments paintable regions; an AI module recommends colors; a path planner converts regions to G-code; and an Arduino Mega with RAMPS 1.4 drives three NEMA 23 motors (dual-X, single-Y) and an adaptive spray system. All intelligence runs on an RTX 3050 laptop; the Arduino executes motion and spray commands received over USB serial at 115200 baud.

## 3.4 Participants
For the qualitative evaluation of the color-recommendation module, a minimum of **five (5) evaluators** will rate recommended palettes on a 1–5 scale for visual appeal and suitability. Evaluators are selected from students and faculty familiar with design aesthetics.

## 3.5 Instruments
**Hardware:** 2040 aluminum extrusion frame, 3× NEMA 23 motors, 3× TB6600 drivers, Arduino Mega 2560 + RAMPS 1.4, 24V/30A PSU, GT2 belts/pulleys, linear rails, USB camera, peristaltic/diaphragm pump, solenoid valve, spray nozzle, limit switches (full list in [[🛒 Bill of Materials]]).
**Software:** Python, PyTorch/TensorFlow, OpenCV, a MobileNetV3-DeepLabV3+ segmentation model, K-means color recommendation, and a pyserial motion controller.

## 3.6 Development Procedure
1. **Mechanical:** assemble the XY gantry per [[⚙️ Mechanical Design]], ensuring squareness and dual-X synchronization.
2. **Electronics:** wire motors, drivers, RAMPS, PSU, and spray relay per [[🔌 Electronics & Wiring]].
3. **Firmware:** flash a G-code firmware (GRBL/Marlin variant); verify homing and commanded motion.
4. **AI:** train and validate the segmentation model and color-recommendation module ([[🔮 Segmentation Model]], [[🎨 Color Recommendation Module]]).
5. **Integration:** connect the laptop pipeline to the Arduino, synchronize spray with position, and run dry-runs then live paint tests.
6. **Testing:** collect all evaluation metrics ([[🧪 Calibration & Testing Log]]).

## 3.7 Evaluation Framework
| Metric | Type | Method | Indicator |
|---|---|---|---|
| Motion Accuracy | Quantitative | Positional error (mm) | Lower = better |
| Segmentation Accuracy | Quantitative | % correct regions vs ground truth (IoU, pixel acc) | Higher = better |
| Spray Consistency | Quantitative | Uniformity of paint distribution (visual/pixel) | More uniform = better |
| Coverage Uniformity | Quantitative | % area evenly painted (no gaps/overlaps) | Higher = better |
| Color Reproduction Accuracy | Quantitative | RGB/HSV difference (recommended vs applied) | Smaller diff = better |
| Color Recommendation Quality | Qualitative | User rating 1–5 (appeal + suitability) | Higher = better |
| Overall Painting Output Quality | Qualitative | Visual inspection (smoothness, alignment, finish) | Higher = better |

## 3.8 Data Analysis
Quantitative metrics are analyzed using **descriptive statistics** (means, standard deviations) and **error metrics** (mean positional error in mm, mean IoU, mean ΔE). Qualitative ratings are summarized descriptively (mean rating, distribution). Where a comparison to a manual/non-adaptive baseline is made, results are interpreted against hypotheses **H₀/H₁** from [[📝 Chapter 1 - Introduction]]. Target thresholds (e.g., positional error ≤ 2 mm, mIoU > 0.65, pixel accuracy > 75%) define prototype adequacy.
