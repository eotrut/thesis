---
tags: [system-design, ai, software]
created: 2026-03-29
status: active
---
# 🧠 AI & Software Design

> [!info] Related
> [[🔮 Segmentation Model]] · [[🎨 Color Recommendation Module]] · [[📐 Path Planning & G-code Generation]] · [[🖥️ Serial Communication Protocol]] · Code in `04 - AI & Code/Code Snippets/`

## Python Pipeline (`main.py` flow)
```
main.py
  1. camera.capture_frame()        -> raw image
  2. preprocess(image)             -> 512x512 tensor
  3. segmentation.infer(tensor)    -> region mask
  4. color_rec.recommend(image)    -> palette + region->color map
  5. path_planner.plan(mask, mm)   -> coordinate list -> G-code
  6. serial_ctrl.stream(gcode)     -> Arduino executes (move + spray)
  7. evaluate.capture_and_score()  -> metrics
```

## Modules
### Module 1 — Image Capture (`camera.py`)
OpenCV `VideoCapture` grabs a frame from the USB camera; crops/resizes to model input; normalizes to ImageNet mean/std. Handles a fixed, calibrated camera pose so pixel→mm mapping stays valid.

### Module 2 — Segmentation (`segmentation.py`)
Loads the trained model (MobileNetV3 + DeepLabV3+), runs inference, `argmax` over channels → class mask, resizes mask back to source resolution. Details in [[🔮 Segmentation Model]].

### Module 3 — Path Planner (`path_planner.py`)
Converts each region mask to a raster (boustrophedon) coordinate list, maps pixels→mm via calibration factor, emits G-code with spray M3/M5 toggles. Details in [[📐 Path Planning & G-code Generation]].

### Module 4 — Color Recommendation (`color_rec.py`)
K-means on the reference image → dominant colors → apply harmony rules (complementary/analogous/triadic) → palette + region assignments. Details in [[🎨 Color Recommendation Module]].

### Module 5 — Serial Controller (`serial_ctrl.py`)
`pyserial` command queue: send one G-code line, block for `ok`, timeout/retry on failure. Details in [[🖥️ Serial Communication Protocol]].

## Module Architecture Diagram (ASCII)
```
 camera.py ──> segmentation.py ──> path_planner.py ──> serial_ctrl.py ──> [Arduino]
      │                                   ^
      └──────────> color_rec.py ──────────┘  (palette + region->color)
                        │
                   evaluate.py  (metrics, offline)
```

## Model Choice Rationale
> [!note] Why MobileNetV3 + DeepLabV3+ (not ResNet/heavy nets)
> The RTX 3050 laptop has **4GB VRAM**. A full ResNet-101 DeepLab would not train comfortably. **MobileNetV3** is a mobile-optimized backbone; paired with a **DeepLabV3+** head it gives strong segmentation at a fraction of the memory, and runs near-real-time. **U-Net** is the fallback if ADE20K multi-class proves too hard — it excels at simple binary masks.

## Dataset Strategy
- **Primary:** ADE20K (contains a `wall` class) for pretraining/transfer.
- **Custom:** a small set of local wall photos annotated with **LabelMe** or **CVAT** (binary paintable / not-paintable) to fine-tune.
- **Augmentation:** flips, brightness/contrast jitter, slight rotation — critical given limited data (Risk R-04, R-13).

## Training Environment (RTX 3050, 4GB)
| Constraint | Setting |
|---|---|
| Input size | 512×512 (fallback 384×384) |
| Batch size | 4 (use gradient accumulation if needed) |
| Precision | Mixed precision (AMP) to save VRAM |
| Backbone | MobileNetV3, ImageNet-pretrained |
| Est. VRAM | ~2.5 GB at batch 4 — safe headroom |

## Evaluation Metrics (in code)
- **mean IoU (mIoU)** — primary segmentation metric.
- **Pixel accuracy** — secondary.
- Targets: **>0.65 mIoU**, **>75% pixel accuracy** on test set (prototype-adequate).

## Color Recommendation Approach
K-means on the input image → top-N dominant colors → apply **color harmony rules** (complementary, analogous, triadic, split-complementary) → output palette (hex + RGB) with **region→color assignments**. Qualitative evaluation by **≥5 human raters** (1–5 scale). See [[🎨 Color Recommendation Module]].
