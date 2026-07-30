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
| Roboflow-labeled custom set | Matches real wall scenarios | Time cost (annotation effort) |
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

### 2026-07-30 — First Custom Fine-Tune Run Complete

**Annotation approach tried:**
1. **Object Detection (bounding boxes)** — attempted first. Result: model only drew bounding boxes around the wall and objects; no pixel-level masks produced. **Not suitable for AURA's needs.** Abandoned.
2. **Instance Segmentation (polygon masks)** — switched annotation type in Roboflow. Result: model now correctly masks the wall region and other objects at the pixel level. **Confirmed correct approach going forward.**

> [!success] Key finding
> Instance segmentation is confirmed as the correct annotation type for AURA. Object detection was ruled out — it cannot produce the pixel masks that the coordinate-mapping and path-planning stages require.

**Dataset status as of 2026-07-30:**
| Metric | Value |
|---|---|
| Total annotated images | ~150 |
| Split | Train / Validation / Test |
| Annotation tool | Roboflow (instance segmentation polygons) |
| Training compute | Kaggle Tesla T4 GPU |
| Model | YOLOv8 instance segmentation |
| Target dataset size | ~1,000 images (by end of thesis) |

**What was validated:** Train → Validate → Test pipeline on Kaggle with the current ~150-image set is working end-to-end. Results screenshots captured (attach to Chapter 4 evidence folder when ready).

**Next steps:**
- Continue expanding dataset toward ~1,000 images
- Re-run fine-tune and re-evaluate metrics as dataset grows
- Document mAP/IoU numbers per training run for Chapter 4 — Results
