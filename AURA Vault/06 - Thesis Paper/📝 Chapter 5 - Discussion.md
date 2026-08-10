---
tags: [thesis, chapter-5, discussion, placeholder]
created: 2026-03-29
updated: 2026-07-12
status: pending
---
# 📝 Chapter 5 — Discussion

> [!warning] Pending
> Complete after [[📝 Chapter 4 - Results]]. Interpretation guidance is pre-written below so writing is fast once data exists.

> [!info] Sync note (2026-07)
> No structural change needed here — this chapter never singled out color reproduction. Just make sure "color performance" in the interpretation below is read as **color recommendation quality** (ISO/IEC 25010-framed Likert ratings), not a recommended-vs-applied color comparison — that comparison is out of scope. See [[📝 Chapter 1 - Introduction]].

## Suggested Structure
1. **Restate purpose** briefly and the hypotheses (H₀/H₁).
2. **Interpret each metric** against its reference standard (ISO 9283:1998, COCO protocol, ASTM D823, ISO/IEC 25010:2011, IEEE 1872-2015 — see [[📝 Chapter 3 - Methodology]]).
3. **Integration findings** — how well perception, motion, color recommendation, and spray worked together.
4. **Limitations.**
5. **Future work.**
6. **Conclusion.**

## If H₁ is Supported
> [!tip]
> Argue that YOLOv8 segmentation, OpenCV calibration, AI color recommendation, adaptive spray, and dual-motor motion **jointly** produced measurable gains over manual/non-adaptive painting. Tie each metric that met its reference-standard target back to a specific objective from [[📝 Chapter 1 - Introduction]], and emphasize the **integration** achievement — the contribution no single cited work made (see [[🔍 Research Gaps & Justification]]).

## If Results Are Mixed
> [!tip]
> Be honest and analytical: identify *which* subsystems met targets and *which* did not, and diagnose why (e.g., spray consistency limited by pump atomization; segmentation limited by dataset size if fine-tuning was triggered). Frame partial success as validating the *architecture* even where a component needs refinement. Distinguish prototype limitations from conceptual ones.

## Framing Prototype Limitations Without Undermining the Contribution
> [!note]
> Position AURA explicitly as a **proof-of-concept** built on a PHP ≤35k budget. Limitations (flat walls only, raster paths, zero-shot-first segmentation, no active Z, no color-reproduction verification) are **declared scope choices**, not failures. State a clear scalability path (larger frame, fine-tuning if triggered, optimized paths, future paint-mixing/color-verification module) so the panel sees the ceiling is practical, not fundamental. Reference [[🔍 Research Gaps & Justification]] to keep the significance in view.

## Future Work (seed list)
- Optimized (non-raster) path planning for complex murals.
- Larger/custom annotated dataset for YOLOv8 fine-tuning; multi-class region segmentation.
- Active Z-axis and curved-surface handling.
- A paint-mixing or color-sensing subsystem that would make recommended-vs-applied color verification (CIE ΔE\*) meaningful — explicitly out of scope for this prototype.
- Neural color recommendation (e.g., CLIP-based) as a stretch approach.
