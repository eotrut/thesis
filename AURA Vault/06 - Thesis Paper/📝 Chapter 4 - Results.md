---
tags: [thesis, chapter-4, results]
created: 2026-03-29
updated: 2026-07-31
status: partial — 4.2 has preliminary data
---
# 📝 Chapter 4 — Results

> [!warning] Pending
> Chapter 4 will be completed after system testing. Sections are pre-structured below; populate each from [[🧪 Calibration & Testing Log]].

> [!warning] Scope correction (2026-07)
> The former "4.5 Color Reproduction Results" section has been **removed**. AURA does not perform paint mixing/color synthesis, so recommended-vs-applied color comparison (ΔE\*) is not a valid evaluation for this system. Color is now evaluated only as **recommendation quality** (Section 4.5 below). See [[📝 Chapter 1 - Introduction]] and [[📝 Chapter 3 - Methodology]] for the scope rationale.

## 4.1 Motion Accuracy Results
*(Positional error table + mean/SD; benchmarked against ISO 9283:1998 pose accuracy/repeatability criteria.)*

## 4.2 Segmentation Accuracy Results
*(IoU and mAP per test image, COCO protocol, IoU ≥ 0.50 threshold; zero-shot vs. fine-tuned comparison if Phase 2 was triggered.)*

> [!success] Preliminary results available (2026-07-31) — 300-image run
> First quantitative numbers are in. **Preliminary** — dataset is still expanding toward the 1,000-image target, so these are expected to be superseded. Source: [[🔮 Segmentation Model]] Run 2 (`aura_seg_v2`).

**Model:** YOLOv8n-seg (COCO-pretrained, fine-tuned) · 300 images · 2 classes (wall, non-paintable) · 100 epochs, early stopping patience 20 · 640×640 · Kaggle Tesla T4 · 70/20/10 split · test set n = 29.

| Metric | Value | Reading |
|---|---|---|
| **mAP@0.50** | **0.780** | Above the 0.70 working threshold |
| **mAP@0.50–0.95** | **0.548** | Strict COCO metric; respectable at this dataset size |
| **Precision** | **0.845** | Of regions called wall, 84.5% correct |
| **Recall** | **0.729** | Of actual wall regions, 72.9% found |

**Interpretation for the write-up.** Precision exceeding recall means the model is **conservative**: it under-segments rather than over-segments. For a painting robot this is the safer failure mode — under-segmentation leaves an unpainted gap that can be corrected, whereas over-segmentation sprays a non-paintable surface (window, outlet, trim), which cannot be undone. Worth stating explicitly rather than presenting recall as a weakness.

**Deployment measurements** (RTX 3050 Laptop, 640×640) — see [[🔌 Backend API & Web Integration]]:

| Measure | Value |
|---|---|
| Inference per image | ~100 ms |
| Cold-start warm-up | ~1.8 s |
| Wall confidence, test images | 0.88 – 0.94 |
| Wall confidence, live webcam | 0.80 – 0.93 |

> [!todo] Still to produce for this section
> - Per-image IoU table (COCO protocol) — currently only aggregate mAP is recorded
> - Zero-shot (COCO baseline) vs. fine-tuned comparison, if Phase 2 framing is kept
> - Re-run after the ~1,000-image training round and replace the numbers above

## 4.3 Spray Consistency Results
*(Uniformity per pass, benchmarked against ASTM D823; representative photos.)*

## 4.4 Coverage Uniformity Results
*(% area evenly painted per ASTM D823; gap/overlap analysis.)*

## 4.5 Color Recommendation Quality Results
*(Evaluator 1–5 ratings, n≥5, framed against ISO/IEC 25010:2011 usability/satisfaction sub-characteristics; mean + distribution.)*

## 4.6 Overall Output Quality / System Integration Results
*(Visual inspection scores; structured integration assessment per IEEE 1872-2015; final painted-design images.)*
