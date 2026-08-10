---
tags: [ai, color, recommendation]
created: 2026-03-29
updated: 2026-08-08
status: implemented
---
# 🎨 Color Recommendation Module

> [!info] Related
> [[🧠 AI & Software Design]] · [[🔍 Research Gaps & Justification]] (Gap 4) · [[🔌 Backend API & Web Integration]] · Evaluated in [[🧪 Calibration & Testing Log]]

> [!success] Implemented 2026-07-31 · revised to CIE LCh 2026-08-04 · reference image + demographic category 2026-08-08
> Approach 1 is **built and running** as `POST /api/recommend-colors` (`backend/color_recommender.py`). One deliberate deviation from the plan below: clustering runs on the **non-wall regions only**, not the whole image.
>
> The harmony maths was **rewritten from HSV/HSL to CIE LCh(ab) on 2026-08-04**. Sections dated 2026-07-31 below describe the superseded HSV build and are kept as record; the **LCh revision section is the current one**.
>
> The two panel-recommended inputs — an optional **reference image** and a **"for whom" demographic category** — shipped 2026-08-08; see § Reference Image + Demographic Category at the end of this note. Both act on the shared palette seed *before* harmony generation, so the LCh sections above still describe the maths accurately.

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
  "context_colors":[{"hex": "#EFEAE2", "name": "Soft Linen", "share": 0.62}],
  "context_source":"non_wall_detections",
  "context_pixel_ratio": 0.41,
  "seed_source":  "chromatic_pixels",

  "reference_used": false,
  "reference_weight": null,
  "reference_dominant_color": null,
  "category_applied": "none"
}
```

The last four landed 2026-08-08 with the reference-image / demographic feature. Every one of them exists so the UI can state **which optional inputs actually reached the palette** — `reference_used` is false whenever a reference was sent but dropped, `reference_weight` is `0.7` on a blend and `1.0` on the reference-only path, and `category_applied` reports the category that really ran rather than the one that was asked for. `seed_source` is one of `chromatic_pixels` · `neutral_room_fallback` · `reference_only` · `unavailable`.

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
| Lightness | **L\* 30–88** | below ~30 reads near-black under domestic lighting; above ~88 is indistinguishable from white and the hue relationship stops being visible |
| Chroma | **C\* 12–60** | below ~10 is grey; above ~60 is poster paint, oppressive over a whole wall |
| Neutral swatch | C\* ≈ 6 | exempt from the floor by design — forcing C\* ≥ 12 would make it a second analogous swatch |

> [!note] Widened 2026-08-08 — was L\* 30–70 / C\* 20–60
> See § Fix round (2026-08-08) below. The original band was set deliberately tight to kill washed-out and hyper-saturated failures first, and it did; it was also tighter than real emulsion, which the limitation callout below already said. Pastels were unreachable outright — a light pink `#F8C8DC` (L\* 85.2) clamped to `#CD9FB2`, a dusty mauve. That surfaced the first time a pastel reference image was tried, which is exactly the evidence the old note said would justify widening.

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

`recommended.relationship` can now also be `"warm-neutral"` in the no-usable-hue case, where it was previously always `"complementary"`. Since 2026-08-08 it is additionally `"reference-match"` whenever a reference image contributed to the seed — see § Fix round. So the full set is `complementary` (room only) · `reference-match` (reference contributed) · `warm-neutral` (no usable hue).

## Cost

100 ms/frame at 1280×720, up from 76 ms — two k-means passes (context + gated seed) instead of one. One pixel selection and one sRGB→Lab conversion are shared between the passes; without that sharing it measured 187 ms.

## Known limitation for the defence

> [!success] Resolved 2026-08-08 — the band was widened
> **This limitation is now historical; kept as the record of why, because it is a good defence answer.** The original band was L\* 30–70 / C\* 20–60. Measured against the module's own 55-entry paint-name table, **Soft Sage Green** (C\* 16.5) and **Slate Grey** (C\* 4.6) fell *below* the old C\* 20 floor and **Honey Gold** (L\* 74.6) *above* the old L\* 70 ceiling — so harmony generation could not reach muted sages or pale neutrals, some of the most common real wall colours. Pastels were unreachable entirely.
>
> The note said widening was a one-line change awaiting evidence. The evidence arrived on 2026-08-08 (§ Fix round, below): a pastel-pink reference image could not produce a pastel-pink recommendation, because L\* 70 clamped it to a dusty mauve. Band is now **L\* 30–88 / C\* 12–60**.
>
> **If asked at the defence:** the tight band was the right first move — it eliminated the washed-out and hyper-saturated failures, which were the loud ones — and it was then loosened against a specific reproducible failure rather than by taste. That is the tuning loop working, not a constant that was wrong.

---

## Still open

- [ ] Evaluator study (n ≥ 5, 1–5 rating) — the ISO/IEC 25010 evaluation is **not yet run**
- [ ] **Re-verify on a real room photo.** The LCh build has only been exercised on synthetic rooms and the annotated gallery images; the "Verified on a real frame" figures above are from the superseded HSV build. Blocked on the same `samples/` photo shoot as [[📐 Path Planning & G-code Generation]]
- [x] **Tune `PAINT_LIGHTNESS` / `PAINT_CHROMA`** — widened to L\* 30–88 / C\* 12–60 on 2026-08-08 against a reproducible pastel failure, see § Fix round. Re-check against evaluator feedback once the study runs
- [ ] Palette set is derived from one dominant colour only; multi-colour rooms use the largest cluster and ignore the rest. **Reference images are the exception** since 2026-08-08 — they pick by share × chroma instead, see § Fix round
- [ ] Approach 2 (deep-learning recommender) remains deferred

---

# ✅ Reference Image + Demographic Category (implemented 2026-08-08)

> [!success] Built and verified 2026-08-08 — same day as the panel recommendation
> Two new optional inputs to `POST /api/recommend-colors`, both **shipped**. Design decided and finalized 2026-08-08, implemented and verified against the loaded YOLOv8 model the same day. The sections below describe the **as-built** behaviour; the bias table and blend weighting are exactly what the code runs. See § As-built record at the end of this section for the file-by-file map and the two deviations. Full context: [[🎯 Post-Defense Recommendations & Action Items]].

## Input 1 — Reference image (second upload)

A **second, optional** image upload, separate from the existing room photo — what the user wants the room to look like (mood/style reference), not another view of the actual wall.

Runs the same `_sample_lab` → chromatic-gate → k-means pipeline already used for the room photo (§ Dominant-colour extraction, above) on the reference image to get its own dominant/seed colour — `mask=None`, since a mood shot has no wall of ours to segment and nothing to exclude. Built as `extract_reference_seed()`; returns `None` when the reference carries no usable hue, which is reported as `reference_used: false` rather than blended in.

## Input 2 — Demographic category ("for whom")

> [!success] Literature check — RRL addition warranted
> Real, citable research exists on color preference by age and gender for interior/residential spaces. Added to [[📚 Literature Review Master]] Theme 7 and [[📝 Chapter 2 - Review of Related Literature]] § 2.8b.

**Category list (full set, with gender splits):** `child_boy`, `child_girl`, `teen`, `adult_man`, `adult_woman`, `elderly`, `none` (default). Presented as a **fixed dropdown** in the UI — no free-text parsing, so there's no ambiguity to handle during a live demo. Built as the `CATEGORY_BIAS` dict, with each row's citation as an inline comment.

**Bias constants as built** — applied as deltas to `lightness` and `base_chroma` (pre-clamp, i.e. before `_clamp(..., *PAINT_LIGHTNESS)` / `_clamp(..., *PAINT_CHROMA)` inside `_paint_color`), plus a hue nudge added via `_shift_hue(base_hue, hue_nudge_deg)` — applied **once**, to the shared `lightness`/`base_chroma`/`base_hue` right after the blended seed is computed (Input 3, below) and before the six-swatch generation, so every swatch in the palette carries the same demographic lean consistently. This mirrors how `WARM_ANCHOR_DEG`/`COOL_ANCHOR_DEG` already work — same mechanism, category-keyed instead of a fixed anchor:

| Category | `lightness_delta` (L\*) | `chroma_delta` (C\*) | `hue_nudge_deg` | Basis |
|---|---|---|---|---|
| `child_boy` | **+8** | **+18** ⚠️ | **+12** (toward `WARM_ANCHOR_DEG`) | Hao et al. (2025) for the warm/bright direction and the boy > girl ordering. **Chroma magnitude is a design choice, not a finding** — see the callout below |
| `child_girl` | **+8** | **+6** ⚠️ | **+12** (toward `WARM_ANCHOR_DEG`) | As above; same warm/bright base, 12 C\* below boys — the *gap* is Hao-derived, the *level* is not |
| `teen` | **+4** | **+8** ⚠️ | **+6** (toward `WARM_ANCHOR_DEG`) | Jiang et al. (2020); Hao et al. (2025) — same direction as child, milder magnitude as age increases. Chroma lifted by half the children's raise to keep that age gradient monotonic |

> [!warning] The three young-occupant chroma values are NOT derived from the literature — know this before the defence
> Every other number in this table follows the direction of its citation. These three do not, and were **raised on 2026-08-08 as a deliberate judgement call** (chroma only; lightness and hue are untouched).
>
> **What Hao et al. actually reported:** children preferring HSV **S ≈ 25/100** at V ≈ 75/100, warm hues. Converted into the units this module works in, that target is roughly **L\* 72 / C\* 20**. Even *before* the raise the module was producing C\* ≈ 33 for a child's room — already ~60% above the cited value. It is now higher still.
>
> **The reasoning for overriding it:** Hao et al. measured preference for a *backdrop* in a paediatric-furniture context. A child's room reads vivid because of toys, bedding and wall decals; the wall itself is the quiet surface in that study. The judgement is that a moderate-low backdrop reads as flat for a children's bedroom wall in this application. That is a defensible position — it is **not** a finding.
>
> **What to say if asked "why these numbers?":** the *direction* (warmer, brighter, boys more saturated than girls, decreasing with age) is cited and holds; the *magnitude* on these three rows is ours and the evaluator study is what settles it. Do not claim Hao et al. supports the level. Same honesty pattern as the L\*/C\* band.
| `adult_man` | **0** | **+8** | **−10** (toward `COOL_ANCHOR_DEG`) | Bogicevic et al. (2018): men prefer "masculine" (cooler, more saturated) schemes |
| `adult_woman` | **0** | **0** | **0** | Bogicevic et al. (2018): women equally satisfied with masculine or feminine schemes — no directional bias is evidence-backed, so this is intentionally a no-op |
| `elderly` | **+6** | **−10** | **+10** (toward `WARM_ANCHOR_DEG`) | Li et al. (2022); Rapuano et al. (2023). Torres et al. (2020) complicates this (warm for activity rooms, cool for bedrooms) — AURA has no room-type context yet, so this defaults to the general/bedroom-leaning finding; documented as a known limitation, same honesty pattern as the L\*/C\* band note above |
| `none` (default) | 0 | 0 | 0 | Current behaviour, unchanged |

> [!note] These are starting values, not proven-optimal
> Same status as `PAINT_LIGHTNESS`/`PAINT_CHROMA` today — defensible, cited starting points, explicitly a tuning target for the evaluator study (§ Still open, above) rather than a claim of precision. State this plainly if asked at defense.

## Input 3 — Blend weighting (reference image vs. room photo)

**70/30, reference-dominant** — the constant `REFERENCE_SEED_WEIGHT = 0.7`. The reference image's extracted seed carries 70% weight, the room photo's gated seed carries 30%, blended in LCh space before category bias or harmony rules run:
- `lightness` and `chroma`: weighted linear average (`0.7 * ref + 0.3 * room`).
- `hue`: weighted **circular** mean (hue is an angle — a plain average breaks near the 0°/360° wrap, e.g. blending 350° and 10° must land near 0°, not 180°). Use a vector-sum circular mean weighted 0.7/0.3, not a plain arithmetic average.

If no reference image is supplied, behaviour is unchanged — 100% room-photo seed, exactly as today.

## Composing all three inputs

Order of operations inside `recommend_colors()` → `build_palette()`:
1. Compute the room photo's gated seed (existing behaviour).
2. If a reference image was supplied, compute its gated seed the same way, then blend 70/30 (reference/room) per Input 3 above.
3. Apply the category bias deltas (Input 2 table) to the blended `lightness`/`base_chroma`/`base_hue`.
4. Run the existing harmony generation (recommended + five alternatives) unchanged, off the now-adjusted seed.

Response reports `reference_used` (bool), `reference_dominant_color` (the reference image's own extracted dominant colour, same shape as `dominant_color`, `null` when unused), and `category_applied` — the category that **actually** ran, not the one that was asked for, so an unrecognised value cannot make the response claim a bias that never happened. Same transparency principle as the rest of this module's explainability design (§ Actual response shape, above).

`dominant_color` deliberately stays the **room's** colour even when a reference is blended in — that field answers "what colour is this room", which a reference image does not change. The blend is reported separately.

> [!warning] Known limitation to state up front
> This is a small, specific literature set (largely hotel rooms, nursing homes, Dutch/Chinese residential surveys, a pediatric clinic furniture study) being generalised to "wall colour for a home room," and the bias constants are hand-derived from directional findings, not fit to data. Reasonable for an undergrad thesis, not a perfect match — flag it in Chapter 5 the same way the L\*/C\* band is already flagged.

## As-built record (2026-08-08)

**`backend/color_recommender.py`**

| Added | What it does |
|---|---|
| `CATEGORY_BIAS` | The seven-row table above, each row carrying its citation as an inline comment |
| `REFERENCE_SEED_WEIGHT` | The reference/room split — 0.6 at first, **raised to 0.7 on 2026-08-08**, see § Third fix round |
| `SEED_ORIGIN_PHRASES` | Three openings for the rationale sentence — see Deviation 2 below |
| `_circular_mean_hue()` | Weighted vector-sum circular mean, closes the last open implementation detail |
| `extract_reference_seed()` | `_sample_lab(frame, None)` → `_gate_lab` → `_cluster_lab`, first cluster or `None` |
| `_blend_seeds()` | L\*/C\* weighted average, hue circular; result gamut-mapped through `_lch_to_rgb` and read back so the seed is always displayable. Carries no `share` — a blend of two images has no single area share, and inventing one would put a false percentage in the UI |
| `build_palette(…, category, seed_origin)` | Bias applied **once**, after `base_chroma` and before the harmony block |
| `recommend_colors(…, reference_frame_bgr, category)` | Blends when a reference is usable; adds the three new response fields on every return path |

Harmony generation (complementary/analogous/triadic/neutral/warm/cool) was **not touched in this first pass** — both new inputs acted on the shared seed upstream of it, exactly as § Composing all three inputs specifies. That turned out to be the bug: see § Fix round below, where the *recommended* swatch's rotation became conditional on where the seed came from. The five alternatives are still untouched.

**`backend/app.py`** — optional `reference_image` multipart field (decoded via the existing `decode_upload`) and a `category` form field validated against `CATEGORY_BIAS` by a new `normalize_category()`. Unknown category → logged warning, downgraded to `none`. Undecodable reference → logged warning, dropped. Neither can fail the request. One safety fix: `frame_from_request()`'s "any file" last resort now skips `reference_image`, so a request carrying only a reference can't get the mood shot segmented as if it were the room (it 400s instead, as it should).

**`website/color-recommendation.html`** — secondary reference upload with a thumbnail and Remove link, the seven-option dropdown, both in a `.tuning-section` below the main drop-zone so the required room photo keeps visual priority. `contextNote` now reports which optional inputs actually reached the palette (e.g. *"…· blended with your reference image (Brick Red, #BE3B5A) at 70% · tuned for a boy's room."*, with the percentage read from the response rather than hardcoded — see § Third fix round), with distinct wording for reference-dropped and reference-only. Changing either input re-runs the palette on the stored room frame rather than leaving a stale one on screen.

**`backend/README.md`** — both optional fields and the three new response keys documented.

### Two deviations from the spec above

1. **Reference-only fallback (new behaviour, not in the spec).** If the room photo yields no readable seed *and* a reference does, the palette is built from the reference alone (`seed_source: "reference_only"`) instead of falling back to the hardcoded warm neutral. The spec covers "no reference" and "no usable reference" but not "no usable room"; discarding an input the user explicitly gave seemed the worse default. Easy to revert if the panel or the write-up wants strict spec behaviour.
2. **Rationale wording follows the seed.** The recommended swatch's `description` used to open with a hardcoded *"The room's dominant colour reads as…"*, which stops being true the moment a reference is blended in. It now varies by seed origin (room / blend / reference-only). Consistent with this module's standing rule that the explanation must name what the suggestion was actually built from.

### Verified 2026-08-08

Against the loaded model (`best.pt`, RTX 3050), via the Flask test client:
- All seven categories produce distinct palettes; `adult_woman` is byte-identical to `none`, as the evidence-backed no-op intends.
- Blending shifts the recommendation while `dominant_color` stays the room's.
- Unknown category → `category_applied: "none"` + warning, HTTP 200.
- Corrupt reference file → dropped, request succeeds, output identical to no-reference.
- All-white reference (no chromatic content) → `reference_used: false`, output identical to no-reference.
- Reference-only path exercised on an unreadable room frame.

> [!warning] Not yet done
> Only exercised on **synthetic** room frames, same gap as the LCh build itself (§ Still open, above). Real-photo verification is blocked on the same `samples/` shoot. The bias constants have **not** been eyeballed against real generated palettes yet — that is the first thing to do once real photos exist, and the evaluator study is what should actually tune them.

## Fix round (2026-08-08, same day) — first real reference image failed

**Symptom.** A pink Hello Kitty children's-room reference + `child_girl` returned muted blues, olives and greys. Nothing in the palette resembled the reference.

**Three compounding causes, all reproduced in code before changing anything:**

| # | Cause | Evidence |
|---|---|---|
| 1 | **Reference seed picked by area, not salience.** `extract_reference_seed` took the largest gated cluster. In that image the wood bed frame and warm mid-tones out-voted the pink **55% / 45%**, so the seed came back `#C08A5A Warm Terracotta` | A mood board's backdrop almost always beats its accent on pixel count; the accent is the whole point of the image |
| 2 | **The recommendation was the seed's complement — structurally.** Even handed a perfect pink seed `#E4477E` (hue 3.7°), the module returned `#00A9A8 Muted Teal` (hue 183.7°). **A pink reference could never produce pink** | The room photo answers "what must this wall contrast with?"; a reference answers "what do I want this to look like?". Blending both into one seed and then rotating 180° turned the user's stated intent into the one hue guaranteed absent |
| 3 | **The paint band forbade pastels.** L\* ceiling 70 clamped a light pink `#F8C8DC` (L\* 85.2) to `#CD9FB2`, a dusty mauve. `child_girl`'s `chroma_delta: −6` compounded it | See the resolved limitation callout above |
| 4 | **The blend averaged a hue that wasn't one.** A neutral room reaches `_blend_seeds` via the `neutral_room_fallback` path carrying a centroid whose hue is sensor noise. The circular mean weighted that noise at 40% regardless. Measured on a grey room — centroid `#D0CDCD`, **C\* 1.1**, nominal "hue" 19.5° — the pink was dragged **33° toward amber**, i.e. into salmon, by an angle that was not a colour at all | The module gates meaningless hues per-pixel (`_chromatic_gate`) and per-centroid (`hue_is_meaningful`); the blend was the one place that skipped the check it states as a founding principle |

**Fixes, in order of impact.** Cause 2 was a design error in how the feature was composed, not a tuning miss — the reference was fed into the seed slot built to answer the opposite question.

1. **`seed_origin` now drives harmony, not just wording.** When the seed follows a reference (`blend` / `reference`), the recommended swatch sits **on** the blended hue with `relationship: "reference-match"` instead of rotating 180°. Room-only mode keeps `complementary` untouched — still correct when the seed describes furniture the wall must stand apart from. The five alternatives still fan out around the hue, so contrast is one click away.
2. **Reference seeds selected by `share × chroma`**, with a 5% share floor (`MIN_REFERENCE_CLUSTER_SHARE`) so a specular highlight or JPEG artefact can't define a palette. Room seeds still select by area — different question, deliberately different estimator.
3. **Band widened** to L\* 30–88 / C\* 12–60.
4. **`_blend_seeds` now only averages hues that mean something.** If the room seed's chroma is below `SEED_MIN_CHROMA` the hue comes from the reference alone; L\* and C\* still blend at `REFERENCE_SEED_WEIGHT` as specified. Symmetric in the other direction for robustness. This does **not** weaken the blend — a room with a genuine hue still pulls the reference exactly as before, verified by regression.

**Result on the same inputs**, through the live endpoint with real segmentation, grey room + pink reference:

| Category | Before | After |
|---|---|---|
| `none` | muted blue | `#E2849D` Orchid Blush — hue **3.6°**, the reference's own pink |
| `child_girl` | muted blue/grey | `#F29FA7` Dusty Rose — L\* 73.8, hue 15.2°, a genuine light pink |

L\* 73.8 is a lightness the old band would have clamped to 70.

> [!note] Residual — and it is now legitimate
> A room with a **real** hue still pulls the reference's hue toward it (70/30 since § Third fix round; this was measured at 60/40), and `child_girl`'s `hue_nudge_deg: +12` still adds ~12° toward `WARM_ANCHOR_DEG`. On a strongly warm-toned room those compose to move pink noticeably toward salmon. Both are the finalized spec behaving as designed, and both are now acting on real colour information rather than on noise — so this is a tuning question, not a bug.
>
> **Open decision if it proves annoying in practice:** damp the category's hue nudge when a reference image supplies the hue, on the principle that *explicit intent should override inferred preference* — the demographic bias exists to fill in a preference the user has not stated, and the L\*/C\* deltas would still apply. Not implemented; it changes a panel-facing constant Kurt finalized, so it is his call.

**Regression-checked** across 28 room × reference × category combinations: all 7 categories on the no-reference path still return `complementary`; an unusable reference still reports `reference_used: false` and produces output byte-identical to no-reference; reference-only and nothing-readable paths intact; a room with a genuine hue still contributes to the blend (fix 4 does not silently disable blending); no swatch escapes the widened band; palette name de-duplication holds.

---

# 🎨 Second fix round (2026-08-08) — child saturation raised

**Trigger.** Kurt's read that a children's palette looked undersaturated. Checked against the citation first, which said the opposite: Hao et al.'s HSV S ≈ 25/100 converts to **C\* ≈ 20**, and the module was already at **C\* ≈ 33**. Kurt's call was to raise anyway as a design decision — recorded, with the citation link explicitly broken for those rows (see the ⚠️ callout in the bias table above).

**Changed:** `child_boy` chroma +6 → **+18**, `child_girl` −6 → **+6**, `teen` +2 → **+8**. Lightness and hue deltas untouched. Both child rows lifted by a uniform +12, so the 12-point boy > girl gap — the part Hao et al. actually supports — is preserved exactly.

## The bug this exposed: the gender split was silently collapsing

Chasing the raise surfaced a real defect. `child_boy` and `child_girl` were rendering **the same hex**:

```
child_boy   asks L* 78, C* 44  ->  #FFA9B7
child_girl  asks L* 78, C* 32  ->  #FCABB8     12 C* apart, visually identical
```

At L\* 78 and a pink hue, sRGB's ceiling is **C\* 32.9**, so both clipped to the same wall. `_lch_to_rgb` resolves an unreachable coordinate by holding L\* and cutting C\* — correct in general, but it destroys any distinction that lives in chroma alone. The gender split, the most panel-sensitive part of this feature, vanished exactly in the pastel region where children's palettes live.

> [!bug] Self-inflicted, earlier the same day
> Widening `PAINT_LIGHTNESS` to L\* 88 (first fix round) is what let the `+8` child lightness delta actually take effect and walk these rows into the gamut wall. At the old L\* 70 ceiling there was headroom — max C\* ≈ 48, both fit. A band change that looked purely additive had a second-order effect on a different feature.

**Fix — `_fit_lightness_for_chroma`:** when the gamut cannot give both, spend lightness (bounded by `CHROMA_LIGHTNESS_GIVEBACK = 12`) to buy the chroma that was asked for, instead of cutting chroma at fixed lightness. Two invariants, both learned by breaking them first:

1. **Never pay lightness without gaining chroma.** A bisection assuming available-chroma is monotonic in lightness returned the floor at hues where no trade exists — costing the plain room palettes 12 points of lightness for nothing. Replaced with a scan; available chroma peaks at a different L\* for every hue.
2. **A larger chroma request must never produce a smaller result.** Falling back to "no trade at all" broke this: `child_girl` (asking +6) found a fitting lightness and rendered C\* 44.7, while `child_boy` (asking +18) found none, stayed put and clipped to C\* 32.6 — the more saturated category came out less saturated. Now the target is capped at the best the range can deliver, which restores monotonicity. Verified across 24 hues × 5 request levels: zero violations.

**Result**, grey room + pink reference:

| Category | Before this round | After |
|---|---|---|
| `child_girl` | `#FFACB3` C\* 32.6 | `#FF909C` **C\* 44.7** |
| `child_boy` | `#FFACB3` C\* 32.6 (identical) | `#FF7689` **C\* 55.9** (distinct) |

Plain no-reference palettes are byte-identical to before — `none` still `#0086AF`, L\* 52.0, C\* 33.9. The trade only engages where the gamut actually binds.

> [!warning] Residual — boy/girl still collapse at cyan-blue (hues ~200–230)
> At hue 210 sRGB's ceiling is **C\* 42.1 at L\* 78 and *lower* at every darker lightness** (39.4 at L\* 72, 34.1 at L\* 60, 20.6 at L\* 30). Both child requests — 44 and 56 — sit above that ceiling at every lightness in the band, so they render identically and the give-back correctly declines to trade.
>
> This is a genuine sRGB limit, not a code fault: **a light, highly saturated cyan-blue is not a colour that exists on a screen or in emulsion.** It bites the no-reference path on warm rooms, whose complement lands in exactly that hue range. Raising the child chroma made it more likely, since both values now sit further above the ceiling. Lowering child chroma toward the cited C\* ≈ 20 would eliminate it; that trade-off is on the table if the evaluator study says the palettes read garish.

**Regression-checked:** 28 room × reference × category combinations — no swatch out of band, no duplicate names, no-reference path still complementary for all 7 categories, unusable reference still byte-identical to no-reference, neutral swatch keeps its lightness (exempt from the chroma trade by design).

---

# ⚖️ Third fix round (2026-08-08) — blend raised to 70/30

**Trigger.** Kurt: *"I don't see the point of the reference image if it doesn't actually get quite referenced."* `REFERENCE_SEED_WEIGHT` 0.6 → **0.7**.

**Measured effect** on a warm-toned room against a pink reference (hue 3.7°) — this is the only case where the weight moves the hue at all:

| Weight | Result | Hue | Drift from the reference |
|---|---|---|---|
| 0.5 | `#CE5C4F` | 33.8° | +30.1° |
| 0.6 (was) | `#D45758` | 26.7° | +23.0° |
| **0.7 (now)** | `#D95261` | **20.2°** | **+16.5°** |
| 0.8 | `#DE4E6A` | 14.7° | +11.0° |

> [!note] The weight does less than it looks like on neutral rooms — and that is correct
> Since the meaningful-hue check went into `_blend_seeds` (§ Fix round, cause 4), a room with no real hue contributes **none** of the blended hue regardless of this constant — the reference already supplies 100%. On those rooms `REFERENCE_SEED_WEIGHT` governs `L*` and `C*` only. So this change is felt on rooms that have a strong colour of their own, which is exactly where the complaint came from.

**Also fixed: the UI was hardcoding "60%" in three places.** Changing the constant alone would have left the page stating a number the backend no longer used. The response now carries `reference_weight` and the page renders that:

- `reference_weight` is `REFERENCE_SEED_WEIGHT` on a blend, **`1.0` on the reference-only path** (there was no room seed to blend against — reporting 0.7 there would be a lie the UI repeats), and `null` when no reference was used.
- The pre-upload hint no longer quotes a figure at all. The only place the page states a percentage is where it is describing a result it actually received.

**Regression-checked:** 28 room × reference × category combinations; no-reference path unchanged and still complementary for all 7 categories; unusable reference still byte-identical to no-reference with `reference_weight: null`; reference-only correctly reports 1.0.

---

# 🧾 Post-commit audit (2026-08-08)

Swept for anything the day's three fix rounds broke or left behind. `/api/recommend-colors` has **no other consumers** — nothing outside `color_recommender.py` calls `build_palette` / `recommend_colors` / `_paint_color`, and `color-recommendation.html` is the only page that hits the endpoint — so the response and constant changes could not have reached another subsystem. Two real defects found, both fixed:

**1. The palette stopped reading as one family.** The five alternatives used hardcoded lightnesses (58 / 55 / 68 / 60 / 56) chosen for the old L\* 30–70 band. Once the band reached 88, a pastel recommendation shipped with alternatives 8–13 L\* darker than it:

```
recommended  #FE8090  L* 68.4
analogous    #CA7557  L* 58.0   -10.4
triadic      #5F9051  L* 55.0   -13.4
cool         #5187D5  L* 56.0   -12.4
```

Another second-order effect of widening the band. Now `ALTERNATIVE_LIGHTNESS_OFFSETS`, expressed relative to the recommendation's own lightness. The values are the old absolutes minus 52 — the seed lightness they were originally chosen around — so a mid-range room reproduces the previous spread almost exactly (57.8 / 55.0 / 67.8 / 59.9 / 55.7) while a pastel one now travels with it.

**2. No test coverage at all.** Every check across three fix rounds was a throwaway script. Two regressions that day — a lightness give-back that paid for nothing, and a chroma request that came back *smaller* when asked to be larger — would have been caught instantly by a standing test. Added `backend/tools/test_color_recommender.py`: 11 invariant checks, no model or server needed, same standalone shape as `test_toolpath.py`.

The checks assert **properties, not golden hexes** — deliberately. The constants here are an explicit tuning target for the evaluator study, so a test pinning exact colours would fail on every legitimate re-tune and end up deleted rather than fixed. These should survive re-tuning: band containment, unique names, determinism, graceful degradation, relationship semantics, salient reference seed, neutral rooms not dragging hue, chroma monotonic in request, lightness never spent without gain, demographic categories staying distinct, palette lightness coherence.

> [!note] The guards were verified to actually fire
> Each of the day's fixes was reverted in memory to confirm its check fails without it. That exposed a gap worth recording: the **monotonicity** check does *not* catch plain clipping, because clipping is monotonic — it just flattens everything above the ceiling onto one value. That is exactly how `child_boy` and `child_girl` came to render the same hex. A separate `demographic categories stay distinct` check now covers it, asserted at a pink hue where the split is renderable and deliberately **not** at cyan-blue, where it genuinely is not.

## Still open (this feature)
- [ ] **Evaluator study should specifically rate the child palettes** — they are now the least evidence-backed values in the module, by explicit choice
- [ ] **Decide on the hue-nudge/reference interaction** — see the residual warning above
- [ ] Eyeball the seven categories against **real** room photos and adjust the constants — same tuning status as `PAINT_LIGHTNESS`/`PAINT_CHROMA`
- [ ] Fold the demographic categories into the evaluator study design (n ≥ 5) so the constants get evidence, not just eyeballing
- [ ] Update Chapter 2 § 2.8b in the actual manuscript — the feature has now shipped, so the RRL addition is no longer premature
