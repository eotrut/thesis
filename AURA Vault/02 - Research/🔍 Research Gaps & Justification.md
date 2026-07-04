---
tags: [research, gaps, justification, defense]
created: 2026-03-29
status: active
---
# 🔍 Research Gaps & Justification

> [!tip] Defense weapon
> This note answers the panel's "**why does this research matter?**" question. Each gap names the papers that prove it exists and states exactly how AURA fills it. Pairs with [[📚 Literature Review Master]] and [[❓ Anticipated Panel Questions & Answers]].

## Gap 1 — Painting robots are pre-programmed, not perceptive
**The gap:** existing wall-painting robots follow fixed motion paths and cannot *decide* where to paint from the wall itself.
**Proof:** [[Kumote 2022 - Auto Wall Painting Robot]], [[Patil 2021 - Autonomous Wall Painting Robot]], and [[RSIS 2025 - Arduino Wall Painting Robot]] all rely on pre-programmed movement; none segment the wall to plan targets.
**How AURA fills it:** a deep-learning segmentation model ([[🔮 Segmentation Model]]) identifies paintable regions from a camera image, so paths are *generated from perception*, not hand-coded.

## Gap 2 — Vision-for-spray work assumes industrial 3D hardware
**The gap:** the strongest AI-spray research depends on 3D point clouds and industrial robots, out of reach for low-cost builds.
**Proof:** [[Tiboni 2022 - PaintNet]] learns trajectories from 3D point clouds; [[Liu & Cheng 2024 - Semantic Segmentation Spray]] pairs segmentation with industrial spray robots.
**How AURA fills it:** AURA uses **2D single-image segmentation** on a 4GB RTX 3050 driving a hobby-grade XY gantry — demonstrating the same perceive-then-spray idea at ~PHP 30k.

## Gap 3 — Capabilities exist in isolation, not integrated
**The gap:** segmentation, trajectory planning, spray control, and color selection appear separately, never as one closed pipeline.
**Proof:** [[Bjekic 2023 - Wall Segmentation CNN]] (segmentation only), [[Nimje 2025 - AI Vision Panel Defects]] (inspection only), Al Mawali & Hussain (2023) (color DB only).
**How AURA fills it:** AURA's architecture ([[🏗️ System Architecture Overview]]) chains camera → segmentation → color recommendation → path planning → serial → motion + adaptive spray as a *single* integrated system.

## Gap 4 — Color decisions are manual or database-lookups, not AI-generated
**The gap:** painting robots either use a fixed color or look up a color from a sensor/database; none *recommend* harmonious palettes.
**Proof:** Al Mawali & Hussain (2023) use a color sensor + database; other painting robots assume a pre-selected paint.
**How AURA fills it:** an AI color-recommendation module ([[🎨 Color Recommendation Module]]) clusters input imagery (K-means) and applies color-harmony rules to *generate* coherent palettes — evaluated by human raters.

## Gap 5 — Adaptive spray coordinated with perception is under-explored at prototype scale
**The gap:** adaptivity in the literature targets arm kinematics; spray flow is rarely coordinated with *where perception says to paint* on affordable hardware.
**Proof:** [[Aziz 2026 - 4DOF SCARA ML]] adds ML to arm kinematics; Kiran & Prabhu (2020) treat flow control in isolation; [[Faheem 2024 - AI Robotics Construction]] notes the domain gap in construction automation.
**How AURA fills it:** AURA times solenoid/pump actuation to gantry position and segmentation output ([[💧 Spray System Design]]), making spray an *adaptive* part of an integrated loop rather than a standalone valve.

> [!note] One-sentence justification
> AURA is justified because it is the first *undergraduate-affordable* system to unify deep-learning wall perception, AI color recommendation, XY-gantry motion, and adaptive spray into one automated painting pipeline — a combination no cited work achieves.
