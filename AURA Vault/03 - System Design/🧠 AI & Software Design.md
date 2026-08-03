---
tags: [system-design, ai, software]
created: 2026-03-29
updated: 2026-07-12
status: synced-with-manuscript
---
# 🧠 AI & Software Design

> [!info] Related
> [[🔮 Segmentation Model]] · [[🎨 Color Recommendation Module]] · [[📐 Path Planning & G-code Generation]] · [[🖥️ Serial Communication Protocol]] · Code in `04 - AI & Code/Code Snippets/`

> [!warning] Sync note (2026-07-12) — superseded decision
> The AI stack originally planned here (**MobileNetV3 + DeepLabV3+**, trained from scratch on ADE20K + a custom set) has been **replaced** by **YOLOv8 (Ultralytics) instance segmentation**, evaluated **zero-shot-first** against COCO-pretrained weights. Custom-dataset fine-tuning (Roboflow annotation → Kaggle Tesla T4 GPU) is now a *conditional fallback*, triggered only if zero-shot performance is judged insufficient — not the default plan. See [[🔮 Segmentation Model]] for the updated module detail and [[📝 Chapter 1 - Introduction]] / [[📚 Literature Review Master]] for the rationale (COCO-pretrained backbones generalize well enough that fine-tuning becomes optional).

> [!important] Module names below are the **original plan**; the built code uses different files (2026-08-04)
> The pipeline was implemented as a Flask service rather than a `main.py` script, so the planned one-module-per-stage layout did not survive contact. Mapping:
>
> | Planned | As built | Note |
> |---|---|---|
> | `main.py` | `backend/app.py` | Flask app; orchestrates the stages as API endpoints |
> | `camera.py` | `backend/app.py` | Frame acquisition + MJPEG stream live in the server |
> | `segmentation.py` | `backend/model_loader.py` (+ `app.py`) | Weight loading vs. per-request inference |
> | `calibration.py` | `backend/coordinate_mapping.py` | Homography + uncalibrated fallback |
> | `path_planner.py` | `backend/toolpath_generator.py` | Raster planning, obstacle subtraction, envelope clipping |
> | `color_rec.py` | `backend/color_recommender.py` | See [[🎨 Color Recommendation Module]] |
> | `serial_ctrl.py` | *not built* | Phase 2 — [[🖥️ Serial Communication Protocol]] |
> | `evaluate.py` | *not built* | Metrics collected ad hoc; `backend/tools/test_toolpath.py` covers the toolpath stage only |

## Python Pipeline (as built) — updated
```
backend/app.py  (Flask, localhost:5000)
  1. frame from webcam / upload        -> raw image
  2. model_loader + run_inference()    -> YOLOv8 instance masks (zero-shot COCO weights, or fine-tuned)
  3. coordinate_mapping.to_mm(masks)   -> OpenCV homography/scaling -> mm-space regions
  4. color_recommender.recommend()     -> palette (CIE LCh harmony)
  5. toolpath_generator.plan(regions)  -> coordinate list -> G-code
  6. [serial_ctrl.stream() — NOT BUILT]-> Arduino executes (move + spray)
  7. [evaluate — NOT BUILT]            -> metrics (IoU/mAP, mm error, coverage %, Likert ratings)
```

## Modules
### Module 1 — Image Capture (planned `camera.py` → built in `backend/app.py`)
OpenCV `VideoCapture` grabs a frame from the USB/HD camera; handles a fixed, calibrated camera pose so pixel→mm mapping (via the homography transform) stays valid.

### Module 2 — Segmentation (planned `segmentation.py` → built as `backend/model_loader.py`)
Loads YOLOv8 (Ultralytics) with COCO-pretrained weights for the zero-shot baseline; runs instance-segmentation inference on the RTX 3050 with CUDA acceleration. If zero-shot IoU/mAP falls below the acceptable threshold, a Roboflow-labeled custom dataset is fine-tuned on a Kaggle Tesla T4 GPU and the resulting weights are redeployed locally. Details in [[🔮 Segmentation Model]].

### Module 3 — Calibration (planned `calibration.py` → built as `backend/coordinate_mapping.py`)
OpenCV homography and scaling transform, computed from physical corner markers affixed to the wall, converts segmentation-mask pixel coordinates into real-world millimeter positions. Stored and reused unless the camera or workpiece geometry changes.

### Module 4 — Path Planner (planned `path_planner.py` → built as `backend/toolpath_generator.py`)
Converts each calibrated region mask to a raster (boustrophedon) coordinate list, emits a sequence of (X, Y, spray) coordinates at 10–20% pass overlap. Details in [[📐 Path Planning & G-code Generation]].

> [!note] No G-code / No Marlin (updated 2026-08-03)
> Build uses Arduino Mega directly wired to TB6600 drivers — no RAMPS, no Marlin firmware. Path planner outputs coordinate lists that `serial_ctrl.py` converts to **custom serial commands** (`MOVE X Y`, `SPRAY ON/OFF`), not standard G-code. See [[🖥️ Serial Communication Protocol]].

> [!bug] As built, the toolpath stage emits G-code — the conversion described above does not exist yet
> `toolpath_generator.events_to_gcode()` produces `G0`/`G1`/`M3`/`M5` lines today. `serial_ctrl.py` is not written, so nothing converts them to `MOVE`/`SPRAY`. Whether to add that translation or replace the emitter is an **open decision** blocking firmware work — see [[🖥️ Serial Communication Protocol]].

### Module 5 — Color Recommendation (planned `color_rec.py` → built as `backend/color_recommender.py`)
Applies color-harmony rules (complementary/analogous/triadic/split-complementary) to dominant colors extracted from a reference image, optionally augmented with a deep-learning palette recommender consistent with the literature (Yuan et al., 2021; Wu et al., 2023). Harmony angles are computed in **CIE LCh(ab)**, not HSV, and output is constrained to an interior-paint L\*/C\* band. Details in [[🎨 Color Recommendation Module]].

### Module 6 — Serial Controller (`serial_ctrl.py` — **not built**, Phase 2)
`pyserial` custom command queue at 115200 baud: send one command (`MOVE X Y` / `SPRAY ON` / `SPRAY OFF` / `HOME`), block for `ok` response, timeout/retry once, halt + spray-off on second failure. **Not standard G-code** — Arduino runs a custom sketch that parses these commands and drives the TB6600 drivers directly. Details in [[🖥️ Serial Communication Protocol]].

## Module Architecture Diagram (ASCII)
```
 app.py ──> model_loader.py (YOLOv8) ──> coordinate_mapping.py ──> toolpath_generator.py ──╮
   │                                                                                      │
   │                                                                      [serial_ctrl.py] │  NOT BUILT
   │                                                                              ╰──> [Arduino]
   └──────────────────────> color_recommender.py ──────────────────────────────────╯  (palette)
                                     │
                             [evaluate.py]  NOT BUILT  (metrics, offline)
```

## Model Choice Rationale — updated
> [!note] Why YOLOv8 (Ultralytics), not MobileNetV3 + DeepLabV3+
> YOLOv8 is COCO-pretrained, runs at real-time speed on an RTX 3050 with CUDA, and — critically — supports a **zero-shot-first evaluation strategy**: the pretrained weights are tested directly against captured wall images before any custom dataset or fine-tuning cost is paid. This is consistent with the broader zero-shot/transfer-learning literature (Ni et al., 2023; R. Zhang et al., 2023), which shows COCO-pretrained backbones generalize well enough that fine-tuning becomes a targeted optimization rather than a prerequisite. Custom fine-tuning (Roboflow-labeled dataset, Kaggle Tesla T4 GPU) remains available as **Phase 2**, triggered only if Phase 1 (zero-shot) metrics are judged insufficient.

## Dataset Strategy — updated
- **Phase 1 (default): Zero-shot baseline.** COCO-pretrained YOLOv8 weights evaluated directly on captured wall images using IoU/mAP.
- **Phase 2 (conditional fallback):** Roboflow-based annotation of a custom wall-image dataset → Kaggle Tesla T4 fine-tuning → redeployment on the RTX 3050 → re-evaluation on the same held-out test set as Phase 1.
- **Augmentation** (if Phase 2 is triggered): flips, brightness/contrast jitter, slight rotation.

## Evaluation Metrics (in code)
- **IoU** and **mAP** at IoU ≥ 0.50, following the COCO evaluation protocol used by Ultralytics' own YOLOv8 evaluation framework — this is the reference standard cited in the manuscript, not an internally-invented threshold.

## Color Recommendation Approach
Harmony-rule-based palette generation (complementary, analogous, triadic, split-complementary) from a reference image's dominant colors, with region→color assignment. Evaluated qualitatively by **≥5 human raters** (1–5 scale), framed against ISO/IEC 25010:2011 usability/satisfaction sub-characteristics. See [[🎨 Color Recommendation Module]].

> [!warning] Removed evaluation linkage
> Color recommendation output is **no longer compared against applied paint color** (CIE ΔE\*) — AURA does not mix or synthesize paint, so that comparison isn't instrumentable. Only the palette's own coherence/suitability is rated.
