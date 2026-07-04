---
tags: [meeting, template]
created: 2026-03-29
status: active
---
# 📓 Meeting Log Template

> [!info] Copy the template block for each new meeting. A filled example follows.

## Template
```
---
date:
attendees:
type: [Adviser Meeting / Team Meeting / Consultation]
tags: [meeting]
---
# Meeting — [Date]
## Agenda
## Discussion Points
## Decisions Made
## Action Items
- [ ] [Task] — [Person] — [Deadline]
## Next Meeting
```

---

## Example — First Post-Concept-Paper Adviser Meeting

---
date: 2026-04-06
attendees: Kurt Manabat, Reymon David Jr., Lester Usi, Adviser
type: Adviser Meeting
tags: [meeting]
---
### Meeting — 2026-04-06

#### Agenda
- Review concept paper feedback
- Confirm methodology direction (Chapter 3)
- Plan procurement wave 1

#### Discussion Points
- Adviser affirmed the integrated scope but cautioned against over-scoping the AI; advised keeping segmentation **binary** for the first working version.
- Confirmed dual-X NEMA 23 decision is sound for anti-racking; adviser asked for a steps-per-mm calibration plan.
- Discussed spray as the highest-risk subsystem; adviser recommended a dedicated spray-only test rig before full integration.
- Budget reviewed; adviser suggested V-wheels over full linear rails to protect the budget.
- Agreed evaluators for color recommendation should be n≥5, mixed students/faculty.

#### Decisions Made
- Start with **binary segmentation** (paintable vs not) on ADE20K + small custom set.
- Order frame, motors, drivers, and controller first (long-lead items).
- Build a **standalone spray test rig** in parallel with the gantry.

#### Action Items
- [ ] Finalize supplier list and place procurement wave 1 — Kurt — 2026-04-20
- [ ] Draft steps-per-mm calibration procedure — Kurt — 2026-04-13
- [ ] Prepare small custom annotation set (LabelMe) — Kurt — 2026-04-27
- [ ] Source spray pump + solenoid for test rig — David/Usi — 2026-04-20

#### Next Meeting
2026-05-04 — review procurement status and assembly start.
