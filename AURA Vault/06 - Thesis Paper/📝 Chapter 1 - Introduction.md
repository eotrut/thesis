---
tags: [thesis, chapter-1, introduction]
created: 2026-03-29
updated: 2026-07-12
status: synced-with-manuscript
---
# 📝 Chapter 1 — Introduction

> [!info] Sync note
> This note now mirrors the finalized manuscript (`aura_thesis_rewrite.md`). The manuscript's Introduction is a much longer, fully-cited prose treatment (~3,900 words, RRL 2021–2026) — this note captures the same claims and structure at synthesis length for quick reference and editing. See [[📚 Literature Review Master]] for the full thematic breakdown.

## Background of the Study
Manual wall painting is labor-intensive, hazardous, and inconsistent: painters face elevated risk of respiratory impairment and asthma from VOC exposure (Sekhar et al., 2024; Arrandale et al., 2025; Boadu et al., 2023; Patel et al., 2024; Bello et al., 2020), plus fall risk and musculoskeletal strain from working at height (NIOSH, 2024). In the Philippines, DOLE Department Order No. 13 s.1998 and RA 11058 codify the resulting safety obligations. Prior automated wall-painting robots (Kumote et al., 2022; Patil, 2021; Megalingam et al., 2020; Sowmya et al., 2024; Thale et al., 2022; Shamseldin, 2024; Zhou et al., 2022; Al-Ayoub et al., 2024) demonstrate that the physical task can be automated, but they operate on **pre-programmed, fixed motion** — they do not perceive the wall or reason about the design. Parallel advances in deep-learning perception (Bjekic et al., 2023; YOLOv8/Ultralytics; He et al., 2017 Mask R-CNN lineage) and AI color recommendation (Yuan et al., 2021; Wu et al., 2023) have matured in isolation, rarely closing the loop into a physical actuator.

**AURA (AI-Based Autonomous Wall Painting Robot)** unifies deep-learning spatial segmentation (YOLOv8), OpenCV-based homography calibration, raster toolpath generation, pyserial-mediated Arduino adaptive spray control, and AI-based color recommendation into a single undergraduate-scale prototype: a 2D vertical gantry (2040 aluminum extrusion, dual-X + single-Y NEMA 23 motors, TB6600 drivers, Arduino Mega + RAMPS 1.4), a USB/HD camera, and a solenoid-actuated spray subsystem. Full RRL synthesis: [[📚 Literature Review Master]].

## Statement of the Problem
Wall painting remains manual, labor-intensive, and hazardous. Existing automated systems use predetermined paths and cannot adapt to wall conditions; existing robotic/AI/vision systems are typically developed in isolation rather than as one integrated pipeline. This study develops an AI-based autonomous wall-painting system to close that gap.

Research questions:
1. How can a 2D vertical gantry (NEMA 23 + TB6600 + Arduino Mega/RAMPS 1.4) achieve accurate, repeatable motion across a flat wall?
2. How can YOLOv8 instance segmentation (zero-shot-first, fine-tuned only if necessary) identify and map paintable regions from camera images?
3. How can OpenCV-based homography calibration, seeded from physical corner markers, convert pixel-space masks into real-world millimeter coordinates?
4. How can a raster toolpath generator produce spray trajectories transmitted as G-code-style commands (pyserial → Arduino Mega), and how reliably does the microcontroller execute them?
5. How can an AI-based color recommendation module generate suitable, visually coherent color combinations?
6. How effective is the system in terms of painting accuracy, segmentation accuracy, spray consistency, coverage uniformity, and alignment with the intended design in color and coverage?

> [!warning] Scope correction (2026-07)
> An earlier draft of RQ6 included "color reproduction accuracy" (recommended vs. applied paint color). **Removed** — AURA sprays pre-loaded paint and does not mix/synthesize color, so there is no mechanism to verify the applied color matches the recommendation. See Scope and Delimitation below.

## Scope and Delimitation
AURA covers: a 2D XY gantry (2040 extrusion, GT2 belts, linear rails, 3× NEMA 23, TB6600); YOLOv8 (Ultralytics/PyTorch/CUDA) instance segmentation on an RTX 3050 laptop; USB/HD camera vision + OpenCV homography/scaling calibration; adaptive spray control (pump, solenoid, nozzle) via Arduino; an AI-based color recommendation module; Arduino Mega + RAMPS 1.4 + 24V DC, driven from Python via pyserial with G-code-style commands. Evaluation covers motion accuracy, segmentation accuracy, spray consistency, painting output quality, and color recommendation quality (visual coherence/suitability).

Limited to: flat wall surfaces; 2D movement only; simple mural designs in controlled environments; prototype-level implementation; zero-shot-first YOLOv8 evaluation strategy (fine-tune on Roboflow/Kaggle T4 only if needed).

Does **not** include: 3D/curved surfaces; fully autonomous navigation beyond the working frame; commercial/industrial scale; real-time continual learning; **verification that the painted output's color matches the AI-recommended color** — the system applies pre-loaded paint and performs no paint mixing or color synthesis, so color reproduction accuracy (CIE ΔE\*) is explicitly out of scope. Only color *recommendation* quality (the coherence/suitability of the suggested palette itself) is evaluated.

## Objectives
**General Objective.** Develop an AI-based autonomous wall-painting system combining deep learning, robotics, color recommendation, and adaptive spray control to improve accuracy and efficiency.

**Specific Objectives.**
1. Design/develop a 2D XY-gantry robotic system (2040 extrusion, GT2 belts, rails, 3× NEMA 23, TB6600, Arduino Mega + RAMPS 1.4, 24V DC) for precise motion.
2. Develop YOLOv8 (Ultralytics) instance segmentation on an RTX 3050 (CUDA) for paintable-region identification — zero-shot first, fine-tuned via Roboflow/Kaggle T4 only if needed.
3. Implement OpenCV-based homography/scaling calibration (physical corner markers) mapping pixel masks to millimeter coordinates, and generate raster toolpaths in Python.
4. Implement adaptive spray control (Arduino-actuated pump/solenoid/nozzle) driven by pyserial G-code-style commands.
5. Integrate vision, motion control, color recommendation, and spray into one unified system.
6. Develop an AI-based color recommendation module for visually coherent color combinations.
7. Evaluate motion accuracy, segmentation accuracy, spray consistency, coverage uniformity, design-to-output alignment, and color recommendation quality.
8. Assess capability on simple mural/multi-region painting tasks.

## Rationale / Significance
Automation addresses safety (DOLE DO-13 s.1998, RA 11058), efficiency, and quality gaps in manual painting. AURA's core innovation is the **unified pipeline** from perception to physical application — no cited prior system connects deep-learning segmentation, calibrated coordinate mapping, and adaptive spray on one reproducible undergraduate-scale prototype (see [[🔍 Research Gaps & Justification]]). Framed via the Triple Bottom Line (worker safety, operational efficiency, material-waste reduction) and aligned to SDG 8, 9, 11, and 12.

## Hypothesis
> [!note] Hypotheses (updated — "color reproduction" replaced by "color performance")
> **H₀:** The system does not show significant improvement in painting accuracy, spray consistency, coverage, and color performance compared to manual/non-adaptive approaches.
> **H₁:** The system significantly improves painting accuracy, spray consistency, coverage, and color performance through YOLOv8 segmentation, OpenCV homography calibration, raster toolpath generation, pyserial-mediated adaptive spray control, and AI color recommendation.

*See also [[📚 Literature Review Master]], [[🔍 Research Gaps & Justification]], and [[🏗️ System Architecture Overview]].*
