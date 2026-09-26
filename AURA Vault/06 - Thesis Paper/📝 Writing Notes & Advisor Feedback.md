---
tags: [thesis, writing, feedback]
created: 2026-03-29
updated: 2026-08-16
status: active
---
# 📝 Writing Notes & Advisor Feedback

## Style Guide Reminders
- **APA 7th edition** for all citations and references.
- Follow **HAU (Holy Angel University)** thesis formatting for margins, spacing, headings, and preliminaries.
- Chapters are **formal, third-person, past/present tense** as appropriate (methods often past; established facts present).
- Every figure/table numbered and captioned; every reference cited in-text.

## Common Weak Phrases to Avoid
| Avoid | Prefer |
|---|---|
| "a lot of / lots of" | "many / substantial" |
| "very accurate" | state the number |
| "the system is good at" | "the system achieved X" |
| "in order to" | "to" |
| "due to the fact that" | "because" |
| "cutting-edge / revolutionary" | describe the actual capability |

## 5 Writing Tips for Engineering Theses
1. **Lead with numbers.** Quantify claims (mm, mIoU, ΔE) rather than adjectives.
2. **Separate what you did from what you found.** Methods ≠ Results ≠ interpretation.
3. **Tie every result to an objective.** The panel checks that Chapter 4 answers Chapter 1.
4. **Be honest about limitations** — declared scope protects you; hidden weaknesses get exposed in defense.
5. **Figures do heavy lifting.** A clear architecture diagram and result photos beat paragraphs.

## Advisor Feedback Log
> [!note] Add a dated entry after every consultation.

### [Date] — Adviser: [Name]
**Feedback:**
**Action items:**
- [ ]

### [Date] — Adviser: [Name]
**Feedback:**
**Action items:**
- [ ]

### 2026-07-18 — Concept Paper Review (Claude, full-document pass on live Google Doc)
**Context:** Full read-through and quality review of the live concept-paper Google Doc (not the local `aura_thesis_rewrite.md` draft). Diagrams were excluded from review per your confirmation that they were already finished and correct.

**Score progression:**
- Initial review: several structural/citation issues found, score not yet final.
- After first round of fixes applied (title, Kumtole/Liyakat spelling, restored Mask R-CNN/UNet++ sentence, IEEE 2022 citation, He 2026 DOI marked unavailable, Hypotheses wording, 3 mechanical fixes): **9/10**.
- Once the 6 residual items below are cleaned up: **9.5–10/10**.

**Fixes applied this round:**
- Title corrected to match the AURA acronym.
- Author surname spelling fixed: "Kumtole" (not "Kumote"); "Sayyad Liyakat" (not "Liyakaf").
- Restored a dropped sentence in the Introduction referencing Mask R-CNN and UNet++ as prior segmentation approaches, with 2 new supporting reference entries.
- Added a missing citation for the IEEE 2022 reference.
- He (2026) reference: original DOI was a duplicate of Chen (2020)'s DOI (wrong paper) — marked as "no DOI available" per your choice; a replacement DOI (`10.1108/IR-07-2025-0261`) was later added by you/the editor but could not be independently confirmed via search — flagged for manual verification.
- Hypotheses (H₀/H₁) wording expanded to explicitly cover "...and color recommendation performance."
- 3 mechanical fixes applied to RQ3, RQ6, and the Testing/Data-Analysis section for internal consistency.
- **Full reference audit** (your choice, "verify all of them") — ~80 APA references checked via parallel web-search verification:
  - Roughly 40 entries had at least one wrong field (volume/issue/pages/DOI/publisher) — corrected APA-formatted replacement text provided for each.
  - 6 references could not be independently verified as real publications (Al-Ayoub 2024, Arrandale 2025, Koh 2023, Elgeme 2025, Patil 2021, Tawade 2024) — **you confirmed these are legitimate/accessible on your end**, so they were kept as-is rather than flagged as errors.
  - ASTM standards D3270 and D4147 (originally cited for coating/spray-consistency testing) were found to be real but unrelated standards (D3270 = fluoride content of atmosphere/plant tissues; D4147 = coil-coating drawdown bars). Corrected to the actual applicable standard: **ASTM D823** ("Standard Practices for Producing Films of Uniform Thickness of Paint, Coatings and Related Products on Test Panels"), consolidating both old citations into this one correct designation across the Standards Set paragraph, the evaluation-matrix table, and the Reference list.

**Still outstanding (your action items in the Google Doc):**
- [ ] Reference-list entry for Sowmya/Prakash (2024) still shows the old "Sowmya, M., Ramesh, K., & Rao, V." author line and volume/pages — in-text citations were fixed but the reference entry itself was not.
- [ ] Suresh (2025) reference-list entry lost its author names during editing (now starts mid-sentence) and still carries the old incorrect DOI.
- [ ] Two literal placeholder artifacts were pasted in verbatim without being filled in: "Cheng, S., et al. (2025)" and "Muas, M., Abdul Salam, [initial], Fair, A., ...".
- [ ] "Vijaya Kumar et al." reference entry is out of alphabetical order (currently sitting between "Republic Act No. 11058" and "Rudzuan"; belongs under V).
- [ ] One missed occurrence of the Bastida/Gabbar "et al." citation-format fix remains (parenthetical list still reads "Bastida et al., 2023" / "Gabbar et al., 2024").
- [ ] One missed occurrence of the ASTM fix remains (Introduction summary paragraph still reads "ASTM D4147 and D3270 for coating uniformity" instead of "ASTM D823").

**Advisor/defense-readiness note:** Document is functionally ready to pass at 9/10; closing the 6 items above is a 15–20 minute cleanup pass, not new work.

### 2026-08-02 — Methods Step 5 (Toolpath Generation) expanded
**Context:** Gantry plate is the last hardware part still on order, so Kurt shifted to software-only work: coordinate mapping (homography) + toolpath generation, the pipeline stage between segmentation and the not-yet-built serial/Arduino bridge.

**Changes made:**
- Manuscript's Procedure Step 5 ("Toolpath Generation") expanded in `Thesis Paper.docx` to describe the finalized design: mask polygon mapped into the Step-2 calibrated mm frame; non-paintable regions (doors/windows/obstacles) geometrically subtracted from the paintable polygon so rows skip over them; serpentine (boustrophedon) row traversal to minimize travel; output serialized into the G-code-style commands used in Step 8. Rendered and visually verified before writing back — no other section touched. Results/Discussion chapters remain intentionally blank pending dataset completion, per Kurt's instruction.
- Vault synced: [[📐 Path Planning & G-code Generation]] (added obstacle-subtraction + calibration-fallback detail, marked in-development) and Chapter 3 Step 5 (cross-referenced).
- Implementation itself (`coordinate_mapping.py`, `toolpath_generator.py`, `POST /api/toolpath`, test/viz script) was handed to Kurt as a Claude Code prompt rather than built in this session — recommended running it under Opus given the polygon/geometry edge cases (row-hole intersection, serpentine ordering). Not yet confirmed built/run.

### 2026-08-03 — Toolpath build verified; envelope-clipping decision made
**Context:** Kurt ran the 2026-08-02 handoff prompt in Claude Code (Opus, extra-high effort). Confirmed on disk: `backend/coordinate_mapping.py`, `backend/toolpath_generator.py`, `backend/tools/test_toolpath.py`, `POST /api/toolpath` in `app.py`, updated `requirements.txt`/`README.md`, and a new Toolpath tab on `camera-view.html`. Tested against the real `best.pt` model (not synthetic data) on existing test images — e.g. test_result_1.jpg: 0.614 m² paintable, 37 rows, 96.5% spray efficiency (1.1 m dry travel of 31.6 m total). Obstacle routing (doors, switch plates) verified visually.

**Open decision from the handoff — resolved:** whether an out-of-envelope wall mask (segmentation extends past the calibrated area) should be clipped or rejected.

**Decision: clip, not reject.** Rationale: the gantry's X-axis rail is only 4.5 ft (1371.6 mm) against walls that are routinely wider — full wall coverage was always planned as multiple gantry positions, manually repositioned and re-calibrated between passes (see [[⚙️ Mechanical Design]], rail lengths locked this session: X = 4.5 ft / 1371.6 mm, Y = 9 ft / 2743.2 mm). Under that plan, a mask extending past the current reachable envelope is the *normal* case on most runs, not an error — reject would refuse to generate a toolpath on nearly every real wall. Clip is what implements the multi-pass workflow: paint what's reachable now, report the leftover for the next repositioned pass.

**Implementation guidance recorded for the next Claude Code pass:** clip against the gantry's **physical rail travel limits** (minus a homing/limit-switch safety margin), not the 4-marker calibration quad — the markers only define the pixel↔mm mapping, not where the machine can physically move. Keep a hard soft-limit check at G-code emission as a backstop (standard GRBL/CNC practice). `/api/toolpath` should report clipped/skipped paintable area so it's visible how much wall still needs another pass. Full detail in [[📐 Path Planning & G-code Generation]] § Envelope Clipping.

**Relevance to Chapter 4/5:** this is a genuine design decision with engineering rationale (not just an implementation detail) — worth a sentence in Methodology if not already covered, and a natural candidate for the Discussion chapter's "system limitations" framing (multi-pass coverage is a scope choice, not a failure mode).

## 2026-08-05 — Concept paper review: pending manual Doc edits

Pending — none of these are applied to the live Google Doc yet.

**Running header** (every page)
Find: `AURA (AI-Based Autonomous Wall Painting Robot)`
Replace: `AURA (Autonomous Unified Robotic Adaptive)`

**Abstract, opening sentence** (p.2)
Find: "This study proposed the design and development of AURA (AI-based Autonomous Wall Painting Robot), a deep learning-based framework that unified spatial perception, color recommendation, and adaptive spray control within a single physical prototype."
Replace: "This study proposed the design and development of AURA (Autonomous Unified Robotic Adaptive), an AI-based autonomous wall-painting robot and deep learning-based framework that unified spatial perception, color recommendation, and adaptive spray control within a single physical prototype."

**Abstract, later sentence** (p.2)
Find: "The resulting motion and spray commands were serialized as G-code-style instructions and transmitted to the Arduino over USB via pyserial, which then actuated the stepper motors and solenoid-controlled spray hardware."
Replace: "The resulting motion and spray commands were serialized internally as G-code-style instructions, translated into a custom command protocol (MOVE, SPRAY ON/OFF, HOME), and transmitted to the Arduino over USB via pyserial, which then actuated the stepper motors and solenoid-controlled spray hardware."

**Introduction, pipeline-summary paragraph** (p.15)
Find: "...a raster toolpath generator that converts segmentation masks into physical scan paths, a pyserial-based bridge that transmits G-code-style commands to an Arduino Mega, and an AI-based color recommendation module..."
Replace: "...a raster toolpath generator that converts segmentation masks into physical scan paths, a pyserial-based bridge that translates internally generated G-code-style commands into a custom command protocol before transmitting them to an Arduino Mega, and an AI-based color recommendation module..."

**Scope and Delimitation, bullet list** (p.19)
Find: "Use of a microcontroller-based control system (Arduino Mega, wired directly to the TB6600 drivers) with a 24 V DC power supply, driven from Python via pyserial over USB using G-code-style commands."
Replace: "Use of a microcontroller-based control system (Arduino Mega, wired directly to the TB6600 drivers) with a 24 V DC power supply, driven from Python via pyserial over USB using a custom command protocol (MOVE, SPRAY ON/OFF, HOME) translated from an internal G-code-style representation."

**Rationale section** (p.22)
Find: "The core innovation of AURA is not any single subsystem but the unified pipeline from perception to physical paint application: a captured wall image is segmented by YOLOv8, calibrated into real-world coordinates through OpenCV homography, converted into a raster toolpath, transmitted to an Arduino Mega via pyserial as G-code-style commands, and executed on a two-axis gantry with adaptive spray control."
Replace: "The core innovation of AURA is not any single subsystem but the unified pipeline from perception to physical paint application: a captured wall image is segmented by YOLOv8, calibrated into real-world coordinates through OpenCV homography, converted into a raster toolpath, translated into a custom command protocol, and transmitted to an Arduino Mega via pyserial, and executed on a two-axis gantry with adaptive spray control."

**Methodology, Data Analysis paragraph**
Find: "Qualitative analysis will involve user evaluation of color recommendations and overall painting output using a rating scale."
Replace: "Qualitative analysis will involve user evaluation of color recommendations using a rating scale, while overall painting output is assessed through the quantitative accuracy and coverage metrics above."

**Diagram fixes — edit at the `.drawio` source, not the Doc text**
- General Block Diagram (p.25): arrow "G-code Commands (Serial)" → "Custom Protocol Commands (Serial)"
- System Block Diagram (p.26): Control Board box "Parses G-code · STEP/DIR/EN breakout · relay control (M3/M5) · endstop homing" → "Parses custom command set (MOVE/SPRAY/HOME) · STEP/DIR/EN breakout · relay control (M3/M5) · endstop homing"
- Flowchart (p.27): "Raster Path Planning + G-code Generation" → "Raster Path Planning + Toolpath Generation"; "Stream G-code Commands / pyserial, 115200 baud – line-by-line, wait for 'ok'" → "Stream Custom Protocol Commands / pyserial, 115200 baud – line-by-line, wait for ack"

## 2026-08-16 — SAM/MobileSAM + demographic §2.8b: pending manual Doc edits

Pending — none of these are applied to the live Google Doc yet. Both additions are also written into [[📚 Literature Review Master]] (Theme 3) and [[📝 Chapter 2 - Review of Related Literature]] (§2.6, §2.8b) already; this note is the exact paste text for the actual manuscript, plus a citation audit.

### A. SAM / MobileSAM (§2.6, concept paper p.11–12)

**Insert new sentence** — after "...Guan et al. (2025) coupled an improved YOLOv8 with a fine-tuned Segment Anything Model to unify detection and segmentation in a single modular pipeline for building defect analysis." and before "These results collectively confirm..." (p.11–12):

> Segment Anything itself (SAM; Kirillov et al., 2023) is the promptable, class-agnostic foundation model underlying that hybrid trend; its lightweight distillation, MobileSAM (Zhang et al., 2023), is the literature basis for AURA's own human-in-the-loop mask-correction tool — used to let an operator refine a YOLOv8 mask after inference, not folded into the segmentation pipeline itself the way Guan et al. (2025) use it.

**Find/Replace** — same paragraph, the justification sentence right after (p.12):

Find: "These results collectively confirm that the YOLOv8 family is well suited to segmenting flat, texture-rich surfaces of the type targeted in the present study, and they justify the study's decision to adopt YOLOv8 rather than an earlier segmentation architecture."

Replace: "These results collectively confirm that the YOLOv8 family is well suited to segmenting flat, texture-rich surfaces of the type targeted in the present study, and they justify the study's decision to adopt YOLOv8 rather than an earlier segmentation architecture, with SAM/MobileSAM adopted as a complementary correction layer, not a competing detector."

**New References entries (both web-verified 2026-08-16):**

- Insert between "Kiran, J. R. V. S., & Prabhu, S. (2020)" and "Koh, I. (2023)" (p.45):
  Kirillov, A., Mintun, E., Ravi, N., Mao, H., Rolland, C., Gustafson, L., Xiao, T., Whitehead, S., Berg, A. C., Lo, W.-Y., Dollar, P., & Girshick, R. (2023). Segment anything. In *Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)* (pp. 4015–4026). IEEE. https://doi.org/10.1109/ICCV51070.2023.00371

- Insert between "Zeng, Y. ... (2024)" and "Zhang, C., Chen, X. ... (2024)" (p.50) — same-surname/same-initial rule, 2023 sorts before 2024:
  Zhang, C., Han, D., Qiao, Y., Kim, J. U., Bae, S.-H., Lee, S., & Hong, C. S. (2023). Faster segment anything: Towards lightweight SAM for mobile applications. arXiv. https://doi.org/10.48550/arXiv.2306.14289

**2026-08-16 addendum — exact placement for all 10 new references, checked against actual current text (list has pre-existing ordering quirks, e.g. Attalla sits before Arrandale on p.41 — placements below use the real neighbors, not idealized alphabetical order):**

| New reference | Insert between | Page |
|---|---|---|
| Bogicevic (2018) | Boadu, E. F. ... (2023) → **Bogicevic** → Brosque, C. ... (2022) | p.42 |
| Hao & Guan (2025) | Guan, Y., Zhao, X., & Liu, H. (2025) → **Hao & Guan** → Hassan, E. ... (2022) | p.44 |
| Jiang (2020) | Jaya, A. ... (2024) → **Jiang** → Jocher, G. ... (2023) | p.45 |
| Kirillov (2023) | Kiran, J. R. V. S., & Prabhu, S. (2020) → **Kirillov** → Koh, I. (2023) | p.45 |
| Li, M. (2022) | Li, H.-C., Wang, L.-K. ... (2025) → **Li, M.** → Lin, T.-Y. ... (2014) | p.46 |
| Rapuano (2023) | Patil, A. (2021) → **Rapuano** → Republic Act No. 11058 (2018) | p.47–48 |
| Torres (2020) | Tiboni, G., Camoriano, R., & Tommasi, T. (2022) → **Torres** → Van der Voordt (next row) | p.49 |
| Van der Voordt (2017) | Torres (above) → **Van der Voordt** → Wahjudi, A., & Yusuf, M. (2025) | p.49 |
| Yıldırım (2007) | Xu, L. ... (2025) → **Yıldırım** → Yuan, L. ... (2021) | p.50 |
| Zhang, C. (2023, MobileSAM) | Zeng, Y. ... (2024) → **Zhang, C. (2023)** → Zhang, C., Chen, X. ... (2024) | p.50 |

Note: no proper "V" section exists yet — Vijaya Kumar, S. et al. (2025) sits misplaced between "Republic Act No. 11058" and "Rudzuan" (outstanding since the 2026-07-18 review). Convenient moment to fix while touching this stretch for Torres/Van der Voordt — optional.

### B. Demographic color preference §2.8b (concept paper p.13–15)

**Citation audit run 2026-08-16** — 8 of 9 in-text citations in the vault's §2.8b draft are confirmed real via web search, with corrections to two in-text forms:
- "Hao et al. (2025)" → **"Hao and Guan (2025)"** — only 2 authors, APA doesn't use "et al." below 3.
- "Voordt et al. (2017)" → **"Van der Voordt et al. (2017)"** — Dutch surname, "Van der" is part of it.
- **"Huang et al. (2009)" could not be verified** after multiple targeted searches — no matching publication found. Do not paste it into the References list. Either supply the original source yourself, or drop it from the sentence below (reads fine as two citations instead of three).

**Insert new paragraphs** — after "...these studies confirm that AI-based color recommendation is a mature enough capability to be embedded, rather than merely referenced, in an autonomous painting system, and they justify AURA's decision to treat color recommendation as a first-class module in the pipeline rather than as an afterthought." and before "From these findings, it becomes clear that current solutions maintain their incomplete state..." (p.13–14):

> Bogicevic et al. (2018) provide the most direct experimental evidence for gender-linked color preference in a room-design context: across 762 participants, male guests preferred "masculine" hotel-room color schemes while female guests rated masculine and feminine schemes equally. Age- and gender-specific preference is further quantified for children by Hao and Guan (2025), whose 3–15-year-old sample preferred warm hues at moderate-low saturation (≈25/100) and high value (≈75/100), with boys preferring higher saturation than girls and preference for saturation decreasing with age — and extended into adolescence (12–16) by Jiang et al. (2020). Elderly preference is independently corroborated by three studies: Torres et al. (2020) tie warm-versus-cool preference to room activity (warm for activity rooms, cool for bedrooms, both genders), Li et al. (2022) find low-saturation, warm, bright tones preferred across 306 Chinese urban elderly respondents, and Rapuano et al. (2023) find the elderly weight color/material more heavily than younger groups when emotionally evaluating a space. Broader survey evidence (Van der Voordt et al., 2017; Yıldırım et al., 2007) confirms age and gender are statistically significant factors in interior color preference across general populations, though the specific direction and magnitude vary with study population, room type, and culture.
>
> None of the literature reviewed above conditions its output on occupant demographics: existing AI-based color-recommendation systems generate or apply color without reference to who the space is for, and every painting-robot system reviewed in this chapter treats color as fixed or database-looked-up rather than personalized. AURA's color recommendation module closes this gap by taking a "for whom" category input that biases the CIE LCh seed — lightness, chroma, and hue angle — before harmony generation runs. The direction of each bias (warmer or cooler, lighter or darker, more or less saturated, by age and gender category) follows the cited findings above; the magnitudes are design parameters set by this study, not values fitted to the cited data, and are evaluated against the ISO/IEC 25010:2011 color-recommendation-quality criterion described in Chapter 3. An optional reference-image upload lets the occupant's own stated intent enter the same seed, blended 70/30 against the room's own measured color.

**Find/Replace** — gap-synthesis paragraph right after (p.14), add the demographic gap alongside the existing color-recommendation gap:

Find: "likewise, AI-based color recommendation systems have proliferated (Wu et al., 2023; Yuan et al., 2021), but they rarely close the loop by driving a physical actuator, so their outputs remain on the screen rather than on the wall."

Replace: "likewise, AI-based color recommendation systems have proliferated (Wu et al., 2023; Yuan et al., 2021) and, where demographic factors are studied at all (Bogicevic et al., 2018; Li et al., 2022), they appear only as human-interior-design survey findings rather than being wired into a generative recommendation system — and even so, they rarely close the loop by driving a physical actuator, so their outputs remain on the screen rather than on the wall."

**Optional consistency tweak** (p.15, Rationale paragraph — not required, matches the "(g) demographic-aware color personalization" phrasing already in [[📚 Literature Review Master]]'s Overall Synthesis):

Find: "...and an AI-based color recommendation module —all executed on a single undergraduate-scale prototype..."

Replace: "...and a demographic-conditioned AI-based color recommendation module —all executed on a single undergraduate-scale prototype..."

**New References entries (alphabetical placement, insert into the existing list):**

- Bogicevic, V., Bujisic, M., Cobanoglu, C., & Feinstein, A. H. (2018). Gender and age preferences of hotel room design. *International Journal of Contemporary Hospitality Management*, *30*(2), 874–899. https://doi.org/10.1108/IJCHM-08-2016-0450
- Hao, K., & Guan, H. (2025). A study of children's color preferences for consultation room furniture. *HERD: Health Environments Research & Design Journal*, *18*(2), 208–220. https://doi.org/10.1177/19375867251327969
- Jiang, L., Cheung, V., Westland, S., Rhodes, P. A., Shen, L., & Xu, L. (2020). The impact of color preference on adolescent children's choice of furniture. *Color Research and Application*, *45*(4), 754–767. https://doi.org/10.1002/col.22507
- Li, M., Cai, Q., Li, C., Wu, X., Wang, T., Xu, J., & Wu, Z. (2022). A study in bedroom living environment preferences of the urban elderly in China. *Sustainability*, *14*(20), 13552. https://doi.org/10.3390/su142013552
- Rapuano, M., Sarno, M., Ruotolo, F., Ruggiero, G., Iuliano, S., Masullo, M., Maffei, L., Cioffi, F., & Iachini, T. (2023). Emotional reactions to different indoor solutions: The role of age. *Buildings*, *13*(7), 1737. https://doi.org/10.3390/buildings13071737
- Torres, A., Serra, J., Llopis, J., & Delcampo, A. (2020). Color preference cool versus warm in nursing homes depends on the expected activity for interior spaces. *Frontiers of Architectural Research*, *9*(4), 739–750. https://doi.org/10.1016/j.foar.2020.06.002
- Van der Voordt, T., Bakker, I., & de Boon, J. (2017). Color preferences for four different types of spaces. *Facilities*, *35*(3/4), 155–169. https://doi.org/10.1108/F-06-2015-0043
- ~~Huang et al. (2009) — NOT independently verifiable, do not paste until Kurt supplies the source.~~
- Yıldırım, K., Akalın-Baskaya, A., & Hidayetoglu, M. L. (2007). Effects of indoor color on mood and cognitive performance. *Building and Environment*, *42*(9), 3233–3240. (DOI not independently located — ScienceDirect record: https://www.sciencedirect.com/science/article/abs/pii/S0360132306002289; flag for manual DOI lookup before final submission, same treatment as the He 2026 DOI issue above)

**Note on Li surname collision:** the References list will now have two different "Li" first authors — Li, H.-C. (2025, clothing color-harmony ML paper, already in the list) and Li, M. (2022, elderly bedroom study, new). Different years and different first initials, so standard APA alphabetization/in-text handling keeps them distinct without extra disambiguation — just don't merge them into one entry when editing.
