---
tags: [thesis, chapter-1, introduction]
created: 2026-03-29
status: draft-complete
---
# 📝 Chapter 1 — Introduction

## Background of the Study
Wall painting remains a labor-intensive, time-consuming, and often hazardous task, particularly at height or across large surfaces. Manual painting is prone to inconsistency in coverage, uneven application, and human fatigue, while exposure to fumes and elevated work poses safety risks. Automation has been explored to address these limitations, and prior systems demonstrate that robotic platforms can paint flat walls with reduced human effort (Kumote et al., 2022; Patil et al., 2021; RSIS International, 2025). However, these systems typically rely on **pre-programmed motion**: they reproduce fixed paths without perceiving the wall or reasoning about the design to be applied.

Parallel advances in artificial intelligence and computer vision have made it possible for machines to *understand* visual scenes. Convolutional neural networks can segment walls from ordinary 2D images (Bjekic et al., 2023), and deep learning has been applied to spray-trajectory generation (Tiboni et al., 2022) and segmentation-guided spray planning (Liu & Cheng, 2024). Yet these capabilities are largely demonstrated in isolation or on industrial hardware requiring 3D sensing, leaving a gap between intelligent perception and affordable, integrated painting systems.

This study proposes **AURA (Autonomous Unified Robotic Artist)**, an AI-assisted autonomous wall-painting robot that unifies deep-learning spatial segmentation, AI color recommendation, XY-gantry motion control, and adaptive spray control into a single prototype built within an undergraduate budget. AURA aims to move beyond mechanical reproduction toward a system that perceives the wall, decides where and in what colors to paint, and executes the result autonomously.

## Statement of the Problem
Existing automated wall-painting systems execute predetermined motions and cannot independently identify paintable regions, recommend coherent color schemes, or adapt paint application to the surface. Meanwhile, the deep-learning methods capable of such perception are typically validated in isolation or on costly industrial platforms. There is therefore no accessible, integrated system that combines visual understanding, color intelligence, motion control, and adaptive spraying for autonomous wall painting at prototype scale. This study addresses that gap.

## Research Questions
1. How can a robotic wall-painting system be designed for accurate movement using an XY gantry?
2. How can deep-learning-based spatial segmentation identify and map paintable wall regions?
3. How can an adaptive spray-control system ensure uniform paint application?
4. How can computer vision, AI, and robotics be integrated into one unified automated painting system?
5. How can an AI color-recommendation system generate visually coherent color combinations?
6. How effective is the system in painting accuracy, spray consistency, coverage uniformity, design alignment, and color reproduction accuracy?

## Scope and Delimitation
The study is limited to **flat wall surfaces** and **2D movement**, targeting **simple mural designs** in **controlled test environments** at **prototype-level** implementation. It does **not** address 3D or curved surfaces, autonomous navigation beyond the working frame, commercial or industrial scale, or real-time continual learning. The prototype target is the reliable painting of a simple two-color design on a 1 m × 1 m flat board.

## Objectives
**General Objective.** To develop an AI-based autonomous wall-painting system that combines deep learning, robotics, color recommendation, and adaptive spray control.

**Specific Objectives.**
1. Design and develop a 2D XY-gantry robotic system for precise wall-surface movement.
2. Develop a deep-learning spatial-segmentation model for identifying paintable regions.
3. Implement an adaptive spray-control system regulating paint flow.
4. Integrate computer vision, motion control, color recommendation, and spray into one system.
5. Develop an AI color-recommendation module for visually coherent color combinations.
6. Evaluate motion accuracy, segmentation accuracy, spray consistency, coverage uniformity, design-to-output alignment, and color performance.
7. Assess the system's capability in executing simple mural designs and multi-region painting.

## Rationale / Significance
AURA contributes an **integrated, affordable proof-of-concept** that demonstrates intelligent wall painting is achievable without industrial hardware. For the construction and finishing domain, where automation remains limited (Faheem et al., 2024), it shows a path toward safer, more consistent painting. For computer engineering education, it demonstrates the practical integration of deep learning, embedded control, and mechatronics on a constrained budget. Its color-recommendation component further extends automation from *how* to paint toward *what* to paint, an under-explored dimension in prior work.

## Hypothesis
> [!note] Hypotheses
> **H₀:** The system does not show significant improvement in accuracy, spray consistency, coverage, and color performance compared to manual or non-adaptive approaches.
> **H₁:** The system significantly improves painting accuracy, spray consistency, coverage, and color performance through deep-learning segmentation, AI color recommendation, adaptive spray control, and robotic automation.

*See also [[📚 Literature Review Master]], [[🔍 Research Gaps & Justification]], and [[🏗️ System Architecture Overview]].*
