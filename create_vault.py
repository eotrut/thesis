No one think about upper objectable everything one fifty nine# -*- coding: utf-8 -*-
"""
create_vault.py
Self-contained generator for the AURA thesis Obsidian vault.

Change VAULT_ROOT below to point at your Obsidian vault location, then run:
    python create_vault.py

Every note is hardcoded as a string. The script creates the full folder
structure and writes each note as a .md file, printing a confirmation per file.
"""

import os

# ---------------------------------------------------------------------------
# CHANGE THIS to point at where you want the "AURA Vault" folder created.
# On Windows, e.g.: r"C:\\Users\\Kurt\\Documents\\Obsidian\\AURA Vault"
# ---------------------------------------------------------------------------
VAULT_ROOT = os.path.join(os.getcwd(), "AURA Vault")

FILES = []


def add(path, content):
    FILES.append((path, content))


# ===========================================================================
# FILE CONTENT DEFINITIONS
# ===========================================================================

add("00 - Dashboard/🏠 AURA Home.md", r'''---
tags: [dashboard, moc, aura]
created: 2026-03-29
status: active
---
# 🏠 AURA — Home

> **AURA — Autonomous Unified Robotic Adaptive**
> *Deep Learning-Based Autonomous Wall Painting Robot*
> Bachelor of Science in Computer Engineering — School of Engineering and Architecture
> **Holy Angel University**, Angeles City, Pampanga, Philippines
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

- [ ] Finalize supplier shortlist for 2040 extrusions and NEMA 23 motors (Lazada PH vs local Pampanga surplus)
- [ ] Confirm TB6600 DIP-switch current/microstepping settings in [[🔌 Electronics & Wiring]] before ordering PSU
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
3. **Arduino Mega 2560 + RAMPS 1.4** as the motion backbone, running a G-code firmware (GRBL/Marlin variant).
4. **Laptop (RTX 3050) does all AI inference**; Arduino only executes motion + spray commands over USB serial.
5. **Lightweight segmentation** (MobileNetV3 + DeepLabV3+) to fit inside the 4GB VRAM budget; raster-scan path planning for reliability.

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

- [[📝 Chapter 1 - Introduction]] — draft complete
- [[📝 Chapter 2 - Review of Related Literature]] — draft complete
- [[📝 Chapter 3 - Methodology]] — draft complete
- [[📝 Chapter 4 - Results]] — pending testing
- [[📝 Chapter 5 - Discussion]] — pending results

> [!tip]
> This vault is the single source of truth for AURA. Log every decision, test, and advisor note here.
''')

add("01 - Project Management/📋 Master Task Tracker.md", r'''---
tags: [project-management, tasks, tracker]
created: 2026-03-29
status: active
---
# 📋 Master Task Tracker

> [!info] How to use
> Tasks are grouped by phase. Check items as you complete them. Home dashboard pulls from this note via Dataview. Related: [[📅 Timeline & Milestones]] · [[⚠️ Risk Register]].

## Phase 0 — Planning & Concept Paper
- [x] Concept paper written and submitted (29/03/2026)
- [x] Literature review completed
- [x] System architecture (IPO) defined
- [x] Hardware components identified
- [x] Budget estimated
- [x] Research questions & objectives locked
- [x] Scope and delimitations defined

## Phase 1 — Hardware Procurement & Assembly
- [x] Source and purchase aluminum extrusion rails
- [x] Purchase Arduino Mega + RAMPS 1.4
- [ ] Purchase NEMA 23 motors (×3)
- [ ] Purchase TB6600 drivers (×3)
- [ ] Purchase GT2 belts, pulleys, bearings
- [ ] Purchase 24V 30A PSU
- [ ] Purchase spray nozzle / airbrush mechanism
- [ ] Purchase pump and solenoid valve
- [ ] Assemble X-axis base rail
- [ ] Assemble Y-axis vertical column
- [ ] Wire motors to drivers
- [ ] Wire drivers to RAMPS 1.4
- [ ] Test motor movement (no load)
- [ ] Calibrate limit switches / homing

## Phase 2 — Firmware & Motion Control
- [ ] Flash Arduino with GRBL or custom firmware
- [ ] Define G-code command set
- [ ] Write Python serial controller script
- [ ] Test XY movement to commanded coordinates
- [ ] Measure positional error (motion accuracy test)
- [ ] Tune stepper speed, acceleration, microstepping

## Phase 3 — AI Model Development
- [ ] Collect/source wall image dataset
- [ ] Annotate images for segmentation
- [ ] Choose model architecture (MobileNet/DeepLab or custom CNN)
- [ ] Train segmentation model
- [ ] Evaluate segmentation accuracy (IoU / pixel accuracy)
- [ ] Integrate model inference into Python pipeline
- [ ] Connect segmentation output to path planner
- [ ] Develop color recommendation module (K-means + harmony rules)
- [ ] Test color recommendations with evaluators (qualitative, n≥5)

## Phase 4 — System Integration
- [ ] Connect laptop AI pipeline to Arduino serial
- [ ] Synchronize spray on/off with gantry position
- [ ] Full dry-run test (no paint)
- [ ] First live paint test (single color, simple shape)
- [ ] Multi-color region test
- [ ] Simple mural design test
- [ ] Record all evaluation metrics

## Phase 5 — Thesis Writing & Defense
- [ ] Complete Chapter 3 (Methodology)
- [ ] Complete Chapter 4 (Results) — after testing
- [ ] Complete Chapter 5 (Discussion)
- [ ] Compile full references in APA format
- [ ] Internal review / proofreading
- [ ] Submit draft to adviser
- [ ] Revise based on feedback
- [ ] Prepare defense presentation
- [ ] Conduct mock defense
- [ ] Final defense
''')

add("01 - Project Management/📅 Timeline & Milestones.md", r'''---
tags: [project-management, timeline, milestones]
created: 2026-03-29
status: active
---
# 📅 Timeline & Milestones

> [!note] Baseline
> Concept paper submitted **29 March 2026**. Defense targeted **late November–December 2026**. Timeline assumes Kurt as sole engineer, part-time alongside coursework, with deliberate risk buffers.

## Month-by-Month Plan

| Month | Focus | Key Milestone | Critical Path? |
|---|---|---|---|
| **Apr 2026** | Detailed design freeze; finalize BOM; first adviser meeting | Design & BOM approved | ✅ |
| **May 2026** | Procurement wave 1 (frame, motors, drivers, controller) | All long-lead parts ordered | ✅ |
| **Jun 2026** | Mechanical assembly (X + Y axes); wiring | Gantry frame standing | ✅ |
| **Jul 2026** | Electronics integration; firmware flash | Motors move under command | ✅ |
| **Aug 2026** | Motion tuning + accuracy tests; dataset collection begins | Positional error < target | ✅ |
| **Sep 2026** | Segmentation model training + eval; color module | Model mIoU ≥ 0.65 | ✅ |
| **Oct 2026** | System integration; spray sync; paint tests | First successful painted design | ✅ |
| **Nov 2026** | Metrics collection; Chapters 4–5; presentation build | Results chapter complete | ✅ |
| **Dec 2026** | Mock defense → revisions → **Final Defense** | Thesis defended | ✅ |

## Milestone Gates

> [!success] M1 — Design Freeze (end Apr)
> BOM locked, wiring diagram final, methodology drafted. Gate to spending.

> [!success] M2 — Moving Gantry (end Jul)
> Frame assembled, motors driven by Arduino, homing works. Gate to AI integration.

> [!success] M3 — AI Ready (end Sep)
> Segmentation + color module validated on test set. Gate to full integration.

> [!success] M4 — First Paint (mid Oct)
> A simple 2-color design painted on a 1m × 1m board. Gate to metrics collection.

> [!success] M5 — Defense (Dec)
> All chapters complete, mock defense passed.

## Risk Buffers
- **2-week buffer** built into Aug (motion tuning historically overruns).
- **2-week buffer** in Oct (spray calibration is the highest-risk task — see [[💧 Spray System Design]]).
- Procurement started early (May) to absorb Lazada/Shopee shipping delays.

## Critical Path Narrative
The critical path runs: **procurement → mechanical assembly → firmware → motion accuracy → integration → paint tests → results**. AI model training (Sep) can partially parallelize with mechanical work, but *cannot be validated end-to-end* until the gantry moves. Any slip in the mechanical build cascades directly to the defense date. See [[⚠️ Risk Register]] R-09 (shipping delays) and R-02 (racking).
''')

add("01 - Project Management/💰 Budget Tracker.md", r'''---
tags: [project-management, budget, finance]
created: 2026-03-29
status: active
---
# 💰 Budget Tracker

> [!warning] Hard cap: **PHP 35,000**. Target spend: **PHP 30,000–35,000**.
> Prices are realistic PH-market estimates (Lazada PH, Shopee PH, Octagon, local Pampanga/Manila surplus). Actuals to be filled as purchases are made. See [[🛒 Bill of Materials]].

## Budget by Category

| # | Item | Qty | Est. Unit (PHP) | Est. Total (PHP) | Actual (PHP) | Source | Flag |
|---|---|---|---|---|---|---|---|
| 1 | 2040 Aluminum Extrusion (per m) | ~8 m | 800 | 6,400 | 2,400 (partial) | Local surplus / Lazada | 💸 budget risk |
| 2 | NEMA 23 Stepper Motor | 3 | 1,200 | 3,600 | — | Lazada PH | 💸 budget risk |
| 3 | TB6600 Driver | 3 | 550 | 1,650 | — | Shopee PH | |
| 4 | Arduino Mega 2560 (clone) | 1 | 500 | 500 | 480 | Lazada PH | ♻️ cheaper local |
| 5 | RAMPS 1.4 shield | 1 | 400 | 400 | 380 | Shopee PH | |
| 6 | GT2 belt + pulleys + idlers | set | 500 | 500 | — | Lazada PH | |
| 7 | Linear rails + blocks (MGN set ×2) | 2 | 1,800 | 3,600 | — | Lazada PH | 💸 budget risk / ♻️ surplus V-wheels |
| 8 | 24V 30A PSU | 1 | 1,300 | 1,300 | — | Octagon / Lazada | |
| 9 | Spray nozzle / airbrush gun | 1 | 1,000 | 1,000 | — | Lazada / hardware | |
| 10 | Electric pump (peristaltic/diaphragm) | 1 | 900 | 900 | — | Lazada PH | ⚠️ spec-critical |
| 11 | Solenoid valve (12/24V) | 1 | 350 | 350 | — | Shopee PH | |
| 12 | Tubing, fittings, reservoir | set | 450 | 450 | — | Hardware store | |
| 13 | USB Camera (HD) | 1 | 800 | 800 | — | Lazada PH | ♻️ reuse webcam |
| 14 | Limit switches | 4 | 60 | 240 | — | Shopee PH | |
| 15 | Power connectors, wiring, terminals | set | 500 | 500 | — | Deeco / hardware | |
| 16 | Screws, brackets, nuts, T-nuts | set | 600 | 600 | — | Local hardware | |
| 17 | Paint supplies (testing) | set | 800 | 800 | — | National Book Store / hardware | |
| 18 | **Contingency (~10%)** | — | — | 2,500 | — | — | keep untouched |
| | **ESTIMATED TOTAL** | | | **26,090** | **~3,640 spent** | | |

## Running Totals

| | PHP |
|---|---|
| Budget cap | 35,000 |
| Estimated total spend | 26,090 |
| Committed / spent so far | ~6,300 (incl. partial extrusion) |
| Remaining vs cap | ~28,700 |
| Head-room vs estimate | ~8,910 |

> [!danger] Most likely to blow the budget
> - **Linear rails (item 7)** — genuine MGN rails are pricey. **Mitigation:** use V-Slot wheels riding directly in the 2040 extrusion for the prototype; save rails for one axis only if precision demands it.
> - **NEMA 23 motors (item 2)** — 3 motors add up fast. **Mitigation:** buy 2 first (dual-X) + reuse a spare/borrowed motor for Y initial testing.
> - **Extrusion (item 1)** — long lengths + shipping. **Mitigation:** buy cut-to-length from a local Pampanga metal supplier instead of shipping full bars.

> [!tip] Cheaper local alternatives
> - Reuse an existing laptop webcam instead of buying a USB camera (item 13).
> - Salvage 24V PSU from a scrapped 3D printer / CCTV supply (item 8).
> - Buy fasteners loose by weight at a Manila hardware surplus rather than kits (item 16).
''')

add("01 - Project Management/⚠️ Risk Register.md", r'''---
tags: [project-management, risk, register]
created: 2026-03-29
status: active
---
# ⚠️ Risk Register

> [!info] Legend
> Likelihood / Impact: **H** = High, **M** = Medium, **L** = Low. Risk Level = combined severity. Review monthly at adviser meetings. Related: [[📅 Timeline & Milestones]] · [[💧 Spray System Design]] · [[💰 Budget Tracker]].

| ID | Description | Category | Likelihood | Impact | Risk Level | Mitigation | Owner |
|---|---|---|---|---|---|---|---|
| R-01 | Spray system drips or clogs, ruining output | Technical | H | H | 🔴 Critical | Water-based acrylic, thinner tuning, purge cycles before each run, solenoid + short tubing near nozzle | Kurt |
| R-02 | Gantry racking from X-axis motor desync | Technical | M | H | 🔴 Critical | Dual NEMA 23 mirrored on RAMPS, matched belts/pulleys, square frame, homing both corners | Kurt |
| R-03 | Serial lag causes misaligned paint strokes | Technical | M | H | 🟠 High | 115200 baud, coordinate-arrival trigger for spray, ack (`ok`) handshake, buffer tuning | Kurt |
| R-04 | AI model underfits on limited training data | Technical | H | M | 🟠 High | Transfer learning from ImageNet, data augmentation, use ADE20K wall class, keep task binary if needed | Kurt |
| R-05 | RTX 3050 4GB VRAM insufficient for model | Technical | M | M | 🟡 Medium | MobileNetV3 backbone, batch size 4, 512×512 input, mixed precision, fallback to U-Net | Kurt |
| R-06 | Budget overrun on mechanical parts | Budget | M | H | 🟠 High | V-wheels instead of full linear rails, local cut-to-length extrusion, 10% contingency held | Kurt |
| R-07 | Single capable member = single point of failure | Team | H | H | 🔴 Critical | Document everything in this vault, cross-train David/Usi on assembly + logging, back up code to GitHub | Kurt |
| R-08 | Adviser rejects methodology | Timeline | L | H | 🟡 Medium | Early adviser meeting (Apr), align Ch.3 with objectives + metrics, iterate before build | Kurt |
| R-09 | Component shipping delays (Lazada/Shopee) | Timeline | M | M | 🟡 Medium | Order long-lead items in May, prefer local stock, keep buffer weeks in schedule | Kurt |
| R-10 | RAMPS 1.4 / drivers overheat | Technical | M | M | 🟡 Medium | Heatsinks + fan on drivers, set TB6600 current correctly, avoid stalling motors | Kurt |
| R-11 | Color recommendation outputs look bad | Technical | M | M | 🟡 Medium | K-means + established harmony rules, cap palette size, evaluator feedback loop (n≥5) | Kurt |
| R-12 | Panel questions lack of industrial applicability | Defense | M | M | 🟡 Medium | Frame as proof-of-concept, cite scalability path, emphasize integrated novelty | Kurt |
| R-13 | Dataset annotation too time-consuming | Timeline | H | M | 🟠 High | Use pre-labeled ADE20K, annotate only a small custom set with LabelMe, binary masks | Kurt |
| R-14 | Paint clogs nozzle mid-test | Technical | H | M | 🟠 High | Strain paint, flush after each run, keep nozzle capped between tests, spare nozzle on hand | Kurt |
| R-15 | Positional error exceeds acceptable threshold | Technical | M | H | 🟠 High | Microstepping 1/8–1/16, belt tension, calibrate steps/mm, closed-loop homing each run | Kurt |
| R-16 | Power supply / wiring short or failure | Technical | L | H | 🟡 Medium | Fusing on 24V line, strain relief, terminal blocks, double-check polarity before power-on | Kurt |
| R-17 | Scope creep (3D, curved walls, mobility) | Timeline | M | M | 🟡 Medium | Hold scope to flat 1m×1m board, 2D, simple murals; defer extras to "future work" | Kurt |

> [!danger] Top 3 to watch
> **R-01 (spray)**, **R-07 (single point of failure)**, and **R-02 (racking)** are the project killers. Every monthly review starts here.
''')

add("02 - Research/📚 Literature Review Master.md", r'''---
tags: [research, literature-review, synthesis]
created: 2026-03-29
status: active
---
# 📚 Literature Review Master

> [!info] Purpose
> A *thematic synthesis* of the literature — not a list of summaries. Feeds directly into [[📝 Chapter 2 - Review of Related Literature]]. Individual paper notes live in `02 - Research/References/`. Gaps are consolidated in [[🔍 Research Gaps & Justification]].

## Theme 1 — Mechanical Wall Painting Automation

The earliest and most consistent thread in the literature is the mechanical automation of wall painting. [[Kumote 2022 - Auto Wall Painting Robot]] and [[Patil 2021 - Autonomous Wall Painting Robot]] both demonstrate XY-based painting platforms driven by pre-programmed motion, with Kumote adding sensor feedback for wall detection. Rudzuan (2019) extends this to a gantry spray system with multi-axis control, and [[Tawade 2024 - XY Gantry Material Handling]] validates the XY-gantry kinematics that AURA reuses for its motion stage. At the applied end, [[RSIS 2025 - Arduino Wall Painting Robot]] shows a low-cost Arduino-driven build closely matching AURA's budget class, while Al Mawali & Hussain (2023) introduce a color sensor and a color database to select paint.

**What exists:** reliable XY/gantry motion, roller/spray end-effectors, Arduino-class controllers, and basic sensor feedback.
**The gap:** these systems execute *fixed, pre-programmed* paths. They do not *perceive* the wall to decide **where** paint should go, nor reason about **which colors** to apply. Painting is mechanical reproduction, not visual understanding.
**How AURA addresses it:** AURA keeps the proven XY-gantry + Arduino motion backbone but replaces fixed programming with a **deep-learning perception layer** that segments paintable regions and an **AI color recommender**, turning a "plotter with paint" into a system that decides its own targets.

## Theme 2 — AI & Computer Vision in Robotic Systems

A second thread applies deep learning to visual understanding for robots. [[Bjekic 2023 - Wall Segmentation CNN]] is the most directly relevant: it segments walls from single 2D images using a CNN, which is precisely the perception primitive AURA needs. [[Tiboni 2022 - PaintNet]] and [[Liu & Cheng 2024 - Semantic Segmentation Spray]] push further into spray robotics — PaintNet learns spray trajectories from 3D point clouds, and Liu & Cheng combine semantic segmentation with trajectory optimization for spray robots. On the inspection side, Shaikh & Kokate (2025) and [[Nimje 2025 - AI Vision Panel Defects]] report deep-vision surface/defect analysis exceeding 95% accuracy, and Ni et al. (2023) survey deep-learning scene understanding for autonomous robots.

**What exists:** mature CNN segmentation for walls and scenes, learned spray trajectories, and high-accuracy visual inspection.
**The gap:** these capabilities are demonstrated in **isolation** — segmentation *or* trajectory learning *or* inspection — and several (PaintNet, Liu & Cheng) assume **3D point clouds and industrial hardware** unavailable to an undergraduate prototype. None couple *lightweight 2D segmentation* to *low-cost gantry actuation* end-to-end.
**How AURA addresses it:** AURA adopts a lightweight 2D segmentation model (MobileNetV3 + DeepLabV3+, per [[🔮 Segmentation Model]]) explicitly chosen to run on a 4GB RTX 3050, and wires its output through a raster path planner to physical motion — closing the perception-to-actuation loop on affordable hardware.

## Theme 3 — Intelligent Control & Adaptive Systems

The third thread concerns intelligence and adaptivity in control. [[Aziz 2026 - 4DOF SCARA ML]] models a 4-DOF SCARA arm and layers machine learning (SVM, Random Forest) onto its kinematics, showing ML can refine robotic control. Kiran & Prabhu (2020) review nano-spray painting robots and highlight flow/atomization control as the decisive quality factor. IEEE (2022) surveys autonomous robotic systems and sensor integration, and [[Faheem 2024 - AI Robotics Construction]] frames AI + robotics as an emerging force in construction automation, of which wall finishing is a natural sub-domain.

**What exists:** evidence that ML improves control, that spray/flow control governs finish quality, and that construction is a legitimate application domain.
**The gap:** adaptive *spray* control tied to *perception* is under-explored at the prototype scale — most adaptivity is in arm kinematics, not in coordinating **where to spray, how much, and in what color** as one loop.
**How AURA addresses it:** AURA treats spray as an *adaptive* subsystem (solenoid + pump timed to gantry position, per [[💧 Spray System Design]]) coordinated with segmentation output and color recommendation — integrating perception, motion, and flow rather than optimizing any one in isolation.

## Overall Synthesis — The Gap AURA Fills

Across all three themes, the literature has independently matured (a) affordable XY/gantry painting mechanics, (b) deep-learning 2D scene/wall segmentation, and (c) intelligent/adaptive control — but **no accessible, undergraduate-scale system unifies perception, color reasoning, motion, and adaptive spray into a single automated wall-painting pipeline.** Prior painting robots are blind and pre-programmed; prior vision work is disembodied or demands industrial 3D sensing; prior adaptive control targets arms, not integrated painting. AURA's contribution is precisely this **integration on a PHP ≤35,000 budget**: lightweight segmentation and AI color recommendation driving a dual-motor XY gantry with adaptive spray — demonstrating that intelligent, self-directed wall painting is achievable without industrial hardware.
''')

add("02 - Research/🔍 Research Gaps & Justification.md", r'''---
tags: [research, gaps, justification, defense]
created: 2026-03-29
status: active
---
# 🔍 Research Gaps & Justification

> [!tip] Defense weapon
> This note answers the panel's "**why does this research matter?**" question. Each gap names the papers that prove it exists and states exactly how AURA fills it. Pairs with [[📚 Literature Review Master]] and [[❓ Anticipated Panel Questions & Answers]].

## Gap 1 — Painting robots are pre-programmed, not perceptive
**The gap:** existing wall-painting robots follow fixed motion paths and cannot *decide* where to paint from the wall itself.
**Proof:** [[Kumote 2022 - Auto Wall Painting Robot]], [[Patil 2021 - Autonomous Wall Painting Robot]], and [[RSIS 2025 - Arduino Wall Painting Robot]] all rely on pre-programmed movement; none segment the wall to plan targets.
**How AURA fills it:** a deep-learning segmentation model ([[🔮 Segmentation Model]]) identifies paintable regions from a camera image, so paths are *generated from perception*, not hand-coded.

## Gap 2 — Vision-for-spray work assumes industrial 3D hardware
**The gap:** the strongest AI-spray research depends on 3D point clouds and industrial robots, out of reach for low-cost builds.
**Proof:** [[Tiboni 2022 - PaintNet]] learns trajectories from 3D point clouds; [[Liu & Cheng 2024 - Semantic Segmentation Spray]] pairs segmentation with industrial spray robots.
**How AURA fills it:** AURA uses **2D single-image segmentation** on a 4GB RTX 3050 driving a hobby-grade XY gantry — demonstrating the same perceive-then-spray idea at ~PHP 30k.

## Gap 3 — Capabilities exist in isolation, not integrated
**The gap:** segmentation, trajectory planning, spray control, and color selection appear separately, never as one closed pipeline.
**Proof:** [[Bjekic 2023 - Wall Segmentation CNN]] (segmentation only), [[Nimje 2025 - AI Vision Panel Defects]] (inspection only), Al Mawali & Hussain (2023) (color DB only).
**How AURA fills it:** AURA's architecture ([[🏗️ System Architecture Overview]]) chains camera → segmentation → color recommendation → path planning → serial → motion + adaptive spray as a *single* integrated system.

## Gap 4 — Color decisions are manual or database-lookups, not AI-generated
**The gap:** painting robots either use a fixed color or look up a color from a sensor/database; none *recommend* harmonious palettes.
**Proof:** Al Mawali & Hussain (2023) use a color sensor + database; other painting robots assume a pre-selected paint.
**How AURA fills it:** an AI color-recommendation module ([[🎨 Color Recommendation Module]]) clusters input imagery (K-means) and applies color-harmony rules to *generate* coherent palettes — evaluated by human raters.

## Gap 5 — Adaptive spray coordinated with perception is under-explored at prototype scale
**The gap:** adaptivity in the literature targets arm kinematics; spray flow is rarely coordinated with *where perception says to paint* on affordable hardware.
**Proof:** [[Aziz 2026 - 4DOF SCARA ML]] adds ML to arm kinematics; Kiran & Prabhu (2020) treat flow control in isolation; [[Faheem 2024 - AI Robotics Construction]] notes the domain gap in construction automation.
**How AURA fills it:** AURA times solenoid/pump actuation to gantry position and segmentation output ([[💧 Spray System Design]]), making spray an *adaptive* part of an integrated loop rather than a standalone valve.

> [!note] One-sentence justification
> AURA is justified because it is the first *undergraduate-affordable* system to unify deep-learning wall perception, AI color recommendation, XY-gantry motion, and adaptive spray into one automated painting pipeline — a combination no cited work achieves.
''')

add("02 - Research/References/Bjekic 2023 - Wall Segmentation CNN.md", r'''---
tags: [reference, ai-vision]
authors: Bjekic et al.
year: 2023
doi: n/a
---
# Wall Segmentation from 2D Images using CNNs
## Citation
Bjekic, M., et al. (2023). *CNN-based wall segmentation from 2D images.* (As cited in AURA concept paper, 2026.)
## Core Argument
Convolutional neural networks can accurately segment wall regions from ordinary single 2D images, without depth sensors or 3D reconstruction. This makes wall perception feasible on commodity cameras.
## Methodology
Trained a CNN segmentation model on annotated indoor images to produce per-pixel wall masks; evaluated with standard segmentation metrics (IoU / pixel accuracy).
## Key Findings
- Single-image 2D input is sufficient for reliable wall segmentation.
- CNN architectures generalize across varied indoor scenes.
- No specialized depth hardware required.
## Limitations
- Segmentation only — no downstream actuation or painting.
- Indoor scene focus; performance on textured/outdoor walls less characterized.
- Model size/latency not optimized for low-VRAM edge deployment.
## Relevance to AURA
This is AURA's core perception primitive: it proves the exact capability AURA needs — turning a wall photo into a paintable-region mask on a plain camera.
## AURA Builds On This By
Adopting 2D wall segmentation but making it **actionable** — feeding the mask into a raster path planner that drives a physical gantry, and choosing a *lightweight* backbone (MobileNetV3) to fit the RTX 3050's 4GB VRAM. See [[🔮 Segmentation Model]].
''')

add("02 - Research/References/Tiboni 2022 - PaintNet.md", r'''---
tags: [reference, ai-vision, spray]
authors: Tiboni et al.
year: 2022
doi: n/a
---
# PaintNet: Deep Learning of Spray Trajectories from 3D Point Clouds
## Citation
Tiboni, G., et al. (2022). *PaintNet: Unstructured multi-path learning from 3D point clouds for robotic spray painting.* (As cited in AURA concept paper, 2026.)
## Core Argument
Spray-painting trajectories can be learned directly from 3D geometry using deep networks, generating multi-path coverage plans for complex surfaces.
## Methodology
Deep model trained on 3D point clouds of objects paired with expert spray trajectories; predicts unstructured multi-path spray plans.
## Key Findings
- Learned trajectories generalize to unseen object geometries.
- Handles complex, non-planar surfaces.
- Removes manual trajectory programming.
## Limitations
- Requires 3D point-cloud input (depth scanners / industrial capture).
- Assumes industrial robot arms and compute.
- Not aimed at flat-wall, low-cost prototypes.
## Relevance to AURA
Demonstrates the "learn where/how to spray" vision AURA shares, and marks the *hardware ceiling* AURA deliberately avoids.
## AURA Builds On This By
Replacing 3D point-cloud learning with **2D segmentation + deterministic raster planning** ([[📐 Path Planning & G-code Generation]]), achieving the same perceive-then-spray goal on flat walls at a fraction of the cost.
''')

add("02 - Research/References/Liu & Cheng 2024 - Semantic Segmentation Spray.md", r'''---
tags: [reference, ai-vision, spray]
authors: Liu & Cheng
year: 2024
doi: n/a
---
# Semantic Segmentation + Trajectory Optimization for Spray Robots
## Citation
Liu, X., & Cheng, Y. (2024). *Semantic segmentation and trajectory optimization for robotic spray painting.* (As cited in AURA concept paper, 2026.)
## Core Argument
Coupling semantic segmentation with trajectory optimization lets spray robots target specific regions and optimize coverage, improving efficiency and finish quality.
## Methodology
Segments the workpiece semantically, then runs an optimization stage to generate efficient, low-overlap spray paths for the identified regions.
## Key Findings
- Segmentation-guided targeting reduces wasted paint and overspray.
- Trajectory optimization improves coverage uniformity.
- Region-aware planning outperforms naive full-surface passes.
## Limitations
- Industrial spray-robot context; heavy compute assumed.
- Optimization complexity beyond a prototype's needs.
- No color-selection dimension.
## Relevance to AURA
Validates AURA's pipeline shape — *segment first, then plan paths for the segmented regions* — and the value of overlap control for uniform coverage.
## AURA Builds On This By
Using a **simpler, reliable raster (boustrophedon) planner with 10–20% overlap** instead of full optimization, appropriate for flat walls and prototype reliability, while retaining segmentation-guided targeting. See [[📐 Path Planning & G-code Generation]].
''')

add("02 - Research/References/Kumote 2022 - Auto Wall Painting Robot.md", r'''---
tags: [reference, mechanical]
authors: Kumote et al.
year: 2022
doi: n/a
---
# Automatic Wall Painting Robot with XY Motion + Sensors
## Citation
Kumote, S., et al. (2022). *Automatic wall painting robot.* (As cited in AURA concept paper, 2026.)
## Core Argument
A wall-painting robot using an XY motion stage with sensor feedback can automate painting of flat walls, reducing manual labor.
## Methodology
Built an XY-motion painting platform with sensors for wall detection/positioning; executed programmed painting motions.
## Key Findings
- XY motion is adequate for flat-wall coverage.
- Sensor feedback aids positioning and boundary detection.
- Automation reduces labor and improves consistency vs manual painting.
## Limitations
- Motion is pre-programmed; no learned perception of design/regions.
- No AI color reasoning.
- Limited to simple coverage tasks.
## Relevance to AURA
Direct mechanical precedent: confirms the XY-gantry approach AURA adopts for flat walls and the labor-reduction motivation.
## AURA Builds On This By
Adding a **deep-learning perception layer and AI color recommendation** on top of the proven XY mechanics, so AURA decides *where* and *what color* rather than replaying fixed motions. See [[⚙️ Mechanical Design]].
''')

add("02 - Research/References/Patil 2021 - Autonomous Wall Painting Robot.md", r'''---
tags: [reference, mechanical]
authors: Patil et al.
year: 2021
doi: n/a
---
# Autonomous Wall Painting Robot (Programmed Movements)
## Citation
Patil, P., et al. (2020/2021). *Autonomous wall painting robot.* (As cited in AURA concept paper, 2026.)
## Core Argument
An autonomous wall-painting robot with programmed movements can consistently paint flat surfaces with minimal human intervention.
## Methodology
Mechanical painting platform executing predefined movement sequences to cover wall areas with a roller/spray end-effector.
## Key Findings
- Consistent, repeatable coverage on flat walls.
- Reduced human effort and exposure to paint fumes/heights.
- Feasible with low-cost microcontroller hardware.
## Limitations
- Entirely pre-programmed — no perception or adaptivity.
- Single-color / fixed-pattern operation.
- No feedback on coverage quality.
## Relevance to AURA
Establishes feasibility and the safety/labor motivation in AURA's problem statement, and the baseline AURA is measured against (manual/non-adaptive).
## AURA Builds On This By
Introducing **perception-driven targeting and adaptive spray** so painting responds to the actual wall and chosen design, addressing exactly the pre-programmed limitation. Baseline for hypothesis H1 in [[📝 Chapter 1 - Introduction]].
''')

add("02 - Research/References/Rudzuan 2019 - Gantry Spray System.md", r'''---
tags: [reference, mechanical, spray]
authors: Rudzuan et al.
year: 2019
doi: n/a
---
# Gantry Spray System with Multi-Axis Control
## Citation
Rudzuan, M., et al. (2019). *Gantry-based spray system with multi-axis control.* (As cited in AURA concept paper, 2026.)
## Core Argument
A gantry framework with multi-axis coordinated motion can carry a spray end-effector for automated surface coating.
## Methodology
Constructed a gantry with coordinated multi-axis control and mounted a spray tool to cover target surfaces.
## Key Findings
- Gantry motion provides stable, repeatable spray positioning.
- Multi-axis coordination enables structured coverage passes.
- Spray-on-gantry is mechanically viable.
## Limitations
- No perception; coverage is geometric, not design-aware.
- Spray timing/flow control not deeply adaptive.
- Industrial/lab framing.
## Relevance to AURA
Confirms mounting a **spray head on an XY gantry** — AURA's exact end-effector strategy — and the importance of coordinated motion for even passes.
## AURA Builds On This By
Coupling the gantry-spray mechanics to **segmentation-driven targeting and position-synchronized solenoid control** ([[💧 Spray System Design]]), making spray adaptive rather than purely geometric.
''')

add("02 - Research/References/Aziz 2026 - 4DOF SCARA ML.md", r'''---
tags: [reference, control, ml]
authors: Aziz et al.
year: 2026
doi: n/a
---
# 4-DOF SCARA: Kinematic Modeling + Machine Learning
## Citation
Aziz, A., et al. (2026). *4-DOF SCARA robot kinematic modeling with machine learning (SVM, Random Forest).* (As cited in AURA concept paper, 2026.)
## Core Argument
Classical kinematic modeling of a SCARA arm can be augmented with machine-learning models (SVM, Random Forest) to improve control accuracy and prediction.
## Methodology
Derived SCARA forward/inverse kinematics and trained SVM and Random Forest models to refine positioning/behavior predictions.
## Key Findings
- ML augmentation improves control accuracy over pure analytical models.
- Classical ML (SVM/RF) is sufficient — deep nets not always required.
- Kinematic + ML hybrid is practical.
## Limitations
- Focused on articulated SCARA arm, not Cartesian gantry.
- Control-only; no perception or painting task.
- ML gains are incremental, task-specific.
## Relevance to AURA
Shows that **modest ML can meaningfully improve robotic control**, supporting AURA's pragmatic (non-heavyweight) AI choices and calibration approach.
## AURA Builds On This By
Applying the *right-sized-AI* philosophy — lightweight segmentation and K-means color logic rather than heavy models — and treating calibration/steps-per-mm tuning as AURA's control-accuracy layer. See [[🧪 Calibration & Testing Log]].
''')

add("02 - Research/References/Nimje 2025 - AI Vision Panel Defects.md", r'''---
tags: [reference, ai-vision, inspection]
authors: Nimje
year: 2025
doi: n/a
---
# AI Vision for Automotive Panel Defect Detection (>95% Accuracy)
## Citation
Nimje, R. (2025). *AI-based visual inspection of automotive panels for defect detection.* (As cited in AURA concept paper, 2026.)
## Core Argument
Deep-vision models detect surface defects on painted panels with >95% accuracy, enabling automated quality control.
## Methodology
Trained deep CNN classifiers/detectors on labeled panel images to flag defects (scratches, uneven coating, etc.).
## Key Findings
- >95% defect-detection accuracy achievable.
- Deep vision reliably assesses surface/finish quality.
- Automates a previously manual QC step.
## Limitations
- Inspection only — no painting or actuation.
- Requires substantial labeled defect data.
- Controlled imaging conditions.
## Relevance to AURA
Supports AURA's **evaluation methodology**: deep/pixel-based visual assessment is a credible way to score spray consistency, coverage uniformity, and output quality.
## AURA Builds On This By
Borrowing pixel/visual analysis for AURA's **evaluation metrics** (spray consistency, coverage uniformity) rather than defect QC, closing the loop from painting to measurable quality. See [[🧪 Calibration & Testing Log]].
''')

add("02 - Research/References/Faheem 2024 - AI Robotics Construction.md", r'''---
tags: [reference, domain, construction]
authors: Faheem et al.
year: 2024
doi: n/a
---
# AI + Robotics in Construction Automation
## Citation
Faheem, M., et al. (2024). *Artificial intelligence and robotics in construction automation.* (As cited in AURA concept paper, 2026.)
## Core Argument
AI-driven robotics is an emerging force in construction, with tasks like finishing, inspection, and material handling ripe for automation.
## Methodology
Review/survey of AI + robotics applications across construction workflows, identifying opportunities and barriers.
## Key Findings
- Construction is under-automated and labor-intensive.
- AI + robotics can improve safety, speed, and consistency.
- Surface finishing (incl. painting) is a natural application.
## Limitations
- Survey-level; no specific painting system built.
- Adoption barriers (cost, integration) noted but unsolved.
- Little prototype-scale guidance.
## Relevance to AURA
Frames AURA's **significance and application domain** — automating a real, labor-intensive construction task — for the introduction and defense.
## AURA Builds On This By
Providing a concrete, buildable **proof-of-concept** within the domain the survey identifies as promising, demonstrating feasibility at undergraduate/prototype scale. See [[📝 Chapter 1 - Introduction]].
''')

add("02 - Research/References/RSIS 2025 - Arduino Wall Painting Robot.md", r'''---
tags: [reference, mechanical, low-cost]
authors: RSIS International
year: 2025
doi: n/a
---
# Arduino-Based Autonomous Wall Painting Robot
## Citation
RSIS International. (2025). *Arduino-based autonomous wall painting robot.* (As cited in AURA concept paper, 2026.)
## Core Argument
A low-cost, Arduino-controlled robot can autonomously paint walls, showing the concept is achievable on hobby-grade hardware and budgets.
## Methodology
Arduino + stepper/motor driven painting mechanism executing autonomous painting routines on flat walls.
## Key Findings
- Autonomous wall painting is feasible on an Arduino-class budget.
- Stepper-driven motion gives adequate control.
- Accessible to student/prototype builders.
## Limitations
- Pre-programmed routines; no computer vision.
- No color intelligence or adaptive spray.
- Basic coverage only.
## Relevance to AURA
Closest **budget and hardware analogue** to AURA — validates that AURA's PHP ≤35k Arduino build is realistic.
## AURA Builds On This By
Keeping the identical low-cost Arduino backbone but adding the **deep-learning perception, color recommendation, and adaptive spray** layers that this system lacks — AURA's core differentiator. See [[🏗️ System Architecture Overview]].
''')

add("03 - System Design/🏗️ System Architecture Overview.md", r'''---
tags: [system-design, architecture, ipo]
created: 2026-03-29
status: active
---
# 🏗️ System Architecture Overview

> [!info] Sub-designs
> [[⚙️ Mechanical Design]] · [[🔌 Electronics & Wiring]] · [[🧠 AI & Software Design]] · [[💧 Spray System Design]] · [[📐 Path Planning & G-code Generation]] · [[🖥️ Serial Communication Protocol]]

## Input–Process–Output (IPO)

| Input | Process | Output |
|---|---|---|
| Wall image (camera) | Image acquisition + preprocessing | Segmented wall regions |
| User design/pattern | Deep-learning spatial segmentation | Identified paintable zones |
| Color preferences | AI color recommendation | Suggested color combinations |
| System parameters | Path planning + coordinate generation (XY gantry) | G-code / motion paths |
| — | Motion control via Arduino + stepper motors | Controlled gantry movement |
| Paint supply | Adaptive spray control (pump, valve, nozzle) | Applied paint on wall |
| — | System integration + execution | Fully painted wall output |
| — | Performance evaluation | Accuracy metrics |

## Block Diagram (ASCII)

```
        [USB Camera] ──img──> [ LAPTOP (RTX 3050) ]
                                     |
   +---------------------------------+----------------------------------+
   | Preprocess -> Segmentation(CNN) -> Color Rec(K-means) -> Path Plan  |
   +---------------------------------+----------------------------------+
                                     | G-code / commands (USB serial, 115200)
                                     v
                            [ Arduino Mega 2560 + RAMPS 1.4 ]
                       +-------------+-------------+-------------+
                       |             |             |             |
                    TB6600        TB6600        TB6600       Relay module
                   (X1 motor)    (X2 motor)    (Y motor)    (pump+solenoid)
                       |             |             |             |
                    NEMA23        NEMA23        NEMA23      [Pump]->[Valve]->[Nozzle]
                       \____ dual X (anti-rack) ___/                 |
                                     |                               v
                              [ XY GANTRY ] ---- carries ----> [ SPRAY HEAD ] -> WALL
                                     ^
                              [Limit switches] (homing)
```

## Data Flow Narrative
1. The **camera** captures the target wall; the frame is preprocessed (resize to 512×512, normalize).
2. The **segmentation model** outputs a per-pixel mask of paintable regions.
3. The **color recommendation module** clusters the design/reference image and proposes a harmonious palette, assigning colors to regions.
4. The **path planner** converts each region mask into a raster (lawn-mower) coordinate list, mapped from pixels to millimeters, then to G-code.
5. The laptop streams G-code over **USB serial (115200 baud)**; the Arduino acknowledges each line with `ok`.
6. The **Arduino** drives the three NEMA 23 motors via TB6600 drivers (dual X mirrored, single Y) and toggles the **spray relay** (M3/M5) synchronized to position.
7. Paint is applied; the process repeats per color region. A final image is captured for **evaluation**.

## Separation of Concerns — Laptop vs Arduino

| Laptop (Python, RTX 3050) | Arduino Mega + RAMPS |
|---|---|
| Camera capture, preprocessing | Parse G-code lines |
| Deep-learning segmentation inference | STEP/DIR pulse generation |
| Color recommendation | Dual-X synchronization |
| Path planning + G-code generation | Limit-switch homing |
| Serial command streaming + logging | Spray relay on/off (M3/M5) |
| All "thinking" | All real-time actuation |

> [!tip] Why this split?
> The Arduino cannot run deep learning; the laptop cannot generate precise real-time step pulses over USB. Putting *intelligence on the laptop* and *deterministic timing on the Arduino* plays to each device's strength and keeps the serial interface simple (see [[🖥️ Serial Communication Protocol]]).

## Communication Protocol Overview
- **Transport:** USB serial, **115200 baud**, 8N1.
- **Motion:** `G1 X{x} Y{y} F{feed}` (linear move), `G28` (home).
- **Spray:** `M3` (spray on), `M5` (spray off) — GRBL-compatible spindle mapping.
- **Handshake:** Arduino returns `ok` after each executed line; Python blocks until `ok` or timeout.

## Key Architectural Decisions & Why
1. **Dual-X motors** — prevents racking of a wide gantry (the dominant accuracy risk). *Why:* a single X motor lets the far side lag, skewing every coordinate.
2. **G-code over custom protocol** — reuses mature firmware (GRBL/Marlin) and tooling. *Why:* less firmware to write/debug for a solo engineer.
3. **2D segmentation, not 3D** — flat walls don't need depth. *Why:* fits 4GB VRAM and a hobby camera.
4. **Raster path planning** — simple, robust coverage. *Why:* reliability beats optimality for a prototype (see [[📐 Path Planning & G-code Generation]]).
''')

add("03 - System Design/⚙️ Mechanical Design.md", r'''---
tags: [system-design, mechanical, gantry]
created: 2026-03-29
status: active
---
# ⚙️ Mechanical Design

> [!info] Related
> [[🔌 Electronics & Wiring]] · [[💧 Spray System Design]] · [[🔧 Assembly Log]] · [[🛒 Bill of Materials]]

## Gantry Configuration — Why Dual X-Axis Motors
The gantry is a **Cartesian XY** frame: a horizontal X-axis carries a vertical Y carriage that holds the spray head. The X-axis is **wide**, so a single motor on one end lets the opposite end lag under acceleration — the beam **racks** (skews out of square), and every commanded coordinate becomes wrong. AURA uses **two NEMA 23 motors on the X-axis**, one at each end, mirrored on the controller so they step in lockstep. This keeps the beam square and is the single most important mechanical decision for painting accuracy. The **Y-axis uses one NEMA 23** — it carries only the lightweight spray head, so racking is not a concern.

> [!warning] Racking is Risk R-02
> Matched belts, matched pulley tooth counts, a square frame, and homing *both* X corners are all required for the dual-motor scheme to actually prevent racking.

## Frame Material — 2040 Aluminum V-Slot Extrusion
| Property | Rationale |
|---|---|
| **Rigidity** | 2040 (20×40mm) resists bending far better than 2020 on the long X span. |
| **Weight** | Aluminum is light enough for NEMA 23 to accelerate without excessive inertia. |
| **Cost** | Widely available in PH; can be cut-to-length locally to save shipping (see [[💰 Budget Tracker]]). |
| **Modularity** | T-nut slots allow bolt-on brackets, motor mounts, and rail carriages without machining. |

## Y-Axis: Single Motor + Linear Motion
The Y carriage rides on a **linear rail + carriage** (or V-Slot wheels for budget) and is driven by a single **GT2 belt** from the Y NEMA 23. It holds the spray head at a fixed **Z standoff (~150mm)** from the wall — there is no active Z axis in the prototype.

## Belt Drive & Steps-per-mm
- **GT2 belt**: 2mm pitch. **Pulley**: 20 teeth → 40mm travel per revolution.
- NEMA 23 = 200 full steps/rev. At **1/8 microstepping** → 1600 steps/rev.
- **Steps per mm** = 1600 / 40 = **40 steps/mm**.
- At **1/16 microstepping** → 3200 / 40 = **80 steps/mm** (finer, slower). Start at 1/8 and tune (see [[🧪 Calibration & Testing Log]]).

```
steps_per_mm = (motor_steps_per_rev * microstep) / (pulley_teeth * belt_pitch)
             = (200 * 8) / (20 * 2) = 40 steps/mm
```

## Estimated Travel Range
| Axis | Range (prototype) | Notes |
|---|---|---|
| X | up to ~2–4 m (frame-dependent) | prototype demo target: 1 m usable |
| Y | up to ~2.5–3 m | prototype demo target: 1 m usable |
| Z | fixed ~150 mm standoff | no active Z |

> Prototype demo works on a **1 m × 1 m** flat board — the frame can be built larger later.

## Carriage & Spray Head Mounting
A printed/bracketed mount fixes the nozzle to the Y carriage, aimed perpendicular to the wall at the ~150mm standoff. Tubing to the pump/reservoir is routed with a small drag chain or zip-tie loops to avoid snagging during motion.

## Assembly Sequence (Order of Operations)
1. Cut and square the X-axis base extrusions; build the outer frame.
2. Mount the two X-axis motors + pulleys/idlers at each end.
3. Install the X gantry beam and its carriages.
4. Mount the Y-axis rail + carriage on the beam; install Y motor + belt.
5. Install limit switches at X (both) and Y home corners.
6. Mount the spray-head carriage and route tubing.
7. Tension all belts evenly; verify frame square with a measurement diagonal.
8. Proceed to wiring ([[🔌 Electronics & Wiring]]).

## Known Mechanical Risks & Mitigations
| Risk | Mitigation |
|---|---|
| Racking (R-02) | Dual-X mirrored motors, matched belts, dual homing |
| Belt slack → lost steps (R-15) | Proper tensioners, GT2 (low stretch), tune steps/mm |
| Frame not square | Measure diagonals, use corner brackets, re-check after tensioning |
| Vibration at speed | Lower acceleration, add feet/damping, brace long spans |
''')

add("03 - System Design/🔌 Electronics & Wiring.md", r'''---
tags: [system-design, electronics, wiring]
created: 2026-03-29
status: active
---
# 🔌 Electronics & Wiring

> [!info] Related
> [[⚙️ Mechanical Design]] · [[💧 Spray System Design]] · [[🖥️ Serial Communication Protocol]] · [[🛒 Bill of Materials]]

## Component Electrical Specs
| Component | Spec |
|---|---|
| NEMA 23 stepper ×3 | ~2.8–4.5 A/phase, 24 V drive |
| TB6600 driver ×3 | up to 4.0 A, 9–42 V, microstep 1–1/32 |
| Arduino Mega 2560 | 5 V logic, USB-powered from laptop |
| RAMPS 1.4 | interface shield, 12–24 V logic power via VMM (careful: see below) |
| PSU | 24 V DC, 30 A |
| Relay module | 5 V logic, drives pump + solenoid |
| Limit switches ×4 | NO/NC to endstop pins |

> [!warning] RAMPS voltage caution
> Stock RAMPS 1.4 stepper power (D8/D9/D10 MOSFETs, thermistors) is rated for ~12V paths. AURA drives the **NEMA 23 via external TB6600 drivers, NOT RAMPS onboard Pololu sockets** — RAMPS is used only to break out STEP/DIR/ENABLE and endstop pins. The 24V/30A PSU feeds the **TB6600 drivers directly**, not the RAMPS 5A/11A input. This avoids overloading RAMPS traces.

## TB6600 DIP-Switch Configuration (per driver)
For NEMA 23 with the 40 steps/mm calc in [[⚙️ Mechanical Design]]:
- **Microstepping: 1/8** (start here; move to 1/16 if smoother motion needed).
- **Current: ~3.0–4.0 A** set to just below motor rating; start ~3.0A and increase only if steps are lost.

| Setting | S1 | S2 | S3 | S4 | S5 | S6 |
|---|---|---|---|---|---|---|
| Microstep 1/8 (typical) | ON | ON | OFF | — | — | — |
| Current ~3.0A (typical) | — | — | — | ON | OFF | ON |

> [!note] DIP tables vary by TB6600 clone — **always confirm against the label printed on your specific driver** before powering motors.

## RAMPS 1.4 Pinout for 3 External Drivers
Break out from the RAMPS stepper headers (STEP/DIR/EN) to the TB6600 PUL/DIR/ENA inputs:
| Axis | STEP pin | DIR pin | EN pin | TB6600 |
|---|---|---|---|---|
| X1 | 54 (A0) | 55 (A1) | 38 | Driver 1 |
| X2 (mirror) | 60 (A6)/E1 header | 61 (A7) | 56 | Driver 2 |
| Y | 60 (A6) | 61 (A7) | 56 | Driver 3 |

> [!tip] Dual-X mirroring
> In Marlin, set `X2` as a driver on the E1 socket header and enable dual-X, or physically wire both X drivers to the same STEP/DIR (simplest for GRBL). Both X motors must step identically — see [[⚙️ Mechanical Design]] anti-racking.

## 24 V Power Distribution
```
[24V 30A PSU] ──+── TB6600 #1 (X1)  VCC/GND
                +── TB6600 #2 (X2)
                +── TB6600 #3 (Y)
                +── (via buck to 12V if pump/solenoid are 12V)
[Laptop USB] ─────> Arduino Mega (5V logic, USB-B)
```
- Motors get **24 V** from the PSU through the drivers.
- Arduino is powered by **laptop USB** (keeps logic ground referenced to the serial host).
- **Common ground** the PSU 0V with the Arduino/RAMPS logic ground for the STEP/DIR signals.

## Spray Pump & Solenoid Wiring
- A **5V relay module** channel is driven by an Arduino digital pin (e.g., **D9**) mapped to **M3/M5**.
- Relay switches the **pump** (and/or **solenoid valve**) on its own 12/24 V rail.
- Flyback protection: use a relay module with onboard diode/opto-isolation.

## Camera
- **USB directly to the laptop.** Not connected to Arduino. Handled entirely by Python/OpenCV ([[🧠 AI & Software Design]]).

## Limit Switch Wiring
- 4 switches → RAMPS endstop pins: **X-min, X-max (for dual homing), Y-min**, plus one spare.
- Wire NC (normally closed) for fail-safe triggering; enable pull-ups in firmware.

## Serial Link
- **Arduino Mega USB-B → laptop USB-A**, 115200 baud. This is also the power source for the Arduino logic.

## Safety Considerations
> [!danger] Before first power-on
> - **Fuse the 24 V line** (e.g., inline 20–25 A) close to the PSU.
> - **Strain-relieve** all moving cables (drag chain) to prevent fatigue breaks.
> - **Heatsink + fan** the TB6600 drivers; they get hot at 3A+.
> - **Double-check polarity** and common ground before connecting motors.
> - Never hot-plug motor wires while powered — can destroy a driver.

## Wiring Diagram (text)
```
PSU 24V+ ─┬─> TB6600(X1) ─> NEMA23 X1
          ├─> TB6600(X2) ─> NEMA23 X2
          └─> TB6600(Y)  ─> NEMA23 Y
Arduino Mega (USB from laptop)
   D54/55  -> X1 PUL/DIR
   (mirror)-> X2 PUL/DIR
   D60/61  -> Y  PUL/DIR
   D9      -> Relay -> Pump/Solenoid (12/24V rail)
   Endstops-> X-min, X-max, Y-min
Common GND: PSU 0V <-> Arduino GND
```
''')

add("03 - System Design/🧠 AI & Software Design.md", r'''---
tags: [system-design, ai, software]
created: 2026-03-29
status: active
---
# 🧠 AI & Software Design

> [!info] Related
> [[🔮 Segmentation Model]] · [[🎨 Color Recommendation Module]] · [[📐 Path Planning & G-code Generation]] · [[🖥️ Serial Communication Protocol]] · Code in `04 - AI & Code/Code Snippets/`

## Python Pipeline (`main.py` flow)
```
main.py
  1. camera.capture_frame()        -> raw image
  2. preprocess(image)             -> 512x512 tensor
  3. segmentation.infer(tensor)    -> region mask
  4. color_rec.recommend(image)    -> palette + region->color map
  5. path_planner.plan(mask, mm)   -> coordinate list -> G-code
  6. serial_ctrl.stream(gcode)     -> Arduino executes (move + spray)
  7. evaluate.capture_and_score()  -> metrics
```

## Modules
### Module 1 — Image Capture (`camera.py`)
OpenCV `VideoCapture` grabs a frame from the USB camera; crops/resizes to model input; normalizes to ImageNet mean/std. Handles a fixed, calibrated camera pose so pixel→mm mapping stays valid.

### Module 2 — Segmentation (`segmentation.py`)
Loads the trained model (MobileNetV3 + DeepLabV3+), runs inference, `argmax` over channels → class mask, resizes mask back to source resolution. Details in [[🔮 Segmentation Model]].

### Module 3 — Path Planner (`path_planner.py`)
Converts each region mask to a raster (boustrophedon) coordinate list, maps pixels→mm via calibration factor, emits G-code with spray M3/M5 toggles. Details in [[📐 Path Planning & G-code Generation]].

### Module 4 — Color Recommendation (`color_rec.py`)
K-means on the reference image → dominant colors → apply harmony rules (complementary/analogous/triadic) → palette + region assignments. Details in [[🎨 Color Recommendation Module]].

### Module 5 — Serial Controller (`serial_ctrl.py`)
`pyserial` command queue: send one G-code line, block for `ok`, timeout/retry on failure. Details in [[🖥️ Serial Communication Protocol]].

## Module Architecture Diagram (ASCII)
```
 camera.py ──> segmentation.py ──> path_planner.py ──> serial_ctrl.py ──> [Arduino]
      │                                   ^
      └──────────> color_rec.py ──────────┘  (palette + region->color)
                        │
                   evaluate.py  (metrics, offline)
```

## Model Choice Rationale
> [!note] Why MobileNetV3 + DeepLabV3+ (not ResNet/heavy nets)
> The RTX 3050 laptop has **4GB VRAM**. A full ResNet-101 DeepLab would not train comfortably. **MobileNetV3** is a mobile-optimized backbone; paired with a **DeepLabV3+** head it gives strong segmentation at a fraction of the memory, and runs near-real-time. **U-Net** is the fallback if ADE20K multi-class proves too hard — it excels at simple binary masks.

## Dataset Strategy
- **Primary:** ADE20K (contains a `wall` class) for pretraining/transfer.
- **Custom:** a small set of local wall photos annotated with **LabelMe** or **CVAT** (binary paintable / not-paintable) to fine-tune.
- **Augmentation:** flips, brightness/contrast jitter, slight rotation — critical given limited data (Risk R-04, R-13).

## Training Environment (RTX 3050, 4GB)
| Constraint | Setting |
|---|---|
| Input size | 512×512 (fallback 384×384) |
| Batch size | 4 (use gradient accumulation if needed) |
| Precision | Mixed precision (AMP) to save VRAM |
| Backbone | MobileNetV3, ImageNet-pretrained |
| Est. VRAM | ~2.5 GB at batch 4 — safe headroom |

## Evaluation Metrics (in code)
- **mean IoU (mIoU)** — primary segmentation metric.
- **Pixel accuracy** — secondary.
- Targets: **>0.65 mIoU**, **>75% pixel accuracy** on test set (prototype-adequate).

## Color Recommendation Approach
K-means on the input image → top-N dominant colors → apply **color harmony rules** (complementary, analogous, triadic, split-complementary) → output palette (hex + RGB) with **region→color assignments**. Qualitative evaluation by **≥5 human raters** (1–5 scale). See [[🎨 Color Recommendation Module]].
''')

add("03 - System Design/💧 Spray System Design.md", r'''---
tags: [system-design, spray, mechanical]
created: 2026-03-29
status: active
---
# 💧 Spray System Design

> [!danger] Highest-risk subsystem
> Spray timing, dripping, and clogging are AURA's hardest calibration problems (Risks R-01, R-14). Treat every design choice here as accuracy-critical. Related: [[⚙️ Mechanical Design]] · [[🔌 Electronics & Wiring]].

## Why Airbrush/Spray Nozzle (not brush or roller)
A spray head applies paint **without contacting the wall**, so it needs no force control or surface compliance — ideal for a lightweight gantry carriage. Brushes/rollers require pressure regulation and leave stroke marks; spray gives **even, controllable coverage** and works naturally with on/off (solenoid) control synchronized to motion.

## Pump Choice — Peristaltic vs Diaphragm
| | Peristaltic | Diaphragm |
|---|---|---|
| Flow precision | **High** (volumetric) | Medium |
| Cleaning | **Easy** (paint only touches tubing) | Harder (internal chambers) |
| Pressure | Lower | **Higher** (better atomization) |
| Cost | Higher | **Cheaper** |
| **AURA choice** | **Preferred** for precise, clean flow | Fallback if atomization/pressure inadequate |

> [!note] Decision
> Start with a **peristaltic pump** for flow precision and easy cleaning (paint contacts only the tube). If atomization is too weak for even coverage, switch to a **diaphragm pump** and add a small pressure buffer.

## Solenoid Valve Role
The **solenoid valve** provides fast **on/off** control of paint flow, toggled by the Arduino relay via **M3/M5** synchronized to gantry position. Placing the solenoid **close to the nozzle** minimizes dribble after shut-off (dead-volume in the line keeps flowing otherwise).

## Flow Rate & Calibration
- Calibrate by spraying a **fixed-time burst** onto paper at the standoff distance and measuring covered area / weight.
- Match flow to **gantry feedrate**: coverage per pass = flow_rate ÷ travel_speed. Tune both together in [[🧪 Calibration & Testing Log]].

## Paint Viscosity
> [!tip] Use **water-based acrylic**, thinned for spray.
> Water-based acrylic cleans up with water (protects the pump/nozzle), is low-odor, and thins predictably. Strain paint before use to avoid nozzle clogs (R-14).

## Tubing & Standoff
- Short tubing from reservoir → pump → solenoid → nozzle; keep runs short to reduce lag and dead volume.
- **Nozzle-to-wall standoff ~100–200 mm** — far enough for a spread pattern, close enough to limit overspray.

## Drip & Clog Mitigation
| Problem | Mitigation |
|---|---|
| Nozzle drip after M5 | Solenoid near nozzle; brief reverse/relief; cap between runs |
| Paint drying in nozzle | Flush with water after every run; keep capped |
| Pump air-lock | Prime before run; keep reservoir above pump if gravity-assist helps |
| Clog mid-run (R-14) | Strain paint, spare nozzle on hand, purge cycle before start |
| Overspray | Correct standoff, mask edges during tests, tune flow vs speed |

## Spray Test Protocol (Coverage Uniformity)
1. Prime and purge until steady stream.
2. Command a **single filled rectangle** (e.g., 100×100 mm) at a fixed feedrate.
3. Photograph under even lighting; analyze pixel intensity variance across the region.
4. Record **coverage %** and **uniformity** in [[🧪 Calibration & Testing Log]].
5. Adjust flow, standoff, overlap (10–20%) and repeat.

## Known Risks
- Paint drying in nozzle (R-14) · pump air-lock · overspray · post-M5 dribble. All logged in [[⚠️ Risk Register]].
''')

add("04 - AI & Code/🔮 Segmentation Model.md", r'''---
tags: [ai, segmentation, deep-learning]
created: 2026-03-29
status: active
---
# 🔮 Segmentation Model

> [!info] Related
> [[🧠 AI & Software Design]] · [[📐 Path Planning & G-code Generation]] · [[Bjekic 2023 - Wall Segmentation CNN]] · Code: [[segmentation_inference.py]]

## Problem Definition
Given a wall image from the fixed camera, output a **per-pixel mask** identifying **paintable regions**. Binary (paintable / not) for the prototype; optionally multi-class per design zone later.

## Dataset Options
| Option | Pros | Cons |
|---|---|---|
| **ADE20K** (has `wall` class) | Large, labeled, free | General scenes, not painting-specific |
| **Custom annotated** (LabelMe/CVAT) | Matches real test walls | Time cost (R-13) |
| **Bjekic-style** wall set | Directly on-task | Availability |
**Plan:** pretrain/transfer on ADE20K, fine-tune on a **small custom binary set** of the actual test walls.

## Chosen Architecture — MobileNetV3 + DeepLabV3+
> [!note] Why
> Real-time-capable on RTX 3050, fits **< 4GB VRAM**, good mIoU on scene segmentation. MobileNetV3's depthwise-separable convolutions keep the model small; DeepLabV3+'s ASPP head captures multi-scale context (useful for large flat wall regions).

**Alternative considered — U-Net:** simpler, excellent for **binary masks**; the fallback if ADE20K multi-class training proves unstable on 4GB.

## Training Procedure
1. Load MobileNetV3 backbone **pretrained on ImageNet**.
2. Attach DeepLabV3+ head; freeze backbone initially, train head.
3. Unfreeze and **fine-tune** on custom wall images.
4. Use **AMP (mixed precision)**, batch size 4, augmentation (flip, jitter, rotate).

## I/O Spec
- **Input size:** 512×512 (fallback 384×384).
- **Output:** per-pixel class mask (same resolution, resized back to source).

## Post-Processing
```
mask -> morphological clean (open/close) -> contour extraction ->
        coordinate grid -> path_planner input
```

## Evaluation
- **mean IoU (mIoU)**, **pixel accuracy**, **boundary precision**.
- **VRAM math:** batch 4 @ 512×512 with MobileNetV3-DeepLab ≈ **~2.5 GB** → safe on 4GB.

## Realistic Prototype Targets
| Metric | Target |
|---|---|
| Pixel accuracy | **> 75%** |
| mIoU | **> 0.65** |

> [!tip] "Good enough" for the thesis
> The mask only needs to be accurate enough that the **raster planner** fills the right area. Small boundary errors are absorbed by spray overlap. Perfect segmentation is not required — reliable region identification is.
''')

add("04 - AI & Code/🎨 Color Recommendation Module.md", r'''---
tags: [ai, color, recommendation]
created: 2026-03-29
status: active
---
# 🎨 Color Recommendation Module

> [!info] Related
> [[🧠 AI & Software Design]] · [[🔍 Research Gaps & Justification]] (Gap 4) · Evaluated in [[🧪 Calibration & Testing Log]]

## Input
Either a **user-uploaded reference image** OR **user-specified color preferences/constraints** (e.g., a base color or mood).

## Approach 1 — Primary (implementable)
**K-means clustering → dominant colors → harmony rules → palette.**
1. Cluster input image pixels with **K-means** (k = number of dominant colors, e.g., 5).
2. Take cluster centroids as **dominant colors**.
3. Apply **color-harmony rules** to expand/refine into a coherent palette.
4. Output **hex + RGB** with **region→color assignments** (map palette to segmentation regions).

## Approach 2 — Stretch
Fine-tuned color-prediction model: **CLIP embeddings → color decoder** to suggest palettes from semantic prompts. Deferred to future work — not required to pass.

## Color Harmony Rules to Implement
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

## Evaluation
- **Qualitative user rating (1–5)** for visual appeal + suitability.
- **≥ 5 evaluators** minimum (Risk R-11 mitigation via feedback loop).
- Also feeds **color reproduction accuracy** (RGB/HSV delta between recommended and applied) in [[🧪 Calibration & Testing Log]].

## Why This Is Defensible AI
> [!note]
> K-means is unsupervised learning; combined with rule-based harmony it is a legitimate **AI-adjacent recommendation system**. It is *implementable within budget/time*, directly addresses **Gap 4** (no cited painting robot generates harmonious palettes), and is honestly framed — not oversold as a neural net.

## Code Outline (pseudocode)
```python
def recommend(image, k=5, rule="complementary"):
    pixels = image.reshape(-1, 3)
    centroids = kmeans(pixels, k)          # dominant colors
    base = pick_dominant(centroids)        # most frequent cluster
    palette = apply_harmony(base, rule)    # HSV math
    return assign_to_regions(palette)      # region -> color map
```
''')

add("04 - AI & Code/🖥️ Serial Communication Protocol.md", r'''---
tags: [ai, serial, firmware, protocol]
created: 2026-03-29
status: active
---
# 🖥️ Serial Communication Protocol

> [!info] Related
> [[🏗️ System Architecture Overview]] · [[🔌 Electronics & Wiring]] · Code: [[serial_command_template.py]] · [[arduino_motion_handler.ino]]

## Link Parameters
- **Baud rate:** 115200 (8N1). High enough to stream G-code without motion starvation.
- **Transport:** USB serial (Arduino Mega USB-B → laptop).

## Command Format (GRBL-compatible)
| Command | Meaning |
|---|---|
| `G1 X{x} Y{y} F{feed}` | Linear move to (x, y) at feedrate |
| `G28` | Home all axes |
| `M3` | Spray ON (spindle-on mapping → relay) |
| `M5` | Spray OFF |
| `G4 P{ms}` | Dwell (pause) |

Example line: `G1 X120.0 Y85.5 F1500\n`

## Handshake Protocol
1. Python sends one line terminated with `\n`.
2. Arduino executes, then replies **`ok`** (or `error:{code}`).
3. Python **blocks** until `ok` or a timeout, then sends the next line.

This flow-control keeps the Arduino's buffer from overflowing and guarantees ordering.

## Python Queue Implementation
- A **command queue** holds the G-code list.
- **Blocking send**: write line → wait for `ok` (with timeout, e.g., 5 s).
- On timeout: retry once, then abort with a logged error.
See [[serial_command_template.py]].

## Error Recovery
> [!warning] If Arduino doesn't respond
> - Timeout → **retry the last line** once.
> - Second failure → **halt streaming**, send `M5` (spray off) for safety, surface an error to the operator.
> - Never blindly continue — a missed move desyncs paint from position (R-03).

## Spray-Timing Strategy (encoder-less)
AURA has no motion encoder, so spray fires by **coordinate-arrival trigger**: because Python waits for `ok` after each move, it *knows* the head has reached the target before sending `M3`. For long strokes, embed `M3`/`M5` **between** the moves that bound the painted segment. Avoid pure time-delay triggering — it drifts.

## Example Command Sequence — paint a single horizontal stripe
```gcode
G28                     ; home
G1 X20 Y50 F2000        ; move to stripe start (no spray)
M3                      ; spray on
G1 X120 Y50 F1200       ; paint across at slower feed
M5                      ; spray off
G1 X20 Y60 F2000        ; reposition for next row
```
''')

add("04 - AI & Code/📐 Path Planning & G-code Generation.md", r'''---
tags: [ai, path-planning, gcode]
created: 2026-03-29
status: active
---
# 📐 Path Planning & G-code Generation

> [!info] Related
> [[🔮 Segmentation Model]] · [[🖥️ Serial Communication Protocol]] · [[🧠 AI & Software Design]]

## Input
A **segmentation mask** (binary image; paintable regions = white).

## Algorithm — Raster Scan (Boustrophedon / Lawn-Mower)
The simplest, most reliable coverage for solid regions: sweep left-to-right on one row, drop down, sweep right-to-left on the next (alternating direction to avoid wasted travel).

> [!note] Why raster, not an optimizer
> For flat walls and simple murals, raster coverage is **deterministic and easy to debug** — exactly what a solo builder needs. Optimal coverage (à la [[Liu & Cheng 2024 - Semantic Segmentation Spray]]) is overkill and adds failure modes.

## Steps
```
mask -> find contours -> bounding box per region ->
        raster rows (spacing = pass width - overlap) ->
        pixel coords -> mm coords (calibration) -> G-code string
```

## Coordinate Mapping (pixels → mm)
- Calibrate a **pixels-per-mm** factor from a known reference in the camera view.
- `x_mm = x_px / pixels_per_mm` (+ origin offset). Same for Y.
- Store the calibration factor in config; re-measure if the camera moves.

## Spray Overlap
> [!tip] Use **10–20% overlap** per pass so adjacent stripes blend with no gaps (uniform coverage metric). Row spacing = spray_width × (1 − overlap).

## Multiple Color Regions
Generate a **separate mask per color**; paint **sequentially** (one color pass, flush nozzle, next color). Order light→dark or by drying needs.

## G-code Output Example — filled 100×100 mm square (10 mm passes)
```gcode
G28
G1 X0 Y0 F2000
M3
G1 X100 Y0 F1200
G1 X100 Y10 F2000
G1 X0 Y10 F1200
G1 X0 Y20 F2000
G1 X100 Y20 F1200
; ... continue rows every 10mm up to Y100 ...
M5
```

## Known Limitation
> [!warning]
> Raster scan is **not optimal for complex/curved shapes** — thin diagonals get stair-stepped and travel isn't minimized. **Acceptable for the prototype** (flat walls, simple murals, per scope). Note this honestly in [[📝 Chapter 5 - Discussion]] as future work.
''')

add("04 - AI & Code/Code Snippets/serial_command_template.py.md", r'''---
tags: [code, python, serial]
created: 2026-03-29
status: draft
---
# serial_command_template.py

> Reference implementation for [[🖥️ Serial Communication Protocol]]. Requires `pyserial` (`pip install pyserial`).

```python
# serial_command_template.py
# Minimal G-code serial controller for AURA (laptop -> Arduino Mega).
import time
import serial  # pip install pyserial


class GantrySerial:
    def __init__(self, port="COM3", baud=115200, timeout=5.0):
        # Windows: "COM3"; Linux: "/dev/ttyUSB0" or "/dev/ttyACM0"
        self.ser = serial.Serial(port, baud, timeout=timeout)
        time.sleep(2.0)  # allow Arduino auto-reset after port open
        self._flush_startup()

    def _flush_startup(self):
        # Drain any boot banner the firmware prints on reset.
        self.ser.reset_input_buffer()

    def send(self, cmd, retries=1):
        # Send one G-code line and block until 'ok'.
        line = (cmd.strip() + "\n").encode("ascii")
        for attempt in range(retries + 1):
            self.ser.write(line)
            resp = self._wait_ok()
            if resp is True:
                return True
            print("[warn] no ok for '%s' (attempt %d)" % (cmd, attempt + 1))
        # Safety: stop spray if we lose sync, then raise.
        self.ser.write(b"M5\n")
        raise RuntimeError("Arduino did not acknowledge: %s" % cmd)

    def _wait_ok(self):
        start = time.time()
        while time.time() - start < self.ser.timeout:
            resp = self.ser.readline().decode("ascii", "ignore").strip()
            if resp == "":
                continue
            if resp.lower().startswith("ok"):
                return True
            if resp.lower().startswith("error"):
                print("[err] firmware:", resp)
                return False
        return False  # timed out

    def move(self, x, y, feed=1500):
        self.send("G1 X%.2f Y%.2f F%d" % (x, y, feed))

    def spray_on(self):
        self.send("M3")

    def spray_off(self):
        self.send("M5")

    def home(self):
        self.send("G28")

    def close(self):
        self.spray_off()
        self.ser.close()


if __name__ == "__main__":
    g = GantrySerial(port="COM3")
    try:
        g.home()
        g.move(20, 50, feed=2000)   # travel to start
        g.spray_on()
        g.move(120, 50, feed=1200)  # paint stripe
        g.spray_off()
    finally:
        g.close()
```

> [!warning] Always wrap runs in try/finally so the spray is turned **off** even if the script crashes mid-stroke (Risk R-01/R-14).
''')

add("04 - AI & Code/Code Snippets/segmentation_inference.py.md", r'''---
tags: [code, python, segmentation, pytorch]
created: 2026-03-29
status: draft
---
# segmentation_inference.py

> Reference implementation for [[🔮 Segmentation Model]]. Requires `torch`, `torchvision`, `opencv-python`, `numpy`.

```python
# segmentation_inference.py
# Load a trained segmentation model, run it on a USB-camera frame, overlay the mask.
import cv2
import numpy as np
import torch
import torchvision.transforms as T

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
INPUT_SIZE = 512
NUM_CLASSES = 2  # binary: 0 = not paintable, 1 = paintable

# ImageNet normalization (backbone was pretrained on ImageNet).
PREPROC = T.Compose([
    T.ToPILImage(),
    T.Resize((INPUT_SIZE, INPUT_SIZE)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def load_model(checkpoint_path):
    # DeepLabV3+ with a MobileNetV3 backbone (see AI & Software Design note).
    from torchvision.models.segmentation import deeplabv3_mobilenet_v3_large
    model = deeplabv3_mobilenet_v3_large(num_classes=NUM_CLASSES, weights=None)
    state = torch.load(checkpoint_path, map_location=DEVICE)
    model.load_state_dict(state)
    model.eval().to(DEVICE)
    return model


def capture_frame(cam_index=0):
    cap = cv2.VideoCapture(cam_index)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError("Camera capture failed")
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


@torch.no_grad()
def infer(model, frame_rgb):
    h, w = frame_rgb.shape[:2]
    x = PREPROC(frame_rgb).unsqueeze(0).to(DEVICE)
    logits = model(x)["out"]                       # (1, C, H, W)
    mask = logits.argmax(1).squeeze(0).byte().cpu().numpy()
    mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
    return mask                                    # 0/1 mask at source size


def overlay(frame_rgb, mask, alpha=0.5):
    color = np.zeros_like(frame_rgb)
    color[mask == 1] = (0, 255, 0)                 # paintable = green
    return cv2.addWeighted(frame_rgb, 1.0, color, alpha, 0)


if __name__ == "__main__":
    model = load_model("checkpoints/aura_seg_best.pt")
    frame = capture_frame(0)
    mask = infer(model, frame)
    vis = overlay(frame, mask)
    cv2.imwrite("mask_overlay.png", cv2.cvtColor(vis, cv2.COLOR_RGB2BGR))
    print("paintable pixel fraction: %.3f" % (mask.mean()))
```
''')

add("04 - AI & Code/Code Snippets/arduino_motion_handler.ino.md", r'''---
tags: [code, arduino, cpp, firmware]
created: 2026-03-29
status: draft
---
# arduino_motion_handler.ino

> Minimal *custom* motion handler illustrating the serial contract from [[🖥️ Serial Communication Protocol]]. For production, a GRBL/Marlin variant is recommended; this shows the concept clearly.

```cpp
// arduino_motion_handler.ino
// Parses simple G-code lines, steps NEMA 23 via TB6600, sprays via relay.
// Dual-X: both X drivers share STEP/DIR so they move identically (anti-racking).

const int X_STEP = 54, X_DIR = 55, X_EN = 38;   // X1 + X2 wired together
const int Y_STEP = 60, Y_DIR = 61, Y_EN = 56;
const int SPRAY_RELAY = 9;
const int XMIN = 3, XMAX = 2, YMIN = 14;

const float STEPS_PER_MM = 40.0;   // see Mechanical Design (1/8 microstep)
long curX = 0, curY = 0;           // current position in steps

void setup() {
  Serial.begin(115200);
  pinMode(X_STEP, OUTPUT); pinMode(X_DIR, OUTPUT); pinMode(X_EN, OUTPUT);
  pinMode(Y_STEP, OUTPUT); pinMode(Y_DIR, OUTPUT); pinMode(Y_EN, OUTPUT);
  pinMode(SPRAY_RELAY, OUTPUT);
  pinMode(XMIN, INPUT_PULLUP); pinMode(XMAX, INPUT_PULLUP); pinMode(YMIN, INPUT_PULLUP);
  digitalWrite(X_EN, LOW); digitalWrite(Y_EN, LOW);   // enable drivers (active low)
  digitalWrite(SPRAY_RELAY, LOW);
  Serial.println("ok");   // ready banner
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    handle(line);
    Serial.println("ok");   // acknowledge every command
  }
}

void handle(String cmd) {
  if (cmd.startsWith("G28")) { homeAxes(); return; }
  if (cmd.startsWith("M3"))  { digitalWrite(SPRAY_RELAY, HIGH); return; }
  if (cmd.startsWith("M5"))  { digitalWrite(SPRAY_RELAY, LOW);  return; }
  if (cmd.startsWith("G1")) {
    float x = parseVal(cmd, 'X', curX / STEPS_PER_MM);
    float y = parseVal(cmd, 'Y', curY / STEPS_PER_MM);
    moveTo((long)(x * STEPS_PER_MM), (long)(y * STEPS_PER_MM));
  }
}

float parseVal(String s, char key, float fallback) {
  int i = s.indexOf(key);
  if (i < 0) return fallback;
  return s.substring(i + 1).toFloat();
}

void moveTo(long tx, long ty) {
  long dx = tx - curX, dy = ty - curY;
  digitalWrite(X_DIR, dx >= 0 ? HIGH : LOW);
  digitalWrite(Y_DIR, dy >= 0 ? HIGH : LOW);
  long nx = abs(dx), ny = abs(dy), n = max(nx, ny);
  for (long i = 0; i < n; i++) {          // naive per-axis stepping
    if (i < nx) pulse(X_STEP);
    if (i < ny) pulse(Y_STEP);
    delayMicroseconds(300);               // speed control (tune)
  }
  curX = tx; curY = ty;
}

void pulse(int pin) {
  digitalWrite(pin, HIGH); delayMicroseconds(5);
  digitalWrite(pin, LOW);  delayMicroseconds(5);
}

void homeAxes() {
  // Back off toward min endstops, then zero.
  digitalWrite(X_DIR, LOW);
  while (digitalRead(XMIN) == HIGH) { pulse(X_STEP); delayMicroseconds(400); }
  digitalWrite(Y_DIR, LOW);
  while (digitalRead(YMIN) == HIGH) { pulse(Y_STEP); delayMicroseconds(400); }
  curX = 0; curY = 0;
}
```

> [!note] This is a teaching skeleton. Real use needs acceleration ramps and proper Bresenham interpolation — reasons to prefer GRBL/Marlin. See [[🖥️ Serial Communication Protocol]].
''')

add("05 - Hardware & Build/🛒 Bill of Materials.md", r'''---
tags: [hardware, bom, procurement]
created: 2026-03-29
status: active
---
# 🛒 Bill of Materials

> [!info] Mirrors [[💰 Budget Tracker]]. Hard cap **PHP 35,000**. All prices are PH-market estimates; update Unit/Total as you buy.

| Item | Spec | Qty | Unit (PHP) | Total (PHP) | Source | Notes |
|---|---|---|---|---|---|---|
| 2040 Aluminum Extrusion | V-Slot, cut to length | ~8 m | 800 | 6,400 | Local surplus / Lazada | Buy cut-to-length locally to save shipping |
| NEMA 23 Stepper Motor | ~3 Nm, 2.8–4.5A | 3 | 1,200 | 3,600 | Lazada PH | 2× X (dual), 1× Y |
| TB6600 Driver | up to 4.0A, 9–42V | 3 | 550 | 1,650 | Shopee PH | Confirm DIP table on label |
| Arduino Mega 2560 | clone | 1 | 500 | 500 | Lazada PH | Motion controller host |
| RAMPS 1.4 shield | breakout only | 1 | 400 | 400 | Shopee PH | STEP/DIR/endstop breakout |
| GT2 belt + pulleys + idlers | 2mm pitch, 20T | set | 500 | 500 | Lazada PH | Low-stretch belt |
| Linear rails + blocks | MGN12 set ×2 | 2 | 1,800 | 3,600 | Lazada PH | ♻️ V-wheels if over budget |
| 24V PSU | 24V, 30A | 1 | 1,300 | 1,300 | Octagon / Lazada | Fuse the output |
| Spray nozzle / airbrush | gravity/siphon | 1 | 1,000 | 1,000 | Lazada / hardware | Spare nozzle advised |
| Electric pump | peristaltic (pref.) | 1 | 900 | 900 | Lazada PH | Diaphragm fallback |
| Solenoid valve | 12/24V | 1 | 350 | 350 | Shopee PH | Mount near nozzle |
| Tubing + fittings + reservoir | food-grade tube | set | 450 | 450 | Hardware store | Short runs |
| USB Camera | 720p+/1080p | 1 | 800 | 800 | Lazada PH | ♻️ reuse webcam |
| Limit switches | mechanical NO/NC | 4 | 60 | 240 | Shopee PH | X-min, X-max, Y-min, spare |
| Power connectors + wiring + terminals | 18–14 AWG | set | 500 | 500 | Deeco / hardware | |
| Screws, brackets, T-nuts, fasteners | assorted | set | 600 | 600 | Local hardware | Buy loose by weight |
| Paint supplies (testing) | water-based acrylic | set | 800 | 800 | NBS / hardware | Strain before use |
| **Contingency (~10%)** | reserve | — | — | 2,500 | — | Do not pre-allocate |
| | | | **TOTAL** | **26,090** | | **Under PHP 35,000 ✅** |

> [!tip] If tight: drop full MGN rails to V-wheels (−~3,000), reuse a webcam (−800), salvage a 24V PSU (−1,300). Buffer to spare: ~PHP 8,900 vs cap.
''')

add("05 - Hardware & Build/🔧 Assembly Log.md", r'''---
tags: [hardware, build, log]
created: 2026-03-29
status: active
---
# 🔧 Assembly Log

> [!info] One entry per build session. Photograph everything (evidence for Chapter 4 + defense). Related: [[⚙️ Mechanical Design]] · [[🔌 Electronics & Wiring]] · [[🧪 Calibration & Testing Log]].

## 2026-03-29 — Planning Phase Complete
**What was done:** Concept paper submitted. Finalized architecture (IPO), hardware stack, and budget. Locked key decisions: dual-X NEMA 23, TB6600 drivers, Arduino Mega + RAMPS, laptop-side AI.
**Issues encountered:** None (design phase).
**How resolved:** —
**Next steps:** Finalize BOM suppliers; place procurement wave 1 (frame, motors, drivers, controller) in May.
**Photos/evidence:** Concept paper PDF in project files.

---

## [Date] — Frame Assembly (X-axis)
**What was done:**
**Issues encountered:**
**How resolved:**
**Next steps:**
**Photos/evidence:**

---

## [Date] — Frame Assembly (Y-axis + carriage)
**What was done:**
**Issues encountered:**
**How resolved:**
**Next steps:**
**Photos/evidence:**

---

## [Date] — Wiring (motors → drivers → RAMPS)
**What was done:**
**Issues encountered:**
**How resolved:**
**Next steps:**
**Photos/evidence:**

---

## [Date] — Spray System Mounting
**What was done:**
**Issues encountered:**
**How resolved:**
**Next steps:**
**Photos/evidence:**

---

## [Date] — First Power-On + Motor Test
**What was done:**
**Issues encountered:**
**How resolved:**
**Next steps:**
**Photos/evidence:**
''')

add("05 - Hardware & Build/🧪 Calibration & Testing Log.md", r'''---
tags: [hardware, testing, calibration, metrics]
created: 2026-03-29
status: active
---
# 🧪 Calibration & Testing Log

> [!info] Structured results feeding [[📝 Chapter 4 - Results]]. Metrics defined in [[📝 Chapter 3 - Methodology]]. Fill rows as tests run.

## 1. Motion Accuracy Tests
Commanded vs actual position; error in mm (target: minimize, define threshold e.g. ≤ 2 mm).

| Run | Commanded (X,Y) mm | Actual (X,Y) mm | Error X (mm) | Error Y (mm) | Notes |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

## 2. Spray Consistency Tests
Coverage and uniformity per burst/pass.

| Run | Feedrate | Flow setting | Coverage % | Uniformity (visual/pixel) | Notes |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

## 3. Segmentation Accuracy Tests
Per test image vs ground-truth mask.

| Image | Ground truth | Predicted | IoU | Pixel Acc | Notes |
|---|---|---|---|---|---|
| img_01 | | | | | |
| img_02 | | | | | |
| img_03 | | | | | |

## 4. Color Reproduction Tests
Recommended vs applied color (delta-E / RGB diff).

| Test | Recommended RGB | Applied RGB | ΔE | RGB diff | Notes |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

## 5. Overall Output Quality (per painted test)
Qualitative visual inspection (1–5): smoothness, alignment, finish.

| Test | Design | Smoothness (1-5) | Alignment (1-5) | Finish (1-5) | Overall (1-5) | Notes |
|---|---|---|---|---|---|---|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

> [!tip] Record raw photos and CSV exports alongside each table for traceability in the defense.
''')

add("06 - Thesis Paper/📝 Chapter 1 - Introduction.md", r'''---
tags: [thesis, chapter-1, introduction]
created: 2026-03-29
status: draft-complete
---
# 📝 Chapter 1 — Introduction

## Background of the Study
Wall painting remains a labor-intensive, time-consuming, and often hazardous task, particularly at height or across large surfaces. Manual painting is prone to inconsistency in coverage, uneven application, and human fatigue, while exposure to fumes and elevated work poses safety risks. Automation has been explored to address these limitations, and prior systems demonstrate that robotic platforms can paint flat walls with reduced human effort (Kumote et al., 2022; Patil et al., 2021; RSIS International, 2025). However, these systems typically rely on **pre-programmed motion**: they reproduce fixed paths without perceiving the wall or reasoning about the design to be applied.

Parallel advances in artificial intelligence and computer vision have made it possible for machines to *understand* visual scenes. Convolutional neural networks can segment walls from ordinary 2D images (Bjekic et al., 2023), and deep learning has been applied to spray-trajectory generation (Tiboni et al., 2022) and segmentation-guided spray planning (Liu & Cheng, 2024). Yet these capabilities are largely demonstrated in isolation or on industrial hardware requiring 3D sensing, leaving a gap between intelligent perception and affordable, integrated painting systems.

This study proposes **AURA (Autonomous Unified Robotic Artist)**, an AI-assisted autonomous wall-painting robot that unifies deep-learning spatial segmentation, AI color recommendation, XY-gantry motion control, and adaptive spray control into a single prototype built within an undergraduate budget. AURA aims to move beyond mechanical reproduction toward a system that perceives the wall, decides where and in what colors to paint, and executes the result autonomously.

## Statement of the Problem
Existing automated wall-painting systems execute predetermined motions and cannot independently identify paintable regions, recommend coherent color schemes, or adapt paint application to the surface. Meanwhile, the deep-learning methods capable of such perception are typically validated in isolation or on costly industrial platforms. There is therefore no accessible, integrated system that combines visual understanding, color intelligence, motion control, and adaptive spraying for autonomous wall painting at prototype scale. This study addresses that gap.

## Research Questions
1. How can a robotic wall-painting system be designed for accurate movement using an XY gantry?
2. How can deep-learning-based spatial segmentation identify and map paintable wall regions?
3. How can an adaptive spray-control system ensure uniform paint application?
4. How can computer vision, AI, and robotics be integrated into one unified automated painting system?
5. How can an AI color-recommendation system generate visually coherent color combinations?
6. How effective is the system in painting accuracy, spray consistency, coverage uniformity, design alignment, and color reproduction accuracy?

## Scope and Delimitation
The study is limited to **flat wall surfaces** and **2D movement**, targeting **simple mural designs** in **controlled test environments** at **prototype-level** implementation. It does **not** address 3D or curved surfaces, autonomous navigation beyond the working frame, commercial or industrial scale, or real-time continual learning. The prototype target is the reliable painting of a simple two-color design on a 1 m × 1 m flat board.

## Objectives
**General Objective.** To develop an AI-based autonomous wall-painting system that combines deep learning, robotics, color recommendation, and adaptive spray control.

**Specific Objectives.**
1. Design and develop a 2D XY-gantry robotic system for precise wall-surface movement.
2. Develop a deep-learning spatial-segmentation model for identifying paintable regions.
3. Implement an adaptive spray-control system regulating paint flow.
4. Integrate computer vision, motion control, color recommendation, and spray into one system.
5. Develop an AI color-recommendation module for visually coherent color combinations.
6. Evaluate motion accuracy, segmentation accuracy, spray consistency, coverage uniformity, design-to-output alignment, and color performance.
7. Assess the system's capability in executing simple mural designs and multi-region painting.

## Rationale / Significance
AURA contributes an **integrated, affordable proof-of-concept** that demonstrates intelligent wall painting is achievable without industrial hardware. For the construction and finishing domain, where automation remains limited (Faheem et al., 2024), it shows a path toward safer, more consistent painting. For computer engineering education, it demonstrates the practical integration of deep learning, embedded control, and mechatronics on a constrained budget. Its color-recommendation component further extends automation from *how* to paint toward *what* to paint, an under-explored dimension in prior work.

## Hypothesis
> [!note] Hypotheses
> **H₀:** The system does not show significant improvement in accuracy, spray consistency, coverage, and color performance compared to manual or non-adaptive approaches.
> **H₁:** The system significantly improves painting accuracy, spray consistency, coverage, and color performance through deep-learning segmentation, AI color recommendation, adaptive spray control, and robotic automation.

*See also [[📚 Literature Review Master]], [[🔍 Research Gaps & Justification]], and [[🏗️ System Architecture Overview]].*
''')

add("06 - Thesis Paper/📝 Chapter 2 - Review of Related Literature.md", r'''---
tags: [thesis, chapter-2, literature]
created: 2026-03-29
status: draft-complete
---
# 📝 Chapter 2 — Review of Related Literature

This chapter reviews existing work across three themes relevant to AURA — mechanical wall-painting automation, AI and computer vision in robotic systems, and intelligent/adaptive control — and identifies the gap the present study addresses. A thematic synthesis is maintained in [[📚 Literature Review Master]].

## 2.1 Mechanical Wall-Painting Automation
Automated wall painting has a well-established mechanical foundation. Kumote et al. (2022) and Patil et al. (2021) demonstrate XY-based painting platforms that reduce manual labor, with Kumote et al. incorporating sensor feedback for positioning, while Patil et al. rely on programmed movement sequences. Extending the actuation approach, Rudzuan et al. (2019) mount a spray end-effector on a multi-axis gantry, and Tawade et al. (2024) validate XY-gantry kinematics for precise material handling that AURA reuses for its motion stage. At the accessible end of the spectrum, RSIS International (2025) shows that autonomous wall painting is feasible on an Arduino-class budget, and Al Mawali and Hussain (2023) add a color sensor and database for paint selection. Collectively, these studies confirm that XY/gantry mechanics, spray end-effectors, and low-cost controllers can reliably cover flat walls; however, they operate through fixed, pre-programmed paths and do not perceive the wall or reason about the design, motivating the perception layer introduced by AURA.

## 2.2 AI and Computer Vision in Robotic Systems
A second body of work brings deep learning to robotic perception. Bjekic et al. (2023) segment walls from single 2D images using convolutional neural networks, establishing the perception primitive AURA requires, while Ni et al. (2023) survey deep-learning scene understanding for autonomous robots more broadly. In spray robotics specifically, Tiboni et al. (2022) learn spray trajectories from 3D point clouds, and Liu and Cheng (2024) pair semantic segmentation with trajectory optimization to improve coverage — both demonstrating the value of perception-driven spraying, yet assuming 3D sensing and industrial platforms. On the inspection side, Shaikh and Kokate (2025) and Nimje (2025) report deep-vision surface and defect analysis exceeding 95% accuracy, indicating that pixel-level visual assessment is mature enough to evaluate painted output quality. Taken together, these works prove that walls can be segmented from 2D imagery and that spraying can be guided by perception; their limitation is that such capabilities remain isolated or hardware-intensive, which AURA addresses by coupling lightweight 2D segmentation to affordable gantry actuation end-to-end.

## 2.3 Intelligent Control and Adaptive Systems
The third theme concerns intelligence and adaptivity in control. Aziz et al. (2026) augment the kinematics of a 4-DOF SCARA arm with machine-learning models (SVM and Random Forest), showing that even modest ML can refine robotic control, while Kiran and Prabhu (2020) review nano-spray painting and identify flow and atomization control as decisive for finish quality. At a domain level, the IEEE (2022) survey of autonomous robotic systems emphasizes sensor integration, and Faheem et al. (2024) frame AI and robotics as an emerging force in construction automation, of which wall finishing is a natural sub-domain. These studies establish that ML improves control and that spray flow governs quality, yet adaptive spray control coordinated with perception remains under-explored at prototype scale — the integration AURA pursues by timing paint flow to gantry position and segmentation output.

## 2.4 Summary of Gaps
Across the three themes, the literature has independently matured affordable gantry mechanics, deep-learning 2D wall segmentation, and intelligent adaptive control, but no accessible, undergraduate-scale system unifies perception, color reasoning, motion, and adaptive spray into a single automated wall-painting pipeline. Prior painting robots are effectively blind and pre-programmed; prior vision work is disembodied or demands industrial 3D sensing; and prior adaptive control targets articulated arms rather than integrated painting. This synthesis of gaps — detailed in [[🔍 Research Gaps & Justification]] — establishes the need for AURA and sets up the methodology described in [[📝 Chapter 3 - Methodology]].
''')

add("06 - Thesis Paper/📝 Chapter 3 - Methodology.md", r'''---
tags: [thesis, chapter-3, methodology]
created: 2026-03-29
status: draft-complete
---
# 📝 Chapter 3 — Methodology

## 3.1 Research Design
This study employs a **developmental-experimental** design. The developmental component covers the iterative design, construction, and integration of the AURA prototype; the experimental component covers the controlled evaluation of its performance against defined metrics. This dual design is appropriate because the study both *builds* a novel artifact and *measures* its effectiveness.

## 3.2 Development Approach
An **iterative prototyping** approach is used, progressing through mechanical, electronic, firmware, AI, and integration stages, with testing after each stage to surface defects early. Each iteration refines the prototype toward the target capability: reliably painting a simple two-color design on a 1 m × 1 m flat board.

## 3.3 System Architecture
AURA follows the Input–Process–Output model detailed in [[🏗️ System Architecture Overview]]. A camera captures the wall; a deep-learning model segments paintable regions; an AI module recommends colors; a path planner converts regions to G-code; and an Arduino Mega with RAMPS 1.4 drives three NEMA 23 motors (dual-X, single-Y) and an adaptive spray system. All intelligence runs on an RTX 3050 laptop; the Arduino executes motion and spray commands received over USB serial at 115200 baud.

## 3.4 Participants
For the qualitative evaluation of the color-recommendation module, a minimum of **five (5) evaluators** will rate recommended palettes on a 1–5 scale for visual appeal and suitability. Evaluators are selected from students and faculty familiar with design aesthetics.

## 3.5 Instruments
**Hardware:** 2040 aluminum extrusion frame, 3× NEMA 23 motors, 3× TB6600 drivers, Arduino Mega 2560 + RAMPS 1.4, 24V/30A PSU, GT2 belts/pulleys, linear rails, USB camera, peristaltic/diaphragm pump, solenoid valve, spray nozzle, limit switches (full list in [[🛒 Bill of Materials]]).
**Software:** Python, PyTorch/TensorFlow, OpenCV, a MobileNetV3-DeepLabV3+ segmentation model, K-means color recommendation, and a pyserial motion controller.

## 3.6 Development Procedure
1. **Mechanical:** assemble the XY gantry per [[⚙️ Mechanical Design]], ensuring squareness and dual-X synchronization.
2. **Electronics:** wire motors, drivers, RAMPS, PSU, and spray relay per [[🔌 Electronics & Wiring]].
3. **Firmware:** flash a G-code firmware (GRBL/Marlin variant); verify homing and commanded motion.
4. **AI:** train and validate the segmentation model and color-recommendation module ([[🔮 Segmentation Model]], [[🎨 Color Recommendation Module]]).
5. **Integration:** connect the laptop pipeline to the Arduino, synchronize spray with position, and run dry-runs then live paint tests.
6. **Testing:** collect all evaluation metrics ([[🧪 Calibration & Testing Log]]).

## 3.7 Evaluation Framework
| Metric | Type | Method | Indicator |
|---|---|---|---|
| Motion Accuracy | Quantitative | Positional error (mm) | Lower = better |
| Segmentation Accuracy | Quantitative | % correct regions vs ground truth (IoU, pixel acc) | Higher = better |
| Spray Consistency | Quantitative | Uniformity of paint distribution (visual/pixel) | More uniform = better |
| Coverage Uniformity | Quantitative | % area evenly painted (no gaps/overlaps) | Higher = better |
| Color Reproduction Accuracy | Quantitative | RGB/HSV difference (recommended vs applied) | Smaller diff = better |
| Color Recommendation Quality | Qualitative | User rating 1–5 (appeal + suitability) | Higher = better |
| Overall Painting Output Quality | Qualitative | Visual inspection (smoothness, alignment, finish) | Higher = better |

## 3.8 Data Analysis
Quantitative metrics are analyzed using **descriptive statistics** (means, standard deviations) and **error metrics** (mean positional error in mm, mean IoU, mean ΔE). Qualitative ratings are summarized descriptively (mean rating, distribution). Where a comparison to a manual/non-adaptive baseline is made, results are interpreted against hypotheses **H₀/H₁** from [[📝 Chapter 1 - Introduction]]. Target thresholds (e.g., positional error ≤ 2 mm, mIoU > 0.65, pixel accuracy > 75%) define prototype adequacy.
''')

add("06 - Thesis Paper/📝 Chapter 4 - Results.md", r'''---
tags: [thesis, chapter-4, results, placeholder]
created: 2026-03-29
status: pending
---
# 📝 Chapter 4 — Results

> [!warning] Pending
> Chapter 4 will be completed after system testing. Sections are pre-structured below; populate each from [[🧪 Calibration & Testing Log]].

## 4.1 Motion Accuracy Results
*(Positional error table + mean/SD; compare to ≤ 2 mm threshold.)*

## 4.2 Segmentation Accuracy Results
*(IoU and pixel-accuracy per test image; mean mIoU vs 0.65 target.)*

## 4.3 Spray Consistency Results
*(Uniformity per pass; representative photos.)*

## 4.4 Coverage Uniformity Results
*(% area evenly painted; gap/overlap analysis.)*

## 4.5 Color Reproduction Results
*(Recommended vs applied RGB; mean ΔE.)*

## 4.6 Color Recommendation Quality Results
*(Evaluator 1–5 ratings, n≥5; mean + distribution.)*

## 4.7 Overall Output Quality Results
*(Visual inspection scores; final painted-design images.)*
''')

add("06 - Thesis Paper/📝 Chapter 5 - Discussion.md", r'''---
tags: [thesis, chapter-5, discussion, placeholder]
created: 2026-03-29
status: pending
---
# 📝 Chapter 5 — Discussion

> [!warning] Pending
> Complete after [[📝 Chapter 4 - Results]]. Interpretation guidance is pre-written below so writing is fast once data exists.

## Suggested Structure
1. **Restate purpose** briefly and the hypotheses (H₀/H₁).
2. **Interpret each metric** against its target threshold.
3. **Integration findings** — how well perception, motion, color, and spray worked together.
4. **Limitations.**
5. **Future work.**
6. **Conclusion.**

## If H₁ is Supported
> [!tip]
> Argue that deep-learning segmentation, AI color recommendation, adaptive spray, and dual-motor motion **jointly** produced measurable gains over manual/non-adaptive painting. Tie each metric that met its threshold back to a specific objective from [[📝 Chapter 1 - Introduction]], and emphasize the **integration** achievement — the contribution no single cited work made.

## If Results Are Mixed
> [!tip]
> Be honest and analytical: identify *which* subsystems met targets and *which* did not, and diagnose why (e.g., spray consistency limited by pump atomization; segmentation limited by dataset size). Frame partial success as validating the *architecture* even where a component needs refinement. Distinguish prototype limitations from conceptual ones.

## Framing Prototype Limitations Without Undermining the Contribution
> [!note]
> Position AURA explicitly as a **proof-of-concept** built on a PHP ≤35k budget. Limitations (flat walls only, raster paths, small dataset, no active Z) are **scope choices**, not failures — the scope was declared in Chapter 1. State a clear scalability path (larger frame, more data, optimized paths) so the panel sees the ceiling is practical, not fundamental. Reference [[🔍 Research Gaps & Justification]] to keep the significance in view.

## Future Work (seed list)
- Optimized (non-raster) path planning for complex murals.
- Larger/custom annotated dataset; multi-class region segmentation.
- Active Z-axis and curved-surface handling.
- Neural color recommendation (CLIP-based) as in the stretch approach.
''')

add("06 - Thesis Paper/📝 Writing Notes & Advisor Feedback.md", r'''---
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
''')

add("07 - Defense Prep/🎤 Defense Script & Talking Points.md", r'''---
tags: [defense, script, presentation]
created: 2026-03-29
status: active
---
# 🎤 Defense Script & Talking Points

> [!info] ~17 minutes. Speaker notes in *italics*. Pairs with [[📊 Presentation Outline]] and [[❓ Anticipated Panel Questions & Answers]].

## 1. Opening (2 min)
"Good [morning/afternoon]. I am Kurt Robyn Manabat, presenting **AURA — Autonomous Unified Robotic Adaptive**, a deep-learning-based autonomous wall-painting robot, for the Bachelor of Science in Computer Engineering at Holy Angel University."
*Speaker note: state names of teammates (David, Usi). Slow down. Make eye contact with each panelist once.*

## 2. Problem Motivation (2 min)
"Manual wall painting is slow, physically demanding, inconsistent, and can be hazardous at height. Existing painting robots automate the motion but are **pre-programmed** — they cannot perceive the wall or decide what to paint."
*Speaker note: this frames the gap. Emphasize 'pre-programmed' — it is the whole justification.*

## 3. Objectives and Scope (1 min)
"AURA develops an AI-based system unifying deep-learning segmentation, color recommendation, XY-gantry motion, and adaptive spray. Scope: **flat walls, 2D motion, simple murals, prototype scale** — a two-color design on a 1 m × 1 m board."
*Speaker note: naming the scope up front disarms 'why not industrial?' questions later.*

## 4. System Overview (3 min)
"The camera feeds a laptop with an RTX 3050. The laptop segments the wall, recommends colors, plans paths, and streams G-code over USB serial to an Arduino Mega with RAMPS 1.4, which drives three NEMA 23 motors and the spray system."
*Speaker note: point at the architecture diagram. Stress the split: laptop thinks, Arduino acts.*

## 5. AI Components (3 min)
"Segmentation uses a lightweight MobileNetV3 + DeepLabV3+ model chosen to fit the 4GB VRAM budget, targeting over 0.65 mIoU. Color recommendation uses K-means clustering plus color-harmony rules to generate coherent palettes, evaluated by at least five raters."
*Speaker note: if asked why not a bigger model — VRAM and real-time. Have the number ready.*

## 6. Mechanical Design (2 min)
"The gantry uses **dual NEMA 23 motors on the X-axis** to prevent racking — the key accuracy decision — with a single Y motor and GT2 belts giving 40 steps per millimeter. TB6600 drivers were chosen over A4988 because NEMA 23 needs higher current."
*Speaker note: racking is the mechanical crux; show you understand why two motors matter.*

## 7. Methodology and Evaluation (2 min)
"We follow a developmental-experimental design with iterative prototyping. We measure motion accuracy in millimeters, segmentation IoU, spray consistency, coverage uniformity, color reproduction as RGB/ΔE difference, and qualitative output quality."
*Speaker note: tie metrics back to the research questions.*

## 8. Expected Contributions (1 min)
"AURA's contribution is **integration on an affordable budget** — the first undergraduate-scale system to unify perception, color reasoning, motion, and adaptive spray into one painting pipeline."
*Speaker note: this is the sentence they will remember. Say it slowly.*

## 9. Closing (1 min)
"AURA demonstrates that intelligent, self-directed wall painting is achievable without industrial hardware. Thank you — I welcome your questions."
*Speaker note: pause, smile, invite questions confidently.*
''')

add("07 - Defense Prep/❓ Anticipated Panel Questions & Answers.md", r'''---
tags: [defense, qa, panel]
created: 2026-03-29
status: active
---
# ❓ Anticipated Panel Questions & Answers

> [!tip] Answer in 3–5 sentences: honest, confident, not defensive. Backed by [[🔍 Research Gaps & Justification]].

## AI Model
**Q1. Why MobileNetV3 + DeepLabV3+ and not a larger model like ResNet-101?**
The laptop has a 4GB RTX 3050, which cannot comfortably train heavy backbones. MobileNetV3 gives strong segmentation with far less memory and near-real-time inference, and the task — flat walls — does not need a very deep model. If accuracy falls short, U-Net is our validated fallback.

**Q2. How do you handle limited training data?**
We use transfer learning from ImageNet and pretrain on ADE20K, which includes a wall class, then fine-tune on a small custom set annotated with LabelMe. We also apply augmentation (flips, jitter, rotation). If multi-class proves unstable, we reduce to a binary paintable/not-paintable mask.

**Q3. What accuracy is "good enough"?**
For a prototype we target over 0.65 mIoU and over 75% pixel accuracy. The mask only needs to be accurate enough that the raster planner fills the correct area; small boundary errors are absorbed by 10–20% spray overlap.

**Q4. Is K-means really "AI"?**
K-means is unsupervised machine learning, and combined with color-harmony rules it forms a legitimate recommendation system. We are transparent that it is not a neural network; we chose it because it is implementable within budget and directly fills a gap — no cited painting robot generates harmonious palettes.

## Simpler Approaches
**Q5. Why not just pre-program the paths like existing robots?**
Pre-programming is exactly the limitation we address: those systems cannot adapt to the actual wall or design. Perception lets AURA generate paths from what it sees, which is the core novelty. Pre-programming would defeat the purpose of the study.

**Q6. Why segmentation instead of simple edge detection or thresholding?**
Thresholding fails under real lighting and texture variation, whereas a learned model generalizes across conditions. Segmentation also extends naturally to multi-region, multi-color painting. It is the more robust and scalable choice.

## Industrial Applicability
**Q7. This is not industrial-scale — why does it matter?**
AURA is a deliberate proof-of-concept, not a product. Its value is demonstrating that an integrated intelligent painting pipeline is achievable at roughly PHP 30,000, which lowers the barrier for future scaling. The scope was declared from the outset.

**Q8. How would this scale to real buildings?**
The same architecture scales with a larger frame, more training data, and optimized path planning; the perception and control logic are size-independent. Scaling is an engineering effort, not a conceptual barrier. We list this explicitly as future work.

## Team
**Q9. Only one member is technically capable — is that a risk?**
Yes, and we manage it directly: everything is documented in a structured vault, code is backed up to GitHub, and teammates are cross-trained on assembly and logging. The risk is registered and mitigated rather than ignored.

## Evaluation
**Q10. Is n=5 evaluators enough for color recommendation?**
For a qualitative usability signal at prototype scale, five raters give an initial indication of appeal and suitability; we report it as descriptive, not inferential. We can expand the sample if time allows. The quantitative color-reproduction metric (ΔE) provides an objective complement.

**Q11. How do you measure spray consistency objectively?**
We photograph painted regions under even lighting and analyze pixel-intensity variance across the area, reporting coverage percentage and uniformity. This mirrors deep-vision inspection methods shown to exceed 95% accuracy in the literature. It removes reliance on subjective judgment.

**Q12. How do you ensure motion-accuracy measurements are valid?**
We command known coordinates and measure the actual head position, computing positional error in millimeters across repeated runs, and report mean and standard deviation. Calibration of steps-per-mm and belt tension precedes testing. We define a threshold (e.g., ≤ 2 mm) for prototype adequacy.

## Limitations
**Q13. Raster scanning is not optimal — why use it?**
For flat walls and simple murals it is deterministic and easy to debug, which matters for a solo builder. Optimal planning adds failure modes without meaningful benefit at this scope. We note optimized planning as future work.

**Q14. No Z-axis — is that a weakness?**
The spray head works at a fixed standoff, so an active Z is unnecessary for flat walls. Adding Z is a clear extension for textured or 3D surfaces, which are outside our declared scope. It is a scope choice, not an oversight.

**Q15. What if the spray drips or clogs?**
This is our highest-risk subsystem and is actively mitigated: water-based acrylic, strained paint, a solenoid mounted near the nozzle, purge cycles before runs, and a spare nozzle. It is tracked in the risk register. We designed the test protocol specifically to characterize and tune it.

## Budget & Feasibility
**Q16. Is PHP 35,000 realistic for all of this?**
Yes; our bill of materials totals about PHP 26,000 with a contingency reserve, using local suppliers and clone controllers. Where needed we substitute V-wheels for linear rails and reuse a webcam. The budget has been itemized and cross-checked.

**Q17. Can you finish by the defense date?**
Our timeline runs procurement to defense across April–December 2026 with buffers in the highest-risk months. AI training partly parallelizes with the mechanical build. The critical path is the mechanical-to-integration chain, which we start early.

## Novelty
**Q18. How is this different from the Arduino wall-painting robot you cited?**
That system, like others, is pre-programmed with no vision or color intelligence. AURA adds deep-learning segmentation, AI color recommendation, and adaptive spray on the same low-cost backbone. The novelty is the integration, not any single part.

**Q19. What is the single most novel contribution?**
Unifying perception, color reasoning, motion, and adaptive spray into one automated pipeline at undergraduate cost — a combination none of our cited works achieve. Individually the pieces exist; together, affordably, they do not.

**Q20. What happens if H₁ is not supported?**
We report results honestly and analyze which subsystems met their targets and which did not, diagnosing causes. Even partial success validates the architecture and yields clear engineering lessons. A rigorous negative or mixed result is still a legitimate contribution.

**Q21. Why is color recommendation part of a painting robot at all?**
Because deciding *what* to paint is as much a part of autonomy as deciding *where*. Prior robots assume a human picks the color; AURA extends automation to the aesthetic decision. It also differentiates the work and addresses a specific literature gap.
''')

add("07 - Defense Prep/📊 Presentation Outline.md", r'''---
tags: [defense, slides, outline]
created: 2026-03-29
status: active
---
# 📊 Presentation Outline

> [!info] ~16 slides, 3 points max each. Speaker-note hints in *italics*. Build in PowerPoint/Canva; align with [[🎤 Defense Script & Talking Points]].

| # | Slide | Key Points | Note hint |
|---|---|---|---|
| 1 | **Title** | AURA; full name; HAU CpE; team; date | *Confident open* |
| 2 | **Agenda** | Problem → System → AI → HW → Method → Results | *10 seconds only* |
| 3 | **Problem Statement** | Manual painting slow/unsafe; robots are pre-programmed; no perception | *Emphasize the gap* |
| 4 | **Objectives & Scope** | General + key specifics; flat wall, 2D, simple mural, prototype | *Declare scope early* |
| 5 | **Related Work (brief)** | Mechanical / AI-vision / adaptive control; isolated capabilities | *Name 3-4 papers max* |
| 6 | **System Overview** | Camera → laptop AI → Arduino → gantry + spray | *Laptop thinks, Arduino acts* |
| 7 | **Architecture Diagram** | IPO / block diagram | *Point, do not read* |
| 8 | **AI Design — Segmentation** | MobileNetV3+DeepLabV3+; 4GB fit; >0.65 mIoU | *Have VRAM number ready* |
| 9 | **AI Design — Color Rec** | K-means + harmony rules; palette output; n≥5 eval | *Defend as AI-adjacent* |
| 10 | **Hardware Design** | Dual-X anti-racking; TB6600; RAMPS; 40 steps/mm | *Racking = crux* |
| 11 | **Spray System** | Pump + solenoid; adaptive on/off; drip/clog mitigation | *Acknowledge top risk* |
| 12 | **Methodology** | Developmental-experimental; iterative prototyping | *Tie to research design* |
| 13 | **Evaluation Framework** | 7 metrics table; targets/thresholds | *Objective + qualitative* |
| 14 | **Expected Results** | Prototype paints 2-color design on 1x1m board | *Set realistic expectation* |
| 15 | **Contributions** | Integration at undergraduate cost; fills 5 gaps | *The memorable sentence* |
| 16 | **Limitations & Future Work** | Flat/2D/raster now; scaling path | *Scope, not failure* |
| 17 | **Conclusion** | Intelligent painting without industrial hardware | *Strong close* |
| 18 | **Q&A** | "Thank you — questions?" | *Breathe; see [[❓ Anticipated Panel Questions & Answers]]* |
''')

add("08 - Meeting Notes/📓 Meeting Log Template.md", r'''---
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
''')

# ===END_OF_FILES===  (do not remove this marker; new files are inserted above)

def main():
    print("Creating AURA vault at: {}".format(VAULT_ROOT))
    os.makedirs(VAULT_ROOT, exist_ok=True)
    for rel_path, content in FILES:
        full = os.path.join(VAULT_ROOT, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        print("  [+] wrote {}".format(rel_path))
    print("Done. {} files created.".format(len(FILES)))


if __name__ == "__main__":
    main()
