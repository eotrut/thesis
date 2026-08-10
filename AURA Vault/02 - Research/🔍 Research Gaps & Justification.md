---
tags: [research, gaps, justification, defense]
created: 2026-03-29
updated: 2026-07-12
status: synced-with-manuscript
---
# 🔍 Research Gaps & Justification

> [!tip] Defense weapon
> This note answers the panel's "**why does this research matter?**" question. Each gap names the papers that prove it exists and states exactly how AURA fills it. Pairs with [[📚 Literature Review Master]] and [[❓ Anticipated Panel Questions & Answers]].

> [!warning] Sync note (2026-07-12)
> Gap 2 and Gap 4 updated below to reflect the finalized system (YOLOv8, not generic "2D single-image segmentation"; color recommendation quality, not K-means-specific framing or color-reproduction comparison). A new Gap 6 added for the external-standards benchmarking contribution.

## Gap 1 — Painting robots are pre-programmed, not perceptive
**The gap:** existing wall-painting robots follow fixed motion paths and cannot *decide* where to paint from the wall itself.
**Proof:** [[Kumote 2022 - Auto Wall Painting Robot]], [[Patil 2021 - Autonomous Wall Painting Robot]], and [[RSIS 2025 - Arduino Wall Painting Robot]] all rely on pre-programmed movement; none segment the wall to plan targets.
**How AURA fills it:** a YOLOv8 instance-segmentation model ([[🔮 Segmentation Model]]) identifies paintable regions from a camera image, so paths are *generated from perception*, not hand-coded.

## Gap 2 — Vision-for-spray work assumes industrial 3D hardware
**The gap:** the strongest AI-spray research depends on 3D point clouds and industrial robots, out of reach for low-cost builds.
**Proof:** [[Tiboni 2022 - PaintNet]] learns trajectories from 3D point clouds; [[Liu & Cheng 2024 - Semantic Segmentation Spray]] pairs segmentation with industrial spray robots.
**How AURA fills it:** AURA uses **YOLOv8 2D instance segmentation**, evaluated zero-shot-first against COCO-pretrained weights, driving a hobby-grade XY gantry — demonstrating the same perceive-then-spray idea at undergraduate budget, without 3D sensing or industrial hardware.

## Gap 3 — Capabilities exist in isolation, not integrated
**The gap:** segmentation, trajectory planning, spray control, and color selection appear separately, never as one closed pipeline.
**Proof:** [[Bjekic 2023 - Wall Segmentation CNN]] (segmentation only), [[Nimje 2025 - AI Vision Panel Defects]] (inspection only), Al Mawali & Hussain (2023) (color database only).
**How AURA fills it:** AURA's architecture ([[🏗️ System Architecture Overview]]) chains camera → YOLOv8 segmentation → OpenCV homography calibration → color recommendation → raster path planning → pyserial → motion + adaptive spray as a *single* integrated system.

## Gap 4 — Color decisions are manual or database-lookups, not AI-generated
**The gap:** painting robots either use a fixed color or look up a color from a sensor/database; none *recommend* harmonious palettes as a first-class module.
**Proof:** Al Mawali & Hussain (2023) use a color sensor + database; other painting robots assume a pre-selected paint.
**How AURA fills it:** an AI-based color recommendation module ([[🎨 Color Recommendation Module]]) applies color-harmony rules (and, where appropriate, deep-learning palette recommendation per Yuan et al., 2021; Wu et al., 2023) to *generate* coherent palettes — evaluated by human raters against ISO/IEC 25010:2011 usability/satisfaction criteria.
**Scope note:** this evaluates recommendation *quality* only. AURA does not mix or synthesize paint, so verifying that the *applied* color matches the *recommended* color (CIE ΔE\*) is explicitly out of scope — see [[📝 Chapter 1 - Introduction]].

## Gap 5 — Adaptive spray coordinated with perception is under-explored at prototype scale
**The gap:** adaptivity in the literature targets arm kinematics; spray flow is rarely coordinated with *where perception says to paint* on affordable hardware.
**Proof:** [[Aziz 2026 - 4DOF SCARA ML]] adds ML to arm kinematics; Kiran & Prabhu (2020) treat flow control in isolation; [[Faheem 2024 - AI Robotics Construction]] notes the domain gap in construction automation.
**How AURA fills it:** AURA times solenoid/pump actuation to gantry position and segmentation output via the pyserial handshake ([[💧 Spray System Design]], [[🖥️ Serial Communication Protocol]]), making spray an *adaptive* part of an integrated loop rather than a standalone valve.

## Gap 6 — Painting-robot evaluation is rarely benchmarked against recognized external standards (new, 2026-07)
**The gap:** most cited wall-painting prototypes report internally-defined accuracy claims rather than measuring against recognized industry/technical standards.
**Proof:** none of the mechanical wall-painting robots reviewed (Kumote et al., 2022; Patil, 2021; Megalingam et al., 2020; Sowmya et al., 2024) cite a positioning, coating, or quality standard.
**How AURA fills it:** AURA's evaluation is explicitly framed against ISO 9283:1998 (positional accuracy), the COCO evaluation protocol (segmentation), ASTM D823 (spray consistency/coverage uniformity), ISO/IEC 25010:2011 (color-recommendation quality), and IEEE 1872-2015 (system integration) — see [[📝 Chapter 3 - Methodology]].

> [!note] One-sentence justification
> AURA is justified because it is the first *undergraduate-affordable* system to unify YOLOv8-based wall perception, calibrated coordinate mapping, AI color recommendation, and adaptive spray into one automated painting pipeline evaluated against recognized external standards — a combination no cited work achieves.
