# AURA Backend

Flask API that connects the trained YOLOv8 instance-segmentation model to the
AURA website.

```
backend/
  app.py                Flask server — /api/segment, /api/stream, /api/status,
                        /api/capture, /api/recommend-colors
  model_loader.py       Weights loading, CUDA/CPU selection, graceful missing-model handling
  color_recommender.py  Dominant-colour extraction (k-means in Lab) + colour-wheel palette
  requirements.txt      Pinned dependencies (read the version-risk notes at the top)
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

## Frontend wiring

`website/nav.js` exposes `window.AURA.apiFetch/apiUrl/toDataUri`. It targets
`http://localhost:5000` for `file://` pages and the same origin otherwise.
Override the port once with `?api=http://localhost:5050` — it is remembered in
`localStorage`.

| Page | Uses |
|---|---|
| `color-recommendation.html` | `POST /api/segment` on upload; `POST /api/recommend-colors` for the palette; `GET /api/capture` for the camera button; wall polygons clip the colour preview |
| `camera-view.html` | `GET /api/stream?overlay=…` in Live mode; `POST /api/segment` per overlay in Upload mode (results cached) |
| `dashboard.html` | `GET /api/status` every 3 s |

## Known limits

- Recorded **video** playback still uses placeholder SVG overlays — there is no
  per-frame video segmentation endpoint yet.
- The colour **palette** itself is still the fixed demo list; only the wall
  region is real. K-means + harmony rules per the vault's Color Recommendation
  Module note are not implemented here.
- Painting progress on the dashboard is a placeholder — no gantry/serial link.
- Flask's dev server is fine for a single-operator demo. It is not hardened, and
  binds `0.0.0.0`; set `AURA_HOST=127.0.0.1` on an untrusted network.
