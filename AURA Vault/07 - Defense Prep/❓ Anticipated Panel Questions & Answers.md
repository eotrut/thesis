---
tags: [defense, qa, panel]
created: 2026-03-29
updated: 2026-08-10
status: active
---
# ❓ Anticipated Panel Questions & Answers

> [!tip] Answer in 3–5 sentences: honest, confident, not defensive. Backed by [[🔍 Research Gaps & Justification]].

> [!info] Sync note (2026-08-10)
> Added Q7b — the panel is now as likely to probe the color module's *implementation constants* (lightness band, alternative offsets) as its literature basis (Q7). Prompted by a code audit that fixed two defects: hardcoded offsets drifting once the lightness band widened, and zero test coverage across three prior fix rounds. See [[🎨 Color Recommendation Module]] § Second fix round.

> [!info] Sync note (2026-08-05)
> Full rewrite. Previous version referenced the superseded MobileNetV3+DeepLabV3+ backbone, the incorrect ASTM D4147/D3270 citations, and CIE ΔE\* color-reproduction testing — all removed per [[📝 Chapter 3 - Methodology]] and [[📝 Chapter 1 - Introduction]] sync notes. Answers below reflect current state: YOLOv8n-seg, ASTM D823, no color-reproduction claim, ~46% overall completion, System Integration at 0%.

> [!info] Sync note (2026-08-06)
> Added Q0 as a likely opening/motivation question, compressed from Chapter 1's Background of the Study and Rationale/Significance sections plus Gap 1 and Gap 3 in [[🔍 Research Gaps & Justification]].

## Opening / Motivation

**Q0. Why did you choose wall-painting as your research area?**
Manual wall painting carries real occupational risk — VOC exposure linked to respiratory impairment, plus fall and musculoskeletal risk from working at height, which is exactly why DOLE and RA 11058 regulate it. Prior wall-painting robots already proved the physical task can be automated, but they run on fixed, pre-programmed paths with no perception of the actual wall or design. At the same time, deep-learning segmentation and AI color recommendation had matured as separate research threads but rarely closed the loop into a physical actuator. We chose this space because it let us unify those threads — perception, calibration, adaptive spray, and color reasoning — into one reproducible, undergraduate-budget system, which no cited work does end to end.

## AI Model

**Q1. Why YOLOv8 and not a heavier segmentation model?**
YOLOv8 is COCO-pretrained and runs at real-time speed on the RTX 3050 with CUDA, and critically supports a zero-shot-first evaluation: we test the pretrained weights directly on wall images before paying for any custom dataset or fine-tuning. That's consistent with recent transfer-learning literature showing COCO-pretrained backbones generalize well enough that fine-tuning becomes optional rather than a prerequisite. Custom fine-tuning via Roboflow + Kaggle T4 remains available as a conditional Phase 2, triggered only if zero-shot underperforms.

**Q2. What segmentation accuracy have you actually achieved?**
On a 300-image preliminary run (YOLOv8n-seg, fine-tuned, 2 classes, 70/20/10 split, test n=29): mAP@0.50 = 0.780, mAP@0.50–0.95 = 0.548, precision = 0.845, recall = 0.729. These clear our 0.70 working threshold but are preliminary — the dataset is still expanding toward a 1,000-image target and these numbers are expected to be superseded before final testing.

**Q3. Precision is higher than recall — isn't that a weakness?**
No, it's the safer failure mode for this application. Higher precision than recall means the model under-segments rather than over-segments: it occasionally misses part of a paintable wall (a correctable gap) rather than calling a non-paintable surface — a window, an outlet, trim — paintable, which can't be undone once sprayed. We treat this as a deliberate design read of the numbers, not a shortfall to explain away.

**Q4. How do you handle limited training data?**
Zero-shot COCO weights are the default and don't need custom data at all. If that underperforms, we fine-tune on a Roboflow-annotated custom set (currently 300 images, targeting 1,000) using a Kaggle Tesla T4, with augmentation — flips, brightness/contrast jitter, slight rotation — applied in Phase 2. The two-phase structure means we only pay the data-collection cost if the pretrained model actually needs it.

## Color Recommendation

**Q5. How does the color recommendation module work, and is it really "AI"?**
It applies color-harmony rules — complementary, analogous, triadic, split-complementary — computed in CIE LCh(ab) rather than HSV, because LCh is closer to perceptually uniform and separates lightness from chroma so output can be constrained to an interior-paint band without disturbing hue relationships. It's not a neural network, and we're upfront about that; we chose it because it's implementable within budget and fills a real literature gap — none of the cited painting robots reason about color at all, they assume a human picks it.

**Q6. Why is color recommendation part of a painting robot at all?**
Deciding what to paint is as much a part of autonomy as deciding where. Every prior system we cite assumes a human supplies the color; AURA extends automation to that aesthetic decision, which both differentiates the work and directly addresses a gap identified in our literature review.

**Q7. Is n≥5 evaluators enough to judge color recommendation quality?**
For a prototype-scale qualitative signal, five raters using a 1–5 scale against ISO/IEC 25010:2011 usability/satisfaction sub-characteristics gives an initial, honestly-reported descriptive result — we're not claiming statistical inference from it. This evaluation hasn't run yet; it's scheduled once the module is finalized, alongside the remaining `samples/` real-photo capture.

**Q7b. Where do the module's specific numeric constants — the lightness band, the alternative-palette offsets — come from?**
Same honesty standard as the demographic bias table in § 2.8b: the direction is reasoned from the colour space, the magnitude is our own tuning call, and the evaluator study is what settles it. The output band is **L\* 30–88 / C\* 12–60**. It started tighter — L\* 30–70 — deliberately, because that killed the washed-out and hyper-saturated failures first, and we widened it only when a specific reproducible case proved it was tighter than real emulsion: a pastel reference image could not produce a pastel recommendation, because the L\* 70 ceiling clamped a light pink (`#F8C8DC`, L\* 85.2) down to a dusty mauve.

Worth stating up front that widening it carried a second-order cost we then had to fix, because it's the honest version of this answer. Raising the ceiling let the demographic *lightness* deltas actually take effect, which pushed the children's palettes into a region where sRGB cannot carry the chroma they ask for — so two categories a full 12 C\* apart both clipped to the same reachable value and rendered as **the identical colour**. The gender split disappeared silently. The fix is that where the gamut cannot give both, we now spend lightness to buy the requested chroma rather than cutting chroma at fixed lightness. It is also why that case has its own test: clipping is *monotonic*, so a monotonicity check passes straight through this bug and a separate distinctness check is what actually catches it.

The five palette alternatives are offsets from the recommendation's own L\* rather than absolute values, so the palette scales as a family wherever the base recommendation lands instead of drifting apart when the band moves — the same band change above had knocked them 8–13 L\* adrift. All of this is now held by an 11-invariant suite (`backend/tools/test_color_recommender.py`) rather than one-off manual checks. Full record: [[🎨 Color Recommendation Module]] §§ Second fix round, Post-commit audit.

## System Design & Simpler Approaches

**Q8. Why not just pre-program the paths like existing robots?**
That's exactly the limitation AURA addresses — pre-programmed systems can't adapt to the actual wall or design. Perception lets AURA generate paths from what the camera actually sees, which is the core novelty; pre-programming would defeat the point of the study.

**Q9. Raster scanning isn't an optimal path strategy — why use it?**
For flat walls and simple murals it's deterministic and easy to debug, which matters for a solo builder responsible for firmware, AI, and integration simultaneously. Optimal path planning adds failure modes without a clear benefit at this scope, so we explicitly scoped it as future work rather than treating it as an oversight.

**Q10. No active Z-axis — is that a weakness?**
The spray head operates at a fixed standoff, so an active Z isn't needed for flat walls, which is our declared scope. It's a clear, stated extension point for textured or 3D surfaces, not something we missed.

## Evaluation & Standards

**Q11. How do you measure motion accuracy, and against what standard?**
We command known coordinates, measure actual head position, and compute positional error in millimeters across repeated runs (mean, SD), benchmarked against ISO 9283:1998's pose accuracy and repeatability criteria for manipulating industrial robots. This hasn't been run yet — it needs the full XY gantry assembled and a working serial link, both still in progress.

**Q12. How do you evaluate spray consistency and coverage uniformity?**
Both are benchmarked against a single corrected standard, ASTM D823-18(2022) — "Standard Practices for Producing Films of Uniform Thickness of Paint, Coatings and Related Products on Test Panels." (We caught and corrected a citation error here during a reference audit: the two standards originally cited, D4147 and D3270, turned out to be real ASTM designations for entirely unrelated things — coil-coating drawdown bars and fluoride content in plant tissue, respectively.) We report uniformity across test panels and percentage of area evenly coated, once system integration reaches physical spray testing.

**Q13. What happened to color-reproduction accuracy (ΔE)?**
We removed it. AURA doesn't mix or synthesize paint — it recommends a palette from a fixed set of pre-mixed colors — so there's no instrumentable way to compare a "recommended" color against an "applied" one; there's nothing to measure a delta against. What we do evaluate is recommendation quality: whether the palette itself is coherent and suitable, via the Likert study. A future paint-mixing or color-sensing module is the extension that would make ΔE meaningful, and we say so explicitly.

## Current Status & Honesty About the Gap

**Q14. You're presenting before integration is done — what's actually built versus planned?**
Segmentation, homography calibration, toolpath generation, and color recommendation are built and running behind a Flask API, with segmentation quantitatively verified (Q2). What's not built yet: `serial_ctrl.py`, the Arduino-facing command layer — so right now the toolpath stage still emits raw G-code (`G0`/`G1`/`M3`/`M5`) with nothing converting it to our custom `MOVE`/`SPRAY` command set, since we're not running Marlin or a RAMPS shield. That translation is an open, tracked decision blocking firmware integration, not something we're hiding — System Integration is honestly logged at 0% and Hardware & Mechanical at roughly 30%, with the frame itself not yet assembled.

**Q15. Can you realistically finish by the defense date, given where things stand?**
The mechanical build is the critical-path item: once the frame is assembled, firmware and integration testing become possible in parallel rather than blocked, which our own progress tracker models as taking the project from ~46% to roughly 66% complete on that step alone. AI/software work is largely decoupled from the mechanical timeline and already sits around 55%. We've built in buffer specifically because hardware is the dependency everything else waits on, and we track it as the top risk rather than assuming it away.

## Novelty

**Q16. How is this different from the Arduino wall-painting robots you cite?**
Those systems are pre-programmed with no vision or color intelligence. AURA adds deep-learning segmentation, palette-level color reasoning, and camera-driven adaptive path generation on comparable low-cost hardware. The contribution is the integration of all three on one budget-constrained platform — no cited work combines them.
