---
tags: [defense, qa, panel]
created: 2026-03-29
status: active
---
# ❓ Anticipated Panel Questions & Answers

> [!tip] Answer in 3–5 sentences: honest, confident, not defensive. Backed by [[🔍 Research Gaps & Justification]].

## AI Model
**Q1. Why MobileNetV3 + DeepLabV3+ and not a larger model like ResNet-101?**
The laptop has a 4GB RTX 3050, which cannot comfortably train heavy backbones. MobileNetV3 gives strong segmentation with far less memory and near-real-time inference, and the task — flat walls — does not need a very deep model. If accuracy falls short, U-Net is our validated fallback.

**Q2. How do you handle limited training data?**
We use transfer learning from ImageNet and pretrain on ADE20K, which includes a wall class, then fine-tune on a small custom set annotated with LabelMe. We also apply augmentation (flips, jitter, rotation). If multi-class proves unstable, we reduce to a binary paintable/not-paintable mask.

**Q3. What accuracy is "good enough"?**
For a prototype we target over 0.65 mIoU and over 75% pixel accuracy. The mask only needs to be accurate enough that the raster planner fills the correct area; small boundary errors are absorbed by 10–20% spray overlap.

**Q4. Is K-means really "AI"?**
K-means is unsupervised machine learning, and combined with color-harmony rules it forms a legitimate recommendation system. We are transparent that it is not a neural network; we chose it because it is implementable within budget and directly fills a gap — no cited painting robot generates harmonious palettes.

## Simpler Approaches
**Q5. Why not just pre-program the paths like existing robots?**
Pre-programming is exactly the limitation we address: those systems cannot adapt to the actual wall or design. Perception lets AURA generate paths from what it sees, which is the core novelty. Pre-programming would defeat the purpose of the study.

**Q6. Why segmentation instead of simple edge detection or thresholding?**
Thresholding fails under real lighting and texture variation, whereas a learned model generalizes across conditions. Segmentation also extends naturally to multi-region, multi-color painting. It is the more robust and scalable choice.

## Industrial Applicability
**Q7. This is not industrial-scale — why does it matter?**
AURA is a deliberate proof-of-concept, not a product. Its value is demonstrating that an integrated intelligent painting pipeline is achievable at roughly PHP 30,000, which lowers the barrier for future scaling. The scope was declared from the outset.

**Q8. How would this scale to real buildings?**
The same architecture scales with a larger frame, more training data, and optimized path planning; the perception and control logic are size-independent. Scaling is an engineering effort, not a conceptual barrier. We list this explicitly as future work.

## Team
**Q9. Only one member is technically capable — is that a risk?**
Yes, and we manage it directly: everything is documented in a structured vault, code is backed up to GitHub, and teammates are cross-trained on assembly and logging. The risk is registered and mitigated rather than ignored.

## Evaluation
**Q10. Is n=5 evaluators enough for color recommendation?**
For a qualitative usability signal at prototype scale, five raters give an initial indication of appeal and suitability; we report it as descriptive, not inferential. We can expand the sample if time allows. The quantitative color-reproduction metric (ΔE) provides an objective complement.

**Q11. How do you measure spray consistency objectively?**
We photograph painted regions under even lighting and analyze pixel-intensity variance across the area, reporting coverage percentage and uniformity. This mirrors deep-vision inspection methods shown to exceed 95% accuracy in the literature. It removes reliance on subjective judgment.

**Q12. How do you ensure motion-accuracy measurements are valid?**
We command known coordinates and measure the actual head position, computing positional error in millimeters across repeated runs, and report mean and standard deviation. Calibration of steps-per-mm and belt tension precedes testing. We define a threshold (e.g., ≤ 2 mm) for prototype adequacy.

## Limitations
**Q13. Raster scanning is not optimal — why use it?**
For flat walls and simple murals it is deterministic and easy to debug, which matters for a solo builder. Optimal planning adds failure modes without meaningful benefit at this scope. We note optimized planning as future work.

**Q14. No Z-axis — is that a weakness?**
The spray head works at a fixed standoff, so an active Z is unnecessary for flat walls. Adding Z is a clear extension for textured or 3D surfaces, which are outside our declared scope. It is a scope choice, not an oversight.

**Q15. What if the spray drips or clogs?**
This is our highest-risk subsystem and is actively mitigated: water-based acrylic, strained paint, a solenoid mounted near the nozzle, purge cycles before runs, and a spare nozzle. It is tracked in the risk register. We designed the test protocol specifically to characterize and tune it.

## Budget & Feasibility
**Q16. Is PHP 35,000 realistic for all of this?**
Yes; our bill of materials totals about PHP 26,000 with a contingency reserve, using local suppliers and clone controllers. Where needed we substitute V-wheels for linear rails and reuse a webcam. The budget has been itemized and cross-checked.

**Q17. Can you finish by the defense date?**
Our timeline runs procurement to defense across April–December 2026 with buffers in the highest-risk months. AI training partly parallelizes with the mechanical build. The critical path is the mechanical-to-integration chain, which we start early.

## Novelty
**Q18. How is this different from the Arduino wall-painting robot you cited?**
That system, like others, is pre-programmed with no vision or color intelligence. AURA adds deep-learning segmentation, AI color recommendation, and adaptive spray on the same low-cost backbone. The novelty is the integration, not any single part.

**Q19. What is the single most novel contribution?**
Unifying perception, color reasoning, motion, and adaptive spray into one automated pipeline at undergraduate cost — a combination none of our cited works achieve. Individually the pieces exist; together, affordably, they do not.

**Q20. What happens if H₁ is not supported?**
We report results honestly and analyze which subsystems met their targets and which did not, diagnosing causes. Even partial success validates the architecture and yields clear engineering lessons. A rigorous negative or mixed result is still a legitimate contribution.

**Q21. Why is color recommendation part of a painting robot at all?**
Because deciding *what* to paint is as much a part of autonomy as deciding *where*. Prior robots assume a human picks the color; AURA extends automation to the aesthetic decision. It also differentiates the work and addresses a specific literature gap.
