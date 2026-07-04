---
tags: [reference, ai-vision]
authors: Bjekic et al.
year: 2023
doi: n/a
---
# Wall Segmentation from 2D Images using CNNs
## Citation
Bjekic, M., et al. (2023). *CNN-based wall segmentation from 2D images.* (As cited in AURA concept paper, 2026.)
## Core Argument
Convolutional neural networks can accurately segment wall regions from ordinary single 2D images, without depth sensors or 3D reconstruction. This makes wall perception feasible on commodity cameras.
## Methodology
Trained a CNN segmentation model on annotated indoor images to produce per-pixel wall masks; evaluated with standard segmentation metrics (IoU / pixel accuracy).
## Key Findings
- Single-image 2D input is sufficient for reliable wall segmentation.
- CNN architectures generalize across varied indoor scenes.
- No specialized depth hardware required.
## Limitations
- Segmentation only — no downstream actuation or painting.
- Indoor scene focus; performance on textured/outdoor walls less characterized.
- Model size/latency not optimized for low-VRAM edge deployment.
## Relevance to AURA
This is AURA's core perception primitive: it proves the exact capability AURA needs — turning a wall photo into a paintable-region mask on a plain camera.
## AURA Builds On This By
Adopting 2D wall segmentation but making it **actionable** — feeding the mask into a raster path planner that drives a physical gantry, and choosing a *lightweight* backbone (MobileNetV3) to fit the RTX 3050's 4GB VRAM. See [[🔮 Segmentation Model]].
