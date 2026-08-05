---
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
| R-02 | Gantry racking from X-axis motor desync | Technical | M | H | 🔴 Critical | Dual NEMA 23 stepped in lockstep **in firmware** (RAMPS removed — see note below), matched belts/pulleys, square frame, homing both corners | Kurt |
| R-03 | Serial lag causes misaligned paint strokes | Technical | M | H | 🟠 High | 115200 baud, coordinate-arrival trigger for spray, ack (`ok`) handshake, buffer tuning | Kurt |
| R-04 | AI model underfits on limited training data | Technical | H | M | 🟠 High | Transfer learning from ImageNet, data augmentation, use ADE20K wall class, keep task binary if needed | Kurt |
| R-05 | RTX 3050 4GB VRAM insufficient for model | Technical | M | M | 🟡 Medium | MobileNetV3 backbone, batch size 4, 512×512 input, mixed precision, fallback to U-Net | Kurt |
| R-06 | Budget overrun on mechanical parts | Budget | M | H | 🟠 High | V-wheels instead of full linear rails, local cut-to-length extrusion, 10% contingency held | Kurt |
| R-08 | Adviser rejects methodology | Timeline | L | H | 🟡 Medium | Early adviser meeting (Apr), align Ch.3 with objectives + metrics, iterate before build | Kurt |
| R-09 | Component shipping delays (Lazada/Shopee) | Timeline | M | M | 🟡 Medium | Order long-lead items in May, prefer local stock, keep buffer weeks in schedule | Kurt |
| R-10 | TB6600 drivers overheat | Technical | M | M | 🟡 Medium | Heatsinks + fan on drivers, TB6600 current confirmed at 3A (bench tested), de-energize via ENA when idle, avoid stalling motors | Kurt |
| R-11 | Color recommendation outputs look bad | Technical | M | M | 🟡 Medium | K-means + established harmony rules, cap palette size, evaluator feedback loop (n≥5) | Kurt |
| R-12 | Panel questions lack of industrial applicability | Defense | M | M | 🟡 Medium | Frame as proof-of-concept, cite scalability path, emphasize integrated novelty | Kurt |
| R-13 | Dataset annotation too time-consuming | Timeline | H | M | 🟠 High | Use pre-labeled ADE20K, annotate only a small custom set with LabelMe, binary masks | Kurt |
| R-14 | Paint clogs nozzle mid-test | Technical | H | M | 🟠 High | Strain paint, flush after each run, keep nozzle capped between tests, spare nozzle on hand | Kurt |
| R-15 | Positional error exceeds acceptable threshold | Technical | M | H | 🟠 High | Microstepping **1/32 (bench confirmed → 160 steps/mm)**, belt tension, calibrate steps/mm, closed-loop homing each run | Kurt |
| R-16 | Power supply / wiring short or failure | Technical | L | H | 🟡 Medium | Fusing on 24V line, strain relief, terminal blocks, double-check polarity before power-on | Kurt |
| R-17 | Scope creep (3D, curved walls, mobility) | Timeline | M | M | 🟡 Medium | Hold scope to flat 1m×1m board, 2D, simple murals; defer extras to "future work" | Kurt |

> [!danger] Top 2 to watch
> **R-01 (spray)** and **R-02 (racking)** are the project killers. Every monthly review starts here.

> [!warning] R-02's mitigation moved from hardware to software (2026-08-03)
> The original mitigation leaned on RAMPS mirroring the two X motors on one axis driver. **RAMPS is no longer in the build** ([[🔌 Electronics & Wiring]]), so nothing enforces lockstep electrically — the Arduino sketch must pulse both X drivers from a single step routine.
>
> This does not raise the likelihood on paper, but it does move the mitigation into code that **does not exist yet**, where a bug produces exactly the failure the dual-motor scheme was bought to prevent. Treat "both X drivers driven from one step routine" as an explicit firmware acceptance test, and verify with the dual-corner homing check (X-min and X-max must trigger within tolerance of each other) before trusting any positional measurement.
