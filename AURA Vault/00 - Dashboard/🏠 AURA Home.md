---
tags: [dashboard, moc, aura]
created: 2026-03-29
updated: 2026-07-31
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
| **Current Phase** | Phase 2 — Gantry Build + Continued Dataset Expansion |
| **AI Status** | ✅ 300-image fine-tune done — mAP@0.50 **0.780**, precision **0.845**, recall **0.729**; expanding toward 1,000 |
| **Software Status** | ✅ Model deployed behind local Flask API (~100 ms/frame on RTX 3050); website running on live inference — see [[🔌 Backend API & Web Integration]] |
| **Hardware Status** | ✅ All parts procured; build starting |
| **Open Decision** | Single vs. dual V-slot rail on bottom axis (see [[🔧 Assembly Log]]) |
| **Next Milestone** | Lock rail config → begin gantry frame assembly |
| **Budget Cap** | PHP 35,000 |
| **Budget Committed** | ~PHP 6,300 (pre-build) — update after hardware purchases confirmed |
| **Budget Remaining** | ~PHP 28,700 |
| **Defense Target** | November–December 2026 |
| **Lead Researcher** | Manabat, Kurt Robyn A. |

---

## 🗺️ Navigation (Map of Content)

- **Project Management** — [[📋 Master Task Tracker]] · [[📅 Timeline & Milestones]] · [[💰 Budget Tracker]] · [[⚠️ Risk Register]]
- **Research** — [[📚 Literature Review Master]] · [[🔍 Research Gaps & Justification]]
- **System Design** — [[🏗️ System Architecture Overview]] · [[⚙️ Mechanical Design]] · [[🔌 Electronics & Wiring]] · [[🧠 AI & Software Design]] · [[💧 Spray System Design]]
- **AI & Code** — [[🔮 Segmentation Model]] · [[🎨 Color Recommendation Module]] · [[🔌 Backend API & Web Integration]] · [[🖥️ Serial Communication Protocol]] · [[📐 Path Planning & G-code Generation]]
- **Hardware & Build** — [[🛒 Bill of Materials]] · [[🔧 Assembly Log]] · [[🧪 Calibration & Testing Log]]
- **Thesis Paper** — [[📝 Chapter 1 - Introduction]] · [[📝 Chapter 2 - Review of Related Literature]] · [[📝 Chapter 3 - Methodology]] · [[📝 Chapter 4 - Results]] · [[📝 Chapter 5 - Discussion]] · [[📝 Writing Notes & Advisor Feedback]]
- **Defense Prep** — [[🎤 Defense Script & Talking Points]] · [[❓ Anticipated Panel Questions & Answers]] · [[📊 Presentation Outline]]
- **Meetings** — [[📓 Meeting Log Template]]

---

## 🎯 Today's Focus (2026-07-31)

- [x] 300-image fine-tune complete with recorded metrics (mAP@0.50 0.780) — [[🔮 Segmentation Model]]
- [x] Model deployed behind local Flask API; all website pages on live inference — [[🔌 Backend API & Web Integration]]
- [x] Colour recommendation implemented against the segmentation mask — [[🎨 Color Recommendation Module]]
- [x] Chapter 4 §4.2 populated with preliminary segmentation results
- [ ] **Decide class names before the next Roboflow export** — `non-paintable` collides with `paintable` under substring matching (see [[🔮 Segmentation Model]])
- [ ] Decide: single vs. dual V-slot rail on bottom axis
- [ ] Begin frame assembly once rail config locked

### Previously (2026-07-30)
- [x] First custom fine-tune run — instance segmentation confirmed working (~150 images)
- [x] Object detection annotation tried and ruled out (bounding boxes only, not masks)
- [x] All gantry parts procured

---

> [!danger] Critical Risks (see [[⚠️ Risk Register]])
> 1. **Spray timing / dripping** — synchronizing solenoid firing with gantry position is the hardest calibration problem; overspray and drip can ruin every output test.
> 2. **Single point of failure** — only Kurt has real technical capability; illness or overload stalls the whole project.
> 3. **Gantry racking** — if the two X-axis NEMA 23 motors lose sync, the frame skews and positional accuracy collapses.
> 4. **Dataset size** — currently 300 images (mAP@0.50 0.780, recall 0.729); 1,000 target needed for robust fine-tune. Recall is the weak metric — the model misses wall area on novel walls, which more data should lift.

---

## 🔒 Key Decisions Made

1. **Dual X-axis NEMA 23 motors** to prevent gantry racking; single motor on Y-axis.
2. **TB6600 drivers over A4988** — NEMA 23 draws up to ~4.5A, far beyond A4988's limit.
3. **Arduino Mega 2560 + RAMPS 1.4** as the motion backbone, used strictly as a STEP/DIR/endstop breakout — RAMPS does not power the motors. The 24V/30A PSU feeds the TB6600 drivers directly.
4. **Laptop (RTX 3050) does all AI inference**; Arduino only executes motion + spray commands over USB serial (pyserial, 115200 baud, GRBL-style G-code).
5. **YOLOv8 (Ultralytics) instance segmentation** confirmed — object detection (bounding boxes) was tested and ruled out. Fine-tuning on Roboflow-labeled dataset via Kaggle Tesla T4 GPU. *(Supersedes earlier MobileNetV3 + DeepLabV3+ plan — see [[🔮 Segmentation Model]].)*
6. **OpenCV-based homography and scaling calibration** (physical corner markers) maps segmentation-mask pixel coordinates to real-world millimeter positions on the wall.
7. **Raster-scan (boustrophedon) toolpath planning** for reliability over optimality at prototype scale.
8. **Performance is benchmarked against recognized external standards**, not internal thresholds: ISO 9283:1998 (positional accuracy), COCO evaluation protocol (segmentation IoU/mAP), ASTM D823 (spray consistency/coverage uniformity), ISO/IEC 25010:2011 (color-recommendation quality), and IEEE 1872-2015 (system integration).
9. **Color reproduction accuracy (CIE ΔE\*) is explicitly out of scope.** AURA sprays pre-loaded paint and does not mix or synthesize color, so there is no mechanism to verify that the *applied* paint color matches the *recommended* color. Evaluation is limited to color **recommendation quality** (visual coherence/suitability, rated by human evaluators) — see [[🔍 Research Gaps & Justification]] and [[📝 Chapter 1 - Introduction]].
10. **Bottom V-slot rail config — PENDING.** Debating single rail vs. dual rails for the bottom axis. Decision must be locked before frame assembly begins.
11. **Local Flask API is the integration layer** between the model and everything else. The website talks to `localhost:5000`; gantry control will attach to the same server rather than running as a separate script. Chosen over FastAPI because the MJPEG webcam stream is a blocking generator that Flask's threaded server handles without async ceremony. See [[🔌 Backend API & Web Integration]].
12. **No CDN dependencies anywhere in the demo UI.** The colour wheel is drawn on a canvas rather than loaded from a CDN, because a `<script src="https://…">` fails silently with no internet and the defense venue's connectivity cannot be assumed.
13. **Colour recommendation clusters the non-wall regions, not the whole image.** Whole-image clustering returns the wall's *current* paint as the dominant colour, so the module would harmonise against the colour being painted over. The segmentation mask is therefore load-bearing for colour recommendation, not just path planning — see [[🎨 Color Recommendation Module]].

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

- [[📝 Chapter 1 - Introduction]] — synced with finalized thesis text (2026-07-18)
- [[📝 Chapter 2 - Review of Related Literature]] — synced with expanded RRL (2026-07-18)
- [[📝 Chapter 3 - Methodology]] — synced with finalized Methods + external-standards evaluation (2026-07-18)
- [[📝 Chapter 4 - Results]] — pending testing (color-reproduction row removed)
- [[📝 Chapter 5 - Discussion]] — pending results

> [!tip]
> This vault is the single source of truth for AURA. Log every decision, test, and advisor note here. The full manuscript prose lives in `aura_thesis_rewrite.md` / the exported Word document — these notes track the *current decisions* that manuscript reflects.
