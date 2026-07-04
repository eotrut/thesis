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
