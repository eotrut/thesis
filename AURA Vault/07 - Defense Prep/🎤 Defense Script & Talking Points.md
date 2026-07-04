---
tags: [defense, script, presentation]
created: 2026-03-29
status: active
---
# 🎤 Defense Script & Talking Points

> [!info] ~17 minutes. Speaker notes in *italics*. Pairs with [[📊 Presentation Outline]] and [[❓ Anticipated Panel Questions & Answers]].

## 1. Opening (2 min)
"Good [morning/afternoon]. I am Kurt Robyn Manabat, presenting **AURA — Autonomous Unified Robotic Artist**, a deep-learning-based autonomous wall-painting robot, for the Bachelor of Science in Computer Engineering at Holy Angel University."
*Speaker note: state names of teammates (David, Usi). Slow down. Make eye contact with each panelist once.*

## 2. Problem Motivation (2 min)
"Manual wall painting is slow, physically demanding, inconsistent, and can be hazardous at height. Existing painting robots automate the motion but are **pre-programmed** — they cannot perceive the wall or decide what to paint."
*Speaker note: this frames the gap. Emphasize 'pre-programmed' — it is the whole justification.*

## 3. Objectives and Scope (1 min)
"AURA develops an AI-based system unifying deep-learning segmentation, color recommendation, XY-gantry motion, and adaptive spray. Scope: **flat walls, 2D motion, simple murals, prototype scale** — a two-color design on a 1 m × 1 m board."
*Speaker note: naming the scope up front disarms 'why not industrial?' questions later.*

## 4. System Overview (3 min)
"The camera feeds a laptop with an RTX 3050. The laptop segments the wall, recommends colors, plans paths, and streams G-code over USB serial to an Arduino Mega with RAMPS 1.4, which drives three NEMA 23 motors and the spray system."
*Speaker note: point at the architecture diagram. Stress the split: laptop thinks, Arduino acts.*

## 5. AI Components (3 min)
"Segmentation uses a lightweight MobileNetV3 + DeepLabV3+ model chosen to fit the 4GB VRAM budget, targeting over 0.65 mIoU. Color recommendation uses K-means clustering plus color-harmony rules to generate coherent palettes, evaluated by at least five raters."
*Speaker note: if asked why not a bigger model — VRAM and real-time. Have the number ready.*

## 6. Mechanical Design (2 min)
"The gantry uses **dual NEMA 23 motors on the X-axis** to prevent racking — the key accuracy decision — with a single Y motor and GT2 belts giving 40 steps per millimeter. TB6600 drivers were chosen over A4988 because NEMA 23 needs higher current."
*Speaker note: racking is the mechanical crux; show you understand why two motors matter.*

## 7. Methodology and Evaluation (2 min)
"We follow a developmental-experimental design with iterative prototyping. We measure motion accuracy in millimeters, segmentation IoU, spray consistency, coverage uniformity, color reproduction as RGB/ΔE difference, and qualitative output quality."
*Speaker note: tie metrics back to the research questions.*

## 8. Expected Contributions (1 min)
"AURA's contribution is **integration on an affordable budget** — the first undergraduate-scale system to unify perception, color reasoning, motion, and adaptive spray into one painting pipeline."
*Speaker note: this is the sentence they will remember. Say it slowly.*

## 9. Closing (1 min)
"AURA demonstrates that intelligent, self-directed wall painting is achievable without industrial hardware. Thank you — I welcome your questions."
*Speaker note: pause, smile, invite questions confidently.*
