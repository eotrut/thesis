---
tags: [reference, ai-vision, spray]
authors: Tiboni et al.
year: 2022
doi: n/a
---
# PaintNet: Deep Learning of Spray Trajectories from 3D Point Clouds
## Citation
Tiboni, G., et al. (2022). *PaintNet: Unstructured multi-path learning from 3D point clouds for robotic spray painting.* (As cited in AURA concept paper, 2026.)
## Core Argument
Spray-painting trajectories can be learned directly from 3D geometry using deep networks, generating multi-path coverage plans for complex surfaces.
## Methodology
Deep model trained on 3D point clouds of objects paired with expert spray trajectories; predicts unstructured multi-path spray plans.
## Key Findings
- Learned trajectories generalize to unseen object geometries.
- Handles complex, non-planar surfaces.
- Removes manual trajectory programming.
## Limitations
- Requires 3D point-cloud input (depth scanners / industrial capture).
- Assumes industrial robot arms and compute.
- Not aimed at flat-wall, low-cost prototypes.
## Relevance to AURA
Demonstrates the "learn where/how to spray" vision AURA shares, and marks the *hardware ceiling* AURA deliberately avoids.
## AURA Builds On This By
Replacing 3D point-cloud learning with **2D segmentation + deterministic raster planning** ([[📐 Path Planning & G-code Generation]]), achieving the same perceive-then-spray goal on flat walls at a fraction of the cost.
