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

## 1b. Camera → Wall Calibration (homography)

> [!info] Method in [[📐 Path Planning & G-code Generation]]. This is the one test that **can be run before the gantry exists** — it only needs a camera, a tape measure and a flat panel.

**Procedure**
1. Mark 4 corners on a flat test panel. Once the gantry is built these should be the corners of its **reachable envelope** — X = 4.5 ft / 1371.6 mm, Y = 9 ft / 2743.2 mm minus homing margin (see [[⚙️ Mechanical Design]]) — so the plan lands in the machine's own coordinate frame. Note: as of 2026-08-03, toolpath clipping is decided to clip against these **physical rail limits**, not the marker quad itself — see [[📐 Path Planning & G-code Generation]] § Envelope Clipping.
2. Measure their real positions with a tape. Record below.
3. Photograph as square-on as practical.
4. `camera-view.html` → **Toolpath** tab → *Pick corners* → click **top-left, top-right, bottom-right, bottom-left** in that order → enter envelope size → *Plan with these corners*.
5. Check the rectified background: **skew or stretch means a mis-clicked corner.**
6. Measure a few known features on the panel and compare against the millimetres the plan reports.

| Run | Envelope W×H (mm) | Camera angle (° off normal) | Feature measured | True (mm) | Reported (mm) | Error (mm) | Notes |
|---|---|---|---|---|---|---|---|
| 1 | | | | | | | |
| 2 | | | | | | | |
| 3 | | | | | | | |

> [!tip] Vary the camera angle deliberately across runs
> The point of the homography is that it should hold up off-axis. Shooting run 1 at ~0°, run 2 at ~15°, run 3 at ~30° turns this table into evidence for Chapter 4 rather than a single unrepeated measurement.

> [!warning] Lens distortion is not corrected
> A homography fixes perspective only. If error is near-zero at the markers but grows toward the mid-edges, that is barrel distortion and needs a separate intrinsic calibration (checkerboard → `cv2.undistort`) applied before the homography. Record whether the measured error justifies it.

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
