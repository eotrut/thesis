---
tags: [dashboard, reminder, transient]
created: 2026-08-03
status: pending
---
# 📌 Next Session — Read First

> [!important] Claude: read this, tell Kurt what it says, then **delete this file** and remove its link from [[🏠 AURA Home]].
> This note is transient by design. It exists to survive one night's sleep, not to become documentation. Everything in it is already recorded properly in the notes linked below — this is a pointer, not a source.

## The one thing to do first

**Shoot wall photographs into `samples/`.**

Nothing else in software is blocked on anything except this. The whole toolpath stage is built and verified, but **every coverage figure measured so far came from `website/assets/test_result_*.jpg`, which are annotated segmentation exports — flat colour fills, not photographs.** The model has been scored against its own output.

Priority order (≈8–12 photos total, full checklist in `samples/README.md`):

1. **A wall with 4 tape-measured corner markers**, shot at ~0°, ~15° and ~30° off normal. Highest value by a distance: it unblocks [[🧪 Calibration & Testing Log]] §1b, which is **real Chapter 4 data obtainable with no gantry**. Tape crosses and a tape measure is the entire setup — record the measured mm in the table in `samples/README.md`.
2. A wall **wider than the 4.5 ft X rail** (1371.6 mm) — makes multi-position envelope clipping a real test rather than one faked by shrinking `AURA_TRAVEL_X_MM`.
3. Obstacles that **aren't doors** — window, outlet, switch plate, skirting.
4. **Hard lighting** — glare, shadow gradient. Where segmentation degrades.

> [!warning] Hold these out of the Roboflow training set
> If the same photographs train the model and validate the pipeline, the reported IoU and confidence measure memorisation, and a panel is entitled to say so. Shoot them deliberately separately from the ~100–200 custom photos in [[📋 Master Task Tracker]].

## Where things stand (2026-08-03)

Built, verified, committed — see [[📐 Path Planning & G-code Generation]]:
coordinate mapping (homography + uncalibrated fallback) · raster toolpath with obstacle subtraction · envelope clipping against the physical rails · G-code with a soft-limit backstop · `POST /api/toolpath` · **Toolpath** tab on `camera-view.html` with click-to-pick corner calibration · `backend/tools/test_toolpath.py`.

Not built: **nothing sends the G-code.** pyserial → Arduino is Phase 2, [[🖥️ Serial Communication Protocol]].

## Still-open decisions (not urgent, don't let them block the photos)

- `AURA_TRAVEL_MARGIN_MM` = 50 mm is a **placeholder** — the homing clearance has never been measured, and it changes how much gets clipped at the edges.
- `AURA_NOZZLE_WIDTH_MM` = 25 mm is a **placeholder** — makes row counts and coverage lengths provisional.
- No feed rate (`F`) and no `G21`/`G90` preamble in the G-code — deliberate, add during motion tuning.
- Lens distortion is uncorrected. A homography fixes perspective only. Measure first; only fix it if the numbers say it matters.
