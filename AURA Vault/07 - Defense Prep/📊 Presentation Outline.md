---
tags: [defense, slides, outline]
created: 2026-03-29
updated: 2026-08-05
status: active
---
# 📊 Presentation Outline

> [!info] 18 slides, dark-charcoal/Times New Roman theme, 24pt+ text. See `AURA_Proposal_Defense.pptx` for the deck and `AURA_Defense_Script_Master.docx` for the full speaker script (split 3 ways — Kurt/David/Usi). Pairs with [[❓ Anticipated Panel Questions & Answers]].

> [!info] Sync note (2026-08-05)
> Full rewrite — previous version (16 slides) referenced the superseded MobileNetV3+DeepLabV3+ backbone, K-means color recommendation, and a slide structure that no longer matches the deck. Table below mirrors the actual 18-slide deck 1:1.

> [!warning] Acronym correction (2026-08-05)
> AURA now correctly expands to **Autonomous Unified Robotic Adaptive** (A-U-R-A verified). "AI-Based Autonomous Wall Painting Robot" is kept only as a descriptive subtitle. See [[📝 Chapter 1 - Introduction]] for the full title and rationale.

| # | Slide | Key Points | Note hint |
|---|---|---|---|
| 1 | **Title** | AURA — Autonomous Unified Robotic Adaptive (subtitle: AI-Based Autonomous Wall Painting Robot); team; HAU SEA; date | *Confident open* |
| 2 | **The Problem** | Labor-intensive & slow; safety risk at height; inconsistent quality; rising labor costs | *Pause after each of the 4 cards* |
| 3 | **Related Work — Painting Robots** | Kumtole et al. 2022 (preset paths, no adaptive vision); Patil et al. 2021 (gantry, limited generalization) | *Name authors clearly* |
| 4 | **Related Work — Spray Systems** | Rudzuan et al. 2019 (solenoid modulation); Tawade et al. 2024 (spray-pattern control); gap: not vision-linked | *Bridges to next slide* |
| 5 | **Related Work — AI & Vision** | Bjekic et al. 2023 (segmentation); Liu & Cheng 2024 (YOLO real-time); gap: not integrated with spray robots | *"Closes all three gaps at once"* |
| 6 | **Research Questions** | 6 RQs: YOLOv8 segmentation accuracy, gantry precision, homography calibration accuracy, Arduino command reliability, color-rec rating, overall effectiveness | *Handoff slide — cue David* |
| 7 | **General Objectives** | Design & evaluate AURA; 5 specific objectives (YOLOv8 pipeline, gantry, spray control, color-rec module, evaluation) | *David opens by acknowledging handoff* |
| 8 | **Scope & Delimitations** | In scope: interior flat walls, YOLOv8 segmentation, gantry motion+spray, palette color-rec. Out: exterior/textured, mobile nav, color-reproduction accuracy, multi-robot | *No ΔE / color-reproduction claim — explain why if asked* |
| 9 | **Triple Bottom Line Impact** | Economic (SDG 9) / Social (SDG 11) / Environmental (SDG 12) | *One SDG per sentence* |
| 10 | **System Conceptual Framework** | Input (camera, color preference) → Process (segmentation, color-rec, toolpath, spray control) → Output (painted wall, metrics log) | *Point at columns, don't just read* |
| 11 | **System Block Diagram** | Camera Input → AI Processing (YOLOv8) → Motion Control → Spray System → Painted Output | *"Laptop thinks, Arduino acts"* |
| 12 | **System Flowchart** | Start → Initialize → Capture → Segment → Generate Commands → Move Gantry → Apply Paint → Collect Metrics → End | *Handoff slide — cue Usi* |
| 13 | **Research Design & Methodology** | Developmental-experimental design, 4 phases: Design, Development, Testing, Evaluation | *Usi opens by acknowledging handoff* |
| 14 | **Hardware Design Stack** | Aluminum extrusion frame, 3× NEMA23 + TB6600, Arduino Mega 2560 (direct-wired, **no RAMPS**), GT2 belt, limit switches + USB camera, spray pump + solenoid (tentative) | *If asked "why not RAMPS" — dropped 2026-08-03, Mega drives TB6600s directly* |
| 15 | **Software Development Stack** | PyTorch+CUDA (RTX 3050), YOLOv8 (Ultralytics), OpenCV, Python toolpath gen, pyserial, Git | *Brisk list, not effortful* |
| 16 | **Data Collection & Participants** | Wall-image dataset (custom + COCO); color-palette dataset; small evaluator panel, 1–5 ratings | *Have target panel size ready* |
| 17 | **Evaluation Metrics** | Quant: motion accuracy (ISO 9283:1998), segmentation accuracy (COCO protocol), spray/coverage uniformity (ASTM D823). Qual: color-rec quality (ISO/IEC 25010), visual inspection (1–5 scale) | *Standards-heavy — slow down* |
| 18 | **Testing & Analysis Plan** | 5 testing phases (mechanical, segmentation, spray, color-rec, full mural); analysis: quant stats, qual rating analysis, iterative refinement | *Closing slide — thank panel, invite questions* |
