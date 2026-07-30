---
tags: [ai, color, recommendation]
created: 2026-03-29
updated: 2026-07-31
status: implemented
---
# 🎨 Color Recommendation Module

> [!info] Related
> [[🧠 AI & Software Design]] · [[🔍 Research Gaps & Justification]] (Gap 4) · [[🔌 Backend API & Web Integration]] · Evaluated in [[🧪 Calibration & Testing Log]]

> [!success] Implemented 2026-07-31 — see "Implementation as built" below
> Approach 1 is **built and running** as `POST /api/recommend-colors` (`backend/color_recommender.py`). One deliberate deviation from the plan below: clustering runs on the **non-wall regions only**, not the whole image.

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

---

# 🛠️ Implementation as built (2026-07-31)

`backend/color_recommender.py` · endpoint `POST /api/recommend-colors` · see [[🔌 Backend API & Web Integration]]

## Deviation from the plan: cluster the *room*, not the whole image

> [!important] This is the key design decision, and it is defensible in the manuscript
> The pseudocode above clusters **every pixel**. In practice the wall is usually the largest region in frame, so whole-image clustering returns *the wall's current paint* as the dominant colour — and the module would then recommend a colour harmonised against the colour we are about to paint over. Circular and useless.
>
> The segmentation mask fixes this: cluster only the **non-wall** pixels (floor, furniture, ceiling, fixtures). The recommendation is then harmonised against the room the wall has to live in.

This is also why `colorthief` was rejected as the library: it only accepts a whole file and has no concept of a mask. OpenCV k-means accepts an arbitrary pixel selection, which is exactly what a segmentation mask produces — **and it adds no new dependency.** The segmentation model is therefore load-bearing for colour recommendation, not just for path planning.

Fallback chain when the room is not readable: non-wall detections → everything outside the wall mask → whole frame (flagged in the response as `context_source`).

## Clustering in CIE-Lab, not RGB

k-means runs in **CIE-Lab**, where Euclidean distance approximates perceived colour difference, so clusters split the way a person would group them. RGB distance over-weights green and merges colours that look clearly different. Sampling is capped at 20,000 pixels with a fixed seed — the same photo must always yield the same palette, or the recommendation flickers between identical uploads.

## Harmony rules as implemented

Six outputs: one primary + five alternatives.

| Role | Rule | Verified |
|---|---|---|
| **Recommended** | Complementary — hue + 180° | exactly 180° across test cases |
| Analogous | hue + 32° | ✅ |
| Triadic | hue + 120° | ✅ |
| Neutral | room hue, saturation ≈ 0.06 | ✅ |
| Warm | anchored at 32° (amber) | ✅ |
| Cool | anchored at 212° (slate blue) | ✅ |

### Two corrections found during implementation

> [!warning] "Warm" was returning pink
> Interpolating from the room hue *toward* amber takes the **short path around the wheel**, which from a blue room passes through magenta — the "warm" swatch came back pink (`#DE85C3`). Warm and cool now **start at their anchor hue** and are only nudged ±18° by the room. The label has to be true.

> [!note] Saturation is clamped to an interior-paint band
> S ∈ [0.14, 0.40], V ∈ [0.74, 0.93]. A raw complementary hue at full saturation is unusable across a whole wall. The hue *relationship* is preserved; only the intensity is tamed. Neutrals use S ≈ 0.06.

## Colour naming

A curated 55-entry paint-name table, matched by nearest **Lab** distance, with names **de-duplicated within a palette** (two swatches showing different hexes under one label reads as a bug). Names are advisory only — the hex is authoritative.

## Manual overrides (not AI)

Users are not forced to accept the recommendation. Two fallbacks sit below it in the UI, clearly separated so it stays obvious which suggestions came from the model:

1. **Six fixed neutrals** — Pure White, Off White, Light Gray, Medium Gray, Charcoal, Matte Black. Hardcoded in the markup, not rendered from the API response, so they survive a backend failure — which is exactly when a fallback is needed.
2. **Custom colour picker** — a canvas HSV wheel + lightness slider + hex entry + system picker, all synced.

## Actual response shape

Supersedes the planned format above (`region_assignments` was never implemented — the frontend clips the preview using the mask polygons returned by `/api/segment` instead):

```json
{
  "recommended":   {"hex": "#E6D38A", "name": "Wheat",
                    "description": "why this works", "relationship": "complementary"},
  "alternatives":  [{"hex": "#A184DB", "name": "Violet Haze", "relationship": "analogous"}],
  "neutrals":      [{"hex": "#FFFFFF", "name": "Pure White"}],
  "dominant_color":{"hex": "#74736C", "name": "Slate Grey", "share": 0.24},
  "context_source":"non_wall_detections"
}
```

The `description` field states *why* the colour was chosen, naming the room's dominant colour. That explainability is what makes this defensible as a recommendation system rather than a lookup table — it matters for the ISO/IEC 25010 usability framing above.

## Verified on a real frame

Live webcam capture → dominant colour read as **Slate Grey `#74736C`** (24% of sampled non-wall pixels) → recommended **Dove Grey**, with Wheat / Seafoam / Soft Linen / Warm Beige / Powder Blue as alternatives. All plausible interior paint colours.

> [!bug] Do not test with the `test_result_*.jpg` gallery images
> Those are already-annotated exports with blue masks burnt in, so the module reads the **annotation colour** (`Slate Blue`) as the room's dominant colour. Always test with a plain room photo.

## Still open

- [ ] Evaluator study (n ≥ 5, 1–5 rating) — the ISO/IEC 25010 evaluation is **not yet run**
- [ ] Palette set is derived from one dominant colour only; multi-colour rooms use the largest cluster and ignore the rest
- [ ] Approach 2 (deep-learning recommender) remains deferred
