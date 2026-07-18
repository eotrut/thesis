---
tags: [thesis, writing, feedback]
created: 2026-03-29
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
