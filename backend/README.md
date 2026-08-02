# AURA Backend

Flask API that connects the trained YOLOv8 instance-segmentation model to the
AURA website.

```
backend/
  app.py                 Flask server — /api/segment, /api/stream, /api/status,
                         /api/capture, /api/recommend-colors, /api/toolpath
  model_loader.py        Weights loading, CUDA/CPU selection, graceful missing-model handling
  color_recommender.py   Dominant-colour extraction (k-means in Lab) + colour-wheel palette
  coordinate_mapping.py  Normalized image polygons -> millimetres on the wall (homography)
  toolpath_generator.py  Serpentine raster fill around obstacles + G-code serialization
  tools/
    test_toolpath.py     Standalone toolpath smoke test + matplotlib visualiser
  requirements.txt       Pinned dependencies (read the version-risk notes at the top)
```

## Quick start

```powershell
# from the project root, with the venv active
pip install -r backend/requirements.txt --extra-index-url https://download.pytorch.org/whl/cu121
python backend/app.py
```

Then open <http://localhost:5000/dashboard.html>. The startup banner reports the
port, whether CUDA is active, whether the model loaded, and whether a camera was
found.

The website pages also work opened straight off disk (`file:///…/website/…`) —
the API sends permissive CORS headers for exactly that case.

## Model weights

Put the fine-tuned checkpoint at `website/model/best.pt`. See
[website/model/README.md](../website/model/README.md).

Missing weights are **not** fatal: the server starts, `/api/status` reports
`model_loaded: false` with the reason, and `/api/segment` returns HTTP 503 with
a clear message instead of a traceback.

To exercise the plumbing before training finishes, run against the COCO baseline:

```powershell
$env:AURA_ALLOW_FALLBACK = "1"; python backend/app.py
```

Every response then carries `using_fallback_model: true`, and the UI shows a
"Fallback model" badge — those numbers are the Phase-1 zero-shot baseline, not
fine-tuned AURA results.

## Endpoints

### `POST /api/segment`

Multipart upload, field name `image` (`file` also accepted). Optional `overlay`
field: `pre` | `during` | `post` (default `post`).

```json
{
  "success": true,
  "wall_detected": true,
  "original_image": "<base64 JPEG>",
  "masked_image": "<base64 JPEG>",
  "image_format": "jpeg",
  "detections": [
    {
      "class_id": 0,
      "class_name": "wall",
      "confidence": 0.8385,
      "bbox": [17.4, 230.1, 800.2, 736.9],
      "polygon": [[0.02, 0.21], [0.98, 0.19], "…normalized 0-1 contour…"],
      "area_ratio": 0.2969,
      "is_wall": true
    }
  ],
  "detection_count": 6,
  "wall_confidence": 0.8385,
  "top_confidence": 0.8779,
  "wall_coverage": 0.2969,
  "wall_class_inferred": false,
  "image_width": 810,
  "image_height": 1080,
  "inference_ms": 179.2,
  "device": "cuda:0",
  "model": "best.pt",
  "using_fallback_model": false
}
```

`polygon` is normalized to 0–1 and simplified with `approxPolyDP`, so the
frontend can clip its colour-preview canvas to the real mask without shipping
every contour pixel.

`wall_class_inferred: true` means the model has no wall-like class name, so the
largest mask in the frame was treated as the wall. The UI labels this rather
than presenting it as a model-declared class.

Errors: `400` unreadable/missing image · `413` over 16 MB · `503` model not
loaded · `500` inference failure. All return `{"success": false, "error": "…"}`.

### `GET /api/stream?overlay=pre|during|post`

MJPEG (`multipart/x-mixed-replace`) webcam stream with live segmentation.

| overlay  | what is drawn                                          |
|----------|--------------------------------------------------------|
| `pre`    | raw frame, no mask (also skips inference entirely)     |
| `during` | wall region only, blue                                 |
| `post`   | wall region blue + all other detected objects amber    |

Use it directly as an image source: `<img src="http://localhost:5000/api/stream?overlay=post">`.

The webcam is opened on the first connection and released when the last one
closes — the frontend clears the `<img>` src when you leave the Live tab, which
is what frees the device.

### `GET /api/status`

Polled by the dashboard every 3 s.

```json
{
  "model_loaded": true, "camera_available": true, "cuda_available": true,
  "gpu_name": "NVIDIA GeForce RTX 3050 Laptop GPU", "gpu_memory_gb": 4.0,
  "device": "cuda:0", "model": "best.pt", "task": "segment",
  "robot_status": "Ready", "robot_status_class": "badge-connected",
  "camera_index": 0, "camera_backend": "DSHOW", "camera_streaming": false,
  "last_inference": { "confidence": 0.83, "wall_detected": true,
                      "detection_count": 6, "inference_ms": 179.2,
                      "source": "upload", "age_seconds": 4.2,
                      "frames_processed": 12 },
  "torch_version": "2.5.1+cu121", "torch_cuda_version": "12.1"
}
```

Camera availability is cached for 30 s — probing a Windows webcam takes 1–2 s
and the dashboard polls faster than that.

### `GET /api/capture`

Grabs one still off the webcam and segments it. Same response shape as
`/api/segment`. Backs the "Capture from Camera" button on the colour page.

### `POST /api/recommend-colors`

Multipart image in (`image` field), wall-colour palette out. Self-contained —
it runs its own inference rather than needing a prior `/api/segment` call.

How it works:

1. Segment the frame, then build a mask of everything that is **not** wall
   (floor, furniture, ceiling). Falls back to "outside the wall mask", then to
   the whole frame, if the non-wall regions are too small to read.
2. k-means cluster those pixels in CIE-Lab (perceptual distance) to find the
   room's dominant colour.
3. Derive six wall colours from it by colour-wheel relationship.

```json
{
  "recommended": { "hex": "#E6D38A", "name": "Wheat",
                   "description": "why this works", "relationship": "complementary" },
  "alternatives": [ { "hex": "#A184DB", "name": "Violet Haze",
                      "relationship": "analogous", "description": "…" } ],
  "dominant_color": { "hex": "#5C78E6", "name": "Slate Blue", "share": 0.4041 },
  "context_colors": [ … ], "context_source": "non_wall_detections",
  "wall_detected": true, "inference_ms": 130.0
}
```

`alternatives` is always 5 entries: analogous, triadic, neutral, warm, cool.

Two deliberate behaviours worth knowing:

- **Saturation is clamped** to an interior-paint band (S 0.14–0.40, V 0.74–0.93).
  A raw complementary hue at full saturation is unusable over a whole wall.
- **Warm/cool start at their anchor hue** (32° / 212°) and are only nudged by
  the room, rather than interpolating toward it. Interpolating from a blue room
  toward amber takes the short path through magenta, so the "warm" swatch came
  back pink — the label has to be true.

Colour names come from a curated table matched by nearest Lab distance, and are
de-duplicated within a palette so no two swatches share a label.

### `POST /api/toolpath`

Multipart image in (`image` field), paint path out. The stage between
segmentation and the serial link: segment the frame, map the wall polygons into
millimetres, subtract every non-paintable detection, raster-fill what is left,
and serialize it to G-code. Self-contained — it runs its own inference.

Optional form fields:

| Field | Format | Default |
|---|---|---|
| `corners` | JSON `[[x_px, y_px] × 4]` — the wall's corner markers in the image, ordered **top-left, top-right, bottom-right, bottom-left** | absent → uncalibrated fallback |
| `wall_corners` | JSON `[[x_mm, y_mm] × 4]` — where those markers actually are on the wall, same order | the `AURA_WALL_*_MM` rectangle |

```json
{
  "success": true,
  "calibration_mode": "uncalibrated_scale",
  "calibration": { "matrix": [[1000.0, 0.0, 0.0], "…3x3…"],
                   "image_width": 640, "image_height": 640,
                   "image_corners_px": [ … ], "wall_corners_mm": [ … ] },
  "wall_detected": true,
  "wall_confidence": 0.8783,
  "wall_polygon_count": 1,
  "obstacle_polygon_count": 4,
  "obstacle_polygons_mm": [ [[229.6, 321.9], "…mm ring per subtracted region…"] ],
  "was_clipped": true,
  "clipped_area_mm2": 9119.68,
  "clipped_pct": 1.48,
  "travel_envelope_mm": [1371.6, 2743.2],
  "travel_margin_mm": 50.0,
  "paintable_area_mm2": 605233.96,
  "row_count": 37,
  "step_over_mm": 20.0,
  "total_paint_length_mm": 30538.72,
  "total_travel_length_mm": 1097.9,
  "bounds_mm": [3.13, 126.56, 998.44, 871.87],
  "events": [ { "type": "paint", "from": [3.13, 136.56], "to": [998.44, 136.56] },
              { "type": "travel", "from": [998.44, 136.56], "to": [998.44, 156.56] } ],
  "gcode": ["G0 X3.13 Y136.56", "M3", "G1 X998.44 Y136.56", "M5", "…"],
  "event_count": 87,
  "inference_ms": 125.2,
  "device": "cuda:0",
  "model": "best.pt",
  "using_fallback_model": false
}
```

**Calibration.** With `corners` the four correspondences are solved into a
perspective transform (`cv2.getPerspectiveTransform`), so a camera that is
off-axis or tilted still plans a square path;
`calibration_mode: "homography"`.

Without them it falls back to `calibration_mode: "uncalibrated_scale"` — the
frame is assumed to be filled edge-to-edge by a wall of the configured size and
scaled straight into it. **This corrects nothing**, so treat every millimetre in
that response as a scale assumption rather than a measurement. It is the normal
case today, because the gantry (and therefore the physical corner markers) does
not exist yet.

The solved transform comes back in `calibration` so a caller can hold onto it
and reuse it until the camera or the workpiece moves —
`WallCalibration.from_dict()` rebuilds it. Nothing persists it server-side.

**Path strategy.** Boustrophedon raster fill. The wall detections are unioned
and the non-paintable ones (`is_wall: false` — doors, windows, outlets, trim)
subtracted, so obstacles become holes in the geometry and routing around them
falls out for free rather than being a special case. Horizontal scan lines are
then cut against the result: a row crossing a hole comes back as several
disjoint spans, each one a stroke, with the spray off between them. Direction
alternates every row so the end of one row sits next to the start of the next
instead of driving the full width of the wall dry.

Row spacing is `AURA_NOZZLE_WIDTH_MM × (1 - AURA_SPRAY_OVERLAP)`. Passes have to
overlap or the seam between them shows once the paint dries.

**G-code** is the GRBL-compatible subset cited in the literature review for
Arduino-class controllers: `G0` rapid (dry), `G1` paint move, `M3`/`M5` spray on
/ off. `M3`/`M5` bracket each contiguous run of strokes rather than each
individual stroke, so the valve does not chatter between adjoining spans, and
the program always ends with `M5`. Coordinates are 2 dp, in millimetres.

No feed rate (`F`) is emitted — motion tuning happens against the built rig
(Phase 2), and a number invented here would silently become the number the
machine runs at.

**Reach.** The plan is clipped to the gantry's reachable travel before any row
is generated, and `clipped_area_mm2` / `clipped_pct` report what was cut.

This is not an error path. The X rail is 4.5 ft (1371.6 mm) — deliberately
shorter than most walls — so covering a full wall is a **multi-position
workflow**: paint what this position reaches, slide the gantry over,
re-calibrate, paint the next section. `was_clipped: true` is the normal case on
a real wall, and the clipped area is what the next position has to cover.

Clipping bounds against the **rails**, not the calibration marker quad. The four
markers define the pixel→mm mapping and nothing else — they can be placed
imprecisely, or deliberately mark a smaller test area, so they are not a safe
statement about where the machine can physically move. `paintable_area_mm2` and
`bounds_mm` are both post-clip.

A second, independent check runs at serialization: any `G0`/`G1` coordinate
outside the **full** rail range (not the margin-shrunk clip box) raises
`SoftLimitError` → HTTP 500 instead of being emitted. Clipping should already
have removed it, so that firing means a calibration or arithmetic bug — standard
GRBL soft-limit practice, and deliberately loud rather than a gantry driving
into an end stop.

The plan ships in two forms. `gcode` is what the machine consumes; `events` is
the same plan as geometry (`travel` = spray off, `paint` = spray on, both in mm)
so a viewer can draw it without writing a G-code parser. `obstacle_polygons_mm`
carries the subtracted regions for the same reason — "routes around obstacles"
is only checkable if you can see the obstacles next to the path avoiding them.

`row_count` counts rows that actually contain paint, not scan lines attempted.
An empty frame, or a wall completely covered by obstacles, is not an error: it
returns `event_count: 0` and an empty `gcode`.

Errors: `400` unreadable/missing image or malformed `corners` (wrong count,
collinear, not JSON) · `503` model not loaded, or `shapely` missing · `500`
anything else. All return `{"success": false, "error": "…"}`.

To see it rather than read it:

```powershell
python backend/tools/test_toolpath.py                 # first photo in samples/
python backend/tools/test_toolpath.py samples/wall_02.jpg
```

Loads the model directly (no server needed), runs the same pipeline, prints the
coverage summary and writes a plot of the path over the source image — paint
moves solid, travel moves dashed, non-paintable outlines dotted, gantry reach as
a dashed box — to the system temp directory. `--wall-width` / `--wall-height` /
`--step-over` override the defaults; `--out` sets the PNG path.

Input photos belong in [`samples/`](../samples/README.md). The script falls back
to `website/assets/test_result_*.jpg` only when that directory is empty, and
prints a **NOT A PHOTOGRAPH** banner when it does: those files are annotated
segmentation exports with the mask burnt in, so scoring the model on them scores
it against its own output. The geometry (mapping, clipping, G-code) is unaffected
either way, but the confidence and mask quality are optimistic.

## Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `AURA_PORT` | `5000` | HTTP port |
| `AURA_HOST` | `0.0.0.0` | Bind address |
| `AURA_MODEL_PATH` | `website/model/best.pt` | Weights location |
| `AURA_ALLOW_FALLBACK` | `0` | Allow the COCO baseline when `best.pt` is missing |
| `AURA_DEVICE` | auto | Force `cpu` or `cuda:0` |
| `AURA_CONF` | `0.25` | Confidence threshold |
| `AURA_IOU` | `0.45` | NMS IoU threshold |
| `AURA_IMGSZ` | `640` | Inference size — lower to 480 if the 4 GB GPU OOMs |
| `AURA_WALL_CLASSES` | `wall,paintable,surface` | Substrings that mark a class as the paintable wall |
| `AURA_NON_WALL_CLASSES` | `non-paintable,…,obstacle` | Substrings that veto the wall match — checked first, because `non-paintable` contains `paintable` |
| `AURA_CAMERA_INDEX` | `0` | Webcam index |
| `AURA_STREAM_FPS` | `15` | Stream frame-rate cap |
| `AURA_WALL_WIDTH_MM` | `1000` | Wall width assumed by the **uncalibrated** toolpath fallback (ignored once `corners` are supplied) |
| `AURA_WALL_HEIGHT_MM` | `1000` | Wall height, same caveat |
| `AURA_NOZZLE_WIDTH_MM` | `25` | Spray deposition width — **placeholder**; measure it on the built rig before quoting coverage |
| `AURA_SPRAY_OVERLAP` | `0.2` | Overlap between passes; `step_over = nozzle_width × (1 − overlap)` |
| `AURA_TRAVEL_X_MM` | `1371.6` | X rail travel (4.5 ft). Toolpath is clipped to this |
| `AURA_TRAVEL_Y_MM` | `2743.2` | Y rail travel (9 ft) |
| `AURA_TRAVEL_MARGIN_MM` | `50` | Homing/limit-switch clearance held back at **each** end — **provisional**, never measured on the frame |

## Frontend wiring

`website/nav.js` exposes `window.AURA.apiFetch/apiUrl/toDataUri`. It targets
`http://localhost:5000` for `file://` pages and the same origin otherwise.
Override the port once with `?api=http://localhost:5050` — it is remembered in
`localStorage`.

| Page | Uses |
|---|---|
| `color-recommendation.html` | `POST /api/segment` on upload; `POST /api/recommend-colors` for the palette; `GET /api/capture` for the camera button; wall polygons clip the colour preview |
| `camera-view.html` | `GET /api/stream?overlay=…` in Live mode; `POST /api/segment` per overlay in Upload mode (results cached); `POST /api/toolpath` in Toolpath mode — canvas render of the path over the frame, coverage tiles, and the G-code listing with a download button |
| `dashboard.html` | `GET /api/status` every 3 s |

## Known limits

- Recorded **video** playback still uses placeholder SVG overlays — there is no
  per-frame video segmentation endpoint yet.
- The colour **palette** itself is still the fixed demo list; only the wall
  region is real. K-means + harmony rules per the vault's Color Recommendation
  Module note are not implemented here.
- Painting progress on the dashboard is a placeholder — no gantry/serial link.
  `/api/toolpath` plans the path and emits G-code, but nothing sends it: the
  pyserial link to the Arduino is Phase 2.
- Toolpath **calibration** is the uncalibrated fallback unless corner pixels are
  passed in by hand. Detecting the markers in the frame automatically is a
  separate task, so today's millimetre figures are scale assumptions.
- `AURA_NOZZLE_WIDTH_MM` is a placeholder until the spray assembly is chosen,
  which makes `row_count` and the coverage lengths provisional too.
- `AURA_TRAVEL_MARGIN_MM` (50 mm) is likewise a placeholder — the frame is not
  built, so the homing clearance has never been measured. It changes how much
  gets clipped at the edges, so measure it before the first live run.
- Flask's dev server is fine for a single-operator demo. It is not hardened, and
  binds `0.0.0.0`; set `AURA_HOST=127.0.0.1` on an untrusted network.
