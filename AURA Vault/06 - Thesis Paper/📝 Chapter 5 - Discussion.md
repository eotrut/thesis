---
tags: [thesis, chapter-5, discussion, placeholder]
created: 2026-03-29
status: pending
---
# 📝 Chapter 5 — Discussion

> [!warning] Pending
> Complete after [[📝 Chapter 4 - Results]]. Interpretation guidance is pre-written below so writing is fast once data exists.

## Suggested Structure
1. **Restate purpose** briefly and the hypotheses (H₀/H₁).
2. **Interpret each metric** against its target threshold.
3. **Integration findings** — how well perception, motion, color, and spray worked together.
4. **Limitations.**
5. **Future work.**
6. **Conclusion.**

## If H₁ is Supported
> [!tip]
> Argue that deep-learning segmentation, AI color recommendation, adaptive spray, and dual-motor motion **jointly** produced measurable gains over manual/non-adaptive painting. Tie each metric that met its threshold back to a specific objective from [[📝 Chapter 1 - Introduction]], and emphasize the **integration** achievement — the contribution no single cited work made.

## If Results Are Mixed
> [!tip]
> Be honest and analytical: identify *which* subsystems met targets and *which* did not, and diagnose why (e.g., spray consistency limited by pump atomization; segmentation limited by dataset size). Frame partial success as validating the *architecture* even where a component needs refinement. Distinguish prototype limitations from conceptual ones.

## Framing Prototype Limitations Without Undermining the Contribution
> [!note]
> Position AURA explicitly as a **proof-of-concept** built on a PHP ≤35k budget. Limitations (flat walls only, raster paths, small dataset, no active Z) are **scope choices**, not failures — the scope was declared in Chapter 1. State a clear scalability path (larger frame, more data, optimized paths) so the panel sees the ceiling is practical, not fundamental. Reference [[🔍 Research Gaps & Justification]] to keep the significance in view.

## Future Work (seed list)
- Optimized (non-raster) path planning for complex murals.
- Larger/custom annotated dataset; multi-class region segmentation.
- Active Z-axis and curved-surface handling.
- Neural color recommendation (CLIP-based) as in the stretch approach.
