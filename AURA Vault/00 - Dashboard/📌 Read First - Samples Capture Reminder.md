---
tags: [reminder, pinned, samples]
created: 2026-08-04
status: pending
---
# 📌 Read First — Samples Capture Reminder

> [!danger] PENDING — do not remove until Kurt confirms it's done
> This note stays until Kurt explicitly says to remove it.

## What to do
Capture the `samples/` test image set for the backend:

1. **Take at least 8–12 photos of a wall that is NOT part of the Roboflow training dataset.** Any wall you haven't already used for annotation/training counts as "held-out."
2. **On that wall, mark all 4 corners with an X using masking tape** before photographing. Keep the X marks in frame in every shot.
3. **Save the photos into `samples/`** (see `samples/README.md`).

## Why
- The masking-tape X's are the physical corner-marker reference points for the OpenCV homography/scaling calibration (pixel → mm mapping) — see [[⚙️ Mechanical Design]] and [[📐 Path Planning & G-code Generation]].
- `backend/tools/test_toolpath.py` and `/api/toolpath` need real, uncalibrated-fallback-free photos to test against. Right now it falls back to `website/assets/` (already-annotated gallery exports) and prints a **NOT A PHOTOGRAPH** banner — which means toolpath/homography testing isn't running against real data yet.
- Keeping this wall **out of Roboflow training** matters: if it's in the training set, IoU/toolpath test results measure memorization, not generalization.

Full detail: [[🔌 Backend API & Web Integration]] → Known limits.

## Status
**Not done yet.** Claude: read this note at the start of every session and remind Kurt this is still pending, until he says otherwise.
