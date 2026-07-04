---
tags: [research, literature-review, synthesis]
created: 2026-03-29
status: active
---
# 📚 Literature Review Master

> [!info] Purpose
> A *thematic synthesis* of the literature — not a list of summaries. Feeds directly into [[📝 Chapter 2 - Review of Related Literature]]. Individual paper notes live in `02 - Research/References/`. Gaps are consolidated in [[🔍 Research Gaps & Justification]].

## Theme 1 — Mechanical Wall Painting Automation

The earliest and most consistent thread in the literature is the mechanical automation of wall painting. [[Kumote 2022 - Auto Wall Painting Robot]] and [[Patil 2021 - Autonomous Wall Painting Robot]] both demonstrate XY-based painting platforms driven by pre-programmed motion, with Kumote adding sensor feedback for wall detection. Rudzuan (2019) extends this to a gantry spray system with multi-axis control, and [[Tawade 2024 - XY Gantry Material Handling]] validates the XY-gantry kinematics that AURA reuses for its motion stage. At the applied end, [[RSIS 2025 - Arduino Wall Painting Robot]] shows a low-cost Arduino-driven build closely matching AURA's budget class, while Al Mawali & Hussain (2023) introduce a color sensor and a color database to select paint.

**What exists:** reliable XY/gantry motion, roller/spray end-effectors, Arduino-class controllers, and basic sensor feedback.
**The gap:** these systems execute *fixed, pre-programmed* paths. They do not *perceive* the wall to decide **where** paint should go, nor reason about **which colors** to apply. Painting is mechanical reproduction, not visual understanding.
**How AURA addresses it:** AURA keeps the proven XY-gantry + Arduino motion backbone but replaces fixed programming with a **deep-learning perception layer** that segments paintable regions and an **AI color recommender**, turning a "plotter with paint" into a system that decides its own targets.

## Theme 2 — AI & Computer Vision in Robotic Systems

A second thread applies deep learning to visual understanding for robots. [[Bjekic 2023 - Wall Segmentation CNN]] is the most directly relevant: it segments walls from single 2D images using a CNN, which is precisely the perception primitive AURA needs. [[Tiboni 2022 - PaintNet]] and [[Liu & Cheng 2024 - Semantic Segmentation Spray]] push further into spray robotics — PaintNet learns spray trajectories from 3D point clouds, and Liu & Cheng combine semantic segmentation with trajectory optimization for spray robots. On the inspection side, Shaikh & Kokate (2025) and [[Nimje 2025 - AI Vision Panel Defects]] report deep-vision surface/defect analysis exceeding 95% accuracy, and Ni et al. (2023) survey deep-learning scene understanding for autonomous robots.

**What exists:** mature CNN segmentation for walls and scenes, learned spray trajectories, and high-accuracy visual inspection.
**The gap:** these capabilities are demonstrated in **isolation** — segmentation *or* trajectory learning *or* inspection — and several (PaintNet, Liu & Cheng) assume **3D point clouds and industrial hardware** unavailable to an undergraduate prototype. None couple *lightweight 2D segmentation* to *low-cost gantry actuation* end-to-end.
**How AURA addresses it:** AURA adopts a lightweight 2D segmentation model (MobileNetV3 + DeepLabV3+, per [[🔮 Segmentation Model]]) explicitly chosen to run on a 4GB RTX 3050, and wires its output through a raster path planner to physical motion — closing the perception-to-actuation loop on affordable hardware.

## Theme 3 — Intelligent Control & Adaptive Systems

The third thread concerns intelligence and adaptivity in control. [[Aziz 2026 - 4DOF SCARA ML]] models a 4-DOF SCARA arm and layers machine learning (SVM, Random Forest) onto its kinematics, showing ML can refine robotic control. Kiran & Prabhu (2020) review nano-spray painting robots and highlight flow/atomization control as the decisive quality factor. IEEE (2022) surveys autonomous robotic systems and sensor integration, and [[Faheem 2024 - AI Robotics Construction]] frames AI + robotics as an emerging force in construction automation, of which wall finishing is a natural sub-domain.

**What exists:** evidence that ML improves control, that spray/flow control governs finish quality, and that construction is a legitimate application domain.
**The gap:** adaptive *spray* control tied to *perception* is under-explored at the prototype scale — most adaptivity is in arm kinematics, not in coordinating **where to spray, how much, and in what color** as one loop.
**How AURA addresses it:** AURA treats spray as an *adaptive* subsystem (solenoid + pump timed to gantry position, per [[💧 Spray System Design]]) coordinated with segmentation output and color recommendation — integrating perception, motion, and flow rather than optimizing any one in isolation.

## Overall Synthesis — The Gap AURA Fills

Across all three themes, the literature has independently matured (a) affordable XY/gantry painting mechanics, (b) deep-learning 2D scene/wall segmentation, and (c) intelligent/adaptive control — but **no accessible, undergraduate-scale system unifies perception, color reasoning, motion, and adaptive spray into a single automated wall-painting pipeline.** Prior painting robots are blind and pre-programmed; prior vision work is disembodied or demands industrial 3D sensing; prior adaptive control targets arms, not integrated painting. AURA's contribution is precisely this **integration on a PHP ≤35,000 budget**: lightweight segmentation and AI color recommendation driving a dual-motor XY gantry with adaptive spray — demonstrating that intelligent, self-directed wall painting is achievable without industrial hardware.
