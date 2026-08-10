---
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
| ~~RAMPS 1.4 shield~~ | ~~breakout only~~ | 1 | 400 | 400 | Shopee PH | ❌ **Not in build (2026-08-03)** — purchased, then dropped; Mega wires straight to the TB6600s |
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

## 🧭 Planned additions — panel recommendations (2026-08-08)

| Item | Spec | Qty | Unit (PHP) | Total (PHP) | Source | Notes |
|---|---|---|---|---|---|---|
| Load cell (bar-type, 5–10 kg) + HX711 module | weight-based paint level sensor | 1 | 250 | 250 | Shopee PH | Panel-recommended — see [[💧 Spray System Design]] § Planned: Paint-Level Monitoring |
| Locking swivel casters + leveling feet | rated for frame weight (TBD) | set | 1,200 | 1,200 | Lazada / hardware | Panel-recommended — see [[⚙️ Mechanical Design]] § Planned: Mobility |

> [!note] Not yet in the TOTAL above
> The two rows above (~₱1,450 combined estimate, see [[🎯 Post-Defense Recommendations & Action Items]]) aren't folded into the 26,090 total yet — caster load rating depends on the frame's actual assembled weight, not yet measured. Even fully added, this stays well under the ₱35,000 cap (~₱7,460 headroom instead of ~₱8,910).
