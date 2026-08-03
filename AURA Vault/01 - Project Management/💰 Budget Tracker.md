---
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
| 5 | ~~RAMPS 1.4 shield~~ | 1 | 400 | 400 | 380 | Shopee PH | ❌ **not in build — ₱380 sunk** |
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
> - **NEMA 23 motors (item 2)** — 3 motors add up fast. **Mitigation:** buy 2 first (dual-X) + reuse a spare/borrowed motor for Y initial testing. ✅ *In effect as of 2026-08-03 — the 2 procured motors are both on X; the Y unit is still to be borrowed. Note this also leaves a **third TB6600 (item 3)** outstanding, which the mitigation did not account for.*
> - **Extrusion (item 1)** — long lengths + shipping. **Mitigation:** buy cut-to-length from a local Pampanga metal supplier instead of shipping full bars.

> [!tip] Cheaper local alternatives
> - Reuse an existing laptop webcam instead of buying a USB camera (item 13).
> - Salvage 24V PSU from a scrapped 3D printer / CCTV supply (item 8).
> - Buy fasteners loose by weight at a Manila hardware surplus rather than kits (item 16).
