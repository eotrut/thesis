---
tags: [ai, color, recommendation]
created: 2026-03-29
updated: 2026-08-04
status: implemented
---
# 🎨 Color Recommendation Module

> [!info] Related
> [[🧠 AI & Software Design]] · [[🔍 Research Gaps & Justification]] (Gap 4) · [[🔌 Backend API & Web Integration]] · Evaluated in [[🧪 Calibration & Testing Log]]

> [!success] Implemented 2026-07-31 · revised to CIE LCh 2026-08-04
> Approach 1 is **built and running** as `POST /api/recommend-colors` (`backend/color_recommender.py`). One deliberate deviation from the plan below: clustering runs on the **non-wall regions only**, not the whole image.
>
> The harmony maths was **rewritten from HSV/HSL to CIE LCh(ab) on 2026-08-04**. Sections dated 2026-07-31 below describe the superseded HSV build and are kept as record; the **LCh revision section is the current one**.

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

> [!warning] Superseded — this table specifies HSV hue
> The built module computes these angles in **CIE LCh(ab) hue**, not HSV. The rule *names* and the *angles* are unchanged; the space they are measured in is not. See the LCh revision section.

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

> [!bug] The determinism claim above was false until 2026-08-04
> The fixed seed covered only the **pixel sampling**. `cv2.kmeans` seeded its own initialisation separately, so identical uploads could still return different palettes. See the LCh revision section. Lab clustering itself was correct and is unchanged — it now runs on true CIE Lab rather than OpenCV's rescaled 8-bit encoding, so it shares units with the L\*/C\* constraints.

## Harmony rules as implemented (HSV — superseded 2026-08-04)

Six outputs: one primary + five alternatives. **Angles below are HSV and no longer current** — see the LCh revision section for the shipping values.

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

> [!note] Saturation is clamped to an interior-paint band — *superseded 2026-08-04*
> S ∈ [0.14, 0.40], V ∈ [0.74, 0.93]. A raw complementary hue at full saturation is unusable across a whole wall. The hue *relationship* is preserved; only the intensity is tamed. Neutrals use S ≈ 0.06.
>
> **Replaced by the L\* 30–70 / C\* 20–60 band.** The principle survives; the units changed, and clamping in LCh no longer disturbs the hue it is applied to.

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

## Verified on a real frame (HSV build — figures superseded)

Live webcam capture → dominant colour read as **Slate Grey `#74736C`** (24% of sampled non-wall pixels) → recommended **Dove Grey**, with Wheat / Seafoam / Soft Linen / Warm Beige / Powder Blue as alternatives. All plausible interior paint colours.

> [!warning] Do not cite these hexes
> They are from the HSV build **and** predate the determinism fix, so they are not reproducible even on that build. The LCh version has not yet been run on a real room photo — see Still open.

> [!bug] Do not test with the `test_result_*.jpg` gallery images
> Those are already-annotated exports with blue masks burnt in, so the module reads the **annotation colour** (`Slate Blue`) as the room's dominant colour. Always test with a plain room photo.

---

# 🎨 LCh revision (2026-08-04) — current implementation

Motivation: palette quality was **inconsistent** — the same kind of room sometimes produced a coherent palette and sometimes did not. Three causes were found, two of them bugs rather than colour-theory problems.

## 1. Harmony now computed in CIE LCh(ab), not HSV

New dependency: **`colour-science==0.4.7`**. Conversions run sRGB → XYZ → Lab → LCh(ab) in floating-point CIE units.

> [!important] Why HSV was the wrong space — the defensible version of this argument
> HSV hue is a formula over sRGB max/min channels. It encodes no model of human vision, so equal hue steps are perceptually uneven: the 60° from red to yellow crosses far less apparent colour change than the 60° from cyan to blue. HSV "lightness" is not lightness either — at S=1, V=0.5 a yellow is bright and a blue is dark.
>
> Two consequences showed up directly in the palettes: a "complementary" pair generated at HSV hue +180° was often **not the visual opposite**, and swatches nominally sharing a V looked **unequal in weight**.
>
> **CIE LCh(ab)** is the cylindrical form of CIE L\*a\*b\* — the same space with the a\*/b\* plane in polar coordinates. L\* is perceptual lightness (0–100), C\* is chroma (colourfulness), h is hue angle. Because Lab is approximately perceptually uniform, a rotation in `h` is a rotation on a wheel that matches what an observer sees, so +180° really is the visual complement and +120° really does divide the wheel in thirds.

> [!note] Why `colour-science` and not `cv2.cvtColor(…, COLOR_BGR2LAB)`
> OpenCV's 8-bit Lab is quantised **and rescaled** — L\* is stored 0–255 and a\*/b\* are offset by 128. Those are not CIE units, so the L\*/C\* limits below would not mean what they say. `colour-science` works in true CIE units under D65, the illuminant sRGB is defined against. It added **no transitive dependencies** to the venv.

### Shipping harmony angles (LCh hue)

| Role | Rule (LCh hue) | Verified |
|---|---|---|
| **Recommended** | Complementary — h + 180° | ✅ within 0.5° across the full hue circle |
| Analogous | h + 30° | ✅ |
| Triadic | h + 120° | ✅ |
| Neutral | room hue at C\* ≈ 6 | ✅ |
| Warm | anchored at **h 48°** (amber/terracotta) | ✅ |
| Cool | anchored at **h 267°** (slate blue) | ✅ |

Warm/cool anchors were **re-measured in LCh** from the paint colours they are named for — Warm Terracotta `#C97B5F` → h 45.7°, Steel Blue `#6C87A8` → h 266.5°. The old HSV anchors (32° / 212°) are meaningless in this space. The ±18° "start at the anchor, nudge by the room" correction from 2026-07-31 is preserved.

## 2. Output constrained by L\* and C\*, not saturation/value

Replaces the HSV band (S 0.14–0.40, V 0.74–0.93):

| Constraint | Value | Reason |
|---|---|---|
| Lightness | **L\* 30–70** | below ~30 reads near-black under domestic lighting; above ~70 washes out and the hue relationship stops being visible |
| Chroma | **C\* 20–60** | below ~10 is grey; above ~60 is poster paint, oppressive over a whole wall |
| Neutral swatch | C\* ≈ 6 | exempt from the floor by design — forcing C\* ≥ 20 would make it a second analogous swatch |

Clamping only ever moves a colour along L\* and C\*. **The hue angle passes through untouched**, so the harmony relationship survives the constraint step intact — which is precisely what HSV could not do without disturbing the hue it had just computed.

> [!important] Gamut mapping — necessary, not optional
> The L\*/C\* band is a **box**; the sRGB gamut is a lumpy solid. How much chroma a hue can carry depends on both hue and lightness (sRGB reaches C\* > 100 for yellow near L\* 97 but barely 40 for the same hue at L\* 40), so a coordinate can sit inside the band and still be **unreachable by any display or paint**.
>
> Clipping the out-of-range RGB channels is the easy fix and the wrong one: clipping moves the colour across the a\*/b\* plane, so the hue shifts and a "complement" stops being opposite the seed. Instead the module holds **L\* and h fixed** and binary-searches the largest displayable chroma (C\* = 0 is grey and always in gamut, so the search always terminates). Without this step the L\*/C\* constraint would have silently undone the LCh harmony.

Verified: **0 band violations and 0 complement-angle failures** across all six swatches swept over the full hue circle at three seed lightnesses.

## 3. Seed pixels gated before k-means

Rooms are mostly neutral — white ceilings, grey floors, black shadow, blown highlights on gloss. Those pixels have **no meaningful hue** (a near-white pixel's hue angle is sensor noise amplified by the polar conversion) but they are numerous, so k-means on the raw region returns a near-neutral centroid and every harmony rotation applied to it is arbitrary.

Pixels are now dropped before clustering when **L\* > 85** (near-white), **L\* < 15** (near-black), or **C\* < 10** (on the neutral axis).

Measured on a synthetic room, 92% white wall/ceiling + 8% terracotta sofa:

| Pass | Seed returned | C\* |
|---|---|---|
| Ungated (old behaviour) | `#F2F2ED` Chalk White | 2.6 — hue is noise |
| Gated (current) | `#B3684B` Copper Clay | 39.9 — the sofa |

`context_colors` in the API response still reports the **unfiltered** area breakdown — "70% of this room is off-white" is true and worth showing the user. Only the palette *seed* uses the gated pass. A new `seed_source` field reports which path ran: `chromatic_pixels`, `neutral_room_fallback`, or `unavailable`.

## Two bugs found during the rewrite

> [!bug] The module was non-deterministic — likely the main cause of the inconsistency
> `cv2.kmeans` draws its k-means++ initial centres from **OpenCV's own global RNG**, which the fixed *sampling* seed never covered. The same photo uploaded twice could land on different centroids and return a visibly different palette — on structured input, not just noise. This directly contradicted the module's own design claim about not flickering between identical uploads.
>
> Fixed with `cv2.setRNGSeed(0)` per call. Re-runs are now byte-identical. **Any palette screenshot taken before 2026-08-04 is not reproducible** — regenerate anything used as a figure.

> [!bug] Neutral rooms recommended a cold blue while claiming to be warm
> When the seed had no usable hue the code fell back to the warm anchor and then **took its complement**, landing on slate blue — while printing "This is a soft warm tone" alongside it. Present in the original build too. The fallback now sits *on* the anchor and is labelled `warm-neutral` rather than `complementary`.

## Response shape — additions

The 2026-07-31 shape is unchanged and the frontend needed no edits. One field added:

```json
"seed_source": "chromatic_pixels"
```

`recommended.relationship` can now also be `"warm-neutral"` in the no-usable-hue case, where it was previously always `"complementary"`.

## Cost

100 ms/frame at 1280×720, up from 76 ms — two k-means passes (context + gated seed) instead of one. One pixel selection and one sRGB→Lab conversion are shared between the passes; without that sharing it measured 187 ms.

## Known limitation for the defence

> [!warning] The L\*/C\* band is narrower than real interior paint
> Measured against the module's own 55-entry paint-name table: **Soft Sage Green** (C\* 16.5) and **Slate Grey** (C\* 4.6) fall *below* the C\* 20 floor, and **Honey Gold** (L\* 74.6) sits *above* the L\* 70 ceiling. So harmony generation can no longer reach muted sages or pale neutrals — some of the most common real wall colours.
>
> Those remain reachable through the six fixed neutral chips and the custom picker, so the user is not blocked. Both limits are single named constants (`PAINT_LIGHTNESS`, `PAINT_CHROMA`) and widening is a one-line change if the evaluator study says the palettes read too dark or too saturated. **Expect a panel question here** — the honest answer is that the band was set deliberately tight to eliminate the washed-out and hyper-saturated failures first, and is a tuning parameter the evaluation is meant to inform.

---

## Still open

- [ ] Evaluator study (n ≥ 5, 1–5 rating) — the ISO/IEC 25010 evaluation is **not yet run**
- [ ] **Re-verify on a real room photo.** The LCh build has only been exercised on synthetic rooms and the annotated gallery images; the "Verified on a real frame" figures above are from the superseded HSV build. Blocked on the same `samples/` photo shoot as [[📐 Path Planning & G-code Generation]]
- [ ] **Tune `PAINT_LIGHTNESS` / `PAINT_CHROMA`** against evaluator feedback (see limitation above)
- [ ] Palette set is derived from one dominant colour only; multi-colour rooms use the largest cluster and ignore the rest
- [ ] Approach 2 (deep-learning recommender) remains deferred
