---
tags: [ai, segmentation, deep-learning]
created: 2026-03-29
updated: 2026-08-16
status: training-in-progress
---
# 🔮 Segmentation Model

> [!info] Related
> [[🧠 AI & Software Design]] · [[📐 Path Planning & G-code Generation]] · [[Bjekic 2023 - Wall Segmentation CNN]] · Code: [[segmentation_inference.py]]

> [!warning] Sync note (2026-07-12) — superseded decision
> This note previously specified **MobileNetV3 + DeepLabV3+** trained on ADE20K + a custom set. That plan is **replaced** by **YOLOv8 (Ultralytics) instance segmentation**, evaluated **zero-shot-first** against COCO-pretrained weights, with custom fine-tuning as a conditional fallback only. Rationale and full citation trail: [[📚 Literature Review Master]] Theme 3.

## Problem Definition
Given a wall image from the fixed camera, output an **instance-segmentation mask** identifying **paintable regions**.

## Evaluation Strategy — Zero-Shot-First
**Phase 1 (default): Zero-shot baseline.** Deploy YOLOv8 on the RTX 3050 (CUDA, Ultralytics library) using pre-trained COCO weights, unmodified. Run inference on captured wall images and evaluate the resulting masks using **IoU** and **mAP**, following the COCO evaluation protocol — the same metrics used by Ultralytics' own YOLOv8 evaluation framework. This determines whether the system can proceed *without* a custom dataset at all.

**Phase 2 (conditional fallback): Fine-tuning.** Triggered *only if* Phase 1 metrics fall below acceptable thresholds. A custom dataset is prepared: wall images collected and annotated with instance-segmentation polygons in **Roboflow**, augmented within the Roboflow workflow, uploaded to **Kaggle**, and used to fine-tune YOLOv8 on a **Tesla T4 GPU**. Resulting weights are redeployed on the RTX 3050 laptop and re-evaluated on the same held-out test set used in Phase 1.

## Dataset Options (if Phase 2 is triggered)
| Option | Pros | Cons |
|---|---|---|
| COCO-pretrained weights (default) | No labeling cost; strong general-object priors | Not painting-specific |
| Roboflow-labeled custom set | Matches real test walls | Time cost (annotation effort) |
| ADE20K (`wall` class) | Large, free, labeled | General scenes, not painting-specific — considered as a fallback pretraining source if Roboflow data proves too limited |

## Why YOLOv8, Not MobileNetV3 + DeepLabV3+
> [!note]
> YOLOv8 is real-time-capable on the RTX 3050 with CUDA acceleration and, critically, ships with strong COCO-pretrained weights that generalize well enough for a **zero-shot-first** strategy — avoiding the labeling/training cost of a from-scratch segmentation model unless it proves necessary. This also aligns AURA's evaluation directly with the COCO benchmark and Ultralytics' own evaluation tooling, which is the reference standard cited in [[📝 Chapter 3 - Methodology]].

## I/O Spec
- **Input:** camera frame (preprocessed/normalized).
- **Output:** per-instance segmentation mask(s) identifying paintable regions, at source resolution (or resized back to it).

## Post-Processing
```
YOLOv8 masks -> morphological clean (open/close) -> contour extraction ->
                OpenCV homography/scaling calibration (pixel -> mm) ->
                path_planner input
```

## Evaluation
- **IoU** and **mAP at IoU ≥ 0.50** — the COCO-protocol convention, matching Ultralytics' YOLOv8 evaluation framework. This is the reference-standard metric cited in the manuscript, not an internally-invented threshold.
- Phase 1 vs. Phase 2 metrics are compared on the same held-out test set to justify (or rule out) the fine-tuning step.

> [!tip] "Good enough" for the thesis
> The mask only needs to be accurate enough that the **raster planner** fills the right area. Small boundary errors are absorbed by spray overlap. Perfect segmentation is not required — reliable region identification is, and the zero-shot-first strategy means fine-tuning effort is spent only if that reliability isn't already there.

---

## 📊 Training & Testing Progress

### 2026-07-30 — Run 1: 150-image dataset (instance segmentation confirmed)
- Object detection tried first → ruled out (bounding boxes only, not masks)
- Switched to instance segmentation → correctly masks wall and non-paintable regions
- Pipeline (Roboflow → Kaggle T4 → best.pt) confirmed working end-to-end
- Metrics: not recorded for this run (exploratory)

---

### 2026-07-30 — Run 2: 300-image dataset (aura_seg_v2)

**Training config:**
| Parameter | Value |
|---|---|
| Model | YOLOv8n-seg (COCO pretrained) |
| Dataset | 300 images, 2 classes (wall, non-paintable) |
| Augmentation | 3x multiplier via Roboflow |
| Epochs | 100 (with patience=20 early stopping) |
| Image size | 640×640 |
| Batch size | 16 |
| Compute | Kaggle Tesla T4 GPU |
| Split | 70/20/10 train/val/test |

**Test set results (29 images):**
| Metric | Value | Notes |
|---|---|---|
| **mAP@0.50** | **0.780** | Above 0.70 threshold — solid result |
| **mAP@0.50-95** | **0.548** | Strict metric, respectable at this dataset size |
| **Precision** | **0.845** | When model says "wall," correct 84.5% of the time |
| **Recall** | **0.729** | Catches 73% of actual wall regions — improves with more data |

> [!success] Assessment
> Strong preliminary results for 300 images. Precision > Recall indicates the model is conservative — it occasionally misses wall edges rather than falsely labeling non-walls. This is the safer failure mode for a painting robot. All metrics expected to improve as dataset grows toward 1,000 images.

**Weights saved:** `best.pt` — deployed to `/website/model/best.pt` for backend integration
**Next training run:** target ~600–1,000 images

---

### 2026-07-31 — Deployed behind the local API

`best.pt` now runs live behind Flask and drives every page of the AURA website. Full detail in [[🔌 Backend API & Web Integration]].

**Confirmed on load:** `task=segment`, `classes={0: 'non-paintable', 1: 'wall'}`, running on `cuda:0` (RTX 3050 Laptop).

**Measured inference (RTX 3050, 640×640):**

| Measure | Value |
|---|---|
| Warm-up pass (cold start) | ~1.8 s |
| Per-image inference | **~100 ms** |
| Wall confidence — test images | 0.88 – 0.94 |
| Wall confidence — live webcam | 0.80 – 0.93 |

> [!danger] Class-naming collision found in deployment — fixed, names finalized
> The backend matched wall classes by substring. **`non-paintable` contains the substring `paintable`**, so every obstacle was being scored as paintable wall: `wall_coverage` inflated to 0.99, confidence reported an obstacle's score, and the during/post overlays rendered identically. Fixed by vetoing negative keywords first.
>
> **Decided (2026-08-04): class names stay `wall` and `non-paintable`** for the next Roboflow export — no rename to `obstacle` or similar. The substring collision is already handled in the backend matcher (negative-keyword veto), so it doesn't need to be designed around at the annotation level.

> [!note] Masks are extracted at full resolution
> Inference uses `retina_masks=True`, so masks come back at input resolution instead of the default 160×160. Mask edges therefore survive into contour extraction and the coordinate mapping — relevant to [[📐 Path Planning & G-code Generation]].

The segmentation mask is also **load-bearing for colour recommendation**, not just path planning: [[🎨 Color Recommendation Module]] clusters the *non-wall* regions to read the room's colour, which is only possible because the model separates wall from non-paintable.

---

## 🖌️ Manual Mask Correction (Brush Tool) — BUILT 2026-08-15

> [!success] Panel recommendation, shipped
> Full context: [[🎯 Post-Defense Recommendations & Action Items]]. Kurt's initial read was that manual mask correction is too much human intervention for an "AI-controlled" pipeline — panel was fine with it as a human-in-the-loop safety net, and it's a reasonable stopgap while the dataset grows from the current 300 images (Run 2, mAP@0.50 0.780) toward the ~1,000-image target logged above. **It does not replace fine-tuning; the ~1,000-image run is still the plan.**

**Scope as built:** add + erase on both the Upload/Playback segmentation preview and the Toolpath planner in `camera-view.html`. Not the Live Feed — server-side MJPEG with no per-frame correction hook. Two ways to make an edit: a freehand **brush**, and **✨ smart select** (click a region — added 2026-08-16, see below).

**Where this sits in the pipeline:** correction happens *after* YOLOv8 inference, *before* the mask is consumed downstream. It patches the output of this module — the same mask that feeds [[🎨 Color Recommendation Module]] (non-wall region clustering) and [[📐 Path Planning & G-code Generation]] (raster toolpath generation).

**State model (decided 2026-08-10, implemented as specified):** one corrected mask per session/image, shared across both consumers — a correction drawn in Upload/Playback is already applied when Toolpath plans the same frame. Switching to the Toolpath tab with a still already loaded in Upload/Playback adopts that frame automatically, so the carry-over is literal rather than something the operator has to re-trigger.

### Mechanics chosen (was "implementation detail, not decided")

| Decision | Choice | Why |
|---|---|---|
| Where the correction is applied | **Server-side**, in `backend/mask_correction.py`, called from `run_inference()` right after `parse_detections` / `resolve_wall` | One patch point that every consumer reads through. The overlay render, the mm-space polygons that become G-code, and the colour recommender's clustering all get the corrected mask without knowing a correction happened — and no polygon geometry has to be reimplemented in JavaScript |
| Payload shape | **Stroke list**, not a rasterised bitmap. JSON in a `mask_correction` form field, next to `corners` | ~1 KB instead of a few hundred KB per request; resolution-independent, which is exactly what makes one correction replay onto both the preview canvas and the full-resolution frame the server segments; and undo is popping the last stroke, which a flattened bitmap can't offer |
| Coordinates | Normalized 0–1 against the image. `radius` is a fraction of image **width**, scaled by width on *both* axes | Keeps the brush circular in pixel space on a non-square frame. The browser draws by the identical rule (`lineWidth = 2 × radius × canvasWidth`, round caps/joins), so the preview and the applied correction are the same shape |
| Stroke compositing | In order, **last stroke wins per pixel** | Erasing back over an earlier add undoes it exactly — the behaviour anyone expects from a brush |
| Bad payload | **HTTP 400**, not a graceful drop | Unlike `reference_image` on the colour endpoint. Correcting a mask is a deliberate override; silently dropping it would show the operator an uncorrected plan that looks like the brush did nothing |

**Semantics.** `add` = "this is paintable wall": unioned into the wall mask, *and* subtracted from any non-paintable detection it covers — claiming a region as paintable has to drop an obstacle's claim on it, or the toolpath would keep routing around what the operator just said to paint. `erase` = "this is not paintable": subtracted from the wall masks, and the part that actually overlapped wall is re-emitted as a synthetic non-paintable region.

> [!important] Why an erase becomes an obstacle rather than only a hole
> A detection carries a **single-ring polygon**. An erase in the *middle* of a wall region would vanish the moment the mask was reduced back to its outer contour — the planner would paint straight over it. Emitting the erased area as a non-paintable region instead routes the raster fill around it through the same subtraction that already handles windows and trim. The binary mask stays hole-accurate for the overlay renderer either way. This is the single most load-bearing detail in the feature and the one a re-implementation would most easily get wrong.

> [!warning] Corrections never touch the reported confidence
> Manual regions carry `confidence: null` and are excluded from `wall_confidence` / `top_confidence`. A hand-drawn region is not a detection, and a fabricated score would make every confidence figure in the paper a mixture of model output and operator opinion — the same class of error as the `non-paintable` substring collision above. `wall_coverage` is the opposite case: it describes the mask that will actually be painted, so corrections *are* counted in it, and the response's `mask_correction` block says by how much. Detections also gain `source` (`"model"` / `"manual"`) so the two can always be told apart.
>
> **For Chapter 4:** mAP/IoU figures must be measured with the brush unused. The correction is an operating aid, not part of the model's score.

**Brush UX (was open, chosen here):** add/erase toggle · size slider as a % of image width, shown as a pixel diameter · undo (also <kbd>Ctrl</kbd>+<kbd>Z</kbd>) · clear · <kbd>Esc</kbd> to close · pointer events, so it works with a trackpad or a touchscreen. The editor is a shared modal — one element for both views, matching the one-mask-per-image state model — and it shows the frame **uncropped**, because the panel it replaces uses `object-fit: cover` and a click there would not map onto a known image pixel.

The preview shows the **corrected mask**, composited the same way the backend composites it, not the model's mask with the strokes scribbled over it. A stroke that changes nothing (adding over wall the model already found, erasing over bare background) correctly shows nothing — so nobody leaves the editor believing a stroke took effect when it didn't.

**Known limitations:**
- The store holds **one correction at a time**. Correcting image A, then loading image B, then returning to A means A's strokes are gone. That follows directly from the decided "one corrected mask per session/image" model and was not worth a multi-image cache for a demo.
- A correction can nudge the planned area **slightly in regions no stroke touched**. Correcting a detection re-derives its polygons from the binary mask, one per connected blob, whereas the uncorrected path takes the single ring Ultralytics exports in `masks.xy`. A model mask that was already two disjoint blobs therefore yields two polygons in the corrected run and one in the uncorrected run. Seen on `test_result_1.jpg`: a wall sliver below the door that the single-polygon export drops. The respawned decomposition is the *more* faithful one — it is the same mask the overlay renders — so it is left as-is; the weaker path is the uncorrected single-polygon export, and changing that would move baseline figures already recorded in [[🔌 Backend API & Web Integration]] and [[📐 Path Planning & G-code Generation]]. **Worth a sentence in Chapter 4 if corrected and uncorrected areas are ever compared directly.**

**Test:** `python backend/tools/test_mask_correction.py` runs one image through both paths and asserts the invariants — confidence unmoved, add-only never removes, erase-only never adds, last-stroke-wins, and an erase mid-wall actually reducing the planned paintable area. All pass on `test_result_1.jpg` (37 → 41 rows, 87 → 105 moves with a two-stroke correction).

**Code:** `backend/mask_correction.py`, wired in `backend/app.py`; editor in `website/camera-view.html`. API contract in [[🔌 Backend API & Web Integration]] § Manual mask correction.

---

### ✨ Smart Select — click a region instead of brushing it (2026-08-16)

> [!success] Built — the demo-facing half of the correction tool
> Kurt's read: the brush works but isn't a *wow factor* on stage. Smart select is the answer — **click a point and the region under it is selected**. It is an input method for the same correction, not a separate feature: the brush still exists for everything smart select grabs wrongly, which is the entire reason a human-in-the-loop correction exists at all.

**Engine: MobileSAM** (Zhang et al. 2023), a distilled **Segment Anything** (Kirillov et al. 2023). The decisive fact that made this cheap: **the ultralytics version AURA already pins ships the SAM predictors**, so this is a **38 MB weights download and no new Python dependency**. Weights live at `website/model/mobile_sam.pt` next to `best.pt`.

**Fallback: a colour wand** — flood fill in CIE Lab (the same working space as [[🎨 Color Recommendation Module]]). No weights, no GPU, ~6 ms, works offline forever. It exists so a missing or failed MobileSAM never leaves a dead button on stage — the same graceful-degradation contract `model_loader` gives `best.pt`. The editor **labels which engine is live**, so the tool never promises a foundation model and delivers a flood fill.

**Measured on the RTX 3050 (640×640 frame):**

| | MobileSAM | Colour wand |
|---|---|---|
| Click on the wall | 61.5% of frame selected | 36.9% at tolerance 18 |
| Click on the door | **12.6% — just the door** | 9.7% |
| Cold (first click, loads weights) | ~1.5 s | — |
| Warm click | ~120–300 ms | ~6 ms |
| VRAM reserved alongside YOLOv8n-seg | ~2.3 GB of 4 GB | 0 |

> [!tip] The number to quote at the defense
> Clicking the wall with MobileSAM and clicking the wall with the trained YOLOv8 agree to within **0.11%** — of the 251,377 px MobileSAM selected, only 265 px fell outside the fine-tuned model's own wall mask. Two independently-trained models converging on the same boundary is a *stronger* statement about the segmentation than either alone, and it is asserted as a test invariant, not a one-off observation.

**Refinement.** Shift+click grows the last selection, right-click carves part of it away (SAM negative points). Verified: wall alone 0.615 → +door 0.743 → −door 0.656.

> [!danger] The bug that would have shipped silently
> Ultralytics reads `points=[p1, p2]` as **two separate objects** and answers with two masks, while `points=[[p1, p2]]` reads them as two prompts for **one** object. The flat form is the shape that looks correct — and it made every refinement click return a second mask that got dropped, so shift+click appeared to do *nothing at all* with no error anywhere. Fixed by nesting; the reason is commented at the call site because nothing about the API surface warns you.

**Storage: the prompt, not the outline.** A smart selection is saved as `{kind:"smart", points, labels, engine, tolerance}` — the click, never the region it produced. That keeps a correction ~1 KB and resolution-independent, which is the same property the brush relies on and the reason the Upload → Toolpath carry-over works at all. The cost is that every re-plan re-resolves every selection, so results are **memoised** by (frame, engine, prompt): **1473 ms cold vs 121 ms warm** on the same corrected toolpath, byte-identical G-code both times.

> [!warning] A saved selection never silently changes engine
> The op records the engine that *actually ran*, not `auto`. If a replay hits a server without those weights, it answers **400 "re-run the smart selection"** rather than resolving the same click with a different engine. Geometry the operator never saw becoming G-code is exactly the failure this feature exists to prevent — same reasoning as the malformed-payload 400.

**Payload version bumped to 2** (`ops` with a `kind` discriminator). Version 1 (`strokes`, brush only) is still parsed, so a browser tab left open across a server restart loses smart select rather than the whole correction.

**Config:** `AURA_SAM_MODEL`, `AURA_SAM_IMGSZ` (1024 → 512 if VRAM is tight), `AURA_SAM_DEVICE=cpu`, `AURA_SMART_SELECT=0`. A CUDA OOM is caught, the cache dropped, and the request degrades to the wand.

> [!todo] Before defense day
> - **Get `mobile_sam.pt` onto the demo machine.** Without it, smart select silently becomes a flood fill. It is git-ignored like `best.pt`, so it does not travel with a clone.
> - **RRL is worth updating** — SAM/MobileSAM is a citable foundation-model line that strengthens Theme 3 alongside the YOLOv8 argument, and "promptable segmentation as human-in-the-loop correction" is a defensible framing. Not written yet: see [[📚 Literature Review Master]].

**Code:** `backend/smart_select.py`, endpoint `POST /api/smart-select` in `backend/app.py`.
