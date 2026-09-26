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
  mask_correction.py     Manual mask correction (brush + smart select) applied to the masks
  smart_select.py        Click-to-select regions — MobileSAM, with a colour-wand fallback
  toolpath_generator.py  Serpentine raster fill around obstacles + G-code serialization
  tools/
    test_toolpath.py     Standalone toolpath smoke test + matplotlib visualiser
    test_color_recommender.py  Invariant tests for the palette maths (no model needed)
    test_mask_correction.py    Before/after correction run + its invariants
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

### Manual mask correction — `mask_correction`

Optional on `/api/segment`, `/api/toolpath` and `/api/recommend-colors`: the
operator's edits, applied to the model's masks between inference and everything
downstream. `/api/stream` does not take it — it is a server-side MJPEG generator
with no per-frame correction hook.

```json
{
  "version": 2,
  "ops": [
    { "kind": "brush", "mode": "add",   "radius": 0.025,
      "points": [[0.10, 0.20], [0.19, 0.23]] },
    { "kind": "smart", "mode": "erase", "engine": "sam",
      "points": [[0.55, 0.48]], "labels": [1] }
  ]
}
```

Two kinds of operation:

- **`brush`** — a freehand stroke: a polyline plus a `radius`.
- **`smart`** — a *click*, resolved into a region by [smart select](#smart-select--apismart-select). What is stored is the prompt, never the outline it produced.

Coordinates are normalized to 0–1 against the image; `radius` is a fraction of
the image **width** for both axes, so the brush stays circular on a non-square
frame. Operations composite in order, last one winning per pixel — so erasing
over an earlier add undoes it exactly, whichever kind either was.

Version 1 payloads (`strokes`, brush only, no `kind`) are still accepted and read
as all-brush, so a browser tab left open across a server upgrade degrades to
"the brush half still works" instead of failing mid-demo. A `smart` op inside a
v1 envelope is rejected.

- `add` — "this is paintable wall": unioned into the wall mask, and subtracted
  from any non-paintable detection it covers (claiming a region as paintable has
  to drop an obstacle's claim on it, or the toolpath keeps routing around it).
- `erase` — "this is not paintable": subtracted from the wall masks, and the
  part that actually overlapped wall is re-emitted as a synthetic non-paintable
  region. A detection carries a single-ring polygon, so an erase *inside* a wall
  would vanish if it were only subtracted; as an obstacle it goes through the
  same subtraction that already handles windows and trim.

Operations rather than a rasterised bitmap: ~1 KB per correction instead of a few
hundred KB, resolution-independent (so one correction replays onto both a
preview canvas and the full-resolution frame), and undoable client-side.

Corrected responses carry a `mask_correction` block — `null` when no correction
was sent — reporting the operation counts, `added_px` / `removed_px`, their area
ratios, region counts, which engines resolved the smart selections, and what the
model alone found:

```json
"mask_correction": {
  "op_count": 2, "stroke_count": 1, "smart_count": 1,
  "engines_used": ["sam"],
  "add_stroke_count": 1, "erase_stroke_count": 1,
  "added_px": 10103, "removed_px": 3209,
  "added_area_ratio": 0.0247, "removed_area_ratio": 0.0078,
  "added_region_count": 1, "removed_region_count": 1,
  "model_detection_count": 5, "model_wall_detected": true
}
```

Detections gain `source` (`"model"` or `"manual"`) and `corrected`. **Manual
regions have `confidence: null` and are excluded from `wall_confidence` /
`top_confidence`** — a hand-drawn region is not a detection, and a fabricated
score would turn every confidence figure into a mixture of model output and
operator opinion. `wall_coverage` is the opposite case: it describes the mask
that will actually be painted, so corrections *are* counted in it.

A malformed payload is a **400**, not a silent drop (unlike `reference_image`,
which degrades gracefully). Correcting a mask is a deliberate override — showing
the operator an uncorrected result would look like the brush did nothing.

`python backend/tools/test_mask_correction.py` runs an image through both paths
and asserts these invariants.

### Smart select — `POST /api/smart-select`

Click a point, get the region under it, so a correction can be made in one click
instead of brushed in by hand. This endpoint **applies nothing** — it answers
with the outline so the editor can preview it. The correction still stores the
click, and `/api/segment` / `/api/toolpath` re-resolve it.

Multipart: `image`, plus

| Field | Format | Default |
|---|---|---|
| `points` | JSON `[[x, y], …]`, normalized 0–1. The click(s) | required |
| `labels` | JSON `[1, 0, …]` — `1` grows the selection, `0` carves away from it | all `1` |
| `engine` | `auto` \| `sam` \| `wand` | `auto` |
| `tolerance` | `0`–`100`, wand only. Lab colour distance the fill will cross | `18` |

```json
{
  "success": true,
  "engine": "sam", "engine_requested": "auto",
  "polygons": [[[0.02, 0.21], "…normalized 0-1 outline…"]],
  "region_count": 2, "area_px": 251377, "area_ratio": 0.6141,
  "looks_like_a_leak": false, "empty": false,
  "image_width": 640, "image_height": 640, "elapsed_ms": 117.9
}
```

**Two engines.** `sam` is **MobileSAM** (Zhang et al. 2023), a distilled Segment
Anything (Kirillov et al. 2023), run through the SAM predictor already vendored
in ultralytics — a 38 MB weights download, no new dependency. `wand` is a flood
fill in CIE Lab, i.e. a magic wand: no weights, no GPU, ~6 ms, works offline
forever. `auto` picks SAM when its weights are present.

The response says which engine **actually ran**, and the editor writes that back
into the saved operation. That is what stops a later replay from resolving the
same click with a different engine and quietly changing the G-code. If a saved
op names an engine the server does not have, `/api/toolpath` answers **400**
asking for the selection to be re-run rather than substituting one.

**Results are memoised** by (frame, engine, prompt). A SAM decode is ~150–300 ms
and every re-plan replays every selection, so the click that made a selection
warms the cache and the plan that follows is free — measured 1473 ms cold vs
121 ms warm on the same corrected toolpath, byte-identical G-code both times.

> **VRAM.** MobileSAM at `imgsz=1024` reserves ~2.3 GB alongside YOLOv8n-seg on
> the 4 GB RTX 3050. It fits, with little headroom. `AURA_SAM_IMGSZ=512` lowers
> it, `AURA_SAM_DEVICE=cpu` sidesteps the GPU, `AURA_SMART_SELECT=0` disables SAM
> entirely. A CUDA OOM is caught, the cache dropped, and the request degrades to
> the wand rather than failing.

Errors: `400` missing/unreadable image, bad `points`/`labels`/`engine`, or no
positive point · `503` the engine is present but could not run (OOM, broken
predictor) · `500` anything else.

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
3. Optionally blend in a reference image's colour and lean the seed toward who
   the room is for (see the optional fields below).
4. Derive six wall colours from the resulting seed by colour-wheel relationship.

Optional form fields — both only tune the palette, and neither can fail the
request; an unusable value is dropped, logged, and reported back as unused:

| Field | Format | Default |
|---|---|---|
| `reference_image` | Second multipart image — what the user wants the room to *look like*, not another view of the wall. Its own gated seed is blended into the room's at 70/30 (reference/room) in CIE LCh, hue via circular mean. The weight actually applied comes back as `reference_weight` | none — 100% room photo |
| `category` | Who the room is for: `child_boy`, `child_girl`, `teen`, `adult_man`, `adult_woman`, `elderly`, `none`. Applies an L\*/C\*/hue delta once to the shared seed, so all six swatches lean together | `none` |

Where the paint band and the sRGB gamut conflict, `_fit_lightness_for_chroma`
spends up to `CHROMA_LIGHTNESS_GIVEBACK` points of L\* to keep the chroma that
was asked for, rather than letting `_lch_to_rgb` cut chroma at fixed lightness.
Without it, two categories requesting C\* 44 and C\* 56 at L\* 78 both clipped to
the gamut ceiling of 32.9 and rendered as the same colour. Two invariants hold:
lightness is never spent without gaining chroma, and a larger chroma request
never yields a smaller result. At cyan-blue hues (~200–230°) the ceiling is below
both requests at every lightness in the band, so the distinction is genuinely
unrenderable there — that is sRGB, not a bug.

```json
{
  "recommended": { "hex": "#E6D38A", "name": "Wheat",
                   "description": "why this works", "relationship": "complementary" },
  "alternatives": [ { "hex": "#A184DB", "name": "Violet Haze",
                      "relationship": "analogous", "description": "…" } ],
  "dominant_color": { "hex": "#5C78E6", "name": "Slate Blue", "share": 0.4041 },
  "context_colors": [ … ], "context_source": "non_wall_detections",
  "reference_used": true,
  "reference_weight": 0.7,
  "reference_dominant_color": { "hex": "#BE3B5A", "name": "Brick Red", "share": 1.0 },
  "category_applied": "elderly",
  "wall_detected": true, "inference_ms": 130.0
}
```

`alternatives` is always 5 entries: analogous, triadic, neutral, warm, cool.

`dominant_color` stays the **room's** colour even when a reference is blended in
— that field answers "what colour is this room", which the reference does not
change. `reference_used` is false whenever the reference had no readable hue, so
the UI can say the input was dropped rather than leave the user guessing why it
changed nothing. The bias constants themselves are cited, hand-derived starting
points, not fitted values — see `CATEGORY_BIAS` in `color_recommender.py`.

Three deliberate behaviours worth knowing:

- **Lightness and chroma are clamped** to an interior-paint band in CIE LCh —
  `PAINT_LIGHTNESS` L\* 30–88, `PAINT_CHROMA` C\* 12–60. A raw complementary hue
  at full chroma is unusable over a whole wall. The hue angle passes through
  untouched, so the harmony relationship survives the clamp. (Widened from
  L\* 30–70 / C\* 20–60 on 2026-08-08 — the old ceiling made pastels
  unreachable.)
- **Warm/cool start at their anchor hue** (`WARM_ANCHOR_DEG` 48°,
  `COOL_ANCHOR_DEG` 267°, both LCh) and are only nudged by the room, rather than
  interpolating toward it. Interpolating from a blue room toward amber takes the
  short path through magenta, so the "warm" swatch came back pink — the label
  has to be true.
- **`recommended.relationship` depends on where the seed came from.** Room photo
  only → `complementary`, the visual opposite, because the wall has to hold its
  own against the floor and furniture. Reference image contributed →
  `reference-match`, sitting *on* the blended hue, because a reference states
  what the user wants rather than what the wall must contrast with. No usable
  hue → `warm-neutral`. The five alternatives are unaffected.

The reference seed is also picked differently from the room seed: **share ×
chroma** rather than share alone, floored at `MIN_REFERENCE_CLUSTER_SHARE`. A
mood board's backdrop beats its accent on pixel count almost every time, and the
accent is what the user is pointing at.

Hue blending only averages hues that carry meaning. If the room seed's chroma is
below `SEED_MIN_CHROMA` its hue is sensor noise, so the blended hue comes from
the reference alone; `L*` and `C*` still blend at the full weight. Without this, a grey room
dragged a pink reference 33° toward amber on the strength of a C\* 1.1 centroid.

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
| `mask_correction` | JSON brush strokes — see [Manual mask correction](#manual-mask-correction--mask_correction). Applied before the wall polygons are mapped into millimetres, so it lands in the G-code | absent → the model's mask unchanged |

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

Errors: `400` unreadable/missing image, malformed `corners` (wrong count,
collinear, not JSON) or malformed `mask_correction` · `503` model not loaded, or
`shapely` missing · `500` anything else. All return
`{"success": false, "error": "…"}`.

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
| `AURA_SAM_MODEL` | `website/model/mobile_sam.pt` | MobileSAM weights for smart select; absent → colour wand |
| `AURA_SAM_IMGSZ` | `1024` | Lower to `512` if VRAM is tight |
| `AURA_SAM_DEVICE` | auto | `cpu` keeps the GPU entirely for YOLOv8 |
| `AURA_SMART_SELECT` | `1` | `0` forces the colour wand everywhere |
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
| `camera-view.html` | `GET /api/stream?overlay=…` in Live mode; `POST /api/segment` per overlay in Upload mode (results cached); `POST /api/toolpath` in Toolpath mode — canvas render of the path over the frame, coverage tiles, and the G-code listing with a download button; a shared add/erase mask-correction brush posts `mask_correction` from both the Upload and Toolpath modes |
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
