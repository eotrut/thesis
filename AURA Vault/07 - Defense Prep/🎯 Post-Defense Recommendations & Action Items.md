---
tags: [defense, panel, recommendations, action-items]
created: 2026-08-08
status: active
---
# 🎯 Post-Defense Recommendations & Action Items

> [!info] Related
> [[📊 Presentation Outline]] · [[❓ Anticipated Panel Questions & Answers]] · [[📋 Master Task Tracker]] Phase 6 · [[📊 Progress Completion Tracker]]

> [!success] Proposal defense — 2026-08-08
> Panel accepted the proposal with six follow-up recommendations, three software-side and two hardware-side (plus one input still open). Logged here as the single source of truth for what changed and why; each item also lives in its own subsystem note (linked below) and as checklist items in [[📋 Master Task Tracker]] Phase 6.
>
> **Status:** both software items that don't need hardware are now built — colour reference-image + category (2026-08-08) and the mask-correction brush (2026-08-15). The paint-level indicator and both hardware items are blocked on the rig.

## Software — Color Recommendation Module

**Panel ask:** add a user-uploaded reference image input, and a "for whom" demographic category (child / girl / guy / etc.), to [[🎨 Color Recommendation Module]].

**Decided (via clarifying questions, 2026-08-08):**
- Reference image is a **second, separate upload** — on top of the existing room photo — representing what the user wants the room to look like.
- Category applies as an **evidence-based bias** on the CIE LCh harmony math itself, because real literature on color preference by age/gender for interior spaces exists — see the new RRL addition below.

**Decided (round 2, same day — all open items resolved):**
- **Category list:** full set with gender splits — `child_boy`, `child_girl`, `teen`, `adult_man`, `adult_woman`, `elderly`, `none`.
- **Category input:** fixed dropdown, not free text.
- **Reference/room blend:** 60/40, reference-dominant (reference image seed weighted 60%, room photo seed 40%, circular mean for hue). **Superseded later the same day — now 70/30**, after the first real reference image read as under-referenced; see [[🎨 Color Recommendation Module]] § Third fix round. Kept here as the record of what was decided when.
- **Bias constants:** concrete starting numbers decided now, not left as placeholders — full table in [[🎨 Color Recommendation Module]] § Reference Image + Demographic Category.

> [!success] Built the same day — 2026-08-08
> Both inputs are **implemented and verified** against the loaded model: optional `reference_image` (70/30 reference-dominant LCh blend, circular-mean hue) and the seven-category `CATEGORY_BIAS` dropdown, plus the UI for both on `color-recommendation.html`. Full record — including three rounds of fixes the same day, and the two constants that ended up as design judgements rather than literature-derived values — in [[🎨 Color Recommendation Module]] §§ As-built record, Fix round, Second fix round, Third fix round.
>
> **Still to do:** the bias constants have only been exercised on synthetic frames. Eyeballing them against real room photos is blocked on the same `samples/` shoot as everything else, and the evaluator study (n ≥ 5) is what should actually tune them.

**Full design + as-built notes:** [[🎨 Color Recommendation Module]] § Reference Image + Demographic Category
**New literature:** [[📚 Literature Review Master]] Theme 7 · [[📝 Chapter 2 - Review of Related Literature]] § 2.8b — the manuscript RRL update is no longer premature now that the feature has shipped

## Software — Camera / Masking View

**Panel ask:** add a brush-style manual correction tool for the segmented wall mask, to fill in paintable area the model missed.

> [!note] Kurt's read
> Initially assumed this was too much manual intervention for an "AI-controlled" pipeline, but the panel was fine with it as a human-in-the-loop safety net — consistent with the dataset still growing toward the ~1,000-image target (currently 300, mAP@0.50 0.780, see [[🔮 Segmentation Model]]). This doesn't replace continued fine-tuning; it's a stopgap for whatever the model still misses.

**Decided:** add + erase brush, available on **both** the Upload/Playback segmentation preview and the Toolpath planner in `camera-view.html`.

**Decided (2026-08-10):** yes — a correction made in Upload/Playback carries over into Toolpath mode automatically. One corrected mask, shared across both views, not a separate correction each time.

> [!success] Built — 2026-08-15
> Add + erase brush shipped on both views as decided, with the carry-over working as specified: one corrected mask per session/image, and switching to the Toolpath tab with a still already loaded in Upload/Playback adopts that frame automatically, so the correction is already applied when it plans. Not on the Live Feed — server-side MJPEG, no per-frame correction hook, as scoped.
>
> **Mechanics chosen** (these were left open): applied **server-side** in `backend/mask_correction.py` from a **stroke list** in a `mask_correction` form field, not a rasterised bitmap and not client-side. One patch point that the overlay, the G-code polygons and the colour clustering all read through; ~1 KB per correction; resolution-independent, which is what makes the carry-over work at all. Brush UX (also open): size slider as a % of image width, undo / <kbd>Ctrl</kbd>+<kbd>Z</kbd>, clear, <kbd>Esc</kbd>, pointer events for trackpad and touch.
>
> **The detail worth defending:** an erase in the *middle* of a wall is re-emitted as a non-paintable region, not just subtracted from the mask — detections carry single-ring polygons, so a mid-wall hole would otherwise vanish and the gantry would paint straight over it. `backend/tools/test_mask_correction.py` asserts that the planned paintable area actually drops.
>
> **Ask-me-this-at-defense:** manual regions carry `confidence: null` and are **excluded from every reported confidence figure**, so a corrected mask can never inflate the model's score — the brush changes the region, not the metric. `wall_coverage` does include them, because it describes what will actually be painted. The Chapter 4 mAP/IoU re-run after the ~1,000-image training must be measured with the brush unused.

> [!success] Extended — 2026-08-16: ✨ Smart select
> Kurt's call: the brush works but isn't a wow factor on stage. Added **click-to-select** next to it — click a point and the region under it is selected, powered by **MobileSAM** (Zhang et al. 2023, a distilled Segment Anything — Kirillov et al. 2023). The decisive fact: **the ultralytics version already pinned ships the SAM predictors**, so this cost a 38 MB weights file and **no new dependency**. A CIE-Lab flood-fill wand is the fallback when the weights are absent, and the editor labels which engine is live.
>
> **The demo moment:** click the wall → the wall. Click the door → *just the door* (12.6% of the frame vs the wall's 61.5%). Shift+click grows a selection, right-click carves part away.
>
> **The number worth quoting:** MobileSAM's wall and the fine-tuned YOLOv8's wall agree to within **0.11%** (265 px of 251,377 outside each other). Two independently-trained models converging on the same boundary says more about the segmentation than either does alone — and it is a test invariant, not an anecdote.
>
> **Before defense day:** `mobile_sam.pt` is git-ignored like `best.pt`, so it does not travel with a clone — **put it on the demo machine**, or smart select silently degrades to a flood fill. Also worth an RRL addition (Theme 3): promptable foundation-model segmentation as a human-in-the-loop correction.

**Full as-built notes:** [[🔮 Segmentation Model]] §§ Manual Mask Correction (Brush Tool) — BUILT 2026-08-15, Smart Select (2026-08-16) · [[🔌 Backend API & Web Integration]] §§ Manual mask correction, POST /api/smart-select

## Software — Paint-Level Indicator

**Panel ask:** notify the operator when paint is running low. Kurt's instinct was a load cell — asked for a second opinion.

**Recommendation: yes, load cell (+ HX711 amplifier) under the reservoir.** Reasoning:
- It's the only one of the common options that doesn't care that the fluid is opaque, pigmented paint — an optical/ultrasonic level sensor has to see or range off the paint surface, and mist/film buildup on a lens or transducer is a real failure mode in a spray environment. A load cell reads mass through the reservoir wall.
- A float switch only gives a binary low-level trip, and moving parts in contact with acrylic paint tend to gum up (same failure class as R-14's nozzle clogging).
- It reuses a methodology AURA already has documented: [[💧 Spray System Design]]'s flow-rate calibration is **already weight-based** ("spray a fixed-time burst onto paper... measuring covered area / weight"). Adding a load cell under the reservoir is the same measurement principle applied continuously, not a new one — a clean thing to say to the panel.
- Gives a **percentage**, not just a threshold trip, which is more useful for both the operator UI and as a defensible data source for Chapter 4 if paint-consumption vs. coverage area ever becomes a metric.

Tradeoff to flag honestly: needs a one-time tare + single-point calibration (known paint mass/volume) after the reservoir/mount is finalized, and a load cell reading in a vibrating gantry environment will need light smoothing (moving average) to avoid false triggers during motion.

**Not yet decided — still needs Kurt (deferred):** mounting point (blocked on reservoir finalization).

**Full design notes:** [[💧 Spray System Design]] § Planned: Paint-Level Monitoring (2026-08-08)

## Hardware — Gantry Mobility

**Panel ask:** rollers and stoppers so the gantry frame can be moved instead of carried.

**Recommendation:** locking **swivel casters** rated for the assembled frame weight, **plus** separate drop-down leveling feet that bear the load and pin the frame square once it's positioned — casters only carry weight in transit, not while spraying. This directly protects the racking mitigation (R-02: dual-X lockstep, square frame, dual homing) — casters alone under an accelerating gantry would reintroduce the wobble the dual-motor scheme exists to prevent.

> [!note] Not the same "mobility" R-17 flags as scope creep
> [[⚠️ Risk Register]] R-17 lists "mobility" as scope creep to avoid — that item means autonomous/self-propelled movement across a room, which is still correctly out of scope. Manually rolling the existing frame between fixed positions is the workflow AURA already documented (see [[⚙️ Mechanical Design]] § Multi-position painting is the plan) — casters just make that manual reposition easier, they don't change what the system does.

**Not yet decided — still needs Kurt (deferred):** exact caster load rating (needs the frame's actual assembled weight, not yet measured).

**Full design notes:** [[⚙️ Mechanical Design]] § Planned: Mobility — Casters & Leveling Feet (2026-08-08) · [[🛒 Bill of Materials]]

## Hardware — Adaptive Spray Control

**Panel ask:** the current "adaptive" spray control is just on/off (binary) synced to gantry position — go further.

**Decided:** start with **PWM time-proportioning on the existing solenoid** — firmware/software only, no new hardware. Rapidly pulsing the solenoid at a duty cycle approximates a continuous average flow rate; this is the same principle used in precision-agriculture PWM spray nozzle control.

**Not yet decided — still needs Kurt (deferred):** whether spray-width tapering near mask edges gets built alongside the PWM base case or later — a natural follow-on since it falls out of having PWM control anyway.

**Full design notes:** [[💧 Spray System Design]] § Planned: Adaptive Spray Control — PWM (2026-08-08) · [[🖥️ Serial Communication Protocol]]

## Not yet decided / needs Kurt

Color-module items are now **all resolved** (see above). Mask correction is **built** (2026-08-15) — carry-over, payload shape and brush UX all settled, see § Software — Camera / Masking View above. Remaining, deferred until we get to each feature:

- [ ] Load cell mounting point and paint reservoir finalization (blocks calibration).
- [ ] Caster load rating — needs the frame's actual assembled weight, not yet measured.
- [ ] Whether spray-width tapering near edges gets built alongside the PWM base case or deferred.
