---
tags: [hardware, testing, calibration, metrics]
created: 2026-03-29
status: active
---
# 🧪 Calibration & Testing Log

> [!info] Structured results feeding [[📝 Chapter 4 - Results]]. Metrics defined in [[📝 Chapter 3 - Methodology]]. Fill rows as tests run.

## 1. Motion Accuracy Tests
Commanded vs actual position; error in mm (target: minimize, define threshold e.g. ≤ 2 mm).

| Run | Commanded (X,Y) mm | Actual (X,Y) mm | Error X (mm) | Error Y (mm) | Notes |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

## 2. Spray Consistency Tests
Coverage and uniformity per burst/pass.

| Run | Feedrate | Flow setting | Coverage % | Uniformity (visual/pixel) | Notes |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

## 3. Segmentation Accuracy Tests
Per test image vs ground-truth mask.

| Image | Ground truth | Predicted | IoU | Pixel Acc | Notes |
|---|---|---|---|---|---|
| img_01 | | | | | |
| img_02 | | | | | |
| img_03 | | | | | |

## 4. Color Reproduction Tests
Recommended vs applied color (delta-E / RGB diff).

| Test | Recommended RGB | Applied RGB | ΔE | RGB diff | Notes |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

## 5. Overall Output Quality (per painted test)
Qualitative visual inspection (1–5): smoothness, alignment, finish.

| Test | Design | Smoothness (1-5) | Alignment (1-5) | Finish (1-5) | Overall (1-5) | Notes |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

> [!tip] Record raw photos and CSV exports alongside each table for traceability in the defense.
