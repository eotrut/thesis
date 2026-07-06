---
tags: [ai, pipeline, training, yolov8, session-notes]
date: 2026-07-06
---

# AI Pipeline & Training Strategy — Session Notes

## Summary

- Full pipeline confirmed with advisor: **Camera → AI Segmentation → Coordinate Mapping → Path Generation → Serial Commands → Arduino → Motors**.
- Training approach confirmed: use **transfer learning** on pre-trained **YOLOv8 segmentation**, not training from scratch. Laptop RTX 3050 is for deployment/dev only; fine-tuning happens on Kaggle's free Tesla T4.
- First step before any fine-tuning: test YOLOv8's out-of-the-box COCO weights on real wall photos.

---

## AI-to-Motor Pipeline (Confirmed with Advisor)

**Pipeline:** Camera → AI Segmentation → Coordinate Mapping → Path Generation → Serial Commands → Arduino → Motors

- **Camera**: Mounted on a tripod, captures the wall.
- **AI Segmentation**: Model outputs a pixel mask identifying paintable vs. non-paintable regions.
- **Coordinate Mapping**: A calibration step using physical corner markers converts pixel coordinates to physical mm coordinates (via homography or a basic scaling ratio).
- **Path Generation**: Python generates a raster toolpath from the mapped coordinates.
- **Serial Commands**: Commands are sent automatically via `pyserial` over USB — no manual coordinate entry required.
- **Arduino → Motors**: Arduino receives the serial commands and drives the motors accordingly.

---

## Training Strategy (Confirmed)

- **Hardware role**: RTX 3050 laptop (4GB VRAM) is a **deployment and development machine**, not a training machine.
- **Approach**: Use **transfer learning**, not training from scratch.
- **Dataset prep**: **Roboflow** handles dataset preparation and labeling.
- **Fine-tuning compute**: **Kaggle** provides a free **Tesla T4 GPU** (16GB VRAM, 30 hrs/week) for fine-tuning.
- **Model choice**: **YOLOv8 segmentation** (Ultralytics) — pre-trained on **COCO**, which already recognizes walls, doors, and windows.
- **Step 1**: Test YOLOv8 with **zero fine-tuning** on actual wall photos first.
- **Step 2**: Only fine-tune if zero-shot results are insufficient.
- **Deployment**: The trained `.pt` model file is downloaded to the laptop and runs **inference locally** during operation.

---

## Key Takeaways

- No manual coordinate entry anywhere in the pipeline — calibration and toolpath generation are automated.
- Compute-heavy training is offloaded to free cloud GPU (Kaggle T4); local hardware only needs to handle inference.
- Validate the pre-trained model's zero-shot performance before investing time in fine-tuning.
