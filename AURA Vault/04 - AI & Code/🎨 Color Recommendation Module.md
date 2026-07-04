---
tags: [ai, color, recommendation]
created: 2026-03-29
status: active
---
# 🎨 Color Recommendation Module

> [!info] Related
> [[🧠 AI & Software Design]] · [[🔍 Research Gaps & Justification]] (Gap 4) · Evaluated in [[🧪 Calibration & Testing Log]]

## Input
Either a **user-uploaded reference image** OR **user-specified color preferences/constraints** (e.g., a base color or mood).

## Approach 1 — Primary (implementable)
**K-means clustering → dominant colors → harmony rules → palette.**
1. Cluster input image pixels with **K-means** (k = number of dominant colors, e.g., 5).
2. Take cluster centroids as **dominant colors**.
3. Apply **color-harmony rules** to expand/refine into a coherent palette.
4. Output **hex + RGB** with **region→color assignments** (map palette to segmentation regions).

## Approach 2 — Stretch
Fine-tuned color-prediction model: **CLIP embeddings → color decoder** to suggest palettes from semantic prompts. Deferred to future work — not required to pass.

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

## Evaluation
- **Qualitative user rating (1–5)** for visual appeal + suitability.
- **≥ 5 evaluators** minimum (Risk R-11 mitigation via feedback loop).
- Also feeds **color reproduction accuracy** (RGB/HSV delta between recommended and applied) in [[🧪 Calibration & Testing Log]].

## Why This Is Defensible AI
> [!note]
> K-means is unsupervised learning; combined with rule-based harmony it is a legitimate **AI-adjacent recommendation system**. It is *implementable within budget/time*, directly addresses **Gap 4** (no cited painting robot generates harmonious palettes), and is honestly framed — not oversold as a neural net.

## Code Outline (pseudocode)
```python
def recommend(image, k=5, rule="complementary"):
    pixels = image.reshape(-1, 3)
    centroids = kmeans(pixels, k)          # dominant colors
    base = pick_dominant(centroids)        # most frequent cluster
    palette = apply_harmony(base, rule)    # HSV math
    return assign_to_regions(palette)      # region -> color map
```
