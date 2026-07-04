---
tags: [ai, path-planning, gcode]
created: 2026-03-29
status: active
---
# 📐 Path Planning & G-code Generation

> [!info] Related
> [[🔮 Segmentation Model]] · [[🖥️ Serial Communication Protocol]] · [[🧠 AI & Software Design]]

## Input
A **segmentation mask** (binary image; paintable regions = white).

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
- Calibrate a **pixels-per-mm** factor from a known reference in the camera view.
- `x_mm = x_px / pixels_per_mm` (+ origin offset). Same for Y.
- Store the calibration factor in config; re-measure if the camera moves.

## Spray Overlap
> [!tip] Use **10–20% overlap** per pass so adjacent stripes blend with no gaps (uniform coverage metric). Row spacing = spray_width × (1 − overlap).

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

## Known Limitation
> [!warning]
> Raster scan is **not optimal for complex/curved shapes** — thin diagonals get stair-stepped and travel isn't minimized. **Acceptable for the prototype** (flat walls, simple murals, per scope). Note this honestly in [[📝 Chapter 5 - Discussion]] as future work.
