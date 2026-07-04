---
tags: [reference, ai-vision, spray]
authors: Liu & Cheng
year: 2024
doi: n/a
---
# Semantic Segmentation + Trajectory Optimization for Spray Robots
## Citation
Liu, X., & Cheng, Y. (2024). *Semantic segmentation and trajectory optimization for robotic spray painting.* (As cited in AURA concept paper, 2026.)
## Core Argument
Coupling semantic segmentation with trajectory optimization lets spray robots target specific regions and optimize coverage, improving efficiency and finish quality.
## Methodology
Segments the workpiece semantically, then runs an optimization stage to generate efficient, low-overlap spray paths for the identified regions.
## Key Findings
- Segmentation-guided targeting reduces wasted paint and overspray.
- Trajectory optimization improves coverage uniformity.
- Region-aware planning outperforms naive full-surface passes.
## Limitations
- Industrial spray-robot context; heavy compute assumed.
- Optimization complexity beyond a prototype's needs.
- No color-selection dimension.
## Relevance to AURA
Validates AURA's pipeline shape — *segment first, then plan paths for the segmented regions* — and the value of overlap control for uniform coverage.
## AURA Builds On This By
Using a **simpler, reliable raster (boustrophedon) planner with 10–20% overlap** instead of full optimization, appropriate for flat walls and prototype reliability, while retaining segmentation-guided targeting. See [[📐 Path Planning & G-code Generation]].
