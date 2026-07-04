---
tags: [project-management, timeline, milestones]
created: 2026-03-29
status: active
---
# 📅 Timeline & Milestones

> [!note] Baseline
> Concept paper submitted **29 March 2026**. Defense targeted **late November–December 2026**. Timeline assumes Kurt as sole engineer, part-time alongside coursework, with deliberate risk buffers.

## Month-by-Month Plan

| Month | Focus | Key Milestone | Critical Path? |
|---|---|---|---|
| **Apr 2026** | Detailed design freeze; finalize BOM; first adviser meeting | Design & BOM approved | ✅ |
| **May 2026** | Procurement wave 1 (frame, motors, drivers, controller) | All long-lead parts ordered | ✅ |
| **Jun 2026** | Mechanical assembly (X + Y axes); wiring | Gantry frame standing | ✅ |
| **Jul 2026** | Electronics integration; firmware flash | Motors move under command | ✅ |
| **Aug 2026** | Motion tuning + accuracy tests; dataset collection begins | Positional error < target | ✅ |
| **Sep 2026** | Segmentation model training + eval; color module | Model mIoU ≥ 0.65 | ✅ |
| **Oct 2026** | System integration; spray sync; paint tests | First successful painted design | ✅ |
| **Nov 2026** | Metrics collection; Chapters 4–5; presentation build | Results chapter complete | ✅ |
| **Dec 2026** | Mock defense → revisions → **Final Defense** | Thesis defended | ✅ |

## Milestone Gates

> [!success] M1 — Design Freeze (end Apr)
> BOM locked, wiring diagram final, methodology drafted. Gate to spending.

> [!success] M2 — Moving Gantry (end Jul)
> Frame assembled, motors driven by Arduino, homing works. Gate to AI integration.

> [!success] M3 — AI Ready (end Sep)
> Segmentation + color module validated on test set. Gate to full integration.

> [!success] M4 — First Paint (mid Oct)
> A simple 2-color design painted on a 1m × 1m board. Gate to metrics collection.

> [!success] M5 — Defense (Dec)
> All chapters complete, mock defense passed.

## Risk Buffers
- **2-week buffer** built into Aug (motion tuning historically overruns).
- **2-week buffer** in Oct (spray calibration is the highest-risk task — see [[💧 Spray System Design]]).
- Procurement started early (May) to absorb Lazada/Shopee shipping delays.

## Critical Path Narrative
The critical path runs: **procurement → mechanical assembly → firmware → motion accuracy → integration → paint tests → results**. AI model training (Sep) can partially parallelize with mechanical work, but *cannot be validated end-to-end* until the gantry moves. Any slip in the mechanical build cascades directly to the defense date. See [[⚠️ Risk Register]] R-09 (shipping delays) and R-02 (racking).
