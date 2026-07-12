---
tags: [ai, color, recommendation]
created: 2026-03-29
updated: 2026-07-12
status: synced-with-manuscript
---
# 🎨 Color Recommendation Module

> [!info] Related
> [[🧠 AI & Software Design]] · [[🔍 Research Gaps & Justification]] (Gap 4) · Evaluated in [[🧪 Calibration & Testing Log]]

> [!warning] Sync note (2026-07-12) — scope correction
> The evaluation linkage to **color reproduction accuracy** (comparing recommended vs. applied RGB/ΔE) has been **removed**. AURA sprays pre-loaded paint and performs no paint mixing or color synthesis, so there is no way to verify that the *applied* color matches the *recommended* color. This module is now evaluated only on **recommendation quality** — the coherence/suitability of the palette itself — framed against ISO/IEC 25010:2011 usability/satisfaction sub-characteristics. See [[📝 Chapter 1 - Introduction]] and [[📝 Chapter 3 - Methodology]].

## Input
Either a **user-uploaded reference image** OR **user-specified color preferences/constraints** (e.g., a base color or mood).

## Approach 1 — Primary (implementable)
**K-means clustering → dominant colors → harmony rules → palette.**
1. Cluster input image pixels with **K-means** (k = number of dominant colors, e.g., 5).
2. Take cluster centroids as **dominant colors**.
3. Apply **color-harmony rules** to expand/refine into a coherent palette.
4. Output **hex + RGB** with **region→color assignments** (map palette to segmentation regions).

This is the "established color-harmony principles" implementation referenced in the manuscript's Methods section.

## Approach 2 — Stretch (deep-learning-based)
A deep-learning palette recommender, consistent with the literature this module now cites (Yuan et al., 2021, *InfoColorizer*; Wu et al., 2023, AIGC-empowered color matching). Deferred to future work unless time/budget allow — not required to pass.

## Color Harmony Rules to Implement
| Rule | Definition (HSV hue) |
|---|---|
| Complementary | base + (hue + 180°) |
| Analogous | base + (hue ± 30°) |
| Triadic | hue, hue+120°, hue+240° |
| Split-complementary | hue, hue+150°, hue+210° |

## Output Format
```json
{
  "palette": [
    {"hex": "#3B6EA5", "rgb": [59,110,165], "role": "primary"},
    {"hex": "#A5723B", "rgb": [165,114,59], "role": "complementary"}
  ],
  "region_assignments": {"region_0": "#3B6EA5", "region_1": "#A5723B"}
}
```

## Evaluation — updated
- **Qualitative user rating (1–5)** for visual coherence + suitability, framed against **ISO/IEC 25010:2011** usability/satisfaction sub-characteristics.
- **≥ 5 evaluators** minimum (Risk R-11 mitigation via feedback loop).
- **No longer** compared against applied paint color (RGB/ΔE delta) — that comparison required a paint-mixing/color-verification capability AURA does not have. See [[🔍 Research Gaps & Justification]] Gap 4 scope note.

## Why This Is Defensible AI
> [!note]
> K-means is unsupervised learning; combined with rule-based harmony it is a legitimate **AI-adjacent recommendation system**, directly addressing **Gap 4** (no cited painting robot generates harmonious palettes as a first-class module) and honestly framed against the literature it now cites (Yuan et al., 2021; Wu et al., 2023) rather than oversold as a neural net.

## Code Outline (pseudocode)
```python
def recommend(image, k=5, rule="complementary"):
    pixels = image.reshape(-1, 3)
    centroids = kmeans(pixels, k)          # dominant colors
    base = pick_dominant(centroids)        # most frequent cluster
    palette = apply_harmony(base, rule)    # HSV math
    return assign_to_regions(palette)      # region -> color map
```
