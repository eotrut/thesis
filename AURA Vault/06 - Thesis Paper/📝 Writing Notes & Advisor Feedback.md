---
tags: [thesis, writing, feedback]
created: 2026-03-29
updated: 2026-08-05
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
