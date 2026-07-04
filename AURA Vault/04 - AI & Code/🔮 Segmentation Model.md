---
tags: [ai, segmentation, deep-learning]
created: 2026-03-29
status: active
---
# 🔮 Segmentation Model

> [!info] Related
> [[🧠 AI & Software Design]] · [[📐 Path Planning & G-code Generation]] · [[Bjekic 2023 - Wall Segmentation CNN]] · Code: [[segmentation_inference.py]]

## Problem Definition
Given a wall image from the fixed camera, output a **per-pixel mask** identifying **paintable regions**. Binary (paintable / not) for the prototype; optionally multi-class per design zone later.

## Dataset Options
| Option | Pros | Cons |
|---|---|---|
| **ADE20K** (has `wall` class) | Large, labeled, free | General scenes, not painting-specific |
| **Custom annotated** (LabelMe/CVAT) | Matches real test walls | Time cost (R-13) |
| **Bjekic-style** wall set | Directly on-task | Availability |
**Plan:** pretrain/transfer on ADE20K, fine-tune on a **small custom binary set** of the actual test walls.

## Chosen Architecture — MobileNetV3 + DeepLabV3+
> [!note] Why
> Real-time-capable on RTX 3050, fits **< 4GB VRAM**, good mIoU on scene segmentation. MobileNetV3's depthwise-separable convolutions keep the model small; DeepLabV3+'s ASPP head captures multi-scale context (useful for large flat wall regions).

**Alternative considered — U-Net:** simpler, excellent for **binary masks**; the fallback if ADE20K multi-class training proves unstable on 4GB.

## Training Procedure
1. Load MobileNetV3 backbone **pretrained on ImageNet**.
2. Attach DeepLabV3+ head; freeze backbone initially, train head.
3. Unfreeze and **fine-tune** on custom wall images.
4. Use **AMP (mixed precision)**, batch size 4, augmentation (flip, jitter, rotate).

## I/O Spec
- **Input size:** 512×512 (fallback 384×384).
- **Output:** per-pixel class mask (same resolution, resized back to source).

## Post-Processing
```
mask -> morphological clean (open/close) -> contour extraction ->
        coordinate grid -> path_planner input
```

## Evaluation
- **mean IoU (mIoU)**, **pixel accuracy**, **boundary precision**.
- **VRAM math:** batch 4 @ 512×512 with MobileNetV3-DeepLab ≈ **~2.5 GB** → safe on 4GB.

## Realistic Prototype Targets
| Metric | Target |
|---|---|
| Pixel accuracy | **> 75%** |
| mIoU | **> 0.65** |

> [!tip] "Good enough" for the thesis
> The mask only needs to be accurate enough that the **raster planner** fills the right area. Small boundary errors are absorbed by spray overlap. Perfect segmentation is not required — reliable region identification is.
