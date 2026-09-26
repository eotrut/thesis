---
tags: [project-management, timeline, milestones]
created: 2026-03-29
status: active
---
# 📅 Timeline & Milestones

> [!note] Baseline
> Concept paper submitted **29 March 2026**. Defense targeted **late November–December 2026**. Timeline assumes Kurt as sole engineer, part-time alongside coursework, with deliberate risk buffers.

> [!success] CPEPRACDSN1 Workplan — confirmed 2026-08-19
> Official course workplan (submitted form) covers **July 2026 – January 2027 (7 months)**. Went through several revisions same day: (1) initial draft assumed Aug–Dec with AI/software still framed as upcoming; (2) corrected to Jul start since most AI/software work was already built July–August; (3) end date pushed to Jan, evaluation spread across Nov+Dec, Jan reserved for prep only; (4) **gantry mechanical assembly given three months instead of one** — Kurt flagged that squeezing assembly into August alone (which hadn't started as of 2026-08-18) was unrealistic given it already slipped once before. Final gantry split: **Aug** = X-axis rail + wiring + start Y-axis, **Sep** = finish Y-axis + homing, **Oct** = custom firmware + serial controller + motion-accuracy testing. Final month plan: **Jul** = segmentation + color module built/deployed; **Aug** = dataset expansion, post-defense software enhancements, homography/toolpath software, gantry assembly starts; **Sep** = gantry assembly finishes + homography validation; **Oct** = gantry firmware/motion + spray control + integration + paint tests + color-module evaluator validation (this month is now the most heavily loaded — see flag below); **Nov** = evaluation begins; **Dec** = evaluation and final testing continues, Chapters 4–5 drafted; **Jan** = final presentation prep (incl. mock defense) + final documentation prep, final defense. See the filled workplan doc (delivered to Kurt 2026-08-19) for the full breakdown — 17 objective/activity rows across 7 month columns (Jul–Jan).

> [!warning] Flagged risk (2026-08-19, not yet resolved) — October is overloaded
> Giving the gantry assembly three months (Aug–Sep–Oct... actually firmware lands in Oct) means October now carries FIVE separate first-time efforts: gantry firmware/motion testing, spray-control firmware, full system integration, first live paint tests, and color-module evaluator validation. None of these have started yet, and spray calibration is independently flagged in the Risk Register as the hardest problem in the whole project. If Kurt wants to de-risk this further, the options are: push spray-control/integration into November (but that eats into the Nov–Dec evaluation window he explicitly wants preserved), or accept October as the highest-risk month and treat Nov–Dec's two-month evaluation buffer as the shock absorber if it slips. Surface this if asked to review the timeline again.

## Month-by-Month Plan

| Month | Focus | Key Milestone | Critical Path? |
|---|---|---|---|
| **Apr 2026** | Detailed design freeze; finalize BOM; first adviser meeting | Design & BOM approved | ✅ |
| **May 2026** | Procurement wave 1 (frame, motors, drivers, controller) | All long-lead parts ordered | ✅ |
| **Jun 2026** | *(originally: mechanical assembly)* — slipped, see Aug | — | ✅ |
| **Jul 2026** | Segmentation model fine-tuned (Kaggle T4) and deployed behind local Flask API; color-recommendation module (K-means + LCh harmony) built and integrated | mAP@0.50 0.780 segmentation model live; color module working | ✅ |
| **Aug 2026** | Dataset expansion toward 1,000 images; post-defense software enhancements (demographic color bias, reference blending, mask-correction/smart-select UI); homography + raster toolpath generator built; gantry X-axis assembled + wired, Y-axis assembly begins | X-axis rail assembled and wired | ✅ |
| **Sep 2026** | Finish gantry Y-axis assembly + homing calibration; homography validated against real wall photos | Fully assembled, wired XY gantry frame with working homing | ✅ |
| **Oct 2026** | Gantry firmware (dual-X lockstep) + motion-accuracy testing; spray control; full system integration; first live paint tests; color-module evaluator testing — **heaviest month, see risk flag above** | First successful painted design | ✅ |
| **Nov 2026** | Evaluation/metrics collection begins across all criteria | Initial performance-evaluation dataset compiled | ✅ |
| **Dec 2026** | Evaluation and final testing continues (repeat trials, additional multi-region/mural runs); Chapters 4–5 drafted | Finalized evaluation dataset; Results/Discussion drafted | ✅ |
| **Jan 2027** | Final presentation prep (incl. mock defense) + final documentation prep → **Final Defense** | Thesis defended | ✅ |

## Milestone Gates

> [!success] M1 — Design Freeze (end Apr)
> BOM locked, wiring diagram final, methodology drafted. Gate to spending.

> [!success] M0 — AI Software Built (end Jul)
> Segmentation model fine-tuned and deployed; color-recommendation module working.

> [!success] M2 — Moving Gantry (end Oct, revised 2026-08-19)
> Frame assembled (Aug–Sep), motors driven by custom firmware, homing works, motion accuracy benchmarked (Oct). *(Revised twice: originally end-Jul, then end-Sep, now end-Oct — assembly kept slipping in every draft of this timeline, which is itself informative: budget real slack here, not just on paper.)* Gate to AI integration.

> [!success] M3 — AI Ready (end Sep)
> Segmentation + color module validated on real-world test data (not just synthetic/annotated). Gate to full integration.

> [!success] M4 — First Paint (end Oct)
> A simple 2-color design painted on a 1m × 1m board. Gate to metrics collection.

> [!success] M5 — Defense (Jan 2027)
> All chapters complete, mock defense passed, final defense held.

## Risk Buffers
- **2-week buffer** built into Oct (motion tuning + spray calibration both historically overrun — this is now the single riskiest month in the plan).
- Procurement started early (May) to absorb Lazada/Shopee shipping delays.
- **Evaluation gets two full months (Nov–Dec)** instead of one, partly so it can absorb an October slip.

## Critical Path Narrative
The critical path runs: **procurement → mechanical assembly → firmware → motion accuracy → integration → paint tests → results**. The AI/software side (segmentation, color recommendation, homography/toolpath code) is *not* on the critical path — it was already built July–August — but its **real-world validation** (homography, color-module evaluator testing) is gated on the `samples/` real-wall-photo shoot, still pending. Mechanical assembly has now slipped in every draft of this timeline (originally Jun/Jul, then Aug, now Aug–Sep) — that pattern is the strongest signal in this whole document that the plan should keep erring toward more slack on hardware, not less. October is currently the most loaded month in the plan (see warning above) and is the one most likely to need renegotiating if Kurt reviews progress again in September. See [[⚠️ Risk Register]] R-09 (shipping delays) and R-02 (racking).
