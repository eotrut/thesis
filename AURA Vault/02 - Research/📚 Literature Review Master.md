---
tags: [research, literature-review, synthesis]
created: 2026-03-29
updated: 2026-08-08
status: synced-with-manuscript
---
# 📚 Literature Review Master

> [!info] Purpose
> A *thematic synthesis* of the literature — not a list of summaries. Feeds directly into [[📝 Chapter 2 - Review of Related Literature]]. Individual paper notes for the original 10 references live in `02 - Research/References/`; the ~70 additional citations added in the 2026-07 RRL expansion (occupational-health, HRC/safety, CNC-hardware, and expanded AI/color-recommendation literature) are tracked here and in the manuscript's References list, not yet as individual atomic notes. Gaps are consolidated in [[🔍 Research Gaps & Justification]].

## Theme 0 — Occupational Hazards and the Case for Automation (new, 2026-07)
Sekhar et al. (2024), Arrandale et al. (2025), Boadu et al. (2023), Patel et al. (2024), and Bello et al. (2020) collectively quantify the health burden of manual painting — elevated respiratory disease odds, carcinogen/sensitizer exposure, and biomonitoring evidence of inadequate exposure control even where PPE is used. NIOSH (2024) frames construction robotics as displacing workers from the most hazardous tasks. Philippine obligations: DOLE DO-13 s.1998, RA 11058.
**Why this matters for AURA:** establishes the safety motivation independent of the productivity argument — automation is framed as a public-health intervention, not just an efficiency gain.

## Theme 1 — Mechanical Wall Painting Automation
[[Kumote 2022 - Auto Wall Painting Robot]] and [[Patil 2021 - Autonomous Wall Painting Robot]] demonstrate XY-based platforms driven by pre-programmed motion; Megalingam et al. (2020) adds an earlier mecanum-wheeled/cascade-lift variant; Sowmya et al. (2024) lowers the cost floor further. Rudzuan (2019) extends to a gantry spray system; [[Tawade 2024 - XY Gantry Material Handling]] validates the XY-gantry kinematics AURA reuses. Thale et al. (2022) and Shamseldin (2024) push into higher-stakes deployment; Zhou et al. (2022) and Al-Ayoub et al. (2024, *PaintBot*) represent the industrial end. [[RSIS 2025 - Arduino Wall Painting Robot]] confirms feasibility at Arduino-class budget. Review-level evidence (Cai et al., 2019; Attalla et al., 2023; Xu et al., 2025; Brosque et al., 2022) shows the field is active but fragmented.

**What exists:** reliable XY/gantry motion, spray end-effectors, Arduino-class controllers, sensor feedback.
**The gap:** fixed, pre-programmed paths — no perception of the wall, no reasoning about color.
**How AURA addresses it:** keeps the proven XY-gantry + Arduino backbone, replaces fixed programming with a YOLOv8 perception layer + AI color recommender.

## Theme 2 — Human–Robot Collaboration and Safety (new, 2026-07)
M. Zhang et al. (2023), Sun et al. (2023), Earnest et al. (2026), and Okpala et al. (2023) establish that mechanical/psychosocial risk dominates when robots share human workspace, and that adaptive programming + HRI interface design are the field's leading research themes.
**Relevance:** motivates framing AURA as a fixed-envelope apparatus operating on a defined wall section — minimizing the interaction-hazard class this literature documents.

## Theme 3 — AI & Computer Vision for Wall Segmentation (updated, 2026-07)
[[Bjekic 2023 - Wall Segmentation CNN]] remains the direct precedent (CNN wall/non-wall classification). Instance segmentation has matured from He et al. (2017, Mask R-CNN) through UNet++ (Zhou et al., 2019) to the YOLO family: YOLOv8 (Jocher et al., 2023), evaluated on the COCO protocol (Lin et al., 2014), with strong recent applications — Zhang et al. (2024, YOLOv8-CM), Lin et al. (2025), Wang et al. (2023, BL-YOLOv8), Guan et al. (2025, YOLOv8+SAM). Ni et al. (2023) and R. Zhang et al. (2023) survey the broader scene-understanding/segmentation landscape.
**What exists:** mature CNN/YOLO segmentation for walls and scenes at real-time speed.
**The gap:** demonstrated in isolation, or on 3D/industrial hardware unavailable to an undergraduate prototype.
**How AURA addresses it:** adopts **YOLOv8 (Ultralytics)**, zero-shot-first against COCO-pretrained weights — explicitly chosen (superseding an earlier MobileNetV3+DeepLabV3+ plan, see [[🔮 Segmentation Model]]) because the zero-shot/transfer-learning literature shows COCO backbones generalize well enough that custom fine-tuning becomes optional, not required.

## Theme 4 — Spray Systems, Trajectory Planning, and Hardware Precision (expanded, 2026-07)
Rudzuan et al. (2019) and Kiran & Prabhu (2020) establish gantry-mounted spray control; Chen et al. (2020), Bastida et al. (2023), Gabbar et al. (2024), and Hua et al. (2024) show that coating-quality gains come from geometry-informed trajectory planning, not the sprayer alone (Hua et al. cut coating-thickness variance from 51.9 μm² to 3.64 μm²). On the hardware-precision side — directly relevant since AURA runs an identical Arduino Mega + TB6600 + NEMA 23 stack — Wahjudi et al. (2025), Muas et al. (2026), Suresh et al. (2025), Elgeme et al. (2025), Das et al. (2024), and Ademi et al. (2025) provide realistic accuracy/repeatability benchmarks against which AURA's own ISO 9283:1998 motion evaluation can be interpreted.
**The gap:** adaptive spray control tied to *perception* remains under-explored at prototype scale.
**How AURA addresses it:** times solenoid/pump actuation to gantry position via the pyserial handshake (see [[💧 Spray System Design]], [[🖥️ Serial Communication Protocol]]), coordinated with segmentation output. **Planned 2026-08:** move beyond binary on/off toward PWM duty-cycle flow modulation — see [[💧 Spray System Design]] § Planned: Adaptive Spray Control — PWM.

## Theme 5 — Deep Learning + Spray-Control Integration
Tiboni et al. (2022, *PaintNet*), Liu et al. (2024), Cheng et al. (2025), and He et al. (2026) demonstrate that spatial understanding can directly drive spray-control decisions — but on industrial platforms with 3D sensing.
**How AURA addresses it:** validates the same perceive-then-spray principle on 2D/undergraduate-scale hardware.

## Theme 6 — AI-Based Color Recommendation (expanded, 2026-07)
Yuan et al. (2021, *InfoColorizer*) and Wu et al. (2023) show deep-learning palette recommendation is mature and user-validated; Koh (2023), Li et al. (2025), and Ananya et al. (2025) extend the space further.
**The gap:** painting-robot literature treats color as fixed or database-looked-up, never AI-recommended as a first-class module.
**How AURA addresses it:** an AI-based color recommendation module ([[🎨 Color Recommendation Module]]) generates palettes evaluated by human raters (ISO/IEC 25010:2011-framed), explicitly *not* verified against applied paint color (out of scope — no paint-mixing capability).

## Theme 7 — Color Preference by Demographic (Age & Gender) in Interior Spaces (new, 2026-08)
Bogicevic et al. (2018) run the most direct evidence for a gendered "masculine vs. feminine" color response (762-participant hotel-room experiment: men prefer masculine schemes, women equally satisfied with either); Hao et al. (2025) quantify children's (ages 3–15) HSV preferences for medical-furniture-adjacent spaces (warm hue, saturation ≈25/100, value ≈75/100, with boys preferring higher saturation than girls and older children preferring lower saturation); Jiang et al. (2020) extend the age/gender effect into adolescent (12–16) furniture-color choice. Elderly-specific preference is corroborated across three independent studies: Torres et al. (2020) find warm colors preferred for activity rooms and cool for bedrooms (both genders, tied to arousal level), Li et al. (2022) find low-saturation, bright, warm tones preferred in a 306-respondent Chinese urban-elderly bedroom study, and Rapuano et al. (2023) find the elderly rely more heavily on color/material for emotional evaluation of a space than middle-aged or younger adults. Voordt et al. (2017, 1,077 Dutch respondents), Huang et al. (2009, 231 Beijing respondents) and Yıldırım et al. (2007) all independently confirm age and gender significantly affect color/lightness/saturation preference and mood response across general residential and commercial interiors, though effect sizes and direction vary by study population and space type. Özsavaş Uluçay (2024) is included for interior color-trend methodology context (Adobe Color palette extraction from award-winning hotel interiors) rather than a demographic finding.
**Why this matters for AURA:** gives [[🎨 Color Recommendation Module]]'s "for whom" category input a real evidentiary basis rather than an invented heuristic — panel-recommended and **shipped** 2026-08-08, see [[🎯 Post-Defense Recommendations & Action Items]]. Each study below maps to a specific row of the `CATEGORY_BIAS` table: Hao (2025) → `child_boy`/`child_girl`, Hao + Jiang (2020) → `teen`, Bogicevic (2018) → `adult_man`/`adult_woman`, Li (2022) + Rapuano (2023) → `elderly`.
**The gap:** none of the existing painting-robot or AI-color-recommendation literature (Theme 6) conditions its output on who the space is for — demographic personalization is treated, where studied at all, purely as a human-interior-design survey question, never wired into a generative/recommendation system.
**How AURA addresses it:** category-conditioned bias applied once to the CIE LCh seed inside `build_palette()`, ahead of harmony generation, so every swatch in the returned palette carries the same demographic lean — built 2026-08-08, see [[🎨 Color Recommendation Module]] § Reference Image + Demographic Category.

> [!warning] Honest framing for the defence — read before citing this theme
> The constants are hand-derived from the *direction* of these findings, not fitted to their data, and this is a small literature set (hotel rooms, nursing homes, Dutch/Chinese residential surveys, a paediatric-furniture study) generalised to "wall colour for a home room". Reasonable for an undergraduate thesis; state it as a limitation, don't claim precision.
>
> **One group is weaker than that and must not be over-claimed.** The `child_boy` / `child_girl` / `teen` **chroma** values were deliberately raised on 2026-08-08 *above* what Hao et al. report. Hao's HSV S ≈ 25/100 converts to roughly **C\* 20**; those rows now sit at C\* 44–56. What Hao et al. still supports in them: the warm hue nudge, the raised lightness, the boy > girl ordering and the size of that gap, and the decrease with age. What it does **not** support: the saturation level. That was a design judgement — a children's wall reading flat at the cited level — and the evaluator study is what settles it. See [[🎨 Color Recommendation Module]] § Second fix round.

## Overall Synthesis — The Gap AURA Fills
Across all themes, the literature has independently matured (a) the occupational-safety case for automation, (b) affordable XY/gantry mechanics, (c) deep-learning 2D wall/scene segmentation (now anchored on YOLOv8), (d) geometry-informed spray trajectory planning, (e) the specific Arduino/TB6600/NEMA23 hardware-precision envelope, (f) AI-based color recommendation, and (g) demographic-aware color personalization — but **no accessible, undergraduate-scale system unifies perception, calibrated coordinate mapping, demographic-conditioned color recommendation, and adaptive spray into one reproducible pipeline, benchmarked against recognized external standards (ISO 9283:1998, COCO, ASTM D823, ISO/IEC 25010:2011, IEEE 1872-2015).** AURA's contribution is precisely this integration.

> [!success] Synthesis sentence revised 2026-08-10
> Added (g), demographic-aware color personalization, now that Theme 7's feature has shipped. Draft rephrasing — Kurt should read it against his own voice before it goes into the live Google Doc concept paper. Also corrected the standards list: it still read ASTM D4147/D3270, the citation error Q12 in [[❓ Anticipated Panel Questions & Answers]] already caught and fixed elsewhere — this paragraph had been missed. Now reads ASTM D823, matching every other synced note.
