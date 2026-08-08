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

**Not yet decided — still needs Kurt (deferred until this feature is up next):** whether a correction made in Upload/Playback should carry over into Toolpath mode automatically, or is a separate correction each time.

**Full design notes:** [[🔮 Segmentation Model]] § Planned: Manual Mask Correction (2026-08-08) · [[🔌 Backend API & Web Integration]] § Planned endpoint changes

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

Color-module items are now **all resolved** (see above). Remaining, deferred until we get to each feature:

- [ ] Whether a mask correction made in Upload/Playback carries over into Toolpath mode automatically, or is a separate correction each time.
- [ ] Load cell mounting point and paint reservoir finalization (blocks calibration).
- [ ] Caster load rating — needs the frame's actual assembled weight, not yet measured.
- [ ] Whether spray-width tapering near edges gets built alongside the PWM base case or deferred.
