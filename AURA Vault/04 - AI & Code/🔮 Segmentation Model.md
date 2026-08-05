---
tags: [ai, segmentation, deep-learning]
created: 2026-03-29
updated: 2026-07-30
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
