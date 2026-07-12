---
tags: [dashboard, moc, aura]
created: 2026-03-29
updated: 2026-07-12
status: active
---
# 🏠 AURA — Home

> **AURA — AI-Based Autonomous Wall Painting Robot**
> *AURA: An AI-Based Autonomous Wall Painting Robot Integrating Deep Learning Segmentation, Color Recommendation, and Adaptive Spray Control*
> Bachelor of Science in Computer Engineering — School of Engineering and Architecture
> **Holy Angel University**, Angeles City, Pampanga, Philippines
> Researchers: **Manabat, Kurt Robyn A.** · David, Reymon Jr G. · Usi, Lester
> Concept Paper submitted: **29 March 2026**

---

## 📊 Status Panel

| Field | Value |
|---|---|
| **Current Phase** | Phase 1 — Hardware Procurement & Assembly |
| **Next Milestone** | Complete component sourcing & first motor test (target: Aug 2026) |
| **Budget Cap** | PHP 35,000 |
| **Budget Committed** | ~PHP 6,300 |
| **Budget Remaining** | ~PHP 28,700 |
| **Defense Target** | November–December 2026 |
| **Lead Researcher** | Manabat, Kurt Robyn A. |

---

## 🗺️ Navigation (Map of Content)

- **Project Management** — [[📋 Master Task Tracker]] · [[📅 Timeline & Milestones]] · [[💰 Budget Tracker]] · [[⚠️ Risk Register]]
- **Research** — [[📚 Literature Review Master]] · [[🔍 Research Gaps & Justification]]
- **System Design** — [[🏗️ System Architecture Overview]] · [[⚙️ Mechanical Design]] · [[🔌 Electronics & Wiring]] · [[🧠 AI & Software Design]] · [[💧 Spray System Design]]
- **AI & Code** — [[🔮 Segmentation Model]] · [[🎨 Color Recommendation Module]] · [[🖥️ Serial Communication Protocol]] · [[📐 Path Planning & G-code Generation]]
- **Hardware & Build** — [[🛒 Bill of Materials]] · [[🔧 Assembly Log]] · [[🧪 Calibration & Testing Log]]
- **Thesis Paper** — [[📝 Chapter 1 - Introduction]] · [[📝 Chapter 2 - Review of Related Literature]] · [[📝 Chapter 3 - Methodology]] · [[📝 Chapter 4 - Results]] · [[📝 Chapter 5 - Discussion]] · [[📝 Writing Notes & Advisor Feedback]]
- **Defense Prep** — [[🎤 Defense Script & Talking Points]] · [[❓ Anticipated Panel Questions & Answers]] · [[📊 Presentation Outline]]
- **Meetings** — [[📓 Meeting Log Template]]

---

## 🎯 Today's Focus

- [x] Finalize supplier shortlist for 2040 extrusions and NEMA 23 motors (Lazada PH vs local Pampanga surplus)
- [x] Confirm TB6600 DIP-switch current/microstepping settings in [[🔌 Electronics & Wiring]] before ordering PSU
- [ ] Download ADE20K subset and draft annotation plan in [[🔮 Segmentation Model]]

---

> [!danger] Critical Risks (see [[⚠️ Risk Register]])
> 1. **Spray timing / dripping** — synchronizing solenoid firing with gantry position is the hardest calibration problem; overspray and drip can ruin every output test.
> 2. **Single point of failure** — only Kurt has real technical capability; illness or overload stalls the whole project.
> 3. **Gantry racking** — if the two X-axis NEMA 23 motors lose sync, the frame skews and positional accuracy collapses.

---

## 🔒 Key Decisions Made

1. **Dual X-axis NEMA 23 motors** to prevent gantry racking; single motor on Y-axis.
2. **TB6600 drivers over A4988** — NEMA 23 draws up to ~4.5A, far beyond A4988's limit.
3. **Arduino Mega 2560 + RAMPS 1.4** as the motion backbone, used strictly as a STEP/DIR/endstop breakout — RAMPS does not power the motors. The 24V/30A PSU feeds the TB6600 drivers directly.
4. **Laptop (RTX 3050) does all AI inference**; Arduino only executes motion + spray commands over USB serial (pyserial, 115200 baud, GRBL-style G-code).
5. **YOLOv8 (Ultralytics) instance segmentation**, evaluated zero-shot-first against COCO-pretrained weights, with fine-tuning on a Roboflow-labeled dataset via Kaggle Tesla T4 GPU pursued only if zero-shot performance proves insufficient. *(Supersedes the earlier MobileNetV3 + DeepLabV3+ plan — see [[🔮 Segmentation Model]].)*
6. **OpenCV-based homography and scaling calibration** (physical corner markers) maps segmentation-mask pixel coordinates to real-world millimeter positions on the wall.
7. **Raster-scan (boustrophedon) toolpath planning** for reliability over optimality at prototype scale.
8. **Performance is benchmarked against recognized external standards**, not internal thresholds: ISO 9283:1998 (positional accuracy), COCO evaluation protocol (segmentation IoU/mAP), ASTM D4147 & D3270 (spray consistency/coverage uniformity), ISO/IEC 25010:2011 (color-recommendation quality), and IEEE 1872-2015 (system integration).
9. **Color reproduction accuracy (CIE ΔE\*) is explicitly out of scope.** AURA sprays pre-loaded paint and does not mix or synthesize color, so there is no mechanism to verify that the *applied* paint color matches the *recommended* color. Evaluation is limited to color **recommendation quality** (visual coherence/suitability, rated by human evaluators) — see [[🔍 Research Gaps & Justification]] and [[📝 Chapter 1 - Introduction]].

---

## ✅ Task Query (Dataview)

```dataview
TASK
FROM "01 - Project Management/📋 Master Task Tracker"
WHERE !completed
GROUP BY header
```

```dataview
TABLE status, file.mtime AS "Last Modified"
FROM "06 - Thesis Paper"
SORT file.name ASC
```

---

## 📝 Chapter Drafts Quick Links

- [[📝 Chapter 1 - Introduction]] — synced with finalized thesis text (2026-07-12)
- [[📝 Chapter 2 - Review of Related Literature]] — synced with expanded RRL (2026-07-12)
- [[📝 Chapter 3 - Methodology]] — synced with finalized Methods + external-standards evaluation (2026-07-12)
- [[📝 Chapter 4 - Results]] — pending testing (color-reproduction row removed)
- [[📝 Chapter 5 - Discussion]] — pending results

> [!tip]
> This vault is the single source of truth for AURA. Log every decision, test, and advisor note here. The full manuscript prose lives in `aura_thesis_rewrite.md` / the exported Word document — these notes track the *current decisions* that manuscript reflects.
