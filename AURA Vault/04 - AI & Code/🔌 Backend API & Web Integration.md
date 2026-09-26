---
tags: [ai, backend, api, web, integration, flask]
created: 2026-07-31
updated: 2026-08-16
status: implemented
---
# 🔌 Backend API & Web Integration

> [!info] Related
> [[🔮 Segmentation Model]] · [[🎨 Color Recommendation Module]] · [[🧠 AI & Software Design]] · [[🖥️ Serial Communication Protocol]] · Repo: `backend/` and `website/`

> [!success] Status (2026-07-31)
> The trained `best.pt` is **live behind a local API** and every page of the AURA website now runs against real inference — no mock data or placeholder overlays remain on the segmentation path. This is the first end-to-end link between the AI model and the demo UI.

## Purpose

Turn the Kaggle-trained checkpoint into something demonstrable: a local server the website (and later the path-planning stage) can call, rather than a notebook that has to be re-run by hand.

## Stack

| Layer | Choice | Why |
|---|---|---|
| Server | **Flask 3.1** (threaded dev server) | The two hard requirements are multipart upload and an MJPEG stream. MJPEG is a blocking generator pushing frames off a shared `VideoCapture`; Flask maps onto that directly. FastAPI would need the sync generator pushed to a threadpool by hand for no gain across three endpoints. |
| Inference | Ultralytics **YOLOv8n-seg**, `retina_masks=True` | Masks at input resolution instead of 160×160, so mask edges survive into the coordinate mapping. |
| Vision | OpenCV (`cv2`) | Already required; also does the k-means for [[🎨 Color Recommendation Module]]. |
| Device | **CUDA on the RTX 3050**, CPU fallback | Matches Decision #4 — laptop does all inference. |

Verified environment: Python 3.11.5 · torch 2.5.1+cu121 · torchvision 0.20.1+cu121 · ultralytics 8.4.90 · RTX 3050 Laptop (4 GB).

## Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/segment` | POST | Multipart image → base64 original + mask overlay + per-detection confidences and polygons. Optional `mask_correction` (brush strokes) — see § Manual mask correction |
| `/api/stream` | GET | MJPEG webcam stream, `?overlay=pre\|during\|post` |
| `/api/status` | GET | Model / camera / CUDA state — drives the dashboard cards |
| `/api/capture` | GET | One segmented still off the webcam |
| `/api/recommend-colors` | POST | Room-derived wall palette. Optional `reference_image` (second multipart image, blended into the seed 70/30) and `category` ("for whom", biases the seed) — see [[🎨 Color Recommendation Module]] |
| `/api/toolpath` | POST | Multipart image → mm-space serpentine paint path + G-code. Optional `corners` / `wall_corners` form fields switch it from the uncalibrated fallback to a real homography — see [[📐 Path Planning & G-code Generation]]. Optional `mask_correction` patches the mask *before* the polygons are mapped into millimetres, so a hand correction lands in the G-code |
| `/api/smart-select` | POST | Multipart image + a clicked point → the region under it, as normalized polygons. MobileSAM, or a colour flood fill when its weights are absent. Preview only — see § POST /api/smart-select |

**Overlay modes** map to the painting stages: `pre` = raw frame, `during` = paintable wall only (green `#22C55E`), `post` = wall plus non-paintable regions (amber `#EAB308`).

## Graceful degradation

`model_loader.py` never lets a missing checkpoint crash the server. If `best.pt` is absent the process still starts, `/api/status` reports `model_loaded: false` **with the reason**, and inference endpoints return HTTP 503 instead of a traceback. This matters for the defense: a mis-copied weights file degrades to a clear on-screen message rather than a dead demo.

---

## ⚠️ Findings from deploying the model

### 1. `non-paintable` was being scored as paintable wall

> [!danger] Class-naming collision — the important finding
> Wall classes were matched by substring against `wall, paintable, surface`. The string **`non-paintable` contains `paintable`**, so *every obstacle was classified as paintable wall.*

Consequences before the fix:

| Symptom | Before | After |
|---|---|---|
| `wall_coverage` on a test frame | 0.99 (nonsense) | 0.87 |
| Wall / non-wall split | 5 wall, 0 obstacle | 1 wall, 4 obstacle |
| `during` vs `post` overlays | byte-identical | correctly different |
| Reported confidence | an obstacle's score | the actual wall's score |

The colour preview would also have tinted windows and trim as paintable surface. Fixed by checking negative keywords **before** the positive match (`AURA_NON_WALL_CLASSES`).

> [!tip] Carry this into future datasets
> Any class name that is a superstring of another class name will collide under substring matching. Worth remembering when labelling the 1,000-image set — prefer names that are not substrings of each other (e.g. `obstacle` rather than `non-paintable`).

### 2. Stale server processes served an old model

Four orphaned `app.py` processes from an earlier session were still bound to port 5000, started *before* `best.pt` existed, so they had fallen back to the COCO baseline and were answering with 80 COCO classes. Symptoms looked like a model-loading bug but were purely environmental.

> [!warning] Before trusting anything on screen
> Check the startup banner reads `Model: LOADED`, `best.pt`, `Classes (2): non-paintable, wall`. If it lists 80 COCO classes, you are talking to a stale process — kill it and restart.

---

## 📈 Measured performance (RTX 3050 Laptop, 640×640)

| Measure | Value |
|---|---|
| Cold-start warm-up pass | ~1.8 s |
| Inference per image | **~100 ms** (range 97–140 ms) |
| Wall confidence, test images | 0.88 – 0.94 |
| Wall confidence, live webcam frame | 0.80 – 0.93 |
| MJPEG raw passthrough | ~13 fps |
| MJPEG with per-frame segmentation (1280×720) | ~5–10 fps |

> [!note] Real-time enough for the demo, not for closed-loop control
> ~100 ms/frame is fine for the operator-facing view. The painting sequence segments **once** per wall and then executes a planned path ([[📐 Path Planning & G-code Generation]]) — it does not need per-frame inference, so the streaming frame-rate is a UI concern only.

---

## Frontend wiring

| Page | Uses |
|---|---|
| `color-recommendation.html` | `POST /api/segment` on upload · `POST /api/recommend-colors` for the palette, carrying the optional `reference_image` + `category` inputs · `GET /api/capture` for the camera button · wall polygons clip the colour preview |
| `camera-view.html` | `GET /api/stream?overlay=…` live · `POST /api/segment` per overlay for uploaded stills · `POST /api/toolpath` in the **Toolpath** tab — canvas render of the path, coverage tiles, G-code listing + download, and click-to-pick corner calibration · a shared add/erase **mask-correction editor** on the Upload/Playback and Toolpath tabs (brush + `POST /api/smart-select`), posting `mask_correction` from both |
| `dashboard.html` | `GET /api/status` every 3 s → robot / camera / CUDA cards |
| `results.html` | Static — real v2 metrics and the six segmentation outputs |

`nav.js` exposes a shared `window.AURA.apiFetch` helper that resolves the API base whether a page is opened over `file://`, served by Flask, or served by a separate static server.

> [!note] CORS
> Written by hand as an `after_request` hook rather than adding `flask-cors` — one less dependency, and it covers the `Origin: null` case that pages opened straight off disk produce.

---

## 🔒 Decision — no CDN dependencies

The custom colour wheel is drawn on a `<canvas>` rather than loaded from a CDN (e.g. iro.js). **A `<script src="https://…">` fails silently with no internet.** The defense venue's connectivity cannot be assumed, and a dead colour picker mid-demo is not a recoverable situation. The site's only external script is the local `nav.js`.

## Known limits

- **Recorded video** playback still uses placeholder SVG overlays — there is no per-frame video segmentation endpoint.
- **Gantry control is not connected.** The dashboard's "Painting Progress" card is inert; the serial link in [[🖥️ Serial Communication Protocol]] is not wired to the API yet. `/api/toolpath` plans the path and emits G-code, but nothing sends it.
- **Toolpath calibration defaults to the uncalibrated fallback.** Corner markers must be clicked by hand in the Toolpath tab (or posted as `corners`); nothing detects them in the frame automatically, so millimetre figures are scale assumptions until they are supplied.
- The API is **localhost-only and unauthenticated** — appropriate for a local demo, not for exposure on a network.
- Test-result images used in the gallery are already-annotated exports, so they are **not valid inputs** for the colour recommender (it samples the burnt-in annotation colour, not the room) — **nor for the toolpath**, where they score the segmentation model against its own output. Real photographs belong in `samples/` (see `samples/README.md`); `backend/tools/test_toolpath.py` reads there first and prints a **NOT A PHOTOGRAPH** banner if it has to fall back to `website/assets/`. **Hold the `samples/` set out of Roboflow training**, or IoU measures memorisation.
  - **Capture spec for `samples/`:** at least **8–12 photos of a wall not used in the Roboflow training set**, with **all 4 corners marked with an X in masking tape**. The X-marked corners are the physical calibration reference for the homography/scaling step ([[📐 Path Planning & G-code Generation]]), so `/api/toolpath` has real corner points to test against instead of the uncalibrated fallback.

## 🖌️ Manual mask correction — `mask_correction` (built 2026-08-15)

Optional form field on `POST /api/segment`, `POST /api/toolpath` and `POST /api/recommend-colors`. Carries the operator's brush strokes; the server applies them to the model's masks between inference and everything downstream. **Not on `/api/stream`** — server-side MJPEG, no per-frame correction hook.

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

**Shape chosen: an operation list, applied server-side.** Coordinates normalized 0–1 against the image; `radius` is a fraction of image *width*, scaled by width on both axes so the brush stays circular on a non-square frame. Rationale and the full semantics table live in [[🔮 Segmentation Model]] § Manual Mask Correction — in short: ~1 KB instead of a few hundred KB of bitmap, resolution-independent (so one correction replays onto both the preview canvas and the full-resolution frame), undoable client-side, and applied at the single point in `run_inference()` that every consumer reads through.

Two kinds of operation. `brush` is a freehand stroke; `smart` is a **click**, resolved by `POST /api/smart-select` (below). Both store the *input*, never the resulting outline. Operations composite in order, last one winning per pixel.

**Version 2** since 2026-08-16. Version 1 (`strokes`, brush only) is still parsed as all-brush so a stale browser tab degrades rather than 400s; a `smart` op inside a v1 envelope is rejected.

Responses gain a `mask_correction` block — `null` when none was sent — with `op_count` / `stroke_count` / `smart_count`, `engines_used`, `added_px` / `removed_px`, their area ratios, region counts, and `model_detection_count` / `model_wall_detected` for what the model alone found. Detections gain `source` (`"model"` / `"manual"`) and `corrected`.

> [!warning] Manual regions carry `confidence: null`
> They are excluded from `wall_confidence` and `top_confidence`. A hand-drawn region is not a detection; inventing a score for it would make every confidence figure a blend of model output and operator opinion. `wall_coverage` *does* include them — it describes the mask that will actually be painted.

A malformed payload is **400**, deliberately unlike `reference_image`'s graceful degradation: a correction is an explicit override, and silently dropping it would show an uncorrected result that looks like the brush did nothing.

`python backend/tools/test_mask_correction.py` asserts the invariants (31 checks).

## ✨ `POST /api/smart-select` (built 2026-08-16)

Click a point, get the region under it — so a correction is one click instead of a hand-drawn stroke. **Applies nothing**: it returns the outline so the mask editor can preview it. The correction still stores the click, and `/api/segment` / `/api/toolpath` re-resolve it.

Multipart `image` plus `points` (JSON normalized `[[x,y],…]`), optional `labels` (`1` grows / `0` carves), `engine` (`auto` | `sam` | `wand`), `tolerance` (wand only). Returns `polygons`, `area_ratio`, `engine` (the one that **actually ran**), `looks_like_a_leak`, `elapsed_ms`.

**MobileSAM, at no dependency cost.** The pinned ultralytics already ships the SAM predictors, so this is a 38 MB weights file at `website/model/mobile_sam.pt` — nothing added to `requirements.txt`. Falls back to a Lab flood-fill wand when the weights are absent, and `/api/status` gains a `smart_select` block reporting which engine is live so the UI can label it honestly. Full engine detail, measured timings and the VRAM budget: [[🔮 Segmentation Model]] § Smart Select.

> [!warning] Two contract details that protect the G-code
> **The engine is pinned on first resolve.** The response says which engine ran; the browser writes that into the saved op. A replay against a server without those weights answers **400 "re-run the smart selection"** rather than silently resolving the same click with a different engine.
>
> **Results are memoised** by (frame, engine, prompt), because every re-plan replays every selection. Measured 1473 ms cold vs 121 ms warm on the same corrected toolpath, byte-identical G-code both times.

## 🧭 Planned endpoint changes (2026-08-08)

> [!success] Panel-recommendation follow-up — two of three now built
> Full context: [[🎯 Post-Defense Recommendations & Action Items]]. Three features need API surface: reference-image + demographic category on the color module (**done 2026-08-08**), mask-correction on segmentation/toolpath (**done 2026-08-15**), and `paint_level_pct` on status (still blocked on hardware).

| Endpoint | Change | For |
|---|---|---|
| ✅ `POST /api/recommend-colors` | **Built 2026-08-08.** Optional multipart `reference_image` and optional `category` form field, validated against `CATEGORY_BIAS` by `normalize_category()`. Response gained `reference_used` (bool), `reference_dominant_color` (same shape as `dominant_color`, `null` when unused) and `category_applied` (the category that *actually* ran). Both inputs degrade gracefully — an undecodable reference or an unknown category logs a warning and is dropped, never a 500. | [[🎨 Color Recommendation Module]] § Reference Image + Demographic Category |
| ✅ `POST /api/segment` + `POST /api/toolpath` | **Built 2026-08-15.** Optional `mask_correction` form field — a JSON stroke list, unioned (add) / subtracted (erase) against the model's own mask in `backend/mask_correction.py` before anything downstream reads it. Also accepted on `/api/recommend-colors` (API only — the colour page has no brush UI, but the mask it clusters from is the same one, so the contract holds). See § Manual mask correction above. | [[🔮 Segmentation Model]] § Manual Mask Correction |
| `GET /api/status` | New `paint_level_pct` field once the load-cell sensor is wired. | [[💧 Spray System Design]] § Planned: Paint-Level Monitoring |

## Next steps

- [ ] Wire `pyserial` motion commands behind an `/api/paint` endpoint once the gantry runs
- [x] Feed mask polygons into [[📐 Path Planning & G-code Generation]] to close the segmentation → toolpath gap — done 2026-08-03 via `/api/toolpath`
- [ ] Re-run and re-record metrics after the ~1,000-image training run — **measure with the brush unused**, or the figures score the operator as well as the model
- [x] Add `reference_image` + `category` handling to `/api/recommend-colors` — done 2026-08-08, see § Planned endpoint changes above
- [x] Add mask-correction payload to `/api/segment` / `/api/toolpath` — done 2026-08-15, see § Manual mask correction above
- [ ] Add a brush to `color-recommendation.html` if the colour module ever needs it — the endpoint already accepts `mask_correction`, only the UI is missing
- [ ] Extend `/api/status` with a `paint_level_pct` field once the load-cell sensor is wired — see [[💧 Spray System Design]] § Planned: Paint-Level Monitoring
