---
tags: [thesis, chapter-1, introduction]
created: 2026-03-29
updated: 2026-08-05
status: synced-with-manuscript
---
# 📝 Chapter 1 — Introduction

> [!info] Sync note (2026-07-18)
> Re-synced against the **live concept-paper Google Doc** (not the local `aura_thesis_rewrite.md` manuscript) after a full review/fix cycle — see [[📝 Writing Notes & Advisor Feedback]] for the session log and score. Note: when this file was last staged from the device, it still showed a much older, stale version (wrong acronym, K-means/MobileNetV3 references, old RQ/objective wording) — either an Obsidian-git sync pulled back an older revision, or the 2026-07-12 commit didn't fully land. This rewrite reflects the actual current state of the paper; if you notice this note reverting again, flag it so the sync process can be checked.

> [!info] Sync note (2026-08-04)
> RQ4, Specific Objective 4, and the Rationale paragraph corrected: the toolpath generator emits G-code-style commands **internally**, but there is no RAMPS shield and no G-code-parsing firmware on the Arduino, so those commands are translated into a custom serial protocol (`MOVE`, `SPRAY ON/OFF`, `HOME`) before transmission — matching [[📝 Chapter 3 - Methodology]] §3.6 step 7-8 and the three `.drawio` architecture diagrams (relabeled the same day).

> [!warning] Acronym correction (2026-08-05)
> "AURA (AI-Based Autonomous Wall Painting Robot)" was never a real acronym — the initials of "AI-Based Autonomous Wall Painting Robot" spell A-B-A-W-P-R, not AURA. Kurt caught this. The project's original expansion, "Autonomous Unified Robotic Artist," did correctly spell A-U-R-A, but got dropped somewhere during the architecture pivot without anyone checking the replacement still worked letter-for-letter. Corrected to **AURA (Autonomous Unified Robotic Adaptive)** — verified A-U-R-A — with "AI-Based Autonomous Wall Painting Robot" kept as a descriptive subtitle, not the acronym expansion. **This same fix still needs to be pasted into the live Google Doc concept paper by hand — there's no Drive edit tool available to do it automatically.**

> [!warning] Concept-paper review (2026-08-05)
> Read the submitted concept-paper PDF end to end. Findings:
> 1. **Acronym fix only half-applied.** Title page and RQ/Objectives already read "AURA (Autonomous Unified Robotic Adaptive)" — but the running header on every page, plus the Abstract's opening sentence, still expand AURA as "AI-Based Autonomous Wall Painting Robot" (wrong letters, doesn't spell AURA). Still not pasted into the live Google Doc — see decision #15.
> 2. **G-code vs. custom-protocol framing bug found in 6 more text locations plus 3 diagram labels**, beyond the RQ4/Objective 4/Rationale instance already logged 2026-08-04. Confirmed still broken: Abstract (two separate sentences, p.2), Introduction pipeline-summary paragraph (p.15), Scope bullet (p.19), and the Rationale paragraph (p.22) — all say commands are "transmitted...as G-code" instead of "translated into the custom protocol, then transmitted." Plus 3 diagram/flowchart labels baked into images (not text-searchable): General Block Diagram (p.25), System Block Diagram (p.26 — Control Board box literally says "Parses G-code," the most visible instance), and the Flowchart (p.27 — step labels plus "wait for 'ok'", which is GRBL/Marlin's ack string, not this project's). These live in the `.drawio` source files.
> 3. Confirmed already correct, no changes needed: Specific Objective 4 (p.20), Procedure Steps 5, 7, and 8 (pp.32–33) — these already model the right "internal G-code-style representation → translated → transmitted" framing.
> Full find/replace text for all 9 fixes logged in [[📝 Writing Notes & Advisor Feedback]].

## Title
**AURA (Autonomous Unified Robotic Adaptive): AI-Based Autonomous Wall Painting Robot Integrating Deep Learning Segmentation, Color Recommendation, and Adaptive Spray Control**

## Background of the Study
Manual wall painting is labor-intensive, hazardous, and inconsistent: painters face elevated risk of respiratory impairment and asthma from VOC exposure (Sekhar et al., 2024; Arrandale et al., 2025; Boadu et al., 2023; Patel et al., 2024; Bello et al., 2020), plus fall risk and musculoskeletal strain from working at height (NIOSH, 2024). In the Philippines, DOLE Department Order No. 13 s.1998 and RA 11058 codify the resulting safety obligations. Prior automated wall-painting robots (**Kumtole** et al., 2022; Patil, 2021; Megalingam et al., 2020; Vijaya Kumar et al., 2025; Thale et al., 2022; Shamseldin, 2024; Zhou et al., 2022; Al-Ayoub et al., 2024) demonstrate that the physical task can be automated, but they operate on **pre-programmed, fixed motion** — they do not perceive the wall or reason about the design. Parallel advances in deep-learning perception — Mask R-CNN (He et al., 2017), UNet++ (Zhou et al., 2019), wall segmentation (Bjekic et al., 2023), YOLOv8/Ultralytics (Jocher et al., 2023) — and AI color recommendation (Yuan et al., 2021; Wu et al., 2023) have matured largely in isolation, rarely closing the loop into a physical actuator.

**AURA (Autonomous Unified Robotic Adaptive)** — an AI-based autonomous wall-painting robot — unifies deep-learning spatial segmentation (YOLOv8), OpenCV-based homography calibration, raster toolpath generation, pyserial-mediated Arduino adaptive spray control, and AI-based color recommendation into a single undergraduate-scale prototype: a 2D vertical gantry (2040 aluminum extrusion, dual-X + single-Y NEMA 23 motors, TB6600 drivers, Arduino Mega 2560), a USB/HD camera, and a solenoid-actuated spray subsystem. Full RRL synthesis: [[📚 Literature Review Master]].

## Statement of the Problem
Wall painting remains manual, labor-intensive, and hazardous. Existing automated systems use predetermined paths and cannot adapt to wall conditions; existing robotic/AI/vision systems are typically developed in isolation rather than as one integrated pipeline. This study develops an AI-based autonomous wall-painting system to close that gap.

Research questions:
1. How can a two-dimensional vertical gantry driven by NEMA 23 stepper motors, TB6600 drivers, and an Arduino Mega 2560 be designed to achieve accurate and repeatable motion across a flat wall surface?
2. How can YOLOv8 instance segmentation, evaluated first in zero-shot mode against public datasets and subsequently fine-tuned when necessary, be used to identify and map paintable regions on wall images captured by a USB high-definition camera?
3. How can OpenCV-based homography calibration, seeded from physical corner markers on the wall, be used to convert segmentation masks in pixel coordinates into real-world millimeter positions on the wall surface?
4. How can a raster toolpath generator, driven by the segmentation output, produce spray trajectories that are translated into a custom command protocol (MOVE, SPRAY ON/OFF, HOME) and transmitted from Python to the Arduino Mega over pyserial, and how reliably can the microcontroller execute those commands to drive the stepper motors and the solenoid-controlled spray subsystem?
5. How can an AI-based color recommendation system be developed to generate suitable and visually coherent color combinations for wall painting, and how effectively can those recommendations be reproduced on the physical wall?
6. How effective is the developed system in terms of: painting accuracy, spray consistency, coverage uniformity, segmentation accuracy, and alignment with the intended design in terms of color and coverage?

> [!warning] Scope correction (carried from 2026-07 sync)
> An earlier draft of RQ6 included "color reproduction accuracy" (recommended vs. applied paint color). **Removed** — AURA sprays pre-loaded paint and does not mix/synthesize color, so there is no mechanism to verify the applied color matches the recommendation. See Scope and Delimitation below.

## Scope and Delimitation
**In scope:** 2D XY gantry (2040 extrusion, GT2 belts, linear rails, 3× NEMA 23, TB6600); YOLOv8 (Ultralytics/PyTorch/CUDA) instance segmentation on an RTX 3050 laptop; USB/HD camera vision + OpenCV homography/scaling calibration; adaptive spray control (pump, solenoid, nozzle) via Arduino; an AI-based color recommendation module; Arduino Mega 2560 + 24V DC, driven from Python via pyserial with a custom command set. Evaluation covers motion accuracy, segmentation accuracy, spray consistency, painting output quality, and color recommendation quality (visual coherence/suitability).

**Limited to:** flat wall surfaces; 2D movement only; simple mural designs in controlled environments; prototype-level implementation; zero-shot-first YOLOv8 evaluation strategy (fine-tune on Roboflow/Kaggle T4 only if needed).

**Does not include:** 3D/curved surfaces; fully autonomous navigation beyond the working frame; commercial/industrial scale; real-time continual learning; **verification that the painted output's color matches the AI-recommended color** — the system applies pre-loaded paint and performs no paint mixing or color synthesis, so color reproduction accuracy (CIE ΔE*) is explicitly out of scope. Only color *recommendation* quality (the coherence/suitability of the suggested palette itself) is evaluated.

## Objectives
**General Objective.** To develop an artificial intelligence-based autonomous wall painting system that combines deep learning, robotics, color recommendation, and adaptable spray control to improve the accuracy and efficiency of wall painting operations.

**Specific Objectives.**
1. Design and develop a 2D XY-gantry robotic system for precise, controlled wall-surface motion.
2. Develop a deep-learning spatial-segmentation model (YOLOv8/Ultralytics, RTX 3050 + CUDA) for identifying paintable regions, tested zero-shot first and fine-tuned on Roboflow/Kaggle T4 only if needed.
3. Implement an OpenCV-based homography/scaling calibration routine (physical corner markers) mapping segmentation-mask pixels to real-world mm positions, and generate raster toolpaths from those masks in Python.
4. Implement an adaptive spray-control system regulating paint flow, actuated by the Arduino Mega and driven by a custom command protocol (MOVE, SPRAY ON/OFF, HOME) transmitted from Python over pyserial, with toolpath data translated from its internal G-code-style representation before transmission.
5. Integrate computer vision, motion control, color recommendation, and spray mechanisms into a unified automated painting system.
6. Evaluate the system's performance in terms of motion accuracy, segmentation accuracy, spray consistency, coverage uniformity, and alignment between intended design and painted output.
7. Develop an AI-based color-recommendation module capable of generating suitable and visually coherent color combinations for wall painting.
8. Assess the system's capability in executing simple mural designs and multi-region painting tasks.

## Rationale / Significance
The core innovation of AURA is not any single subsystem but the **unified pipeline** from perception to physical paint application: a captured wall image is segmented by YOLOv8, calibrated into real-world coordinates through OpenCV homography, converted into a raster toolpath, translated into a custom command protocol and transmitted to an Arduino Mega via pyserial, and executed on a two-axis gantry with adaptive spray control. Prior wall-painting robots have automated the scanning motion (Kumtole et al., 2022; Megalingam et al., 2020; Zhou et al., 2022) and prior deep-learning work has segmented walls accurately (Bjekic et al., 2023; Lin et al., 2025; Zhang et al., 2024), but few systems connect these threads on one reproducible prototype — the gap AURA fills (see [[🔍 Research Gaps & Justification]]).

Framed through the **Triple Bottom Line**: worker safety (removing humans from hazardous tasks), operational efficiency (lower labor/material cost, less rework), and environmental benefit (reduced paint waste). Aligns with UN SDGs 9 (Industry, Innovation & Infrastructure), 11 (Sustainable Cities & Communities), 12 (Responsible Consumption & Production), and 8 (Decent Work & Economic Growth). Because the system is built entirely from off-the-shelf components and open-source software (Python, PyTorch, Ultralytics, OpenCV, pyserial, Arduino), the design is deliberately reproducible at undergraduate scale rather than positioned as a commercial product.

## Hypothesis
> [!note] Hypotheses (corrected 2026-07-18 — explicitly restored "color recommendation performance")
> **H₀:** The developed AI-based autonomous wall painting system — integrating YOLOv8-based spatial segmentation, OpenCV-based homography calibration, raster toolpath generation, pyserial-mediated Arduino adaptive spray control, and AI-based color recommendation — does not show significant improvement in painting accuracy, spray consistency, coverage, **and color recommendation performance**, compared to conventional manual approaches and non-adaptive automated approaches.
>
> **H₁:** The developed AI-based autonomous wall painting system significantly improves painting accuracy, spray consistency, coverage, **and color recommendation performance** through the incorporation of YOLOv8-based deep learning spatial segmentation, OpenCV-based homography calibration, raster toolpath generation, pyserial-mediated Arduino-driven adaptive spray control, and AI-based color recommendation.

*See also [[📚 Literature Review Master]], [[🔍 Research Gaps & Justification]], and [[🏗️ System Architecture Overview]].*
