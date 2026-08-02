---
tags: [ai, path-planning, gcode, coordinate-mapping]
created: 2026-03-29
updated: 2026-08-03
status: implemented
---
# 📐 Path Planning & G-code Generation

> [!info] Related
> [[🔮 Segmentation Model]] · [[🖥️ Serial Communication Protocol]] · [[🧠 AI & Software Design]]

> [!success] Status (2026-08-03) — built and verified
> Everything specced below is implemented: `backend/coordinate_mapping.py` (homography + `uncalibrated_scale` fallback), `backend/toolpath_generator.py` (raster generation, obstacle subtraction, envelope clipping, G-code serialization), `POST /api/toolpath`, a **Toolpath** tab on `camera-view.html` with click-to-pick corner calibration, and `backend/tools/test_toolpath.py` for standalone runs. Verified against the real `best.pt`. G-code is emitted but **nothing sends it** — that is [[🖥️ Serial Communication Protocol]], Phase 2.
>
> ⚠️ Every coverage figure measured so far came from `website/assets/test_result_*.jpg`, which are **annotated segmentation exports, not photographs**. The geometry is unaffected; the segmentation quality behind it is optimistic. Real photos go in `samples/` — see `samples/README.md`.

## Input
A **segmentation mask** (binary image; paintable regions = white) — in practice, the normalized 0–1 polygon already returned per-detection by `/api/segment`.

## Algorithm — Raster Scan (Boustrophedon / Lawn-Mower)
The simplest, most reliable coverage for solid regions: sweep left-to-right on one row, drop down, sweep right-to-left on the next (alternating direction to avoid wasted travel).

> [!note] Why raster, not an optimizer
> For flat walls and simple murals, raster coverage is **deterministic and easy to debug** — exactly what a solo builder needs. Optimal coverage (à la [[Liu & Cheng 2024 - Semantic Segmentation Spray]]) is overkill and adds failure modes.

## Steps
```
mask -> find contours -> bounding box per region ->
        raster rows (spacing = pass width - overlap) ->
        pixel coords -> mm coords (calibration) -> G-code string
```

## Coordinate Mapping (pixels → mm)
- `WallCalibration.from_corner_markers()` — real path: OpenCV homography (`cv2.getPerspectiveTransform`/`findHomography`) from 4 physical corner-marker correspondences, per Chapter 3 Step 2. Stored/reusable (serializable) so it doesn't need recomputing every run.
- `WallCalibration.uncalibrated()` — fallback used now, before markers exist: simple axis-aligned scale from the full camera frame to a configured `AURA_WALL_WIDTH_MM` × `AURA_WALL_HEIGHT_MM`. Results carry a `calibration_mode` flag so anything downstream (including thesis figures) can distinguish "real calibration" from "placeholder scale."

## Obstacle / Non-Paintable Handling
Non-wall detections (doors, windows, other obstacles — already classes in the dataset) are converted to the same mm frame and **subtracted** from the paintable wall polygon (Shapely `.difference()`) before rows are generated, so a row skips over an obstacle span instead of scanning through it.

## Spray Overlap
> [!tip] Use **10–20% overlap** per pass so adjacent stripes blend with no gaps (uniform coverage metric). Row spacing = spray_width × (1 − overlap). Implemented as `AURA_NOZZLE_WIDTH_MM` (placeholder default 25 mm — spray assembly not finalized, see [[💧 Spray System Design]]) × `AURA_SPRAY_OVERLAP` (default 0.2).

## Multiple Color Regions
Generate a **separate mask per color**; paint **sequentially** (one color pass, flush nozzle, next color). Order light→dark or by drying needs.

## G-code Output Example — filled 100×100 mm square (10 mm passes)
```gcode
G28
G1 X0 Y0 F2000
M3
G1 X100 Y0 F1200
G1 X100 Y10 F2000
G1 X0 Y10 F1200
G1 X0 Y20 F2000
G1 X100 Y20 F1200
; ... continue rows every 10mm up to Y100 ...
M5
```

## Envelope Clipping — Decision (2026-08-03) → **implemented**

> [!success] As built
> Clipping happens on the **geometry**, once, before any scan row is generated — `paintable.intersection(box(...))` after obstacle subtraction. Clipping already-generated events instead would mean splitting spans and re-deriving row counts and lengths from the leftovers.
>
> Config: `AURA_TRAVEL_X_MM` (1371.6) · `AURA_TRAVEL_Y_MM` (2743.2) · `AURA_TRAVEL_MARGIN_MM` (50, **provisional** — never measured on the frame).
>
> `/api/toolpath` returns `was_clipped`, `clipped_area_mm2`, `clipped_pct`, `travel_envelope_mm`, `travel_margin_mm`. `paintable_area_mm2` and `bounds_mm` are both **post-clip**. The Toolpath tab shows a banner when clipped; the test script prints the figures and draws the reach boundary on the plot.
>
> Soft-limit backstop is live: any `G0`/`G1` outside the **full** rail range raises `SoftLimitError` → HTTP 500 instead of being emitted.
>
> Measured with realistic travel, only the 50 mm homing margin bites — `test_result_1` clips 1.5%, `test_result_4` clips 5.3%. Forcing 500 × 500 mm travel clips 82.6% and drops 37 rows to 16, with all G-code inside `[50, 450]`.

**Clip, not reject.** The Claude Code handoff (2026-08-03) flagged this as open: a detected wall mask can extend past the calibrated 4-marker envelope, and the unclipped homography extrapolation produces unreachable coordinates (e.g. an 1800×1200 mm envelope test produced bounds `[-117.6, -176.31, 1899.35, 1223.55]` mm).

**Why clip and not reject:** the gantry's X-axis rail is only 4.5 ft (1371.6 mm) — see [[⚙️ Mechanical Design]] — against walls that are routinely wider. Covering a full wall was always planned as **multiple gantry positions**, manually repositioned and re-calibrated between passes. Under that plan, "the mask extends past what this position can reach" isn't an error condition, it's the *normal* case on almost every run. A reject policy would refuse to generate a toolpath on nearly every real wall; clip is what actually implements the multi-pass workflow — paint what's reachable from the current position, report what's left over for the next one.

**Clip boundary = physical rail limits, not the marker quad.** The 4 calibration markers define the pixel↔mm mapping; they are not necessarily an accurate statement of where the gantry can physically move. Clip against the hardware's real travel envelope (1371.6 × 2743.2 mm minus a homing/limit-switch safety margin — placeholder 50 mm per side until measured on the built frame — see [[⚙️ Mechanical Design]]), independent of exactly where the markers were placed.

**Belt-and-suspenders:** keep a hard soft-limit check at G-code emission too (reject/flag any individual `G0`/`G1` command outside the physical envelope even after clipping) as a backstop against calibration or math errors — standard GRBL/CNC practice, not redundant with the clip step.

**API contract implication:** `/api/toolpath` response should report clipped/skipped paintable area (mm² and/or % of the detected mask) alongside the toolpath itself, so it's visible how much of the wall still needs a repositioned pass.

## Known Limitation
> [!warning]
> Raster scan is **not optimal for complex/curved shapes** — thin diagonals get stair-stepped and travel isn't minimized. **Acceptable for the prototype** (flat walls, simple murals, per scope). Note this honestly in [[📝 Chapter 5 - Discussion]] as future work.
