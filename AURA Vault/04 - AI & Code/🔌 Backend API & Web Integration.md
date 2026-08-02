---
tags: [ai, backend, api, web, integration, flask]
created: 2026-07-31
updated: 2026-07-31
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
| `/api/segment` | POST | Multipart image → base64 original + mask overlay + per-detection confidences and polygons |
| `/api/stream` | GET | MJPEG webcam stream, `?overlay=pre\|during\|post` |
| `/api/status` | GET | Model / camera / CUDA state — drives the dashboard cards |
| `/api/capture` | GET | One segmented still off the webcam |
| `/api/recommend-colors` | POST | Room-derived wall palette — see [[🎨 Color Recommendation Module]] |
| `/api/toolpath` | POST | Multipart image → mm-space serpentine paint path + G-code. Optional `corners` / `wall_corners` form fields switch it from the uncalibrated fallback to a real homography — see [[📐 Path Planning & G-code Generation]] |

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
| `color-recommendation.html` | `POST /api/segment` on upload · `POST /api/recommend-colors` for the palette · `GET /api/capture` for the camera button · wall polygons clip the colour preview |
| `camera-view.html` | `GET /api/stream?overlay=…` live · `POST /api/segment` per overlay for uploaded stills · `POST /api/toolpath` in the **Toolpath** tab — canvas render of the path, coverage tiles, G-code listing + download, and click-to-pick corner calibration |
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

## Next steps

- [ ] Wire `pyserial` motion commands behind an `/api/paint` endpoint once the gantry runs
- [x] Feed mask polygons into [[📐 Path Planning & G-code Generation]] to close the segmentation → toolpath gap — done 2026-08-03 via `/api/toolpath`
- [ ] Re-run and re-record metrics after the ~1,000-image training run
